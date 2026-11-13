"""F4 — Análise: camada de agregados (A01..A22).

Escopo analítico (SPEC §6): material, **não regulado** e **não pandemia**.
Pandemia e regulação entram como diagnósticos separados (visão comparativa e lista EVITAR).

Todos os números saem daqui; o painel consome apenas `panel_data.json`, gerado destes agregados.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from .. import paths
from ..config import load_config
from ..logging_utils import RunLog, write_json

# escopo analítico padrão (material, não regulado, não pandemia)
ESC = "(NOT is_regulado) AND (NOT is_pandemia)"


def conectar() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("SET threads TO 4")
    con.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{paths.TREATED_PARQUET.as_posix()}')")
    return con


def q(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.execute(sql).fetch_df()


def _escrever(df: pd.DataFrame, nome: str, log: RunLog) -> dict[str, Any]:
    """Grava o agregado com ordenação total, para que duas execuções gerem bytes idênticos.

    O DuckDB não garante ordem em agregações multi-thread e vários ORDER BY da análise têm
    empates (ex.: duas famílias com o mesmo valor). Ordenar por todas as colunas elimina
    a dependência da ordem de produção — requisito do teste A1.
    """
    if len(df):
        df = df.sort_values(by=list(df.columns), kind="mergesort", na_position="last").reset_index(drop=True)
    destino = paths.AGGREGATES / f"{nome}.parquet"
    df.to_parquet(destino, index=False, compression="snappy")
    h = hashlib.sha256(destino.read_bytes()).hexdigest()
    tam = destino.stat().st_size / 1024
    log(f"  [ok] {nome}.parquet  linhas={len(df):>7,}  {tam:>9.1f} KB")
    return {"arquivo": f"{nome}.parquet", "linhas": len(df), "kb": round(tam, 1), "sha256": h}


# ---------------------------------------------------------------------------------
# Agregados
# ---------------------------------------------------------------------------------

SQL: dict[str, str] = {}


SQL["agg_familia_ano"] = f"""
SELECT familia_key,
       min(familia_catalogo)                       AS familia_catalogo,
       ano,
       count(*)                                    AS linhas,
       count(DISTINCT afm_aps)                     AS afms,
       count(DISTINCT ug_key)                      AS ugs,
       count(DISTINCT fornecedor_id)               AS fornecedores,
       round(sum(valor_total_nominal), 2)          AS valor_nominal,
       round(sum(valor_total_real), 2)             AS valor_real
FROM t WHERE {ESC}
GROUP BY familia_key, ano
ORDER BY familia_key, ano
"""

SQL["agg_sazonalidade"] = f"""
SELECT familia_key, mes,
       round(sum(valor_total_real) / 5.0, 2) AS valor_medio_real,
       count(*) AS linhas
FROM t WHERE {ESC}
GROUP BY familia_key, mes
ORDER BY familia_key, mes
"""

SQL["agg_orgao_familia"] = f"""
SELECT secretaria_key,
       min(secretaria)                                      AS secretaria,
       familia_key,
       ano,
       count(*)                                             AS linhas,
       round(sum(valor_total_real), 2)                      AS valor_real,
       round(sum(valor_total_nominal), 2)                   AS valor_nominal,
       round(sum(valor_total_real) FILTER (WHERE is_dispensa), 2) AS valor_dispensa_real,
       round(sum(valor_total_real) FILTER (WHERE is_dispensa)
             / nullif(sum(valor_total_real), 0), 4)         AS share_dispensa
FROM t WHERE {ESC}
GROUP BY secretaria_key, familia_key, ano
ORDER BY valor_real DESC
"""

SQL["agg_canal_familia"] = f"""
SELECT familia_key, canal, ano,
       count(*)                          AS linhas,
       round(sum(valor_total_real), 2)   AS valor_real,
       round(sum(valor_total_nominal), 2) AS valor_nominal,
       round(median(valor_total_real), 2) AS ticket_mediano
