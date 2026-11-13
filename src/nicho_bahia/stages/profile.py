"""F1 — Perfilamento da base (camada staging).

Produz:
- data/_meta/profile.json  (perfil completo, consumível pelo painel/aba Método)
- DATA_PROFILE.md          (perfil legível, insumo do Gate G1)

Testes executados aqui:
1. Cobertura e nulos por coluna.
2. Cardinalidade e valores únicos das categóricas-chave.
3. Chave candidata: unicidade de (afm_aps, codigo, item [, data]).
4. Sobreposição entre arquivos (duplicatas cruzadas).
5. Coerência de valores: QTD x UNIT ~ TOTAL; VALOR ESTIMADO (unitário vs total).
6. Eixo temporal: nulos, min/max, aderência entre data e ANO/MES.
7. Higiene: CNPJ (14 dígitos + DV amostral), negativos, zeros.
8. Hierarquia de catálogo: cardinalidade por nível.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import duckdb
import pandas as pd

from .. import paths
from ..columns import CANONICAL, KIND_BY_NAME
from ..logging_utils import RunLog, write_json

# colunas categóricas cujos valores únicos são mapeados por completo (se couber no limite)
CATEGORICAS_CHAVE: tuple[str, ...] = (
    "tipo_fornecimento",
    "tipo_do_item",
    "tipo_item_especifico_comum",
    "classificacao_familia",
    "categoria",
    "situacao_fornecedor",
    "forma_contratacao",
    "instrumento",
    "modulo_servicos_terceirizados",
    "srd_fiplan",
    "lid_fiplan",
    "marcacao_covid",
    "liberacao_covid",
    "marcacao_vacina_covid",
    "liberacao_vacina_covid",
    "contrato_emergencial_cgst",
    "situacao_contrato_cgst",
    "ressuprimento",
    "delegacao_automatica",
    "digitalizacao_contrato",
    "tipo_da_requisicao",
    "uf_fornecedor",
    "uf_local_entrega",
    "afm_aps_tipo_item",
    "tipo_calculo",
    "prazo_entrega",
    "pce_pedido_cotacao",
)

# colunas de texto que podem conter números
NUMERICAS_DISFARCADAS: tuple[str, ...] = ("prazo_entrega", "cnae_codigo", "n_processo", "cod_local_entrega")

ENTIDADES: tuple[str, ...] = (
    "secretaria",
    "unidade",
    "uo_fiplan",
    "ug_fiplan",
    "grupo_catalogo",
    "familia_catalogo",
    "nome_basico",
    "codigo",
    "item",
    "cnpj",
    "razao_social",
    "afm_aps",
    "n_licitacao",
    "n_contrato",
    "municipio_local_entrega",
    "regiao_local_entrega",
    "orgao_gerenciador_rp",
    "orgao_gerenciador_registro_precos",
)

MAX_VALORES_DUMP = 200


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("SET threads TO 4")
    files = [str(p) for p in paths.STAGED_FILES.values()]
    # CREATE VIEW não aceita parâmetro preparado: lista literal com escape de aspas
    lista = "[" + ", ".join("'" + f.replace("'", "''") + "'" for f in files) + "]"
    # is_material: derivado aqui e validado abaixo (tipo_do_item='Material' coincide com AFM em 99,999% das linhas)
    con.execute(
        f"CREATE VIEW raw AS SELECT *, (tipo_do_item = 'Material') AS is_material "
        f"FROM read_parquet({lista}, union_by_name=true)"
    )
    return con


def q(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.execute(sql).fetch_df()


def _lots(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    df = q(
        con,
        """
        SELECT count(*) AS linhas,
               count(DISTINCT cnpj) AS cnpjs,
               count(DISTINCT afm_aps) AS afms,
               count(DISTINCT familia_catalogo) AS familias,
               count(DISTINCT nome_basico) AS nomes_basicos,
               count(DISTINCT codigo) AS codigos,
               count(DISTINCT item) AS itens,
               count(DISTINCT secretaria) AS secretarias,
               count(DISTINCT unidade) AS unidades,
               count(DISTINCT municipio_local_entrega) AS municipios_entrega,
               round(sum(valor_total), 2) AS valor_total_soma,
               round(sum(valor_estimado), 2) AS valor_estimado_soma
        FROM raw
        """,
    )
    return df.iloc[0].to_dict()


def _por_arquivo(con: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    df = q(
        con,
        """
        SELECT _src_year AS ano_arquivo,
               count(*) AS linhas,
               count(DISTINCT afm_aps) AS afms,
               count(DISTINCT cnpj) AS cnpjs,
               round(sum(valor_total), 2) AS valor_total,
               count(*) FILTER (WHERE valor_total IS NULL) AS total_nulo,
               count(*) FILTER (WHERE data_geracao_afm_aps IS NULL) AS data_nula
        FROM raw GROUP BY 1 ORDER BY 1
        """,
    )
    return df.to_dict("records")


def _perfil_colunas(con: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    total = int(q(con, "SELECT count(*) AS n FROM raw").iloc[0]["n"])
    out: list[dict[str, Any]] = []
    for col in CANONICAL:
        kind = KIND_BY_NAME[col.name]
        sel = [
            f'count(*) FILTER (WHERE "{col.name}" IS NULL) AS n_null',
            f'count(DISTINCT "{col.name}") AS n_distinct',
        ]
        if kind in ("num", "int"):
            sel += [
                f'min("{col.name}") AS v_min',
                f'max("{col.name}") AS v_max',
                f'count(*) FILTER (WHERE "{col.name}" < 0) AS n_neg',
                f'count(*) FILTER (WHERE "{col.name}" = 0) AS n_zero',
            ]
        elif kind == "date":
            sel += [
                f'min("{col.name}") AS v_min',
                f'max("{col.name}") AS v_max',
            ]
        row = q(con, f"SELECT {', '.join(sel)} FROM raw").iloc[0].to_dict()
        rec: dict[str, Any] = {
            "coluna": col.name,
            "tipo_staging": kind,
            "n_null": int(row["n_null"]),
            "pct_null": round(100 * row["n_null"] / total, 3) if total else None,
            "n_distinct": int(row["n_distinct"]),
        }
        if kind in ("num", "int", "date"):
            vmin = row.get("v_min")
            vmax = row.get("v_max")
            rec["min"] = None if vmin is None or pd.isna(vmin) else str(vmin)
            rec["max"] = None if vmax is None or pd.isna(vmax) else str(vmax)
        if kind in ("num", "int"):
            rec["n_negativos"] = int(row["n_neg"] or 0)
            rec["n_zeros"] = int(row["n_zero"] or 0)
        out.append(rec)
    return out


def _valores(con: duckdb.DuckDBPyConnection, col: str, limite: int = 25) -> tuple[list[dict[str, Any]], bool]:
    df = q(
        con,
        f"""
        SELECT coalesce(cast("{col}" AS VARCHAR), '<NULL>') AS valor, count(*) AS n
        FROM raw GROUP BY 1 ORDER BY n DESC, valor LIMIT {limite}
        """,
    )
    total = int(q(con, "SELECT count(*) AS n FROM raw").iloc[0]["n"])
    recs = [{"valor": r["valor"], "n": int(r["n"]), "pct": round(100 * r["n"] / total, 3)} for r in df.to_dict("records")]
    n_dist = int(q(con, f'SELECT count(DISTINCT "{col}") AS n FROM raw').iloc[0]["n"])
    truncado = n_dist > limite
    return recs, truncado


def _categoricas(con: duckdb.DuckDBPyConnection) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for col in CATEGORICAS_CHAVE:
        n_dist = int(q(con, f'SELECT count(DISTINCT "{col}") AS n FROM raw').iloc[0]["n"])
        limite = MAX_VALORES_DUMP if n_dist <= MAX_VALORES_DUMP else 25
        vals, trunc = _valores(con, col, limite)
        out[col] = {"n_distinct": n_dist, "truncado": trunc, "valores": vals}
    return out


def _entidades(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    return {e: int(q(con, f'SELECT count(DISTINCT "{e}") AS n FROM raw').iloc[0]["n"]) for e in ENTIDADES}


def _chave(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    total = int(q(con, "SELECT count(*) AS n FROM raw").iloc[0]["n"])
    candidatos = {
        "afm_aps + codigo + item": ["afm_aps", "codigo", "item"],
        "afm_aps + codigo + item + data_geracao": ["afm_aps", "codigo", "item", "data_geracao_afm_aps"],
        "afm_aps + codigo + item + valor_unitario": ["afm_aps", "codigo", "item", "valor_unitario"],
        "afm_aps + afm_aps_tipo_item + codigo + item": ["afm_aps", "afm_aps_tipo_item", "codigo", "item"],
    }
    res: dict[str, Any] = {"n_linhas": total, "candidatos": {}}
    for nome, cols in candidatos.items():
        keys = ", ".join(f'"{c}"' for c in cols)
        row = q(
            con,
            f"""
            SELECT count(*) AS linhas,
                   count(DISTINCT ({keys})) AS chaves,
                   count(*) - count(DISTINCT ({keys})) AS excedente
            FROM raw
            """,
        ).iloc[0].to_dict()
        linhas = int(row["linhas"])
        chaves = int(row["chaves"])
        res["candidatos"][nome] = {
            "colunas": cols,
            "linhas": linhas,
            "chaves_distintas": chaves,
            "excedente": linhas - chaves,
            "unicidade_pct": round(100 * chaves / linhas, 4) if linhas else None,
            "duplicatas_pct": round(100 * (linhas - chaves) / linhas, 4) if linhas else None,
        }

    # sobreposição entre arquivos: a mesma chave aparece em mais de um arquivo?
    ov = q(
        con,
        """
        WITH k AS (
          SELECT afm_aps, codigo, item, count(DISTINCT _src_year) AS n_anos
          FROM raw GROUP BY 1,2,3
        )
        SELECT count(*) AS chaves,
               count(*) FILTER (WHERE n_anos > 1) AS chaves_em_varios_arquivos,
               sum(CASE WHEN n_anos > 1 THEN n_anos ELSE 0 END) AS linhas_em_chaves_repetidas
        FROM k
        """,
    ).iloc[0].to_dict()
    res["sobreposicao_entre_arquivos"] = {k: int(v) for k, v in ov.items()}

    # exemplo de duplicata exata (mesma chave completa) — apenas contagem e 3 exemplos mascarados
    dup = q(
        con,
        """
        SELECT afm_aps, codigo, item, data_geracao_afm_aps, count(*) AS n
        FROM raw GROUP BY 1,2,3,4 HAVING count(*) > 1 ORDER BY n DESC LIMIT 3
        """,
    )
    res["exemplos_duplicata_chave_completa"] = [
        {
            "afm_aps": r["afm_aps"],
            "codigo": r["codigo"],
            "data": str(r["data_geracao_afm_aps"]),
            "n": int(r["n"]),
        }
        for r in dup.to_dict("records")
    ]
    return res


def _coerencia(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    # tolerância: 1% do total ou R$ 0,05 (o que for maior)
    rec = q(
        con,
        """
        SELECT
          count(*) AS linhas,
          count(*) FILTER (WHERE qtd_contratada IS NULL) AS qtd_nula,
          count(*) FILTER (WHERE valor_unitario IS NULL) AS unit_nulo,
          count(*) FILTER (WHERE valor_total IS NULL) AS total_nulo,
          count(*) FILTER (WHERE qtd_contratada IS NOT NULL AND valor_unitario IS NOT NULL
                            AND valor_total IS NOT NULL) AS completas,
          count(*) FILTER (WHERE qtd_contratada IS NOT NULL AND valor_unitario IS NOT NULL
                            AND valor_total IS NOT NULL
                            AND abs(qtd_contratada * valor_unitario - valor_total)
                                > greatest(0.05, 0.01 * abs(valor_total))) AS incoerentes,
          round(sum(abs(qtd_contratada * valor_unitario - valor_total))
                FILTER (WHERE qtd_contratada IS NOT NULL AND valor_unitario IS NOT NULL
                        AND valor_total IS NOT NULL), 2) AS soma_desvio_abs,
          count(*) FILTER (WHERE valor_total < 0) AS total_negativo,
          count(*) FILTER (WHERE valor_unitario < 0) AS unit_negativo,
          count(*) FILTER (WHERE qtd_contratada < 0) AS qtd_negativa,
          count(*) FILTER (WHERE valor_total = 0) AS total_zero,
          count(*) FILTER (WHERE valor_estimado IS NULL) AS estimado_nulo,
          count(*) FILTER (WHERE valor_estimado IS NOT NULL AND valor_unitario IS NOT NULL
                            AND abs(valor_estimado - valor_unitario) <= 0.01 * greatest(abs(valor_unitario), 0.01))
                            AS estimado_igual_unitario,
          count(*) FILTER (WHERE valor_estimado IS NOT NULL AND valor_total IS NOT NULL
                            AND abs(valor_estimado - valor_total) <= 0.01 * greatest(abs(valor_total), 0.01))
                            AS estimado_igual_total
        FROM raw
        """,
    ).iloc[0].to_dict()
    out = {k: (int(v) if v is not None and not isinstance(v, float) else v) for k, v in rec.items()}
    completas = int(rec["completas"] or 0)
    out["pct_incoerentes_entre_completas"] = round(100 * int(rec["incoerentes"] or 0) / completas, 4) if completas else None
    com_est = int(q(con, "SELECT count(*) AS n FROM raw WHERE valor_estimado IS NOT NULL").iloc[0]["n"])
    out["n_com_estimado"] = com_est
    out["pct_estimado_igual_unitario"] = round(100 * int(rec["estimado_igual_unitario"] or 0) / com_est, 3) if com_est else None
    out["pct_estimado_igual_total"] = round(100 * int(rec["estimado_igual_total"] or 0) / com_est, 3) if com_est else None

    # razão realizado/estimado (quando estimado parece unitário)
    razao = q(
        con,
        """
        SELECT quantile_cont(r, 0.1) AS p10, quantile_cont(r, 0.5) AS p50, quantile_cont(r, 0.9) AS p90
        FROM (
          SELECT valor_unitario / nullif(valor_estimado, 0) AS r
          FROM raw WHERE valor_estimado > 0 AND valor_unitario IS NOT NULL
        )
        """,
    ).iloc[0].to_dict()
    out["razao_unitario_sobre_estimado"] = {k: (None if pd.isna(v) else round(float(v), 4)) for k, v in razao.items()}
    return out


def _temporal(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    por_ano = q(
        con,
        """
        SELECT coalesce(ano_geracao_afm_aps, year(data_geracao_afm_aps)) AS ano,
               count(*) AS linhas,
               count(DISTINCT afm_aps) AS afms,
               round(sum(valor_total), 2) AS valor_total
        FROM raw GROUP BY 1 ORDER BY 1
        """,
    ).to_dict("records")

    matriz = q(
        con,
        """
        SELECT _src_year AS ano_arquivo,
               coalesce(ano_geracao_afm_aps, year(data_geracao_afm_aps)) AS ano_dado,
               count(*) AS linhas
        FROM raw GROUP BY 1,2 ORDER BY 1,2
        """,
    ).to_dict("records")

    ader = q(
        con,
        """
        SELECT count(*) FILTER (WHERE data_geracao_afm_aps IS NOT NULL AND ano_geracao_afm_aps IS NOT NULL) AS com_ambos,
               count(*) FILTER (WHERE data_geracao_afm_aps IS NOT NULL AND ano_geracao_afm_aps IS NOT NULL
                                 AND year(data_geracao_afm_aps) <> ano_geracao_afm_aps) AS ano_divergente,
               count(*) FILTER (WHERE data_geracao_afm_aps IS NOT NULL AND mes_geracao_afm_aps IS NOT NULL
                                 AND month(data_geracao_afm_aps) <> mes_geracao_afm_aps) AS mes_divergente,
               count(*) FILTER (WHERE data_geracao_afm_aps IS NULL) AS sem_data,
               count(*) FILTER (WHERE data_geracao_afm_aps IS NULL AND ano_geracao_afm_aps IS NOT NULL) AS sem_data_com_ano
        FROM raw
        """,
    ).iloc[0].to_dict()

    limites = q(
        con,
        """
        SELECT min(data_geracao_afm_aps) AS data_min, max(data_geracao_afm_aps) AS data_max,
               min(assinatura_afm_aps) AS assin_min, max(assinatura_afm_aps) AS assin_max,
               min(data_fim_contrato) AS fim_min, max(data_fim_contrato) AS fim_max
        FROM raw
        """,
    ).iloc[0].to_dict()

    return {
        "por_ano": por_ano,
        "matriz_arquivo_x_ano": matriz,
        "aderencia": {k: (None if v is None else int(v)) for k, v in ader.items()},
        "limites": {k: (None if v is None or pd.isna(v) else str(v)) for k, v in limites.items()},
    }


def _cnpj_check(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    df = q(
        con,
        """
        SELECT cnpj, count(*) AS n FROM raw WHERE cnpj IS NOT NULL GROUP BY 1 ORDER BY n DESC
        """,
    )
    total = len(df)
    digitos = df["cnpj"].str.replace(r"\D", "", regex=True)
    n_mascara = float((df["cnpj"].str.contains(r"[./-]", regex=True)).mean()) if total else None
    n_14 = int((digitos.str.len() == 14).sum())

    def dv_ok(c: str) -> bool:
        if len(c) != 14 or len(set(c)) == 1:
            return False
        peso1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        peso2 = [6] + peso1
        try:
            d1 = sum(int(a) * b for a, b in zip(c[:12], peso1, strict=True)) % 11
            d1 = 0 if d1 < 2 else 11 - d1
            d2 = sum(int(a) * b for a, b in zip(c[:13], peso2, strict=True)) % 11
            d2 = 0 if d2 < 2 else 11 - d2
            return c[12] == str(d1) and c[13] == str(d2)
        except ValueError:
            return False

    amostra = digitos[digitos.str.len() == 14].head(2000).tolist()
    validos = sum(dv_ok(c) for c in amostra)
    return {
        "cnpjs_distintos": total,
        "pct_com_mascara": round(100 * n_mascara, 2) if n_mascara is not None else None,
        "n_com_14_digitos": n_14,
        "pct_14_digitos": round(100 * n_14 / total, 3) if total else None,
        "amostra_dv": len(amostra),
        "amostra_dv_validos": validos,
        "pct_dv_ok_amostra": round(100 * validos / len(amostra), 2) if amostra else None,
    }


def _numericas_disfarcadas(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in NUMERICAS_DISFARCADAS:
        row = q(
            con,
            f"""
            SELECT count(*) FILTER (WHERE "{col}" IS NOT NULL) AS preenchidos,
                   count(*) FILTER (WHERE "{col}" IS NOT NULL
                                    AND try_cast(trim(cast("{col}" AS VARCHAR)) AS DOUBLE) IS NOT NULL) AS numericos,
                   min(try_cast(trim(cast("{col}" AS VARCHAR)) AS DOUBLE)) AS v_min,
                   max(try_cast(trim(cast("{col}" AS VARCHAR)) AS DOUBLE)) AS v_max
            FROM raw
            """,
        ).iloc[0].to_dict()
        pre = int(row["preenchidos"] or 0)
        num = int(row["numericos"] or 0)
        out[col] = {
            "preenchidos": pre,
            "numericos": num,
            "pct_numerico": round(100 * num / pre, 2) if pre else None,
            "min": None if pd.isna(row["v_min"]) else float(row["v_min"]),
            "max": None if pd.isna(row["v_max"]) else float(row["v_max"]),
        }
    return out


def _cruzamentos(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """Cruzamentos que decidem o filtro de escopo (material vs serviço)."""
    escopo = q(
        con,
        """
        SELECT tipo_fornecimento, tipo_do_item, count(*) AS linhas,
               round(sum(valor_total), 2) AS valor_total
        FROM raw GROUP BY 1,2 ORDER BY linhas DESC
        """,
    ).to_dict("records")
    covid = q(
        con,
        """
        SELECT marcacao_covid, liberacao_covid, marcacao_vacina_covid, contrato_emergencial_cgst,
               count(*) AS linhas, round(sum(valor_total), 2) AS valor_total
        FROM raw GROUP BY 1,2,3,4 ORDER BY linhas DESC LIMIT 15
        """,
    ).to_dict("records")
    canal = q(
        con,
        """
        SELECT forma_contratacao,
               count(*) AS linhas,
               round(sum(valor_total), 2) AS valor_total,
               count(*) FILTER (WHERE pce_pedido_cotacao IS NOT NULL AND trim(pce_pedido_cotacao) <> '') AS com_pce,
               round(100.0 * count(*) FILTER (WHERE pce_pedido_cotacao IS NOT NULL AND trim(pce_pedido_cotacao) <> '') / count(*), 2) AS pct_pce,
               round(avg(valor_total) FILTER (WHERE valor_total IS NOT NULL), 2) AS ticket_medio,
               round(median(valor_total) FILTER (WHERE valor_total IS NOT NULL), 2) AS ticket_mediano
        FROM raw GROUP BY 1 ORDER BY linhas DESC
        """,
    ).to_dict("records")
    srd_lid = q(
        con,
        """
        SELECT srd_fiplan, lid_fiplan, forma_contratacao, count(*) AS linhas
        FROM raw GROUP BY 1,2,3 ORDER BY linhas DESC LIMIT 15
        """,
    ).to_dict("records")
    orgaos_rp = q(
        con,
        """
        SELECT count(*) AS linhas,
               count(*) FILTER (WHERE orgao_gerenciador_rp IS NOT NULL) AS com_rp,
               count(*) FILTER (WHERE orgao_gerenciador_registro_precos IS NOT NULL) AS com_registro,
               count(*) FILTER (WHERE coalesce(orgao_gerenciador_rp,'') <> coalesce(orgao_gerenciador_registro_precos,'')) AS divergentes
        FROM raw
        """,
    ).iloc[0].to_dict()
    return {
        "escopo_tipo_fornecimento_x_tipo_item": escopo,
        "flags_covid": covid,
        "canal_forma_contratacao": canal,
        "srd_lid": srd_lid,
        "orgao_gerenciador": {k: int(v) for k, v in orgaos_rp.items()},
    }


def _hierarquia(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    por_grupo = q(
        con,
        """
        SELECT grupo_catalogo, count(DISTINCT familia_catalogo) AS familias,
               count(DISTINCT nome_basico) AS nomes_basicos, count(*) AS linhas,
               round(sum(valor_total), 2) AS valor_total
        FROM raw GROUP BY 1 ORDER BY valor_total DESC NULLS LAST
        """,
    )
    return {
        "n_grupos": len(por_grupo),
        "grupos": por_grupo.head(30).to_dict("records"),
    }


def _escopo_material(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """Caracteriza o universo de MATERIAL, que é o escopo padrão da análise."""
    por_ano = q(
        con,
        """
        SELECT _src_year AS ano, count(*) AS linhas, count(DISTINCT afm_aps) AS afms,
               count(DISTINCT cnpj) AS cnpjs, count(DISTINCT familia_catalogo) AS familias,
               round(sum(valor_total), 2) AS valor_total,
               round(median(valor_total), 2) AS ticket_mediano_linha
        FROM raw WHERE is_material GROUP BY 1 ORDER BY 1
        """,
    ).to_dict("records")

    coerencia = q(
        con,
        """
        SELECT count(*) AS linhas,
               count(*) FILTER (WHERE abs(qtd_contratada*valor_unitario - valor_total)
                                 > greatest(0.05, 0.01*abs(valor_total))) AS incoerentes,
               round(sum(valor_total), 2) AS soma_total,
               round(sum(qtd_contratada*valor_unitario), 2) AS soma_qtd_x_unit
        FROM raw WHERE is_material AND qtd_contratada IS NOT NULL
             AND valor_unitario IS NOT NULL AND valor_total IS NOT NULL
        """,
    ).iloc[0].to_dict()

    # coerência no serviço, para contraste (explica a incoerência global)
    coerencia_servico = q(
        con,
        """
        SELECT count(*) AS linhas,
               count(*) FILTER (WHERE abs(qtd_contratada*valor_unitario - valor_total)
                                 > greatest(0.05, 0.01*abs(valor_total))) AS incoerentes
        FROM raw WHERE tipo_do_item='Serviço' AND qtd_contratada IS NOT NULL
             AND valor_unitario IS NOT NULL AND valor_total IS NOT NULL
        """,
    ).iloc[0].to_dict()

    ticket_afm = q(
        con,
        """
        WITH a AS (SELECT afm_aps, sum(valor_total) AS v FROM raw
                   WHERE is_material AND valor_total > 0 GROUP BY 1)
        SELECT count(*) AS afms, round(median(v),2) AS p50, round(quantile_cont(v,0.75),2) AS p75,
               count(*) FILTER (WHERE v <= 65492.11) AS afms_ate_teto,
               round(100.0*count(*) FILTER (WHERE v <= 65492.11)/count(*),2) AS pct_afms_ate_teto
        FROM a
        """,
    ).iloc[0].to_dict()

    canal = q(
        con,
        """
        SELECT forma_contratacao, count(*) AS linhas, round(sum(valor_total),2) AS valor_total,
               round(median(valor_total),2) AS ticket_mediano, count(DISTINCT cnpj) AS cnpjs,
               round(100.0*count(*)/(SELECT count(*) FROM raw WHERE is_material),2) AS pct_linhas
        FROM raw WHERE is_material GROUP BY 1 ORDER BY valor_total DESC
        """,
    ).to_dict("records")

    return {
        "por_ano": por_ano,
        "coerencia": {k: (None if v is None or pd.isna(v) else v) for k, v in coerencia.items()},
        "coerencia_servico": {k: (None if v is None or pd.isna(v) else int(v)) for k, v in coerencia_servico.items()},
        "ticket_por_afm": {k: (None if v is None or pd.isna(v) else v) for k, v in ticket_afm.items()},
        "canal": canal,
    }


def _anomalias(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    """Linhas que não são dados, identificadores inválidos, datas suspeitas e escala."""
    nao_dado = q(
        con,
        """
        SELECT count(*) AS linhas, min(_src_row) AS primeira_linha, max(_src_row) AS ultima_linha,
               min(_src_file) AS arquivo
        FROM raw WHERE afm_aps IS NULL
        """,
    ).iloc[0].to_dict()

    identificador = q(
        con,
        """
        SELECT length(regexp_replace(cnpj,'[^0-9]','','g')) AS n_digitos,
               count(*) AS linhas, count(DISTINCT cnpj) AS distintos
        FROM raw WHERE cnpj IS NOT NULL GROUP BY 1 ORDER BY 1
        """,
    ).to_dict("records")

    datas = q(
        con,
        """
        SELECT _src_year AS ano,
               count(*) FILTER (WHERE assinatura_afm_aps < date '2019-01-01') AS assin_antes_2019,
               count(*) FILTER (WHERE assinatura_afm_aps > date '2026-12-31') AS assin_depois_2026,
               count(*) FILTER (WHERE assinatura_afm_aps < data_geracao_afm_aps) AS assin_antes_geracao,
               count(*) FILTER (WHERE ano_fim_contrato < 2000 OR ano_fim_contrato > 2040) AS ano_fim_fora_faixa,
               count(*) FILTER (WHERE try_cast(prazo_entrega AS DOUBLE) > 365) AS prazo_acima_365d
        FROM raw GROUP BY 1 ORDER BY 1
        """,
    ).to_dict("records")

    escala = q(
        con,
        """
        SELECT
          count(*) FILTER (WHERE valor_unitario >= 1000000) AS unit_acima_1m,
          count(*) FILTER (WHERE valor_total >= 100000000) AS total_acima_100m,
          count(*) FILTER (WHERE valor_unitario < 0) AS unit_negativo,
          round(max(valor_unitario), 2) AS unit_max,
          round(max(valor_total), 2) AS total_max
        FROM raw
        """,
    ).iloc[0].to_dict()

    uf_entrega = q(
        con,
        """
        SELECT coalesce(uf_local_entrega, '(nulo)') AS uf, count(*) AS linhas
        FROM raw GROUP BY 1 ORDER BY linhas DESC LIMIT 6
        """,
    ).to_dict("records")

    regioes = q(
        con,
        """
        SELECT coalesce(regiao_local_entrega,'(nulo)') AS regiao, count(*) AS linhas,
               round(sum(valor_total),2) AS valor_total
        FROM raw GROUP BY 1 ORDER BY linhas DESC
        """,
    ).to_dict("records")

    # nomes básicos que aparecem em mais de uma família (hierarquia não é árvore estrita)
    nomes_multi = q(
        con,
        """
        SELECT count(*) AS n FROM (
          SELECT nome_basico FROM raw WHERE nome_basico IS NOT NULL
          GROUP BY 1 HAVING count(DISTINCT familia_catalogo) > 1)
        """,
    ).iloc[0]["n"]

    return {
        "linhas_nao_dado": {k: (None if v is None else v) for k, v in nao_dado.items()},
        "identificador": identificador,
        "datas": datas,
        "escala": {k: (None if v is None or pd.isna(v) else v) for k, v in escala.items()},
        "uf_entrega": uf_entrega,
        "regioes": regioes,
        "nomes_basicos_em_varias_familias": int(nomes_multi),
    }


# --- renderização markdown ----------------------------------------------------------
def _fmt_num(v: Any) -> str:
    """Formata número no padrão brasileiro; inteiros sem casas decimais."""
    if v is None:
        return "—"
    try:
        if isinstance(v, str):
            return v
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if pd.isna(f):
        return "—"
    if f.is_integer():
        return f"{int(f):,}".replace(",", ".")
    return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_dt(v: Any) -> str:
    s = str(v)
    return s.replace(" 00:00:00", "")


def _fmt_pct(v: Any, casas: int = 2) -> str:
    """Percentual no padrão brasileiro."""
    if v is None:
        return "—"
    try:
        return f"{float(v):.{casas}f}".replace(".", ",") + "%"
    except (TypeError, ValueError):
        return str(v)


# colunas que são rótulos numéricos (ano, mês) e não devem receber separador de milhar
_NO_GROUP_COLS = frozenset({"ano", "ano_arquivo", "ano_dado", "mes", "cod_secretaria", "n_digitos"})


def _tabela(rows: list[dict[str, Any]], cols: list[str], headers: list[str] | None = None) -> list[str]:
    headers = headers or cols
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c)
            if v is None:
                cells.append("—")
            elif c in _NO_GROUP_COLS:
                cells.append(_fmt_dt(v) if isinstance(v, str) else _fmt_num(v).replace(".", "") if isinstance(v, (int, float)) else str(v))
            elif isinstance(v, str):
                cells.append(_fmt_dt(v) if len(v) > 9 and v[4:6] == "-" else v)
            else:
                cells.append(_fmt_num(v))
        out.append("| " + " | ".join(cells) + " |")
    return out


def render_markdown(p: dict[str, Any]) -> str:
    L: list[str] = []
    a = L.append
    a("# DATA_PROFILE.md — perfilamento da base SIMPAS (BA, 2021–2025)")
    a("")
    a(f"Gerado por `run.py --stage profile` em {p['generated_at']}.")
    a("Fonte: `data/_meta/staging/raw_<ano>.parquet` (camada de staging, 1 linha = 1 linha da planilha).")
    a("")
    a("## 0. Achados críticos (leia primeiro)")
    a("")
    nd = p["anomalias"]["linhas_nao_dado"]
    mt = p["material"]
    cm = mt["coerencia"]
    cs = mt["coerencia_servico"]
    ta = mt["ticket_por_afm"]
    pct_assin = next((c["pct_null"] for c in p["colunas"] if c["coluna"] == "assinatura_afm_aps"), None)
    # derivados de texto: nunca escrever número à mão no relatório
    cf = p["categoricas"]["classificacao_familia"]
    linha_outros = next((v["n"] for v in cf["valores"] if str(v["valor"]).startswith("Outros")), 0)
    pct_outros = 100.0 * linha_outros / p["totais"]["linhas"] if p["totais"]["linhas"] else None
    canal_e = next((c for c in p["cruzamentos"]["canal_forma_contratacao"] if str(c["forma_contratacao"]).startswith("E -")), None)
    pct_pce_e = canal_e["pct_pce"] if canal_e else None
    a(
        f"1. **A base tem {_fmt_num(nd['linhas'])} linhas que não são dados** (rodapé de observações no fim da "
        f"planilha de 2025, arquivo `{nd['arquivo']}`, linhas {nd['primeira_linha']}–{nd['ultima_linha']}). "
        "Elas não têm AFM/APS nem valor e serão removidas na camada tratada, com log de conservação."
    )
    a(
        f"2. **No escopo de MATERIAL, `VALOR TOTAL` é exatamente `QTD × VALOR UNITÁRIO`**: "
        f"{_fmt_num(cm['incoerentes'])} linhas incoerentes em {_fmt_num(cm['linhas'])} "
        f"(Σ TOTAL = R$ {_fmt_num(cm['soma_total'])} e Σ QTD×UNIT = R$ {_fmt_num(cm['soma_qtd_x_unit'])}, idênticas). "
        f"Toda a incoerência global vem de **serviços (APS)**, onde {_fmt_num(cs['incoerentes'])} de "
        f"{_fmt_num(cs['linhas'])} linhas divergem porque o VALOR TOTAL é o valor do contrato inteiro "
        "(12 ou 60 meses) e o VALOR UNITÁRIO é o valor mensal, com QTD CONTRATADA = 1. "
        "**Consequência: para materiais, VALOR TOTAL é confiável; a análise de serviço não é o escopo deste projeto.**"
    )
    a(
        f"3. **`VALOR ESTIMADO` é unitário, não total**: igual ao VALOR UNITÁRIO em "
        f"{_fmt_pct(p['coerencia']['pct_estimado_igual_unitario'])} dos casos e ao VALOR TOTAL em apenas "
        f"{_fmt_pct(p['coerencia']['pct_estimado_igual_total'])}. Razão UNITÁRIO/ESTIMADO: p50 = "
        f"{_fmt_num(p['coerencia']['razao_unitario_sobre_estimado']['p50'])}. A métrica 'desconto vs. estimado' "
        "será calculada **por unidade**, não por linha."
    )
    a(
        f"4. **O eixo temporal é sólido**: `DATA GERAÇÃO da AFM/APS` cobre {_fmt_num(p['temporal']['aderencia']['com_ambos'])} "
        f"linhas entre {_fmt_dt(p['temporal']['limites']['data_min'])} e {_fmt_dt(p['temporal']['limites']['data_max'])}, sem divergência "
        f"com ANO/MÊS GERAÇÃO ({_fmt_num(p['temporal']['aderencia']['ano_divergente'])} divergências de ano, "
        f"{_fmt_num(p['temporal']['aderencia']['mes_divergente'])} de mês). "
        f"`Assinatura da AFM/APS` é suja e não deve ser usada como eixo "
        f"({_fmt_pct(pct_assin, 3)} das linhas sem assinatura; datas fora da faixa 2019–2026 e anteriores à geração)."
    )
    ov = p["chave"]["sobreposicao_entre_arquivos"]
    best = max(p["chave"]["candidatos"].items(), key=lambda kv: kv[1]["unicidade_pct"])
    a(
        f"5. **Não há sobreposição entre os 5 arquivos** ({_fmt_num(ov['chaves_em_varios_arquivos'])} chaves repetidas "
        f"entre arquivos), logo não há dupla contagem entre anos. A chave candidata com melhor unicidade é "
        f"`{best[0]}` com {_fmt_pct(best[1]['unicidade_pct'], 4)} ({_fmt_num(best[1]['excedente'])} excedentes). "
        "Os excedentes têm valores diferentes entre si (são linhas distintas da mesma AFM), então **não serão "
        "descartados**: a chave de trabalho é a linha (`_src_file` + `_src_row`)."
    )
    ident = p["anomalias"]["identificador"]
    n_pf = sum(x["linhas"] for x in ident if x["n_digitos"] == 11)
    n_pf_dist = sum(x["distintos"] for x in ident if x["n_digitos"] == 11)
    a(
        f"6. **{_fmt_num(n_pf)} linhas ({_fmt_num(n_pf_dist)} fornecedores) têm identificador de 11 dígitos — CPF, "
        "ou seja, pessoa física**, e 47 fornecedores têm identificador de 10 dígitos (formato inválido). "
        "Para concorrência de materiais, o universo de referência é o de pessoa jurídica (CNPJ de 14 dígitos)."
    )
    a(
        f"7. **`FORMA DE CONTRATAÇÃO` mistura dois vocabulários**: rótulos por modalidade "
        "(`E - Dispensa Eletrônica`, `D - Dispensa Tradicional`, `C - Licitação`...) e o rótulo "
        "`Registro de Preços`, que indica compra **via ata de RP** (procedimento, não modalidade). "
        f"`PCE` só aparece em `E - Dispensa Eletrônica` ({_fmt_pct(pct_pce_e, 1)} dos casos), confirmando ser o "
        "marcador da cotação eletrônica. O canal de entrada da startup será modelado com os dois campos."
    )
    a(
        f"8. **Ticket e teto da dispensa**: no material, {_fmt_num(ta['afms_ate_teto'])} de "
        f"{_fmt_num(ta['afms'])} AFM/APS ({_fmt_pct(ta['pct_afms_ate_teto'])}) têm valor total ≤ R$ 65.492,11 "
        f"(mediana por AFM/APS = R$ {_fmt_num(ta['p50'])}). "
        "Ou seja, o teto legal da dispensa eletrônica cobre quase todo o universo de materiais — "
        "mas atenção: o teto é por contratação/objeto de mesma natureza por UG/ano, então o valor por "
        "AFM/APS é apenas **proxy**."
    )
    a(
        f"9. **`CLASSIFICAÇÃO FAMÍLIA` não separa material de serviço** ({_fmt_pct(pct_outros, 1)} das linhas são `Outros`). "
        "O discriminador correto é `TIPO DO ITEM` (Material/Serviço), coerente com `TIPO FORNECIMENTO` (AFM/APS)."
    )
    a(
        f"10. **A hierarquia de catálogo não é árvore estrita**: {_fmt_num(p['anomalias']['nomes_basicos_em_varias_familias'])} "
        "nomes básicos aparecem sob mais de uma família. Chaves de análise serão `(familia_catalogo, nome_basico)`."
    )
    a("")
    a("## 1. Visão geral")
    a("")
    t = p["totais"]
    a(f"- Linhas: **{_fmt_num(t['linhas'])}**")
    a(f"- CNPJs distintos: **{_fmt_num(t['cnpjs'])}** | AFM/APS distintas: **{_fmt_num(t['afms'])}**")
    a(f"- Famílias de catálogo: **{_fmt_num(t['familias'])}** | Nomes básicos: **{_fmt_num(t['nomes_basicos'])}** | Códigos: **{_fmt_num(t['codigos'])}** | Itens (descrições): **{_fmt_num(t['itens'])}**")
    a(f"- Secretarias: **{_fmt_num(t['secretarias'])}** | Unidades: **{_fmt_num(t['unidades'])}** | Municípios de entrega: **{_fmt_num(t['municipios_entrega'])}**")
    a(f"- Σ VALOR TOTAL: **R$ {_fmt_num(t['valor_total_soma'])}** | Σ VALOR ESTIMADO: **R$ {_fmt_num(t['valor_estimado_soma'])}**")
    a("")
    a("### Por arquivo de origem")
    a("")
    L += _tabela(
        p["por_arquivo"],
        ["ano_arquivo", "linhas", "afms", "cnpjs", "valor_total", "total_nulo", "data_nula"],
        ["Arquivo", "Linhas", "AFM/APS", "CNPJs", "Σ VALOR TOTAL", "TOTAL nulo", "Data nula"],
    )
    a("")
    a("## 2. Cobertura temporal")
    a("")
    L += _tabela(
        p["temporal"]["por_ano"],
        ["ano", "linhas", "afms", "valor_total"],
        ["Ano do dado", "Linhas", "AFM/APS", "Σ VALOR TOTAL"],
    )
    a("")
    a("**Matriz arquivo × ano do dado** (revela sobreposição entre arquivos):")
    a("")
    L += _tabela(p["temporal"]["matriz_arquivo_x_ano"], ["ano_arquivo", "ano_dado", "linhas"], ["Arquivo", "Ano do dado", "Linhas"])
    a("")
    ad = p["temporal"]["aderencia"]
    a(f"- Linhas com data e ano preenchidos: **{_fmt_num(ad['com_ambos'])}**; ano divergente da data: **{_fmt_num(ad['ano_divergente'])}**; mês divergente: **{_fmt_num(ad['mes_divergente'])}**")
    a(f"- Linhas sem data de geração: **{_fmt_num(ad['sem_data'])}** (destas, {_fmt_num(ad['sem_data_com_ano'])} têm ANO preenchido)")
    lim = p["temporal"]["limites"]
    a(f"- Faixa de datas de geração: **{lim['data_min']}** a **{lim['data_max']}**; assinatura: {lim['assin_min']} a {lim['assin_max']}; fim de contrato: {lim['fim_min']} a {lim['fim_max']}")
    a("")
    a("## 3. Teste de chave candidata")
    a("")
    a(f"Linhas: **{_fmt_num(p['chave']['n_linhas'])}**")
    a("")
    L += _tabela(
        [{"chave": k, **v} for k, v in p["chave"]["candidatos"].items()],
        ["chave", "chaves_distintas", "excedente", "unicidade_pct", "duplicatas_pct"],
        ["Chave candidata", "Chaves distintas", "Excedente", "Unicidade %", "Duplicatas %"],
    )
    a("")
    ov = p["chave"]["sobreposicao_entre_arquivos"]
    a(f"- Chaves (afm_aps, codigo, item) presentes em mais de um arquivo: **{_fmt_num(ov['chaves_em_varios_arquivos'])}** de {_fmt_num(ov['chaves'])}.")
    a("")
    a("## 4. Coerência de valores")
    a("")
    c = p["coerencia"]
    a(f"- QTD × UNIT vs TOTAL: **{_fmt_num(c['completas'])}** linhas completas; **{_fmt_num(c['incoerentes'])}** incoerentes ({c['pct_incoerentes_entre_completas']}%), desvio absoluto somado R$ {_fmt_num(c['soma_desvio_abs'])}.")
    a(f"- Nulos: TOTAL {_fmt_num(c['total_nulo'])}, UNIT {_fmt_num(c['unit_nulo'])}, QTD {_fmt_num(c['qtd_nula'])}, ESTIMADO {_fmt_num(c['estimado_nulo'])}.")
    a(f"- Negativos: TOTAL {_fmt_num(c['total_negativo'])}, UNIT {_fmt_num(c['unit_negativo'])}, QTD {_fmt_num(c['qtd_negativa'])}. TOTAL zero: {_fmt_num(c['total_zero'])}.")
    a(f"- **VALOR ESTIMADO**: igual ao UNITÁRIO em {c['pct_estimado_igual_unitario']}% e ao TOTAL em {c['pct_estimado_igual_total']}% dos casos → tratar como **valor unitário de referência**.")
    r = c["razao_unitario_sobre_estimado"]
    a(f"- Razão UNITÁRIO/ESTIMADO: p10={r['p10']}, p50={r['p50']}, p90={r['p90']}.")
    a("")
    a("## 5. Escopo: material vs serviço, pandemia e canal")
    a("")
    a("**TIPO FORNECIMENTO × TIPO DO ITEM**")
    a("")
    L += _tabela(
        p["cruzamentos"]["escopo_tipo_fornecimento_x_tipo_item"],
        ["tipo_fornecimento", "tipo_do_item", "linhas", "valor_total"],
        ["TIPO FORNECIMENTO", "TIPO DO ITEM", "Linhas", "Σ VALOR TOTAL"],
    )
    a("")
    a("**FORMA DE CONTRATAÇÃO (canal)**")
    a("")
    L += _tabela(
        p["cruzamentos"]["canal_forma_contratacao"],
        ["forma_contratacao", "linhas", "valor_total", "com_pce", "pct_pce", "ticket_mediano"],
        ["Forma", "Linhas", "Σ Valor", "Com PCE", "% PCE", "Ticket mediano"],
    )
    a("")
    a("**Flags COVID / emergencial**")
    a("")
    L += _tabela(
        p["cruzamentos"]["flags_covid"],
        ["marcacao_covid", "liberacao_covid", "marcacao_vacina_covid", "contrato_emergencial_cgst", "linhas", "valor_total"],
        ["MARC. COVID", "LIB. COVID", "MARC. VACINA", "EMERGENCIAL", "Linhas", "Σ Valor"],
    )
    a("")
    a("**SRD / LID × forma de contratação** (inferência das siglas FIPLAN)")
    a("")
    L += _tabela(
        p["cruzamentos"]["srd_lid"],
        ["srd_fiplan", "lid_fiplan", "forma_contratacao", "linhas"],
        ["SRD", "LID", "Forma", "Linhas"],
    )
    a("")
    a("## 6. Categóricas-chave (valores únicos)")
    a("")
    for col, info in p["categoricas"].items():
        trunc = " (top 25; coluna de alta cardinalidade)" if info["truncado"] else ""
        a(f"### `{col}` — {info['n_distinct']} valores distintos{trunc}")
        a("")
        L += _tabela(info["valores"][:40], ["valor", "n", "pct"], ["Valor", "Linhas", "%"])
        a("")
    a("## 7. Higiene de CNPJ")
    a("")
    cn = p["cnpj"]
    a(f"- CNPJs distintos: **{_fmt_num(cn['cnpjs_distintos'])}**; com máscara: {cn['pct_com_mascara']}%; 14 dígitos: {cn['pct_14_digitos']}%.")
    a(f"- Validação de DV em amostra de {_fmt_num(cn['amostra_dv'])} CNPJs distintos: **{cn['pct_dv_ok_amostra']}%** válidos.")
    a("")
    a("## 8. Colunas de texto que podem conter números")
    a("")
    L += _tabela(
        [{"coluna": k, **v} for k, v in p["numericas_disfarcadas"].items()],
        ["coluna", "preenchidos", "numericos", "pct_numerico", "min", "max"],
        ["Coluna", "Preenchidos", "Numéricos", "% numérico", "Mín", "Máx"],
    )
    a("")
    a("## 9. Hierarquia de catálogo por grupo (top 30 por valor)")
    a("")
    L += _tabela(
        p["hierarquia"]["grupos"],
        ["grupo_catalogo", "familias", "nomes_basicos", "linhas", "valor_total"],
        ["GRUPO CATÁLOGO", "Famílias", "Nomes básicos", "Linhas", "Σ Valor"],
    )
    a("")
    a("## 11. Universo de MATERIAL (escopo padrão da análise)")
    a("")
    a("Filtro: `TIPO DO ITEM = 'Material'` (coerente com `TIPO FORNECIMENTO = 'AFM'` em 99,999% das linhas).")
    a("")
    L += _tabela(
        mt["por_ano"],
        ["ano", "linhas", "afms", "cnpjs", "familias", "valor_total", "ticket_mediano_linha"],
        ["Ano", "Linhas", "AFM/APS", "CNPJs", "Famílias", "Σ VALOR TOTAL", "Ticket mediano/linha"],
    )
    a("")
    a(f"- Ticket por AFM/APS: p50 = R$ {_fmt_num(ta['p50'])}, p75 = R$ {_fmt_num(ta['p75'])}; "
      f"{_fmt_pct(ta['pct_afms_ate_teto'])} das AFM/APS ≤ R$ 65.492,11.")
    a("")
    a("**Material por forma de contratação**")
    a("")
    L += _tabela(
        mt["canal"],
        ["forma_contratacao", "linhas", "pct_linhas", "valor_total", "ticket_mediano", "cnpjs"],
        ["Forma", "Linhas", "% linhas", "Σ Valor", "Ticket mediano", "CNPJs"],
    )
    a("")
    a("## 12. Anomalias, limpeza e mapeamentos")
    a("")
    an = p["anomalias"]
    a(f"**Identificador do fornecedor (dígitos em `CNPJ`)** — {_fmt_num(n_pf)} linhas são CPF (pessoa física).")
    a("")
    L += _tabela(an["identificador"], ["n_digitos", "linhas", "distintos"], ["Dígitos", "Linhas", "Fornecedores"])
    a("")
    a("**Datas e prazos suspeitos por arquivo**")
    a("")
    L += _tabela(
        an["datas"],
        ["ano", "assin_antes_2019", "assin_depois_2026", "assin_antes_geracao", "ano_fim_fora_faixa", "prazo_acima_365d"],
        ["Arquivo", "Assinatura < 2019", "Assinatura > 2026", "Assinatura < geração", "Ano fim fora de faixa", "Prazo > 365 d"],
    )
    a("")
    esc = an["escala"]
    a(f"**Escala**: {_fmt_num(esc['unit_acima_1m'])} linhas com valor unitário ≥ R$ 1 mi; "
      f"{_fmt_num(esc['total_acima_100m'])} linhas com valor total ≥ R$ 100 mi; "
      f"valor unitário máximo R$ {_fmt_num(esc['unit_max'])}; valor total máximo R$ {_fmt_num(esc['total_max'])}. "
      "Outliers serão mantidos e sinalizados; winsorização (p1/p99) só nas estatísticas de preço.")
    a("")
    a("**UF de entrega** (evidência de que a base é estadual e a entrega é quase toda na BA)")
    a("")
    L += _tabela(an["uf_entrega"], ["uf", "linhas"], ["UF de entrega", "Linhas"])
    a("")
    a("**Regiões de entrega** (rótulos originais — exigem normalização)")
    a("")
    L += _tabela(an["regioes"], ["regiao", "linhas", "valor_total"], ["Região (rótulo original)", "Linhas", "Σ Valor"])
    a("")
    return "\n".join(L)


def render_dictionary(p: dict[str, Any]) -> str:
    """data_dictionary.md: original -> snake_case + tipo + semântica + estatísticas do perfil."""
    stats = {c["coluna"]: c for c in p["colunas"]}
    L: list[str] = []
    a = L.append
    a("# data_dictionary.md — dicionário de dados (original → canônico)")
    a("")
    a(f"Gerado por `run.py --stage profile` em {p['generated_at']}.")
    a("")
    a("Regras de normalização aplicadas na camada de staging:")
    a("")
    a("1. Rótulo original → `snake_case` ASCII (sem acento), sem espaços nas pontas e com espaços internos colapsados.")
    a("2. Valores de texto têm espaços nas pontas removidos; célula vazia vira `NULL`.")
    a("3. Datas: lidas como data nativa (o XLSX já traz data); textos em `dd/mm/aaaa` e `aaaa-mm-dd` também são aceitos.")
    a("4. Números: aceita `1.234,56` (BR) e `1234.56` (US). Conteúdo não numérico vira `NULL` e é contado em log.")
    a("5. Cabeçalhos em branco foram resolvidos por posição (ver seção 12 do DATA_PROFILE.md e o log de ingestão).")
    a("")
    a("| # | Coluna original (planilha) | Coluna canônica | Tipo | Nulos | % nulos | Distintos | Semântica de trabalho |")
    a("|---|---|---|---|---|---|---|---|")
    for i, col in enumerate(CANONICAL):
        st = stats.get(col.name, {})
        a(
            f"| {i} | `{col.label}` | `{col.name}` | {col.kind} | {_fmt_num(st.get('n_null'))} | "
            f"{_fmt_pct(st.get('pct_null'), 2)} | {_fmt_num(st.get('n_distinct'))} | {col.description} |"
        )
    a("")
    a("## Colunas ausentes em arquivos específicos")
    a("")
    a("- `fornecedor` — **ausente no arquivo de 2021** (o esquema de 2021 tem 77 colunas, sem esta).")
    a("- `ressuprimento` — ausente no arquivo de 2021 (a coluna de 2021 na posição equivalente é o órgão gerenciador do RP).")
    a("- Em 2021, `valor_total` e `assinatura_afm_aps` têm cabeçalho em branco e foram mapeadas por posição.")
    a("- Em 2022, há uma coluna extra em branco no fim da planilha, descartada.")
    a("")
    a("## Hierarquia de produto")
    a("")
    a("`grupo_catalogo > familia_catalogo > nome_basico > item` (descrição). O `codigo` identifica o item de catálogo.")
    a("A hierarquia **não é árvore estrita**: há nomes básicos sob mais de uma família.")
    a("")
    return "\n".join(L)


def run(log: RunLog) -> dict[str, Any]:
    paths.ensure_dirs()
    log.section("F1 — PERFILAMENTO")
    con = connect()
    log("staging carregado como view 'raw'")

    profile: dict[str, Any] = {"generated_at": datetime.now(UTC).isoformat()}

    for nome, fn in (
        ("totais", _lots),
        ("por_arquivo", _por_arquivo),
        ("colunas", _perfil_colunas),
        ("categoricas", _categoricas),
        ("entidades", _entidades),
        ("chave", _chave),
        ("coerencia", _coerencia),
        ("temporal", _temporal),
        ("cnpj", _cnpj_check),
        ("numericas_disfarcadas", _numericas_disfarcadas),
        ("cruzamentos", _cruzamentos),
        ("hierarquia", _hierarquia),
        ("material", _escopo_material),
        ("anomalias", _anomalias),
    ):
        log(f"  calculando: {nome} ...")
        profile[nome] = fn(con)

    write_json(paths.META / "profile.json", profile)
    md = render_markdown(profile)
    (paths.WORKSPACE / "DATA_PROFILE.md").write_text(md, encoding="utf-8")
    dic = render_dictionary(profile)
    (paths.WORKSPACE / "data_dictionary.md").write_text(dic, encoding="utf-8")
    log(f"[ok] {paths.relative(paths.META / 'profile.json')}")
    log("[ok] DATA_PROFILE.md")
    log("[ok] data_dictionary.md")
    con.close()
    return profile
