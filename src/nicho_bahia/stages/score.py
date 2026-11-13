"""F4 — Score, penalidades, sensibilidade e teses.

Entradas: data/aggregates/agg_familia_metricas.parquet (e demais agregados).
Saídas:
- data/aggregates/agg_score.parquet          (A09)
- data/aggregates/agg_evitar.parquet         (A12)
- data/aggregates/agg_sensibilidade.parquet  (A13)
- nicho_score.csv, top_itens.csv, orgaos_alvo.csv
- data/aggregates/teses/*.md
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from .. import paths
from ..config import load_config
from ..logging_utils import RunLog, write_json

DIMENSOES = (
    "demanda",
    "crescimento",
    "recorrencia",
    "fit_dispensa",
    "fragmentacao",
    "estabilidade_preco",
    "logistica",
)

# vocabulário que indica bem durável (exige assistência técnica/instalação, venda não recorrente)
KEYWORDS_DURAVEL = (
    "EQUIPAMENTO", "APARELHO", "MAQUINA", "VEICULO", "TRATOR", "CAMINHAO", "ONIBUS", "MOTO",
    "CONDICIONADOR", "REFRIGERADOR", "FREEZER", "GELADEIRA", "BEBEDOURO", "FOGO", "FORNO",
    "COMPUTADOR", "NOTEBOOK", "IMPRESSORA", "MONITOR", "PROJETOR", "CAMERA", "TELEVISOR",
    "MOTOR", "GERADOR", "COMPRESSOR", "BALANCA", "AUTOCLAVE", "CENTRIFUGA", "ESTUFA",
    "ULTRASSOM", "ELETROCARDIOGRAFO", "DESFIBRILADOR", "VENTILADOR", "PURIFICADOR",
)


def _perfil_uso(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Rótulo informativo: a família é de consumo recorrente, de bem durável ou mista?

    Não entra no score (que segue os pesos aprovados). Existe para que o decisor veja o que
    o score não mede: um ar-condicionado tem ticket e concorrência atraentes, mas é venda
    pontual com instalação e assistência técnica.
    """
    cond = " OR ".join(f"nome_key LIKE '%{k}%'" for k in KEYWORDS_DURAVEL)
    return con.execute(
        f"""
        SELECT familia_key,
               round(sum(valor_total_real) FILTER (WHERE {cond})
                     / nullif(sum(valor_total_real), 0), 4) AS share_duravel
        FROM t GROUP BY 1
        """
    ).fetch_df()


def _percentil(s: pd.Series) -> pd.Series:
    """Percentil 0-100 entre as famílias elegíveis; NaN vira 0.

    method='max': quem empata no topo recebe 100 (com 'average', famílias com 60/60 meses
    ficariam em ~84 e a dimensão perderia parte do seu peso).
    """
    return (s.rank(pct=True, method="max") * 100).fillna(0.0)


def _calcular_score(df: pd.DataFrame, pesos: dict[str, float], pesos_norm: bool = True) -> pd.Series:
    """Score 0-100 = média ponderada dos percentis das dimensões."""
    total = sum(pesos.values()) if pesos_norm else 100.0
    acc = pd.Series(0.0, index=df.index)
    for dim in DIMENSOES:
        acc = acc + df[f"p_{dim}"] * pesos[dim]
    return (acc / total).round(2)