FROM t WHERE {ESC}
GROUP BY familia_key, canal, ano
ORDER BY familia_key, canal, ano
"""

SQL["agg_ticket_afm"] = f"""
WITH afm AS (
  SELECT familia_key, afm_aps, ano,
         sum(valor_total_real)    AS v_real,
         sum(valor_total_nominal) AS v_nom
  FROM t WHERE {ESC}
  GROUP BY 1,2,3
)
SELECT familia_key,
       count(*)                                                   AS n_afm,
       round(quantile_cont(v_real, 0.25), 2)                      AS ticket_p25,
       round(median(v_real), 2)                                   AS ticket_p50,
       round(quantile_cont(v_real, 0.75), 2)                      AS ticket_p75,
       round(quantile_cont(v_real, 0.95), 2)                      AS ticket_p95,
       round(avg(CASE WHEN v_real <= 65492.11 THEN 1 ELSE 0 END), 4) AS pct_afm_ate_teto,
       round(avg(CASE
              WHEN ano <= 2023 AND v_nom <= 50000.00 THEN 1
              WHEN ano = 2024 AND v_nom <= 59906.02 THEN 1
              WHEN ano = 2025 AND v_nom <= 62725.59 THEN 1
              ELSE 0 END), 4)                                     AS pct_afm_ate_teto_hist
FROM afm GROUP BY 1 ORDER BY 1
"""

SQL["agg_recorrencia"] = f"""
WITH base AS (
  SELECT familia_key, ano_mes, ug_key, data, afm_aps
  FROM t WHERE {ESC}
),
meses AS (
  SELECT familia_key, count(DISTINCT ano_mes) AS meses_com_compra
  FROM base GROUP BY 1
),
por_ug AS (
  SELECT familia_key, ug_key, data,
         date_diff('day', lag(data) OVER (PARTITION BY familia_key, ug_key ORDER BY data), data) AS intervalo
  FROM (SELECT DISTINCT familia_key, ug_key, data FROM base)
),
inter AS (
  SELECT familia_key, median(intervalo) AS med_ug
  FROM por_ug WHERE intervalo IS NOT NULL GROUP BY 1, ug_key
)
SELECT m.familia_key, m.meses_com_compra,
       round(m.meses_com_compra / 60.0, 4)          AS recorrencia,
       round(median(i.med_ug), 1)                   AS intervalo_mediano_dias
FROM meses m LEFT JOIN inter i USING (familia_key)
GROUP BY 1,2,3
"""

SQL["agg_concorrencia"] = f"""
WITH f AS (
  SELECT familia_key, ano, fornecedor_id, sum(valor_total_real) AS v
  FROM t WHERE {ESC} AND NOT is_pf AND cnpj14 IS NOT NULL
  GROUP BY 1,2,3
),
s AS (
  SELECT familia_key, ano, fornecedor_id, v,
         v / nullif(sum(v) OVER (PARTITION BY familia_key, ano), 0) AS share,
         row_number() OVER (PARTITION BY familia_key, ano ORDER BY v DESC) AS rn
  FROM f
)
SELECT familia_key, ano,
       count(*)                                        AS n_fornecedores,
       round(sum(share*share) * 10000, 2)              AS hhi,
       round(sum(share) FILTER (WHERE rn <= 3), 4)     AS share_top3,
       round(max(share), 4)                            AS share_maior
FROM s GROUP BY 1,2 ORDER BY 1,2
"""

SQL["agg_fornecedor_familia"] = f"""
SELECT familia_key, fornecedor_id,
       min(razao_social)                AS razao_social,
       min(uf_fornecedor_norm)          AS uf,
       min(categoria)                   AS categoria,
       ano,
       count(*)                         AS linhas,
       count(DISTINCT afm_aps)          AS afms,
       round(sum(valor_total_real), 2)  AS valor_real
FROM t WHERE {ESC} AND NOT is_pf AND cnpj14 IS NOT NULL
GROUP BY familia_key, fornecedor_id, ano
ORDER BY valor_real DESC
"""

SQL["agg_entrantes"] = f"""
WITH primeira AS (
  SELECT fornecedor_id, min(ano) AS ano_primeira
  FROM t WHERE NOT is_pf AND cnpj14 IS NOT NULL
  GROUP BY 1
),
ativos AS (
  SELECT familia_key, ano, count(DISTINCT fornecedor_id) AS ativos
  FROM t WHERE {ESC} AND NOT is_pf AND cnpj14 IS NOT NULL
  GROUP BY 1,2
),
novos AS (
  SELECT t.familia_key, t.ano, count(DISTINCT t.fornecedor_id) AS novos
  FROM t JOIN primeira p USING (fornecedor_id)
  WHERE {ESC} AND NOT t.is_pf AND t.cnpj14 IS NOT NULL
    AND p.ano_primeira = t.ano AND t.ano >= 2022
  GROUP BY 1,2
)
SELECT a.familia_key, a.ano, a.ativos, coalesce(n.novos, 0) AS novos,
       round(coalesce(n.novos, 0) / nullif(a.ativos, 0), 4) AS pct_novos
