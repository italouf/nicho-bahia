"""F3 — Tratamento: staging -> camada tratada (material, com flags e valores reais).

Regras (SPEC.md §3–§5):
- Escopo: TIPO DO ITEM = Material; remove rodapé (sem AFM/APS) e linhas sem data.
- Nenhuma linha é descartada em silêncio: cada passo grava linhas antes/depois e Δ de valor.
- Deflação por IPCA com convenção vinda do config.
- Flags: is_pandemia, is_regulado, is_pf, canal, is_dispensa, is_pce, is_via_ata, preco_outlier.

Saídas:
- data/treated/compras_tratadas.parquet
- logs/conservacao.log, logs/reconciliacao.json
- data/_meta/tratamento.json
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from .. import paths
from ..config import Config, load_config
from ..logging_utils import RunLog, write_json
from ..textops import deflator_fatores, normalize_key

# ---------------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------------

NORM_SQL = r"trim(regexp_replace(upper(strip_accents(coalesce({x}, ''))), '\s+', ' ', 'g'))"
DIGITS_SQL = r"regexp_replace(coalesce({x}, ''), '[^0-9]', '', 'g')"


def _norm(col: str) -> str:
    return NORM_SQL.format(x=col)


def _sql_str_list(valores: list[str]) -> str:
    """Lista literal SQL com escape de aspas simples."""
    return ", ".join("'" + str(v).replace("'", "''") + "'" for v in valores)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def conectar() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("SET threads TO 4")
    con.execute("SET preserve_insertion_order TO true")
    arquivos = [str(p) for p in paths.STAGED_FILES.values()]
    lista = "[" + ", ".join("'" + f.replace("'", "''") + "'" for f in arquivos) + "]"
    con.execute(f"CREATE VIEW staging AS SELECT * FROM read_parquet({lista}, union_by_name=true)")
    return con


def _criar_dim_deflator(con: duckdb.DuckDBPyConnection, cfg: Config) -> dict[int, float]:
    fatores = deflator_fatores(
        cfg.get("deflacao.ipca_ano_pct"),
        ano_base=int(cfg.get("meta.ano_base_deflacao")),
        convencao=str(cfg.get("deflacao.convencao")),
    )
    con.execute("CREATE TABLE dim_deflator (ano INTEGER, fator DOUBLE)")
    con.executemany("INSERT INTO dim_deflator VALUES (?, ?)", sorted(fatores.items()))
    return fatores


def _criar_dim_canal(con: duckdb.DuckDBPyConnection, cfg: Config) -> int:
    mapa: dict[str, str] = cfg.get("dispensa.mapa_canal")
    con.execute("CREATE TABLE dim_canal (rotulo VARCHAR, canal VARCHAR)")
    con.executemany("INSERT INTO dim_canal VALUES (?, ?)", sorted(mapa.items()))
    return len(mapa)


def _expressao_regulado(cfg: Config) -> str:
    """Monta a condição SQL de `is_regulado` a partir das famílias e keywords do config."""
    familias = [str(f).strip().upper() for f in cfg.get("regulados.familias")]
    keywords = [normalize_key(k) or "" for k in cfg.get("regulados.keywords")]
    partes: list[str] = []
    if familias:
        cond = " OR ".join(f"familia_key LIKE '{f}%'" for f in familias)
        partes.append(f"({cond})")
    alvos = [
        _norm("familia_catalogo"),
        _norm("nome_basico"),
    ]
    for kw in keywords:
        if not kw:
            continue
        cond = " OR ".join(f"{alvo} LIKE '%{kw}%'" for alvo in alvos)
        partes.append(f"({cond})")
    return " OR ".join(partes) if partes else "FALSE"


def _expressao_pandemia(cfg: Config) -> str:
    colunas = list(cfg.get("pandemia.colunas_flag")) + [cfg.get("pandemia.coluna_emergencial")]
    return " OR ".join(f"upper(trim(coalesce({c},''))) = 'SIM'" for c in colunas)


def _expressao_raio(cfg: Config) -> str:
    """classifica a região de entrega em dentro / indeferida / fora do raio de 200 km."""
    dentro = [normalize_key(r) for r in cfg.get("logistica.regioes_dentro_raio")]
    indef = [normalize_key(r) for r in cfg.get("logistica.regioes_indefinidas")]
    dentro_sql = _sql_str_list([d for d in dentro if d])
    indef_sql = _sql_str_list([d for d in indef if d])
    return (
        "CASE WHEN regiao_key IS NULL THEN 'indefinida' "
        f"WHEN regiao_key IN ({dentro_sql}) THEN 'dentro' "
        f"WHEN regiao_key IN ({indef_sql}) THEN 'indefinida' "
        "ELSE 'fora' END"
    )


# ---------------------------------------------------------------------------------
# Conservação
# ---------------------------------------------------------------------------------

def _conservacao(con: duckdb.DuckDBPyConnection, cfg: Config) -> list[dict[str, Any]]:
    """Conta linhas e valor em cada passo do pipeline de exclusão E0..E4."""
    pas = q_one(
        con,
        """
        SELECT count(*) AS linhas, round(sum(valor_total), 2) AS valor
        FROM staging
        """,
    )
    material_expr = f"tipo_do_item IN ({_sql_str_list(cfg.get('escopo.valores_material'))})"
    # serviço = tipo_do_item preenchido e diferente de material.
    # Linhas com tipo_do_item NULL (rodapé) NÃO são contadas aqui: em SQL, NOT (NULL IN (...)) é NULL.
    servico_expr = f"tipo_do_item IS NOT NULL AND NOT ({material_expr})"
    pas_servico = q_one(
        con,
        f"""
        SELECT count(*) AS linhas, round(sum(valor_total), 2) AS valor
        FROM staging WHERE {servico_expr}
        """,
    )
    pas_rodape = q_one(con, "SELECT count(*) AS linhas FROM staging WHERE afm_aps IS NULL")
    pas_sem_data = q_one(
        con,
        f"""
        SELECT count(*) AS linhas FROM staging
        WHERE {material_expr} AND afm_aps IS NOT NULL AND data_geracao_afm_aps IS NULL
        """,
    )
    pas_final = q_one(
        con,
        f"""
        SELECT count(*) AS linhas, round(sum(valor_total), 2) AS valor
        FROM staging
        WHERE {material_expr} AND afm_aps IS NOT NULL AND data_geracao_afm_aps IS NOT NULL
        """,
    )

    l0, v0 = int(pas["linhas"]), float(pas["valor"] or 0)
    l_serv, v_serv = int(pas_servico["linhas"]), float(pas_servico["valor"] or 0)
    l_rod = int(pas_rodape["linhas"])
    l_sem_data = int(pas_sem_data["linhas"])
    l4, v4 = int(pas_final["linhas"]), float(pas_final["valor"] or 0)

    return [
        {"passo": "E0", "descricao": "staging (todas as linhas)", "linhas": l0, "valor": v0, "delta_linhas": 0, "delta_valor": 0.0, "motivo": "base bruta tipada"},
        {"passo": "E1", "descricao": "remove serviço (TIPO DO ITEM ≠ Material)", "linhas": l_serv, "valor": v_serv, "delta_linhas": -l_serv, "delta_valor": -v_serv, "motivo": "escopo = material (G1/Q1)"},
        {"passo": "E2", "descricao": "remove rodapé (sem AFM/APS e sem tipo)", "linhas": l_rod, "valor": 0.0, "delta_linhas": -l_rod, "delta_valor": 0.0, "motivo": "4 linhas de observação no fim da planilha 2025"},
        {"passo": "E3", "descricao": "remove material sem data", "linhas": l_sem_data, "valor": 0.0, "delta_linhas": -l_sem_data, "delta_valor": 0.0, "motivo": "eixo temporal obrigatório"},
        {"passo": "E4", "descricao": "escopo tratado", "linhas": l4, "valor": v4, "delta_linhas": 0, "delta_valor": 0.0, "motivo": "entrada da análise"},
    ]


def q_one(con: duckdb.DuckDBPyConnection, sql: str) -> dict[str, Any]:
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    return dict(zip(cols, row, strict=True))


# ---------------------------------------------------------------------------------
# Construção da tabela tratada
# ---------------------------------------------------------------------------------

def _criar_tabela_tratada(con: duckdb.DuckDBPyConnection, cfg: Config) -> None:
    material_expr = f"tipo_do_item IN ({_sql_str_list(cfg.get('escopo.valores_material'))})"
    canais_dispensa = _sql_str_list(cfg.get("dispensa.canais_dispensa"))
    prazo_max = int(cfg.get("logistica.prazo_maximo_valido_dias"))

    cnpj_digits = DIGITS_SQL.format(x="cnpj")
    regiao_raio = _expressao_raio(cfg)

    con.execute(
        f"""
        CREATE TABLE base AS
        SELECT
          printf('%d:%d', _src_year, _src_row)            AS linha_id,
          _src_file, _src_sheet, _src_row, _src_year,
          -- identificação / órgão
          cod_secretaria, secretaria, unidade, uo_fiplan, ug_fiplan,
          {_norm('secretaria')}                           AS secretaria_key,
          {_norm('unidade')}                              AS unidade_key,
          {_norm('ug_fiplan')}                            AS ug_key,
          tipo_fornecimento, grupo_licitacao,
          grupo_catalogo, {_norm('grupo_catalogo')}       AS grupo_key,
          familia_catalogo, {_norm('familia_catalogo')}   AS familia_key,
          codigo, nome_basico, {_norm('nome_basico')}     AS nome_key,
          item, {_norm('item')}                           AS item_desc_key,
          tipo_item_especifico_comum, um, {_norm('um')}   AS um_key,
          tipo_do_item,
          -- quantidades e valores nominais
          qtd_contratada, tipo_calculo, valor_detalhe,
          valor_unitario, valor_total, valor_estimado,
          -- fornecedor
          cnpj,
          CASE WHEN length({cnpj_digits}) = 14 THEN {cnpj_digits} END AS cnpj14,
          length({cnpj_digits}) = 11                      AS is_pf,
          CASE WHEN length({cnpj_digits}) = 14 THEN {cnpj_digits}
               WHEN length({cnpj_digits}) = 11 THEN 'PF:' || {cnpj_digits}
               ELSE 'INVALIDO:' || coalesce(cnpj, 'SEM') END AS fornecedor_id,
          cnae_codigo, cnae_descricao, uf_receita, razao_social, nome_fantasia,
          coalesce(fornecedor, razao_social)              AS fornecedor,
          categoria, situacao_fornecedor,
          upper(trim(coalesce(uf_fornecedor, uf_receita))) AS uf_fornecedor_norm,
          -- canal
          forma_contratacao,
          coalesce(cm.canal, 'outros')                    AS canal,
          (cm.rotulo IS NOT NULL)                         AS canal_mapeado,
          n_licitacao, requisicao_rm_rs, dotacao, afm_aps, afm_aps_tipo_item,
          -- tempo
          data_geracao_afm_aps                            AS data,
          year(data_geracao_afm_aps)                      AS ano,
          month(data_geracao_afm_aps)                     AS mes,
          strftime(data_geracao_afm_aps, '%Y-%m')         AS ano_mes,
          assinatura_afm_aps,
          -- local de entrega
          cod_local_entrega, endereco_local_entrega, bairro_local_entrega,
          municipio_local_entrega, {_norm('municipio_local_entrega')} AS municipio_key,
          upper(trim(uf_local_entrega))                   AS uf_local_entrega_norm,
          regiao_local_entrega, {_norm('regiao_local_entrega')} AS regiao_key,
          {regiao_raio}                                   AS regiao_raio,
          regiao_principal_municipio, regiao_registro_precos,
          -- flags de exceção
          marcacao_covid, liberacao_covid, marcacao_vacina_covid, liberacao_vacina_covid,
          contrato_emergencial_cgst, situacao_contrato_cgst,
          ({_expressao_pandemia(cfg)})                    AS is_pandemia,
          -- demais campos originais preservados
          pce_pedido_cotacao,
          (pce_pedido_cotacao IS NOT NULL AND trim(pce_pedido_cotacao) <> '') AS is_pce,
          srd_fiplan, lid_fiplan, digitalizacao_contrato, classificacao_familia,
          situacao_fornecedor_lid, modulo_servicos_terceirizados, instrumento,
          unidade_licitante, tipo_da_requisicao, delegacao_automatica,
          ano_geracao_afm_aps, mes_geracao_afm_aps,
          n_processo, n_contrato,
          prazo_entrega,
          try_cast(try_cast(prazo_entrega AS DOUBLE) AS INTEGER) AS prazo_entrega_dias_bruto,
          CASE WHEN try_cast(prazo_entrega AS DOUBLE) BETWEEN 0 AND {prazo_max}
               THEN try_cast(try_cast(prazo_entrega AS DOUBLE) AS INTEGER) END AS prazo_entrega_dias,
          orgao_gerenciador_registro_precos, ressuprimento, orgao_gerenciador_rp,
          data_fim_contrato, ano_fim_contrato,
          aviso_edital_pncp, ata_rp_pncp, contratos_pncp
        FROM staging r
        LEFT JOIN dim_canal cm ON trim(r.forma_contratacao) = cm.rotulo
        WHERE {material_expr}
          AND r.afm_aps IS NOT NULL
          AND r.data_geracao_afm_aps IS NOT NULL
        """
    )

    # colunas dependentes de agregação/joins
    con.execute(
        f"""
        CREATE TABLE tratado AS
        SELECT
          b.*,
          (b.canal IN ({canais_dispensa}))                 AS is_dispensa,
          (b.canal = 'dispensa_eletronica')                AS is_dispensa_eletronica,
          (b.canal = 'registro_precos')                    AS is_via_ata,
          ({_expressao_regulado(cfg)})                     AS is_regulado,
          b.familia_key || '|' || b.nome_key               AS nome_item_key,
          b.familia_key || '|' || b.nome_key || '|' || b.um_key AS item_key,
          d.fator                                          AS deflator,
          b.valor_total                                    AS valor_total_nominal,
          round(b.valor_total * d.fator, 2)                AS valor_total_real,
          b.valor_unitario                                 AS valor_unitario_nominal,
          round(b.valor_unitario * d.fator, 6)             AS valor_unitario_real,
          b.valor_estimado                                 AS valor_estimado_nominal,
          round(b.valor_estimado * d.fator, 6)             AS valor_estimado_real
        FROM base b
        JOIN dim_deflator d ON d.ano = b.ano
        """
    )

    # outliers de preço por item (p1/p99) — sinaliza, NÃO remove
    con.execute(
        """
        CREATE OR REPLACE TABLE tratado AS
        SELECT
          t.*,
          coalesce(
            (t.valor_unitario_real < lim.p1 OR t.valor_unitario_real > lim.p99),
            false
          ) AS preco_outlier
        FROM tratado t
        LEFT JOIN (
          SELECT item_key,
                 quantile_cont(valor_unitario_real, 0.01) AS p1,
                 quantile_cont(valor_unitario_real, 0.99) AS p99
          FROM tratado
          WHERE valor_unitario_real IS NOT NULL AND valor_unitario_real > 0
          GROUP BY 1
        ) lim ON lim.item_key = t.item_key
        ORDER BY t.linha_id
        """
    )


def _estatisticas_tratado(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    total = q_one(con, "SELECT count(*) AS n FROM tratado")["n"]
    por_ano = con.execute(
        """
        SELECT ano, count(*) AS linhas, count(DISTINCT afm_aps) AS afms,
               count(DISTINCT fornecedor_id) AS fornecedores,
               round(sum(valor_total_nominal), 2) AS valor_nominal,
               round(sum(valor_total_real), 2) AS valor_real
        FROM tratado GROUP BY 1 ORDER BY 1
        """
    ).fetch_df()

    nulos = con.execute(
        """
        SELECT
          count(*) FILTER (WHERE data IS NULL) AS data_nula,
          count(*) FILTER (WHERE valor_total_real IS NULL) AS valor_real_nulo,
          count(*) FILTER (WHERE familia_key IS NULL) AS familia_nula,
          count(*) FILTER (WHERE item_key IS NULL) AS item_key_nula,
          count(*) FILTER (WHERE canal = 'outros') AS canal_outros,
          count(*) FILTER (WHERE is_regulado) AS regulados,
          count(*) FILTER (WHERE is_pandemia) AS pandemia,
          count(*) FILTER (WHERE is_pf) AS pessoa_fisica,
          count(*) FILTER (WHERE preco_outlier) AS preco_outlier,
          count(*) FILTER (WHERE prazo_entrega_dias IS NULL) AS prazo_invalido
        FROM tratado
        """
    ).fetch_df().iloc[0].to_dict()

    canal = con.execute(
        """
        SELECT canal, count(*) AS linhas, round(sum(valor_total_real), 2) AS valor_real
        FROM tratado GROUP BY 1 ORDER BY valor_real DESC
        """
    ).fetch_df().to_dict("records")

    return {
        "linhas": int(total),
        "por_ano": por_ano.to_dict("records"),
        "nulos_e_flags": {k: int(v) for k, v in nulos.items()},
        "canal": canal,
    }


# ---------------------------------------------------------------------------------
# Dicionário das colunas derivadas (vai para o data_dictionary.md e para o painel)
# ---------------------------------------------------------------------------------

COLUNAS_DERIVADAS: tuple[dict[str, str], ...] = (
    {"coluna": "linha_id", "tipo": "text", "descricao": "chave técnica única da linha (ano:linha da planilha)"},
    {"coluna": "data", "tipo": "date", "descricao": "data de geração da AFM/APS (eixo temporal)"},
    {"coluna": "ano / mes / ano_mes", "tipo": "int/text", "descricao": "partições temporais derivadas de data"},
    {"coluna": "secretaria_key / unidade_key / ug_key", "tipo": "text", "descricao": "chaves normalizadas (sem acento, caixa alta)"},
    {"coluna": "grupo_key / familia_key", "tipo": "text", "descricao": "chaves normalizadas da hierarquia de catálogo"},
    {"coluna": "nome_key / item_desc_key / um_key", "tipo": "text", "descricao": "chaves normalizadas de nome básico, descrição e unidade"},
    {"coluna": "item_key", "tipo": "text", "descricao": "familia|nome_basico|um normalizados — chave de comparação de preço"},
    {"coluna": "nome_item_key", "tipo": "text", "descricao": "familia|nome_basico normalizados"},
    {"coluna": "cnpj14", "tipo": "text", "descricao": "CNPJ com 14 dígitos; nulo para CPF/inválido"},
    {"coluna": "is_pf", "tipo": "bool", "descricao": "fornecedor pessoa física (CPF de 11 dígitos)"},
    {"coluna": "fornecedor_id", "tipo": "text", "descricao": "identidade do fornecedor (CNPJ, PF:CPF ou INVALIDO:...)"},
    {"coluna": "uf_fornecedor_norm", "tipo": "text", "descricao": "UF do fornecedor em caixa alta"},
    {"coluna": "canal", "tipo": "text", "descricao": "canal normalizado a partir de FORMA DE CONTRATAÇÃO (SPEC §5.3)"},
    {"coluna": "is_dispensa", "tipo": "bool", "descricao": "canal em dispensa eletrônica ou tradicional"},
    {"coluna": "is_dispensa_eletronica", "tipo": "bool", "descricao": "canal = dispensa eletrônica"},
    {"coluna": "is_pce", "tipo": "bool", "descricao": "PCE - Pedido de Cotação Eletrônica preenchido"},
    {"coluna": "is_via_ata", "tipo": "bool", "descricao": "compra via ata de Registro de Preços"},
    {"coluna": "municipio_key / regiao_key", "tipo": "text", "descricao": "município e região de entrega normalizados"},
    {"coluna": "regiao_raio", "tipo": "text", "descricao": "dentro / fora / indefinida em relação ao raio de 200 km"},
    {"coluna": "is_pandemia", "tipo": "bool", "descricao": "qualquer flag COVID = Sim ou contrato emergencial = Sim"},
    {"coluna": "is_regulado", "tipo": "bool", "descricao": "família ou keyword da lista EVITAR (config.regulados)"},
    {"coluna": "prazo_entrega_dias", "tipo": "int", "descricao": "prazo em dias; nulo se > 365 (cauda inválida)"},
    {"coluna": "deflator", "tipo": "double", "descricao": "fator IPCA do ano para R$ de dez/2025"},
    {"coluna": "valor_total_nominal / valor_total_real", "tipo": "double", "descricao": "valor da linha em R$ nominais e em R$ de dez/2025"},
    {"coluna": "valor_unitario_real / valor_estimado_real", "tipo": "double", "descricao": "valor unitário e estimado em R$ de dez/2025"},
    {"coluna": "preco_outlier", "tipo": "bool", "descricao": "preço unitário fora de [p1, p99] do item (sinaliza, não remove)"},
)

_MARCADOR_INICIO = "<!-- INICIO:COLUNAS-DERIVADAS -->"
_MARCADOR_FIM = "<!-- FIM:COLUNAS-DERIVADAS -->"


def _atualizar_dicionario() -> None:
    """Anexa (idempotente) a seção de colunas derivadas ao data_dictionary.md."""
    caminho = paths.WORKSPACE / "data_dictionary.md"
    if not caminho.exists():
        return
    texto = caminho.read_text(encoding="utf-8")
    if _MARCADOR_INICIO in texto:
        ini = texto.index(_MARCADOR_INICIO)
        fim = texto.index(_MARCADOR_FIM) + len(_MARCADOR_FIM)
        texto = texto[:ini] + texto[fim:]

    linhas = [
        "",
        _MARCADOR_INICIO,
        "## Colunas derivadas (camada tratada)",
        "",
        "Criadas no estágio `treat`; ver `SPEC.md §3`.",
        "",
        "| Coluna | Tipo | Semântica |",
        "|---|---|---|",
    ]
    for c in COLUNAS_DERIVADAS:
        linhas.append(f"| `{c['coluna']}` | {c['tipo']} | {c['descricao']} |")
    linhas += ["", _MARCADOR_FIM, ""]
    caminho.write_text(texto.rstrip() + "\n" + "\n".join(linhas), encoding="utf-8")


def run(log: RunLog) -> dict[str, Any]:
    paths.ensure_dirs()
    log.section("F3 — TRATAMENTO")
    cfg = load_config()
    log(f"config.yaml v{cfg.get('meta.versao')} | convenção de deflação: {cfg.get('deflacao.convencao')}")
    log(f"escopo: material = {cfg.get('escopo.valores_material')}")

    con = conectar()
    fatores = _criar_dim_deflator(con, cfg)
    n_canais = _criar_dim_canal(con, cfg)
    log("\nfatores de deflação (para R$ de %s):" % cfg.get("meta.ano_base_deflacao"))
    for ano, f in sorted(fatores.items()):
        log(f"  {ano}: {f:.6f}")
    log(f"mapa de canais carregado: {n_canais} rótulos")

    conservacao = _conservacao(con, cfg)
    log("\nconservação de dados (E0..E4):")
    for p in conservacao:
        log(
            f"  {p['passo']} {p['descricao']:42s} linhas={p['linhas']:>9,} "
            f"Δlinhas={p['delta_linhas']:>9,} valor=R$ {p['valor']:>18,.2f}"
        )

    _criar_tabela_tratada(con, cfg)
    stats = _estatisticas_tratado(con)
    log(f"\ntabela tratada: {stats['linhas']:,} linhas")
    for r in stats["por_ano"]:
        log(
            f"  {r['ano']}: linhas={r['linhas']:>8,} afms={r['afms']:>7,} "
            f"fornecedores={r['fornecedores']:>6,} nominal=R$ {r['valor_nominal']:>16,.2f} "
            f"real=R$ {r['valor_real']:>16,.2f}"
        )
    log("\nflags e nulos:")
    for k, v in stats["nulos_e_flags"].items():
        log(f"  {k}: {v:,}")

    # reconciliação
    e0 = next(p for p in conservacao if p["passo"] == "E0")
    e4 = next(p for p in conservacao if p["passo"] == "E4")
    soma_material = float(q_one(
        con,
        f"SELECT sum(valor_total) AS v FROM staging WHERE tipo_do_item IN ({_sql_str_list(cfg.get('escopo.valores_material'))})",
    )["v"] or 0)
    soma_tratado_staging = float(q_one(con, "SELECT sum(valor_total) AS v FROM tratado")["v"] or 0)
    soma_real = float(q_one(con, "SELECT sum(valor_total_real) AS v FROM tratado")["v"] or 0)
    delta = abs(soma_tratado_staging - soma_material)
    rel = delta / soma_material if soma_material else 0.0
    tol = cfg.tolerancia_reconciliacao
    status = "OK" if rel <= tol else "FALHA"
    log("\nreconciliação (Σ VALOR TOTAL):")
    log(f"  bruto material: R$ {soma_material:,.2f}")
    log(f"  tratado       : R$ {soma_tratado_staging:,.2f}")
    log(f"  diferença     : R$ {delta:,.2f} ({rel * 100:.6f}%) -> {status} (tolerância {tol * 100:.2f}%)")
    log(f"  Σ valor_total_real (dez/2025): R$ {soma_real:,.2f}")

    # exporta parquet
    destino = paths.TREATED_PARQUET
    tmp = destino.with_suffix(".tmp.parquet")
    con.execute(
        f"COPY tratado TO '{tmp.as_posix()}' (FORMAT PARQUET, COMPRESSION SNAPPY)"
    )
    tmp.replace(destino)
    tamanho = destino.stat().st_size / 1024 / 1024
    log(f"\n[ok] {paths.relative(destino)} ({tamanho:.1f} MB, sha256={_sha256(destino)[:16]})")

    # logs
    with (paths.LOGS / "conservacao.log").open("w", encoding="utf-8") as fh:
        fh.write("passo\tdescricao\tlinhas\tdelta_linhas\tvalor\tdelta_valor\tmotivo\n")
        for p in conservacao:
            fh.write(
                f"{p['passo']}\t{p['descricao']}\t{p['linhas']}\t{p['delta_linhas']}\t"
                f"{p['valor']}\t{p['delta_valor']}\t{p['motivo']}\n"
            )

    resultado = {
        "gerado_em": datetime.now(UTC).isoformat(),
        "config_versao": cfg.get("meta.versao"),
        "convencao_deflacao": cfg.get("deflacao.convencao"),
        "deflatores": {str(k): round(v, 6) for k, v in sorted(fatores.items())},
        "conservacao": conservacao,
        "reconciliacao": {
            "soma_bruta_material": round(soma_material, 2),
            "soma_tratado": round(soma_tratado_staging, 2),
            "diferenca_abs": round(delta, 2),
            "diferenca_rel": round(rel, 8),
            "tolerancia": tol,
            "status": status,
            "soma_valor_real": round(soma_real, 2),
        },
        "estatisticas": stats,
        "parquet": {
            "caminho": paths.relative(destino),
            "tamanho_mb": round(tamanho, 2),
            "sha256": _sha256(destino),
            "linhas": stats["linhas"],
        },
    }
    write_json(paths.META / "tratamento.json", resultado)
    write_json(paths.LOGS / "reconciliacao.json", resultado["reconciliacao"])
    _atualizar_dicionario()
    log(f"[ok] {paths.relative(paths.META / 'tratamento.json')}")
    log("[ok] logs/conservacao.log, logs/reconciliacao.json")
    log("[ok] data_dictionary.md (seção de colunas derivadas)")

    con.close()
    if status != "OK":
        raise RuntimeError(f"reconciliação falhou: {rel * 100:.6f}% > {tol * 100:.2f}%")
    return resultado