def _preparar_dimensoes(df: pd.DataFrame, cfg) -> pd.DataFrame:  # noqa: ANN001
    """Converte as métricas brutas em percentis (0-100) entre as famílias elegíveis."""
    eleg = df["elegivel"].fillna(False)
    out = df.copy()

    def pct(serie: pd.Series) -> pd.Series:
        res = pd.Series(np.nan, index=out.index)
        res.loc[eleg] = _percentil(serie.loc[eleg])
        return res.fillna(0.0)

    out["p_demanda"] = pct(out["valor_2024_2025_real"])
    out["p_crescimento"] = pct(out["cagr_real"])
    out["p_recorrencia"] = pct(out["recorrencia"])
    out["p_fit_dispensa"] = pct(out["fit_dispensa_raw"].fillna(0.0))

    # fragmentação: 70% (1 - HHI normalizado) + 30% percentil do log do nº de fornecedores
    p_inv_hhi = pct(1.0 - (out["hhi"].fillna(10000) / 10000.0).clip(0, 1))
    p_nforn = pct(np.log1p(out["n_fornecedores"].fillna(0)))
    w1 = float(cfg.get("score.composicao.fragmentacao.peso_inverso_hhi"))
    w2 = float(cfg.get("score.composicao.fragmentacao.peso_log_fornecedores"))
    out["p_fragmentacao"] = (w1 * p_inv_hhi + w2 * p_nforn).round(2)

    # estabilidade de preço: 1 - min(CV, 1)
    estab = 1.0 - out["cv_mediano"].fillna(1.0).clip(0, 1)
    out["p_estabilidade_preco"] = pct(estab)

    # logística: share do valor dentro do raio
    out["p_logistica"] = pct(out["pct_valor_no_raio"].fillna(0.0))
    return out


def _penalidades(df: pd.DataFrame, cfg) -> tuple[pd.Series, pd.Series]:  # noqa: ANN001
    """Penalidades numéricas e o texto que as explica (por família)."""
    lim_pandemia = float(cfg.get("pandemia.limiar_dependencia_pandemia"))
    pen_pandemia = float(cfg.get("score.penalidades.dependencia_pandemia"))
    pen_queda = float(cfg.get("score.penalidades.queda_2_ultimos_anos"))

    penal = pd.Series(0.0, index=df.index)
    motivos = pd.Series("", index=df.index, dtype="object")

    dep = df["dependencia_pandemia"].fillna(0.0)
    m_pandemia = dep > lim_pandemia
    penal.loc[m_pandemia] -= pen_pandemia
    motivos.loc[m_pandemia] = "dependência de pandemia " + (dep[m_pandemia] * 100).round(1).astype(str) + "%"

    m_queda = df["dir_2_ultimos"].fillna(0) == -1
    penal.loc[m_queda] -= pen_queda
    motivos.loc[m_queda] = (
        motivos.loc[m_queda].where(motivos.loc[m_queda] == "", motivos.loc[m_queda] + "; ")
        + "queda nos 2 últimos anos"
    )
    return penal, motivos


def _aplicar_penalidades(df: pd.DataFrame, score_bruto: pd.Series, cfg) -> tuple[pd.Series, pd.Series]:  # noqa: ANN001
    """Aplica penalidades e devolve (score_final, texto_das_penalidades)."""
    penal, motivos = _penalidades(df, cfg)
    final = (score_bruto + penal).clip(lower=0).round(2)
    return final, motivos


def _sensibilidade(
    df: pd.DataFrame, pesos: dict[str, float], cfg, score_ref: pd.Series, penal: pd.Series
) -> pd.DataFrame:
    """Reexecuta o score com cada peso ±delta (14 cenários) e mede a estabilidade do top-10.

    Cada cenário aplica as mesmas penalidades do score de referência — caso contrário os ranks
    não seriam comparáveis.
    """
    delta = float(cfg.get("score.sensibilidade_delta"))
    top_n = int(cfg.get("score.top_n"))

    cenarios: dict[str, dict[str, float]] = {"referencia": dict(pesos)}
    for dim in DIMENSOES:
        for sinal, nome in ((1 + delta, "mais"), (1 - delta, "menos")):
            p = dict(pesos)
            p[dim] = p[dim] * sinal
            cenarios[f"{dim}_{nome}{int(delta * 100)}"] = p

    ranks: dict[str, pd.Series] = {}
    top_ref = set(score_ref.nlargest(top_n).index)
    for nome, p in cenarios.items():
        bruto = _calcular_score(df, p)
        final = (bruto + penal).clip(lower=0)
        ranks[nome] = final.rank(ascending=False, method="min")

    rank_df = pd.DataFrame(ranks)
    perturbados = [c for c in rank_df.columns if c != "referencia"]
    res = pd.DataFrame(index=df.index)
    res["familia_key"] = df["familia_key"]
    res["familia_catalogo"] = df["familia_catalogo"]
    res["score_ref"] = score_ref
    res["rank_ref"] = score_ref.rank(ascending=False, method="min").astype(int)
    res["rank_min"] = rank_df[perturbados].min(axis=1).astype(int)
    res["rank_max"] = rank_df[perturbados].max(axis=1).astype(int)
    no_top = (rank_df[perturbados] <= top_n).sum(axis=1)
    res["estabilidade_top10"] = (no_top / len(perturbados)).round(3)
    res["presenca_no_top10_ref"] = res.index.isin(top_ref)
    res["n_cenarios_top10"] = no_top.astype(int)
    return res.reset_index(drop=True)