FROM ativos a LEFT JOIN novos n USING (familia_key, ano)
ORDER BY 1,2
"""

SQL["agg_preco_item"] = f"""
SELECT familia_key, item_key,
       min(nome_basico)                          AS nome_basico,
       min(um)                                   AS um,
       ano,
       count(*)                                  AS linhas,
       round(median(valor_unitario_real), 4)     AS preco_mediano,
       round(quantile_cont(valor_unitario_real, 0.25), 4) AS preco_p25,
       round(quantile_cont(valor_unitario_real, 0.75), 4) AS preco_p75,
       round(median(valor_unitario), 4)          AS preco_mediano_nom,
       round(quantile_cont(valor_unitario, 0.25), 4) AS preco_p25_nom,
       round(quantile_cont(valor_unitario, 0.75), 4) AS preco_p75_nom,
       round(stddev_samp(valor_unitario_real), 4) AS preco_dp
FROM t WHERE {ESC} AND valor_unitario_real > 0
GROUP BY familia_key, item_key, ano
ORDER BY familia_key, item_key, ano
"""

SQL["agg_desconto"] = f"""
SELECT familia_key, ano,
       count(*) FILTER (WHERE valor_estimado_real > 0)          AS n_comparaveis,
       round(median(1 - valor_unitario_real / nullif(valor_estimado_real, 0))
             FILTER (WHERE valor_estimado_real > 0), 4)          AS desconto_mediano
FROM t WHERE {ESC}
GROUP BY 1,2 ORDER BY 1,2
"""

SQL["agg_regiao_familia"] = f"""
SELECT familia_key, regiao_key, regiao_raio, ano,
       count(*)                          AS linhas,
       round(sum(valor_total_real), 2)   AS valor_real,
       round(sum(valor_total_nominal), 2) AS valor_nominal
FROM t WHERE {ESC}
GROUP BY 1,2,3,4 ORDER BY 1,4,6 DESC
"""

SQL["agg_prazo"] = f"""
SELECT familia_key,
       count(*) FILTER (WHERE prazo_entrega_dias IS NOT NULL) AS n_com_prazo,
       round(median(prazo_entrega_dias), 1)                   AS prazo_mediano,
       round(quantile_cont(prazo_entrega_dias, 0.9), 1)       AS prazo_p90,
       round(avg(CASE WHEN prazo_entrega_dias <= 30 THEN 1 ELSE 0 END), 4) AS pct_ate_30d
FROM t WHERE {ESC}
GROUP BY 1 ORDER BY 1
"""

SQL["agg_municipio"] = f"""
SELECT familia_key, municipio_key, min(municipio_local_entrega) AS municipio, regiao_raio,
       count(*)                        AS linhas,
       round(sum(valor_total_real), 2) AS valor_real
FROM t WHERE {ESC}
GROUP BY 1,2,4
ORDER BY valor_real DESC
"""

SQL["agg_pandemia"] = """
SELECT familia_key, ano, is_pandemia,
       count(*) AS linhas, round(sum(valor_total_real), 2) AS valor_real
FROM t
GROUP BY 1,2,3 ORDER BY 1,2,3
"""

SQL["agg_regulados"] = """
SELECT familia_key, min(familia_catalogo) AS familia_catalogo,
       count(*) AS linhas,
       count(DISTINCT afm_aps) AS afms,
       count(DISTINCT fornecedor_id) AS fornecedores,
       round(sum(valor_total_real), 2) AS valor_real,
       round(100.0 * sum(valor_total_real)
             / (SELECT sum(valor_total_real) FROM t), 2) AS pct_valor_total
