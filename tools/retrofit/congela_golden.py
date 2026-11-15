"""T1.1 — congela o golden snapshot dos números ANTES do retrofit.

Captura, do painel atualmente publicado em docs/index.html:
- dados de cada gráfico (séries, eixos, markLines) por aba;
- o CSV exportado pela tabela;
- contagem de linhas e de gráficos.

O resultado é a testemunha do AR-25: depois do retrofit, os mesmos gráficos precisam ter
exatamente os mesmos valores.
"""
from __future__ import annotations

import hashlib
import json
import sys
from typing import Any

from playwright.sync_api import sync_playwright

from nicho_bahia import paths

DESTINO = paths.TESTS / "retrofit"
SAIDA = DESTINO / "golden_series.json"


def snapshot_abas(pg) -> dict[str, Any]:  # noqa: ANN001
    """Todos os gráficos de todas as abas, com dados normalizados."""
    return pg.evaluate(
        """() => {
            const out = {};
            document.querySelectorAll('.chart').forEach(n => {
                const c = window.echarts && echarts.getInstanceByDom(n);
                if (!c) { out[n.id] = null; return; }
                const o = c.getOption() || {};
                const norm = v => {
                    if (v === null || v === undefined) return null;
                    if (Array.isArray(v)) return v.map(norm);
                    if (typeof v === 'object') return {v: norm(v.value ?? null), n: v.name ?? null};
                    if (typeof v === 'number') return Math.round(v * 1e6) / 1e6;
                    return v;
                };
                out[n.id] = {
                    series: (o.series || []).map(s => ({type: s.type, name: s.name || '', data: norm(s.data)})),
                    x: norm(o.xAxis && o.xAxis[0] && o.xAxis[0].data),
                    y: norm(o.yAxis && o.yAxis[0] && o.yAxis[0].data),
                };
            });
            return out;
        }"""
    )


def main() -> None:
    url = (paths.WORKSPACE / "docs" / "index.html").as_uri()
    DESTINO.mkdir(parents=True, exist_ok=True)
    dados: dict[str, Any] = {"fonte": "docs/index.html (pré-retrofit)", "abas": {}, "csv": None}

    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--allow-file-access-from-files"])
        pg = nav.new_context(viewport={"width": 1440, "height": 900}).new_page()
        pg.goto(url, wait_until="load")
        pg.wait_for_timeout(2200)

        abas = pg.query_selector_all("#tabs button")
        for i in range(len(abas)):
            abas[i].click()
            pg.wait_for_timeout(650)
            dados["abas"][str(i)] = snapshot_abas(pg)

        # CSV que a tabela exporta hoje
        dados["csv"] = pg.evaluate("() => document.getElementById('t_score').dataset.csv || ''")
        dados["linhas_tabela"] = pg.evaluate("() => document.querySelectorAll('#t_score tbody tr').length")
        dados["graficos"] = pg.evaluate("() => document.querySelectorAll('.chart').length")
        dados["recomendados_top5"] = pg.evaluate(
            """() => [...document.querySelectorAll('.niche h3')].map(h => h.textContent.trim())"""
        )
        nav.close()

    dados["csv_sha256"] = hashlib.sha256(dados["csv"].encode("utf-8")).hexdigest()
    dados["series_sha256"] = hashlib.sha256(
        json.dumps(dados["abas"], sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"golden salvo em {SAIDA.relative_to(paths.WORKSPACE)}")
    print(f"  gráficos: {dados['graficos']} | linhas da tabela: {dados['linhas_tabela']}")
    print(f"  csv_sha256: {dados['csv_sha256'][:16]}")
    print(f"  series_sha256: {dados['series_sha256'][:16]}")
    print(f"  top5 (ordem atual): {dados['recomendados_top5']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