def _itens_ancora(con: duckdb.DuckDBPyConnection, familia_keys: list[str], cfg) -> pd.DataFrame:
    """Itens-âncora por família: valor, recorrência, nº fornecedores, preço e barreira (COMUM)."""
    lista = ", ".join("'" + k.replace("'", "''") + "'" for k in familia_keys)
    esc = "(NOT is_regulado) AND (NOT is_pandemia)"
    df = con.execute(
        f"""
        WITH it AS (
          SELECT familia_key, item_key,
                 min(familia_catalogo)           AS familia_catalogo,
                 min(nome_basico)                AS nome_basico,
                 min(um)                         AS um,
                 count(*)                        AS linhas,
                 count(DISTINCT afm_aps)         AS afms,
                 count(DISTINCT ano_mes)         AS meses,
                 count(DISTINCT fornecedor_id)   AS fornecedores,
                 round(sum(valor_total_real), 2) AS valor_real,
                 round(median(valor_unitario_real), 4) AS preco_mediano,
                 round(quantile_cont(valor_unitario_real, 0.25), 4) AS preco_p25,
                 round(quantile_cont(valor_unitario_real, 0.75), 4) AS preco_p75,
                 round(avg(CASE WHEN upper(tipo_item_especifico_comum) = 'COMUM' THEN 1 ELSE 0 END), 3) AS pct_comum
          FROM t
          WHERE {esc} AND familia_key IN ({lista}) AND valor_unitario_real > 0
          GROUP BY familia_key, item_key
        )
        SELECT * FROM it
        """
    ).fetch_df()

    # score do item-âncora: volume, recorrência e menor barreira (item comum)
    df["p_valor"] = df.groupby("familia_key")["valor_real"].rank(pct=True) * 100
    df["p_meses"] = df.groupby("familia_key")["meses"].rank(pct=True) * 100
    df["ancora_score"] = (0.5 * df["p_valor"] + 0.3 * df["p_meses"] + 20 * df["pct_comum"]).round(2)
    df = df.sort_values(["familia_key", "ancora_score", "item_key"], ascending=[True, False, True])
    top = int(cfg.get("metricas.top_itens_por_familia"))
    return df.groupby("familia_key").head(top).reset_index(drop=True)


def _orgaos_alvo(con: duckdb.DuckDBPyConnection, familia_keys: list[str], cfg) -> pd.DataFrame:
    lista = ", ".join("'" + k.replace("'", "''") + "'" for k in familia_keys)
    esc = "(NOT is_regulado) AND (NOT is_pandemia)"
    df = con.execute(
        f"""
        SELECT familia_key, familia_catalogo, ug_key, ug_fiplan, secretaria,
               count(DISTINCT afm_aps)          AS afms,
               round(sum(valor_total_real), 2)  AS valor_real,
               round(sum(valor_total_real) FILTER (WHERE is_dispensa)
                     / nullif(sum(valor_total_real), 0), 4) AS share_dispensa,
               round(sum(valor_total_real) FILTER (WHERE regiao_raio = 'dentro')
                     / nullif(sum(valor_total_real), 0), 4) AS share_no_raio,
               round(median(valor_total_real), 2) AS ticket_mediano,
               min(regiao_key)                   AS regiao
        FROM t
        WHERE {esc} AND familia_key IN ({lista})
        GROUP BY 1,2,3,4,5
        ORDER BY familia_key, valor_real DESC, ug_key
        """
    ).fetch_df()
    top = int(cfg.get("metricas.top_orgaos"))
    return df.groupby("familia_key").head(top).reset_index(drop=True)


