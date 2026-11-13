"""Diagnóstico: quais gráficos realmente reagem a cada filtro global.

Para cada combinação (filtro, aba, gráfico) compara a opção do ECharts antes/depois.
Saída: logs/diagnostico_filtros.json + tabela no console.
"""
from __future__ import annotations

import json
import sys
from typing import Any

from playwright.sync_api import sync_playwright

from nicho_bahia import paths

ABAS = {0: "Decisão", 1: "Mercado", 2: "Sazonalidade", 3: "Compradores",
        4: "Concorrência", 5: "Preços", 6: "Logística", 7: "Método"}


def snapshot(pg) -> dict[str, str]:  # noqa: ANN001
    """Hash estável de cada gráfico ECharts visível (série + eixos + dados)."""
    return pg.evaluate(
        """() => {
            const out = {};
            document.querySelectorAll('.chart').forEach(n => {
                const c = window.echarts && echarts.getInstanceByDom(n);
                if (!c) { out[n.id] = 'SEM_INSTANCIA'; return; }
                const o = c.getOption() || {};
                const s = (o.series || []).map(x => ({
                    t: x.type, n: x.name || '',
                    ml: !!x.markLine, mlx: x.markLine ? JSON.stringify(x.markLine.data) : '',
                    d: Array.isArray(x.data) ? x.data.map(v => (v && typeof v === 'object') ? (v.value ?? v.name ?? JSON.stringify(v)) : v) : null
                }));
                out[n.id] = JSON.stringify({s, x: o.xAxis && o.xAxis[0] && o.xAxis[0].data, y: o.yAxis && o.yAxis[0] && o.yAxis[0].data,
                                             yml: o.yAxis && o.yAxis[0] && o.yAxis[0].markLine ? JSON.stringify(o.yAxis[0].markLine.data) : ''});
            });
            out['__cards'] = (document.getElementById('cards') || {}).textContent || '';
            out['__tabela'] = (document.getElementById('t_score') || {}).textContent || '';
            out['__escopo'] = (document.getElementById('escopo') || {}).textContent || '';
            return out;
        }"""
    )


def main() -> None:
    url = (paths.WORKSPACE / "output" / "painel_decisao.html").as_uri()
    resultado: dict[str, Any] = {"abas": {}, "filtros": {}}
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        ctx = nav.new_context(viewport={"width": 1600, "height": 1000})
        pg = ctx.new_page()
        erros: list[str] = []
        pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: erros.append(str(e)))
        pg.goto(url, wait_until="load")
        pg.wait_for_timeout(2500)

        # inicializa todas as abas
        abas = pg.query_selector_all("#tabs button")
        for b in abas:
            b.click()
            pg.wait_for_timeout(400)

        # baseline por aba
        base: dict[int, dict[str, str]] = {}
        for idx in ABAS:
            abas[idx].click()
            pg.wait_for_timeout(500)
            base[idx] = snapshot(pg)

        testes = [
            ("ano", "#f_ano", "2023"),
            ("secretaria", "#f_sec", "1"),
            ("regiao", "#f_reg", "1"),
            ("familia", "#f_fam", "1"),
        ]

        for nome, seletor, valor in testes:
            pg.select_option(seletor, valor)
            pg.wait_for_timeout(700)
            reacao: dict[str, list[str]] = {}
            for idx in ABAS:
                abas[idx].click()
                pg.wait_for_timeout(500)
                atual = snapshot(pg)
                mudaram = [k for k in atual if base[idx].get(k) != atual[k]]
                reacao[str(idx)] = mudaram
            resultado["filtros"][nome] = reacao
            # limpa
            pg.select_option(seletor, "")
            pg.wait_for_timeout(500)
            for idx in ABAS:
                abas[idx].click()
                pg.wait_for_timeout(300)
            # restaura baseline (recalcula, pois o reset pode alterar)
            for idx in ABAS:
                abas[idx].click()
                pg.wait_for_timeout(300)
                base[idx] = snapshot(pg)

        resultado["console_errors"] = erros
        nav.close()

    (paths.LOGS / "diagnostico_filtros.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    print("graph TD")
    for filtro, por_aba in resultado["filtros"].items():
        total = sum(len(v) for v in por_aba.values())
        print(f"\n### filtro '{filtro}' — {total} gráficos reagiram")
        for aba, mudaram in por_aba.items():
            print(f"  aba {aba} ({ABAS[int(aba)]}): {mudaram if mudaram else '— NENHUM'}")
    print(f"\nerros de console: {len(erros)}")
    for e in erros[:5]:
        print("  ", e)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
