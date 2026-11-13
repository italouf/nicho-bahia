"""Empacotador do panel_data.json — único insumo do painel.

O JSON é colunar/compacto e usa índices inteiros em vez de repetir strings
(família, secretaria, canal, região, município). Orçamento: ≤ 8 MB.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from . import paths
from .config import load_config
from .logging_utils import write_json

# ids dos agregados exibidos no rodapé de cada gráfico
IDS: dict[str, str] = {
    "A01": "agg_familia_ano", "A02": "agg_familia_periodo", "A03": "agg_familia_tendencia",
    "A04": "agg_familia_metricas", "A05": "agg_sazonalidade", "A06": "agg_orgao_familia",
    "A07": "agg_canal_familia", "A08": "agg_ticket_afm", "A09": "agg_score",
    "A10": "agg_fornecedor_familia", "A11": "agg_concorrencia", "A12": "agg_evitar",
    "A13": "agg_sensibilidade", "A14": "agg_entrantes", "A15": "agg_top_fornecedores",
    "A16": "agg_preco_item", "A17": "agg_preco_dispersao", "A18": "agg_desconto",
    "A19": "agg_regiao_familia", "A20": "agg_prazo", "A21": "agg_municipio",
    "A22": "agg_qualidade",
}


def _ler(nome: str) -> pd.DataFrame:
    return pd.read_parquet(paths.AGGREGATES / f"{nome}.parquet")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _num(v: Any, casas: int = 2) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if pd.isna(f):
        return None
    return round(f, casas)


def _limpar_md(texto: str) -> str:
    """Remove marcação markdown leve (negrito/código) para exibição em HTML."""
    t = texto.replace("**", "").replace("`", "")
    return t.strip()


def _parse_assumptions(texto: str) -> list[list[str]]:
    """Extrai as premissas de ASSUMPTIONS.md (id | premissa | status) para a aba Método."""
    linhas: list[list[str]] = []
    for linha in texto.splitlines():
        if not linha.startswith("| A") or linha.startswith("| id"):
            continue
        partes = [p.strip() for p in linha.strip("|").split("|")]
        if len(partes) >= 4:
            # | id | Premissa | Status | Evidência |
            linhas.append([_limpar_md(partes[0]), _limpar_md(partes[1]), _limpar_md(partes[2])])
    return linhas


def construir(version: str = "1.0") -> dict[str, Any]:
    cfg = load_config()
    anos = cfg.anos

    score = _ler("agg_score").sort_values("rank", na_position="last")
    score["idx"] = range(len(score))
    fam_index = {k: int(i) for i, k in zip(score["idx"], score["familia_key"], strict=True)}
    nomes = score["familia_catalogo"].tolist()

    # --- dimensões e famílias -----------------------------------------------------
    familias: list[dict[str, Any]] = []
    dim: dict[str, list[float]] = {}
    sens: dict[str, list[Any]] = {}
    metricas: dict[str, list[Any]] = {}
    for _, r in score.iterrows():
        i = int(r["idx"])
        familias.append(
            {
                "i": i,
                "k": r["familia_key"],
                "n": r["familia_catalogo"],
                "s": _num(r["score"], 2),
                "r": None if pd.isna(r["rank"]) else int(r["rank"]),
                "e": bool(r["elegivel"]),
                "m": r["motivo_exclusao"] or "",
                "pu": r["perfil_uso"],
            }
        )
        dim[str(i)] = [_num(r[f"p_{d}"], 1) for d in ("demanda", "crescimento", "recorrencia", "fit_dispensa", "fragmentacao", "estabilidade_preco", "logistica")]
        metricas[str(i)] = [
            _num(r["valor_2024_2025_real"], 0), _num(r["valor_total_real"], 0),
            _num(r["cagr_real"], 4), _num(r["recorrencia"], 3), int(r["afms"]) if pd.notna(r["afms"]) else 0,
            _num(r["ticket_p50"], 0), _num(r["pct_afm_ate_teto"], 4),
            int(r["n_fornecedores"]) if pd.notna(r["n_fornecedores"]) else 0,
            _num(r["hhi"], 0), _num(r["share_top3"], 4), _num(r["share_dispensa"], 4),
            _num(r["pct_valor_no_raio"], 4), _num(r["cv_mediano"], 4), _num(r["desconto_mediano"], 4),
            _num(r["dependencia_pandemia"], 4), str(r["penalidades"] or ""),
            _num(r["pct_afm_ate_teto_hist"], 4), _num(r["prazo_mediano"], 0),
            _num(r["pct_novos_medio"], 4), int(r["linhas"]) if pd.notna(r["linhas"]) else 0,
        ]

    sens_df = _ler("agg_sensibilidade")
    for _, r in sens_df.iterrows():
        i = fam_index.get(r["familia_key"])
        if i is None:
            continue
        sens[str(i)] = [int(r["rank_min"]), int(r["rank_max"]), _num(r["estabilidade_top10"], 3),
                        int(r["rank_ref"]), int(r["n_cenarios_top10"])]

    # --- série anual (nominal e real) --------------------------------------------
    fa = _ler("agg_familia_ano")
    serie: dict[str, dict[str, list[float | None]]] = {}
    for k, g in fa.groupby("familia_key"):
        i = fam_index.get(k)
        if i is None:
            continue
        g = g.set_index("ano").reindex(anos)
        serie[str(i)] = {
            "n": [_num(v, 0) for v in g["valor_nominal"].tolist()],
            "r": [_num(v, 0) for v in g["valor_real"].tolist()],
            "l": [int(v) if pd.notna(v) else 0 for v in g["linhas"].tolist()],
        }

    # --- sazonalidade -------------------------------------------------------------
    saz_df = _ler("agg_sazonalidade")
    saz: dict[str, list[float | None]] = {}
    for k, g in saz_df.groupby("familia_key"):
        i = fam_index.get(k)
        if i is None:
            continue
        idx = g.set_index("mes")["indice_mes"].reindex(range(1, 13))
        saz[str(i)] = [_num(v, 3) for v in idx.tolist()]

    # --- secretarias / canais / regiões / municípios (índices) --------------------
    org = _ler("agg_orgao_familia")
    secretarias = sorted(org["secretaria_key"].dropna().unique().tolist())
    sec_index = {s: i for i, s in enumerate(secretarias)}
    sec_nome = org.drop_duplicates("secretaria_key").set_index("secretaria_key")["secretaria"].to_dict()
    orgaos = [
        [fam_index[r["familia_key"]], sec_index[r["secretaria_key"]], int(r["ano"]),
         _num(r["valor_real"], 0), _num(r["share_dispensa"], 4), _num(r["valor_nominal"], 0)]
        for _, r in org.iterrows()
        if r["familia_key"] in fam_index and r["secretaria_key"] in sec_index
    ]

    canal_df = _ler("agg_canal_familia")
    canais = sorted(canal_df["canal"].dropna().unique().tolist())
    canal_index = {c: i for i, c in enumerate(canais)}
    canal = [
        [fam_index[r["familia_key"]], canal_index[r["canal"]], int(r["ano"]),
         _num(r["valor_real"], 0), int(r["linhas"]), _num(r["valor_nominal"], 0)]
        for _, r in canal_df.iterrows()
        if r["familia_key"] in fam_index
    ]

    reg_df = _ler("agg_regiao_familia")
    regioes = sorted(reg_df["regiao_key"].dropna().unique().tolist())
    reg_index = {c: i for i, c in enumerate(regioes)}
    raio_por_regiao = reg_df.drop_duplicates("regiao_key").set_index("regiao_key")["regiao_raio"].to_dict()
    regiao = [
        [fam_index[r["familia_key"]], reg_index[r["regiao_key"]], int(r["ano"]),
         _num(r["valor_real"], 0), _num(r["valor_nominal"], 0)]
        for _, r in reg_df.iterrows()
        if r["familia_key"] in fam_index and r["regiao_key"] in reg_index
    ]

    mun_df = _ler("agg_municipio")
    # [família, município, valor] — permite que o filtro de família recorte os municípios
    mun_df = mun_df.groupby(["familia_key", "municipio"], as_index=False)["valor_real"].sum()
    municipios = [
        [fam_index[r["familia_key"]], r["municipio"], _num(r["valor_real"], 0)]
        for _, r in mun_df.iterrows()
        if r["familia_key"] in fam_index
    ]

    # --- ticket, concorrência, prazo ---------------------------------------------
    # ATENÇÃO: estas tabelas são indexadas pelo ÍNDICE da família (igual a SERIE/SAZ/DIM),
    # não pela familia_key — o JS acessa DATA.x[i].
    tk = _ler("agg_ticket_afm")
    ticket = {
        str(fam_index[r["familia_key"]]): [
            _num(r["ticket_p25"], 0), _num(r["ticket_p50"], 0), _num(r["ticket_p75"], 0),
            _num(r["ticket_p95"], 0), _num(r["pct_afm_ate_teto"], 4),
            _num(r["pct_afm_ate_teto_hist"], 4), int(r["n_afm"]),
        ]
        for _, r in tk.iterrows()
        if r["familia_key"] in fam_index
    }

    conc = _ler("agg_concorrencia")
    conc = conc.merge(_ler("agg_entrantes")[["familia_key", "ano", "novos", "ativos"]], on=["familia_key", "ano"], how="left")
    concorrencia = [
        [fam_index[r["familia_key"]], int(r["ano"]), _num(r["hhi"], 0), int(r["n_fornecedores"]),
         _num(r["share_top3"], 4), int(r["novos"] or 0), int(r["ativos"] or 0)]
        for _, r in conc.iterrows()
        if r["familia_key"] in fam_index
    ]

    pz = _ler("agg_prazo")
    prazo = {
        str(fam_index[r["familia_key"]]): [
            _num(r["prazo_mediano"], 0), _num(r["prazo_p90"], 0),
            _num(r["pct_ate_30d"], 4), int(r["n_com_prazo"] or 0),
        ]
        for _, r in pz.iterrows()
        if r["familia_key"] in fam_index
    }

    # --- itens de preço (top 3 por família) --------------------------------------
    preco_df = _ler("agg_preco_item")
    itens = pd.read_parquet(paths.AGGREGATES / "agg_familia_metricas.parquet")[["familia_key"]]  # noqa: F841
    tops = (
        preco_df.groupby(["familia_key", "item_key"], as_index=False)["linhas"].sum()
        .sort_values(["familia_key", "linhas"], ascending=[True, False])
        .groupby("familia_key").head(3)
    )
    chaves = set(zip(tops["familia_key"], tops["item_key"], strict=True))
    preco_df = preco_df[[(f, i) in chaves for f, i in zip(preco_df["familia_key"], preco_df["item_key"], strict=True)]]
    preco: dict[str, list[list[Any]]] = {}
    for k, g in preco_df.groupby("familia_key"):
        i = fam_index.get(k)
        if i is None:
            continue
        itens_fam: list[list[Any]] = []
        for item_key, gi in g.groupby("item_key"):
            gi = gi.set_index("ano").reindex(anos)
            itens_fam.append([
                gi["nome_basico"].dropna().iloc[0] if gi["nome_basico"].notna().any() else "",
                gi["um"].dropna().iloc[0] if gi["um"].notna().any() else "",
                [_num(v, 2) for v in gi["preco_p25"].tolist()],
                [_num(v, 2) for v in gi["preco_mediano"].tolist()],
                [_num(v, 2) for v in gi["preco_p75"].tolist()],
                [int(v) if pd.notna(v) else 0 for v in gi["linhas"].tolist()],
                [_num(v, 2) for v in gi["preco_p25_nom"].tolist()],
                [_num(v, 2) for v in gi["preco_mediano_nom"].tolist()],
                [_num(v, 2) for v in gi["preco_p75_nom"].tolist()],
            ])
        preco[str(i)] = itens_fam

    # --- fornecedores top (5 por família, período) --------------------------------
    ff = _ler("agg_fornecedor_familia")
    ff = ff.groupby(["familia_key", "fornecedor_id", "razao_social", "uf", "categoria"], as_index=False)["valor_real"].sum()
    ff = ff.sort_values(["familia_key", "valor_real", "fornecedor_id"], ascending=[True, False, True]).groupby("familia_key").head(5)
    fornecedores: dict[str, list[list[Any]]] = {}
    for k, g in ff.groupby("familia_key"):
        i = fam_index.get(k)
        if i is None:
            continue
        total = g["valor_real"].sum()
        fornecedores[str(i)] = [
            [r["razao_social"], r["uf"], r["categoria"], _num(r["valor_real"], 0),
             _num(r["valor_real"] / total if total else None, 4)]
            for _, r in g.iterrows()
        ]

    # --- EVITAR -------------------------------------------------------------------
    ev = _ler("agg_evitar")
    evitar = [
        [r["familia_catalogo"], _num(r["valor_real"], 0), _num(r["pct_valor_total"], 2),
         bool(r["excluida_do_ranking"]), int(r["linhas"]), int(r["fornecedores"])]
        for _, r in ev.iterrows()
    ]

    # --- qualidade / filtros ------------------------------------------------------
    trat = json.loads((paths.META / "tratamento.json").read_text(encoding="utf-8"))
    qualidade = {
        "conservacao": trat["conservacao"],
        "reconciliacao": trat["reconciliacao"],
        "convencao": trat["convencao_deflacao"],
        "deflatores": trat["deflatores"],
    }

    texto_assump = (paths.WORKSPACE / "ASSUMPTIONS.md").read_text(encoding="utf-8")
    assumptions = _parse_assumptions(texto_assump)

    hashes = {}
    for nome in sorted(IDS.values()):
        p = paths.AGGREGATES / f"{nome}.parquet"
        if p.exists():
            hashes[nome] = _sha256(p)[:16]

    return {
        "meta": {
            "gerado_em": datetime.now(UTC).isoformat(),
            "versao": version,
            "anos": anos,
            "n_familias": len(familias),
            "n_elegiveis": int(score["elegivel"].sum()),
            "teto": float(cfg.get("dispensa.teto_2026")),
            "teto_hist": cfg.get("dispensa.tetos_nominais_por_ano"),
            "raio_km": int(cfg.get("negocio.raio_logistico_km")),
            "ids": IDS,
            "hashes": hashes,
            "pesos": cfg.pesos,
            "limiares": {
                "min_afm": int(cfg.get("metricas.minimo_afm_para_ranking")),
                "min_valor": float(cfg.get("metricas.minimo_valor_real_para_ranking")),
                "pandemia": float(cfg.get("pandemia.limiar_dependencia_pandemia")),
            },
        },
        "familias": familias,
        "dim": dim,
        "metricas": metricas,
        "sens": sens,
        "serie": serie,
        "saz": saz,
        "secretarias": [sec_nome.get(s, s) for s in secretarias],
        "orgaos": orgaos,
        "canais": canais,
        "canal": canal,
        "regioes": regioes,
        "raio_regiao": [raio_por_regiao.get(r, "fora") for r in regioes],
        "regiao": regiao,
        "municipios": municipios,
        "ticket": ticket,
        "concorrencia": concorrencia,
        "prazo": prazo,
        "preco": preco,
        "fornecedores": fornecedores,
        "evitar": evitar,
        "qualidade": qualidade,
        "assumptions": assumptions,
        "evitar_metas": {
            "n_reguladas": len(evitar),
            "n_excluidas": int(sum(1 for e in evitar if e[3])),
        },
    }


def salvar(dados: dict[str, Any]) -> Path:
    destino = paths.AGGREGATES / "panel_data.json"
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    destino.write_text(texto, encoding="utf-8")
    return destino