def _teses(
    top: pd.DataFrame,
    itens: pd.DataFrame,
    orgaos: pd.DataFrame,
    saz: pd.DataFrame,
    sens: pd.DataFrame,
) -> None:
    destino = paths.AGGREGATES / "teses"
    destino.mkdir(parents=True, exist_ok=True)
    for _, fam in top.iterrows():
        k = fam["familia_key"]
        it = itens[itens["familia_key"] == k].head(6)
        og = orgaos[orgaos["familia_key"] == k].head(5)
        sz = saz[saz["familia_key"] == k]
        picos = sz[sz["indice_mes"] >= 1.2].sort_values("indice_mes", ascending=False)
        s = sens[sens["familia_key"] == k]
        L: list[str] = []
        a = L.append
        a(f"# Tese — {fam['familia_catalogo']}")
        a("")
        a(f"**Score: {fam['score']:.1f}/100** · rank {int(fam['rank'])} · "
          f"{fam['linhas']:,} linhas · {int(fam['afms']):,} AFM/APS · "
          f"R$ {fam['valor_total_real']:,.2f} no período (R$ de dez/2025)")
        a("")
        a("## Por que atacar")
        a(f"- Demanda recente (média 2024–2025): R$ {fam['valor_2024_2025_real']:,.2f} por ano")
        cagr = fam.get("cagr_real")
        a(f"- Crescimento real 2021–2025: {'n/d' if pd.isna(cagr) else f'{cagr * 100:.1f}% a.a.'}")
        a(f"- Recorrência: {int(fam['meses_com_compra'])} de 60 meses com compra "
          f"({fam['recorrencia'] * 100:.0f}%)")
        a(f"- Ticket por AFM/APS: mediana R$ {fam['ticket_p50']:,.2f} "
          f"(p75 R$ {fam['ticket_p75']:,.2f}); {fam['pct_afm_ate_teto'] * 100:.1f}% abaixo do teto de dispensa")
        a(f"- Concorrência: {int(fam['n_fornecedores'])} fornecedores, HHI {fam['hhi']:.0f}, "
          f"top-3 com {fam['share_top3'] * 100:.1f}%")
        a(f"- Canal: {fam['share_dispensa'] * 100:.1f}% do valor em dispensa; "
          f"{fam['share_pce'] * 100:.1f}% com PCE")
        a(f"- Logística: {fam['pct_valor_no_raio'] * 100:.1f}% do valor entregue no raio de 200 km; "
          f"prazo mediano {fam['prazo_mediano']:.0f} dias")
        a("")
        a("## Itens-âncora")
        a("")
        a("| Item (nome básico) | UM | Valor | Meses | Fornecedores | Preço mediano | p25–p75 | % comum |")
        a("|---|---|---|---|---|---|---|---|")
        for _, r in it.iterrows():
            a(f"| {r['nome_basico']} | {r['um']} | R$ {r['valor_real']:,.2f} | {int(r['meses'])} | "
              f"{int(r['fornecedores'])} | R$ {r['preco_mediano']:,.2f} | "
              f"R$ {r['preco_p25']:,.2f}–{r['preco_p75']:,.2f} | {r['pct_comum'] * 100:.0f}% |")
        a("")
        a("## Órgãos-alvo")
        a("")
        a("| UG / órgão | Secretaria | AFM/APS | Valor | % dispensa | % no raio | Ticket mediano |")
        a("|---|---|---|---|---|---|---|")
        for _, r in og.iterrows():
            a(f"| {r['ug_fiplan']} | {r['secretaria']} | {int(r['afms'])} | R$ {r['valor_real']:,.2f} | "
              f"{(r['share_dispensa'] or 0) * 100:.0f}% | {(r['share_no_raio'] or 0) * 100:.0f}% | "
              f"R$ {r['ticket_mediano']:,.2f} |")
        a("")
        a("## Calendário")
        if len(picos):
            a("- Meses de pico (índice ≥ 1,2): " + ", ".join(
                f"{int(r['mes']):02d} ({r['indice_mes']:.2f}x)" for _, r in picos.head(6).iterrows()))
        else:
            a("- Sem pico sazonal relevante (compra distribuída no ano).")
        a("")
        a("## Riscos")
        a(f"- Dependência de pandemia: {fam['dependencia_pandemia'] * 100:.1f}% do valor material da família")
        a(f"- Índice de concentração do maior comprador: {fam['concentracao_maior_comprador'] * 100:.1f}%")
        a(f"- Desconto mediano vs. estimado: {fam['desconto_mediano'] * 100:.1f}%")
        a(f"- Estabilidade do rank sob ±20% nos pesos: rank {int(s['rank_min'].iloc[0])}–{int(s['rank_max'].iloc[0])} "
          f"em 14 cenários ({s['estabilidade_top10'].iloc[0] * 100:.0f}% no top-10)")
        a("")
        a("## Critérios de abandono")
        a("- Nenhuma dispensa eletrônica da família em 2 trimestres consecutivos na região de atuação;")
        a("- ticket mediano por AFM/APS subir acima do teto de dispensa, exigindo pregão e atestados;")
        a("- HHI acima de 2.500 (concentração) com top-3 acima de 70% do valor;")
        a("- preço mediano cair abaixo do custo de reposição por 2 medições trimestrais.")
        a("")
        (destino / f"{k.split(' - ')[0]}.md").write_text("\n".join(L), encoding="utf-8")


