"""F5 — Construção do painel: panel_data.json -> output/painel_decisao.html.

Regra bloqueante: só constrói se os gates G3 e G4 estiverem VERDES.
O HTML não faz nenhuma requisição externa: ECharts e dados vão embutidos.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from .. import panel_data, panel_html, paths
from ..config import load_config
from ..logging_utils import RunLog, write_json

ECHARTS_PATH = paths.WORKSPACE / "assets" / "echarts.min.js"


def _checar_gates(log: RunLog) -> dict[str, Any]:
    estados = {}
    for gate, arquivo in (("G3", "gate_g3.json"), ("G4", "gate_g4.json")):
        caminho = paths.LOGS / arquivo
        if not caminho.exists():
            raise RuntimeError(f"{gate} ausente ({arquivo}). Rode --stage validate e --stage score.")
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        estados[gate] = dados.get("status")
        log(f"  {gate}: {dados.get('status')}")
        if dados.get("status") != "VERDE":
            raise RuntimeError(f"{gate} está {dados.get('status')} — painel não pode ser construído.")
    return estados


def run(log: RunLog) -> dict[str, Any]:
    paths.ensure_dirs()
    log.section("F5 — CONSTRUÇÃO DO PAINEL")
    cfg = load_config()

    log("verificando gates (regra bloqueante):")
    gates = _checar_gates(log)

    log("\nempacotando panel_data.json ...")
    dados = panel_data.construir(version=str(cfg.get("meta.versao")))
    destino_json = panel_data.salvar(dados)
    mb_json = destino_json.stat().st_size / 1024 / 1024
    log(f"  [ok] {paths.relative(destino_json)} ({mb_json:.2f} MB)")
    max_json = float(cfg.get("painel.json_maximo_mb"))
    if mb_json > max_json:
        raise RuntimeError(f"panel_data.json com {mb_json:.2f} MB excede o orçamento de {max_json} MB")

    if not ECHARTS_PATH.exists():
        raise RuntimeError(
            "assets/echarts.min.js não encontrado — baixe uma vez e o painel continua offline."
        )
    echarts_js = ECHARTS_PATH.read_text(encoding="utf-8")
    log(f"  ECharts embutido: {len(echarts_js) / 1024:.0f} KB")

    gerado = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    html = panel_html.render(dados, echarts_js, versao=str(cfg.get("meta.versao")), gerado=gerado)

    destino = paths.WORKSPACE / str(cfg.get("painel.arquivo"))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    mb = destino.stat().st_size / 1024 / 1024
    log(f"  [ok] {paths.relative(destino)} ({mb:.2f} MB)")

    max_mb = float(cfg.get("painel.tamanho_maximo_mb"))
    if mb > max_mb:
        raise RuntimeError(f"painel com {mb:.2f} MB excede o limite de {max_mb} MB")

    # inventário dos gráficos para o QA conferir (A7)
    graficos = {
        "c_sens": "A13", "c_serie": "A01", "c_treemap": "A02", "c_cagr": "A03",
        "c_heat": "A05", "c_cal": "A05", "c_orgaos": "A06", "c_canal": "A07",
        "c_ticket": "A08", "c_conc": "A11", "c_ent": "A14", "c_forn": "A15",
        "c_preco": "A16", "c_cv": "A17", "c_desc": "A18", "c_regiao": "A19",
        "c_prazo": "A20", "c_mun": "A21",
    }
    if len(graficos) < int(cfg.get("painel.min_graficos")):
        raise RuntimeError(f"apenas {len(graficos)} gráficos; mínimo {cfg.get('painel.min_graficos')}")

    manifesto = {
        "gerado_em": datetime.now(UTC).isoformat(),
        "gates": gates,
        "panel_data": {"arquivo": paths.relative(destino_json), "mb": round(mb_json, 2),
                       "familias": len(dados["familias"]), "n_elegiveis": dados["meta"]["n_elegiveis"]},
        "html": {"arquivo": paths.relative(destino), "mb": round(mb, 2),
                 "echarts_kb": round(len(echarts_js) / 1024, 0)},
        "graficos": graficos,
        "abas": 8,
        "n_graficos": len(graficos),
        "offline": True,
    }
    write_json(paths.LOGS / "painel_manifest.json", manifesto)
    log(f"  gráficos registrados: {len(graficos)} em 8 abas")
    log(f"[ok] {paths.relative(paths.LOGS / 'painel_manifest.json')}")
    return manifesto