FROM t WHERE is_regulado
GROUP BY 1 ORDER BY valor_real DESC
"""

SQL["agg_ug_periodo"] = f"""
SELECT familia_key, ug_key, min(ug_fiplan) AS ug_fiplan, min(secretaria) AS secretaria,
       min(regiao_key)                         AS regiao_key,
       count(DISTINCT afm_aps)                 AS afms,
       round(sum(valor_total_real), 2)         AS valor_real,
       round(sum(valor_total_real) FILTER (WHERE is_dispensa)
             / nullif(sum(valor_total_real), 0), 4) AS share_dispensa,
       round(median(valor_total_real), 2)      AS ticket_mediano
FROM t WHERE {ESC}
GROUP BY 1,2 ORDER BY valor_real DESC
"""


def _construir_metricas(con: duckdb.DuckDBPyConnection, cfg) -> pd.DataFrame:  # noqa: ANN001
    """A04 — junta todas as métricas de §6 em uma linha por família."""
    familia_ano = q(con, SQL["agg_familia_ano"])
    ticket = q(con, SQL["agg_ticket_afm"])
    rec = q(con, SQL["agg_recorrencia"])
    conc = q(con, SQL["agg_concorrencia"])
    prazo = q(con, SQL["agg_prazo"])
    desc = q(con, SQL["agg_desconto"])

    # base por família a partir da série anual
    piv_real = familia_ano.pivot(index="familia_key", columns="ano", values="valor_real").fillna(0.0)
    piv_real.columns = [f"valor_{c}_real" for c in piv_real.columns]
    label = familia_ano.groupby("familia_key")["familia_catalogo"].first()

    base = pd.DataFrame(index=piv_real.index)
    for a in cfg.anos:
        base[f"valor_{a}_real"] = piv_real.get(f"valor_{a}_real", 0.0)

    # demanda e tendência
    base["valor_total_real"] = base[[f"valor_{a}_real" for a in cfg.anos]].sum(axis=1)
    base["valor_2024_2025_real"] = base[["valor_2024_real", "valor_2025_real"]].mean(axis=1)
    v21, v25 = base["valor_2021_real"], base["valor_2025_real"]
    cagr = pd.Series(index=base.index, dtype="float64")
    ok = (v21 > 0) & (v25 > 0)
    cagr.loc[ok] = (v25[ok] / v21[ok]) ** (1 / 4) - 1
    base["cagr_real"] = cagr

    yoy = {}
    for a, anterior in zip(cfg.anos[1:], cfg.anos[:-1], strict=True):
        yoy[f"yoy_{a}"] = (base[f"valor_{a}_real"] / base[f"valor_{anterior}_real"].replace(0, pd.NA)) - 1
    for k, v in yoy.items():
        base[k] = v
    ult2 = [f"yoy_{a}" for a in cfg.anos[-2:]]
    pos = base[ult2].gt(0).all(axis=1)
    neg = base[ult2].lt(0).all(axis=1)
    base["dir_2_ultimos"] = 0
    base.loc[pos, "dir_2_ultimos"] = 1
    base.loc[neg, "dir_2_ultimos"] = -1

    # contagens
    cnt = familia_ano.groupby("familia_key").agg(
        linhas=("linhas", "sum"),
        afms=("afms", "sum"),
        ugs=("ugs", "max"),
        fornecedores=("fornecedores", "max"),
    )
    base = base.join(cnt)

    # ticket
    base = base.join(ticket.set_index("familia_key"), how="left")
    # recorrência
    base = base.join(rec.set_index("familia_key"), how="left")
    # concorrência no período (recalculada sobre o total, não a média dos anos)
    conc_periodo = q(
        con,
        f"""
        WITH f AS (
          SELECT familia_key, fornecedor_id, sum(valor_total_real) AS v
          FROM t WHERE {ESC} AND NOT is_pf AND cnpj14 IS NOT NULL
          GROUP BY 1,2
        ),
        s AS (
          SELECT familia_key, fornecedor_id, v,
                 v / nullif(sum(v) OVER (PARTITION BY familia_key), 0) AS share,
                 row_number() OVER (PARTITION BY familia_key ORDER BY v DESC) AS rn
          FROM f
        )
        SELECT familia_key, count(*) AS n_fornecedores,
               round(sum(share*share)*10000, 2) AS hhi,
               round(sum(share) FILTER (WHERE rn <= 3), 4) AS share_top3,
               round(max(share), 4) AS share_maior
        FROM s GROUP BY 1
        """,
    )
    base = base.join(conc_periodo.set_index("familia_key"), how="left")
    # entrantes (média do % de novos em 2022-2025)
    ent = q(con, "SELECT familia_key, avg(pct_novos) AS pct_novos_medio FROM (" + SQL["agg_entrantes"] + ") GROUP BY 1")
    base = base.join(ent.set_index("familia_key"), how="left")
    # preço: CV mediano dos itens com >= min_linhas
    min_linhas = int(cfg.get("metricas.min_linhas_para_cv"))
    cv = q(
        con,
        f"""
        WITH it AS (
          SELECT familia_key, item_key, count(*) AS n,
                 stddev_samp(valor_unitario_real) AS dp, avg(valor_unitario_real) AS media
          FROM t WHERE {ESC} AND valor_unitario_real > 0
          GROUP BY 1,2
        )
        SELECT familia_key,
               round(median(CASE WHEN media > 0 THEN dp / media END), 4) AS cv_mediano,
               count(DISTINCT item_key) FILTER (WHERE n >= {min_linhas}) AS itens_analisados
        FROM it GROUP BY 1
        """,
    )
    base = base.join(cv.set_index("familia_key"), how="left")
    base = base.join(desc.groupby("familia_key")["desconto_mediano"].median().rename("desconto_mediano"), how="left")
    # prazo
    base = base.join(prazo.set_index("familia_key"), how="left")
    # logística: share do valor no raio
    raio = q(
        con,
        f"""
        SELECT familia_key,
               round(sum(valor_total_real) FILTER (WHERE regiao_raio = 'dentro')
                     / nullif(sum(valor_total_real), 0), 4) AS pct_valor_no_raio,
               count(DISTINCT municipio_key) AS n_municipios
        FROM t WHERE {ESC} GROUP BY 1
        """,
    )
    base = base.join(raio.set_index("familia_key"), how="left")
    # canal
    canal = q(
        con,
        f"""
        SELECT familia_key,
               round(sum(valor_total_real) FILTER (WHERE is_dispensa)
                     / nullif(sum(valor_total_real), 0), 4) AS share_dispensa,
               round(sum(valor_total_real) FILTER (WHERE is_pce)
                     / nullif(sum(valor_total_real), 0), 4) AS share_pce,
               round(sum(valor_total_real) FILTER (WHERE is_via_ata)
                     / nullif(sum(valor_total_real), 0), 4) AS share_ata
        FROM t WHERE {ESC} GROUP BY 1
        """,
    )
    base = base.join(canal.set_index("familia_key"), how="left")
    # compradores
    comp = q(
        con,
        f"""
        WITH s AS (
          SELECT familia_key, secretaria_key, sum(valor_total_real) AS v
          FROM t WHERE {ESC} GROUP BY 1,2
        )
        SELECT familia_key, count(*) AS n_secretarias,
               round(max(v) / nullif(sum(v), 0), 4) AS concentracao_maior_comprador
        FROM s GROUP BY 1
        """,
    )
    base = base.join(comp.set_index("familia_key"), how="left")

    # diagnósticos sobre o universo material completo (inclui regulado/pandemia)
    diag = q(
        con,
        """
        SELECT familia_key,
               round(sum(valor_total_real) FILTER (WHERE is_pandemia)
                     / nullif(sum(valor_total_real), 0), 4) AS dependencia_pandemia,
               round(sum(valor_total_real) FILTER (WHERE is_regulado)
                     / nullif(sum(valor_total_real), 0), 4) AS share_regulado,
               round(sum(valor_total_real), 2) AS valor_total_material
        FROM t GROUP BY 1
        """,
    )
    base = base.join(diag.set_index("familia_key"), how="left")

    base["familia_catalogo"] = label
    base["familia_key"] = base.index

    # fit dispensa
    p50 = cfg.get("score.composicao.fit_dispensa.peso_pct_ate_teto")
    p50b = cfg.get("score.composicao.fit_dispensa.peso_share_dispensa")
    base["fit_dispensa_raw"] = (
        p50 * base["pct_afm_ate_teto"].fillna(0) + p50b * base["share_dispensa"].fillna(0)
    )

    # elegibilidade
    min_afm = int(cfg.get("metricas.minimo_afm_para_ranking"))
    min_val = float(cfg.get("metricas.minimo_valor_real_para_ranking"))
    base["elegivel"] = (base["afms"] >= min_afm) & (base["valor_total_real"] >= min_val) & (
        base["share_regulado"].fillna(0) < 0.5
    )
    motivo = pd.Series("", index=base.index, dtype="object")
    motivo[base["afms"] < min_afm] = "menos de %d AFM/APS" % min_afm
    motivo[(base["afms"] >= min_afm) & (base["valor_total_real"] < min_val)] = "valor abaixo de R$ 1 mi"
    motivo[base["share_regulado"].fillna(0) >= 0.5] = "família regulada (EVITAR)"
    base["motivo_exclusao"] = motivo

    return base.reset_index(drop=True)


def run(log: RunLog) -> dict[str, Any]:
    paths.ensure_dirs()
    log.section("F4 — ANÁLISE (AGREGADOS)")
    cfg = load_config()
    con = conectar()
    meta: dict[str, Any] = {"gerado_em": datetime.now(UTC).isoformat(), "agregados": {}}

    escopo = q(
        con,
        f"""
        SELECT count(*) AS linhas, count(DISTINCT familia_key) AS familias,
               count(DISTINCT fornecedor_id) AS fornecedores,
               round(sum(valor_total_real), 2) AS valor_real
        FROM t WHERE {ESC}
        """,
    ).iloc[0].to_dict()
    log(
        f"escopo analítico (material, não regulado, não pandemia): {escopo['linhas']:,} linhas | "
        f"{escopo['familias']} famílias | R$ {escopo['valor_real']:,.2f}"
    )
    meta["escopo_analitico"] = {k: (int(v) if k != "valor_real" else float(v)) for k, v in escopo.items()}

    log("\nagregados:")
    for nome, sql in SQL.items():
        df = q(con, sql)
        meta["agregados"][nome] = _escrever(df, nome, log)

    log("\nmontando métricas por família (A04)...")
    metricas = _construir_metricas(con, cfg)
    meta["agregados"]["agg_familia_metricas"] = _escrever(metricas, "agg_familia_metricas", log)
    log(
        f"  elegíveis para ranking: {int(metricas['elegivel'].sum())} de {len(metricas)} famílias "
        f"(≥{cfg.get('metricas.minimo_afm_para_ranking')} AFM e ≥R$ 1 mi)"
    )

    # participação e ranking (A02) a partir das métricas
    periodo = metricas[["familia_key", "familia_catalogo", "valor_total_real", "linhas", "afms", "ugs", "fornecedores"]].copy()
    total = periodo["valor_total_real"].sum()
    periodo["share_valor"] = (periodo["valor_total_real"] / total if total else 0).round(6)
    periodo = periodo.sort_values("valor_total_real", ascending=False).reset_index(drop=True)
    periodo["rank_valor"] = periodo.index + 1
    meta["agregados"]["agg_familia_periodo"] = _escrever(periodo, "agg_familia_periodo", log)

    # tendência (A03)
    tend = metricas[
        ["familia_key", "familia_catalogo", "cagr_real", "dir_2_ultimos"]
        + [f"valor_{a}_real" for a in cfg.anos]
        + [f"yoy_{a}" for a in cfg.anos[1:]]
    ].copy()
    meta["agregados"]["agg_familia_tendencia"] = _escrever(tend, "agg_familia_tendencia", log)

    # dispersão de preço por família (A17)
    disp = metricas[["familia_key", "familia_catalogo", "cv_mediano", "itens_analisados", "desconto_mediano"]].copy()
    disp["amplitude_ratio"] = (
        metricas["ticket_p75"] / metricas["ticket_p25"].replace(0, pd.NA)
    ).round(2)
    meta["agregados"]["agg_preco_dispersao"] = _escrever(disp, "agg_preco_dispersao", log)

    # qualidade / conservação (A22)
    trat = paths.META / "tratamento.json"
    import json as _json

    conserv = _json.loads(trat.read_text(encoding="utf-8")) if trat.exists() else {}
    qual = pd.DataFrame(conserv.get("conservacao", []))
    meta["agregados"]["agg_qualidade"] = _escrever(qual, "agg_qualidade", log)

    con.close()
    meta["total_agregados"] = len(meta["agregados"])
    write_json(paths.META / "analise.json", meta)
    log(f"\n[ok] {len(meta['agregados'])} agregados em data/aggregates/")
    return meta