def _gate_g4(
    log: RunLog,
    cfg,  # noqa: ANN001
    a09: pd.DataFrame,
    a13: pd.DataFrame,
    nicho: pd.DataFrame,
    evitar: pd.DataFrame,
    agregados: list[str],
) -> dict[str, Any]:
    """Gate G4 (automático): o score é reproduzível, o ranking é consistente e os agregados fecham."""
    checks: list[dict[str, Any]] = []

    def add(id_: str, desc: str, esperado: Any, obtido: Any, ok: bool) -> None:
        checks.append({"id": id_, "descricao": desc, "esperado": esperado, "obtido": obtido, "status": "OK" if ok else "FALHA"})

    # D01 — agregados presentes
    faltando = [a for a in agregados if not (paths.AGGREGATES / f"{a}.parquet").exists()]
    add("D01", "todos os agregados gravados", "0 ausentes", faltando or "nenhum", not faltando)

    # D02 — score recalculável a partir das dimensões (round-trip)
    pesos = cfg.pesos
    soma_pesos = sum(pesos.values())
    recalc = sum(a09[f"p_{d}"] * pesos[d] for d in DIMENSOES) / soma_pesos
    dif = (recalc - a09["score_bruto"]).abs().max()
    add("D02", "score bruto recalculado = gravado", "desvio <= 0.02", f"max {dif:.4f}", dif <= 0.02)

    # D03 — score final = bruto + penalidades, >= 0
    penal_valor = a09["penalidades"].fillna("").map(
        lambda t: -float(cfg.get("score.penalidades.dependencia_pandemia")) * ("pandemia" in t)
        - float(cfg.get("score.penalidades.queda_2_ultimos_anos")) * ("queda" in t)
    )
    dif2 = ((a09["score_bruto"] + penal_valor).clip(lower=0) - a09["score"]).abs().max()
    add("D03", "score final = bruto + penalidades (>=0)", "desvio <= 0.02", f"max {dif2:.4f}", dif2 <= 0.02)

    # D04 — ranking 1..n sem empates
    ranks = a09["rank"].dropna().astype(int)
    ok_rank = len(ranks) == len(set(ranks)) and set(ranks) == set(range(1, len(ranks) + 1))
    add("D04", "rank sequencial 1..n sem empates", f"1..{len(ranks)}", f"{len(ranks)} posições", ok_rank)

    # D05 — CSV == agregado (A5)
    top_csv = nicho.head(10)[["familia_catalogo", "score"]].reset_index(drop=True)
    top_agg = a09[a09["elegivel"]].head(10)[["familia_catalogo", "score"]].reset_index(drop=True)
    iguais = bool((top_csv["familia_catalogo"] == top_agg["familia_catalogo"]).all() and
                  (top_csv["score"] - top_agg["score"]).abs().max() <= 1e-6)
    add("D05", "nicho_score.csv == agg_score (top-10)", "idênticos", "idênticos" if iguais else "divergem", iguais)

    # D06 — sensibilidade: 14 cenários e rank coerente
    n_cen = int(a13["n_cenarios_top10"].max()) if len(a13) else 0
    ok_sens = n_cen == 14 and (a13["rank_min"] <= a13["rank_ref"]).all() and (a13["rank_ref"] <= a13["rank_max"]).all()
    add("D06", "sensibilidade com 14 cenários e rank coerente", 14, n_cen, ok_sens)

    # D07 — reconciliação agregados vs escopo analítico
    meta = json.loads((paths.META / "analise.json").read_text(encoding="utf-8"))
    total_escopo = float(meta["escopo_analitico"]["valor_real"])
    familia_ano = pd.read_parquet(paths.AGGREGATES / "agg_familia_ano.parquet")
    total_agg = float(familia_ano["valor_real"].sum())
    rel = abs(total_agg - total_escopo) / total_escopo
    add("D07", "Σ agg_familia_ano == escopo analítico", "<= 0.1%", f"{rel * 100:.6f}%", rel <= 0.001)

    # D08 — EVITAR contém as famílias reguladas
    add("D08", "lista EVITAR preenchida", "> 0 famílias", len(evitar), len(evitar) > 0)

    # D09 — família majoritariamente regulada (>=50% do valor) não pode estar ranqueada
    lim_reg = float(cfg.get("regulados.limiar_valor_regulado"))
    majoritarias = set(a09.loc[a09["share_regulado"].fillna(0) >= lim_reg, "familia_key"])
    conflito = a09[(a09["elegivel"]) & (a09["familia_key"].isin(majoritarias))]
    add("D09", "família majoritariamente regulada fora do ranking", "0", len(conflito), len(conflito) == 0)

    falhas = [c for c in checks if c["status"] != "OK"]
    gate = {
        "gate": "G4",
        "gerado_em": datetime.now(UTC).isoformat(),
        "status": "VERDE" if not falhas else "VERMELHO",
        "checks": checks,
        "resumo": {"n_checks": len(checks), "n_falhas": len(falhas)},
    }
    write_json(paths.LOGS / "gate_g4.json", gate)
    for c in checks:
        log(f"  [{c['status']:5s}] {c['id']} {c['descricao']:52s} esperado={c['esperado']} obtido={c['obtido']}")
    log(f"[{'VERDE' if not falhas else 'VERMELHO'}] Gate G4 — {len(checks) - len(falhas)}/{len(checks)} verificações OK")
    if falhas:
        raise RuntimeError("Gate G4 VERMELHO: " + ", ".join(c["id"] for c in falhas))
    return gate


def run(log: RunLog) -> dict[str, Any]:
    paths.ensure_dirs()
    log.section("F4 — SCORE E SENSIBILIDADE")
    cfg = load_config()

    metricas = pd.read_parquet(paths.AGGREGATES / "agg_familia_metricas.parquet")
    reg = pd.read_parquet(paths.AGGREGATES / "agg_regulados.parquet")
    log(f"famílias no escopo analítico: {len(metricas)} | elegíveis: {int(metricas['elegivel'].sum())}")

    con = duckdb.connect()
    con.execute("SET threads TO 4")
    con.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{paths.TREATED_PARQUET.as_posix()}')")

    df = _preparar_dimensoes(metricas, cfg)
    penal, _ = _penalidades(df, cfg)
    # rótulo informativo de perfil de uso (não entra no score)
    perfil = _perfil_uso(con).set_index("familia_key")["share_duravel"]
    df["share_duravel"] = df["familia_key"].map(perfil).fillna(0.0)
    df["perfil_uso"] = np.select(
        [df["share_duravel"] > 0.5, df["share_duravel"] < 0.2],
        ["bem durável", "consumo recorrente"],
        default="misto",
    )

    pesos = cfg.pesos
    score_bruto = _calcular_score(df, pesos)
    score_final, motivos = _aplicar_penalidades(df, score_bruto, cfg)

    df["score_bruto"] = score_bruto
    df["score"] = score_final
    df["penalidades"] = motivos
    eleg = df["elegivel"].fillna(False)
    df["rank"] = np.nan
    # rank sequencial (1..n) na ordem do score, sem empates, apenas entre elegíveis
    ordem = df.loc[eleg].sort_values("score", ascending=False).index
    df.loc[ordem, "rank"] = np.arange(1, len(ordem) + 1)

    # A09
    cols_score = [
        "familia_key", "familia_catalogo", "score", "score_bruto", "rank", "elegivel",
        "motivo_exclusao", "penalidades",
        *[f"p_{d}" for d in DIMENSOES],
        "valor_total_real", "valor_2024_2025_real", "cagr_real", "recorrencia", "meses_com_compra",
        "n_afm", "ticket_p50", "ticket_p75", "pct_afm_ate_teto", "pct_afm_ate_teto_hist",
        "n_fornecedores", "hhi", "share_top3", "pct_novos_medio", "share_dispensa", "share_pce",
        "cv_mediano", "desconto_mediano", "pct_valor_no_raio", "prazo_mediano",
        "dependencia_pandemia", "share_regulado", "dir_2_ultimos", "afms", "linhas",
        "perfil_uso", "share_duravel",
    ]
    a09 = df[cols_score].sort_values(["elegivel", "score", "familia_key"], ascending=[False, False, True])
    a09 = a09.reset_index(drop=True)
    a09.to_parquet(paths.AGGREGATES / "agg_score.parquet", index=False, compression="snappy")
    log(f"  [ok] agg_score.parquet ({len(a09)} famílias)")

    # A12 — EVITAR
    lim_reg = float(cfg.get("regulados.limiar_valor_regulado"))
    share_reg = metricas.set_index("familia_key")["share_regulado"]
    evitar = reg.copy()
    evitar["share_regulado"] = evitar["familia_key"].map(share_reg).fillna(1.0).round(4)
    evitar["motivo"] = "família regulada (registro sanitário / ANVISA / produto controlado)"
    evitar["criterio"] = "config.yaml → regulados.familias"
    evitar["excluida_do_ranking"] = evitar["share_regulado"] >= lim_reg
    evitar = evitar.sort_values(["valor_real", "familia_key"], ascending=[False, True]).reset_index(drop=True)
    evitar.to_parquet(paths.AGGREGATES / "agg_evitar.parquet", index=False, compression="snappy")
    log(f"  [ok] agg_evitar.parquet ({len(evitar)} famílias, "
        f"{int(evitar['excluida_do_ranking'].sum())} excluídas do ranking)")

    # A13 — sensibilidade
    sens = _sensibilidade(df, pesos, cfg, df["score"], penal)
    sens = sens.sort_values("familia_key").reset_index(drop=True)
    sens.to_parquet(paths.AGGREGATES / "agg_sensibilidade.parquet", index=False, compression="snappy")
    top_n = int(cfg.get("score.top_n"))
    top_ref = df[eleg].nlargest(top_n, "score")
    estab = sens.set_index("familia_key").loc[top_ref["familia_key"], "estabilidade_top10"]
    log(f"  [ok] agg_sensibilidade.parquet (14 cenários)")
    log(f"  top-10 com estabilidade média {estab.mean() * 100:.1f}% "
        f"(mínima {estab.min() * 100:.0f}%, máxima {estab.max() * 100:.0f}%)")

    # CSVs
    csv_cols = [
        "rank", "familia_catalogo", "score", "score_bruto", "penalidades", "perfil_uso",
        "valor_total_real", "valor_2024_2025_real", "cagr_real", "recorrencia",
        "n_afm", "ticket_p50", "pct_afm_ate_teto", "n_fornecedores", "hhi", "share_top3",
        "share_dispensa", "pct_valor_no_raio", "dependencia_pandemia",
    ]
    nicho = a09.loc[a09["elegivel"], csv_cols].copy()
    # A11: a estabilidade do rank sob ±20% nos pesos acompanha o CSV
    nicho["_k"] = a09.loc[a09["elegivel"], "familia_key"].to_numpy()
    nicho = nicho.merge(
        sens[["familia_key", "rank_min", "rank_max", "estabilidade_top10"]],
        left_on="_k", right_on="familia_key", how="left",
    ).drop(columns=["_k", "familia_key"])
    nicho.to_csv(paths.WORKSPACE / "nicho_score.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    log(f"  [ok] nicho_score.csv ({len(nicho)} nichos ranqueados, com estabilidade)")

    # itens-âncora e órgãos-alvo dos top N
    familias_top = top_ref["familia_key"].tolist()
    itens = _itens_ancora(con, familias_top, cfg)
    orgaos = _orgaos_alvo(con, familias_top, cfg)
    con.close()

    itens.to_csv(paths.WORKSPACE / "top_itens.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    orgaos.to_csv(paths.WORKSPACE / "orgaos_alvo.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")
    log(f"  [ok] top_itens.csv ({len(itens)} itens de {len(familias_top)} famílias)")
    log(f"  [ok] orgaos_alvo.csv ({len(orgaos)} órgãos)")

    # sazonalidade com índice por família
    saz = pd.read_parquet(paths.AGGREGATES / "agg_sazonalidade.parquet")
    media_fam = saz.groupby("familia_key")["valor_medio_real"].transform("mean")
    saz["indice_mes"] = (saz["valor_medio_real"] / media_fam.replace(0, np.nan)).round(3)
    saz.to_parquet(paths.AGGREGATES / "agg_sazonalidade.parquet", index=False, compression="snappy")

    top_out = top_ref.merge(
        sens[["familia_key", "rank_min", "rank_max", "estabilidade_top10"]], on="familia_key", how="left"
    )
    _teses(top_out, itens, orgaos, saz, sens)
    n_teses = len(list((paths.AGGREGATES / "teses").glob("*.md")))
    log(f"  [ok] teses: {n_teses} arquivos")

    resultado = {
        "gerado_em": datetime.now(UTC).isoformat(),
        "pesos": pesos,
        "n_familias": len(df),
        "n_elegiveis": int(eleg.sum()),
        "top10": [
            {
                "rank": int(r["rank"]),
                "familia": r["familia_catalogo"],
                "score": float(r["score"]),
                "valor_2024_2025": float(r["valor_2024_2025_real"]),
                "estabilidade_top10": float(estab.get(r["familia_key"], 0)),
            }
            for _, r in top_ref.iterrows()
        ],
        "estabilidade_media_top10": round(float(estab.mean()), 3),
        "evitar": evitar[["familia_catalogo", "valor_real", "pct_valor_total"]].to_dict("records"),
    }
    write_json(paths.META / "score.json", resultado)
    log("\ntop-5:")
    for r in resultado["top10"][:5]:
        log(f"  {r['rank']}. {r['familia'][:62]:62s} score={r['score']:5.1f} "
            f"R$ {r['valor_2024_2025']:,.0f}/ano estab={r['estabilidade_top10'] * 100:.0f}%")

    # gates
    log("\nGate G4:")
    agregados = [p.stem for p in paths.AGGREGATES.glob("*.parquet")]
    _gate_g4(log, cfg, a09, sens, nicho, evitar, sorted(agregados))
    return resultado
