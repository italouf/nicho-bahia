"""R0 — auditoria de UI/UX do painel, com medição (não opinião).

Coleta, por viewport: screenshot, overflow, tipografia < 12px, alvos de toque < 44px,
violações axe-core (critical/serious), tempos de first paint / troca de aba / filtro.
Coleta também dívidas estruturais verificáveis por seletor.

Saída: logs/retrofit/audit.json + screenshots em logs/retrofit/r0/.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

from nicho_bahia import paths

VIEWPORTS = [
    {"nome": "mobile", "width": 360, "height": 800},
    {"nome": "tablet", "width": 768, "height": 1024},
    {"nome": "desktop", "width": 1440, "height": 900},
]
AXE = paths.WORKSPACE / "tmp" / "axe" / "axe.min.js"
SAIDA = paths.LOGS / "retrofit"
SHOTS = SAIDA / "r0"


def main() -> None:
    html = (paths.WORKSPACE / "docs" / "index.html").as_uri()
    SHOTS.mkdir(parents=True, exist_ok=True)
    SAIDA.mkdir(parents=True, exist_ok=True)
    rel: dict[str, Any] = {"alvo": html, "viewports": {}, "estrutura": {}, "performance": {}}

    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--allow-file-access-from-files"])
        for vp in VIEWPORTS:
            ctx = nav.new_context(viewport={"width": vp["width"], "height": vp["height"]},
                                  device_scale_factor=1, is_mobile=vp["nome"] == "mobile",
                                  has_touch=vp["nome"] == "mobile")
            pg = ctx.new_page()
            erros: list[str] = []
            pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: erros.append(str(e)))

            t0 = time.perf_counter()
            pg.goto(html, wait_until="load")
            pg.wait_for_timeout(2200)
            rel["viewports"][vp["nome"]] = {
                "viewport": f'{vp["width"]}x{vp["height"]}',
                "carga_ms": round((time.perf_counter() - t0) * 1000),
                **pg.evaluate(
                    """() => {
                        const all = [...document.querySelectorAll('body *')];
                        const visivel = n => { const r = n.getBoundingClientRect();
                            return r.width > 0 && r.height > 0 && getComputedStyle(n).visibility !== 'hidden'; };
                        const fs = n => parseFloat(getComputedStyle(n).fontSize);
                        const semTexto = n => !n.textContent || !n.textContent.trim();
                        const pequenos = all.filter(n => visivel(n) && !semTexto(n) && fs(n) < 12);
                        const alvos = all.filter(n => {
                            const tag = n.tagName.toLowerCase();
                            if (!['button','select','a','input'].includes(tag) && !n.onclick) return false;
                            if (!visivel(n)) return false;
                            const r = n.getBoundingClientRect();
                            return r.height < 44 || r.width < 44;
                        });
                        const doc = document.documentElement;
                        const caixas = all.filter(n => visivel(n) && n.getBoundingClientRect().right > doc.clientWidth + 1);
                        return {
                            overflow_x: doc.scrollWidth > doc.clientWidth,
                            scroll_w: doc.scrollWidth, client_w: doc.clientWidth,
                            elementos_fora_da_tela: caixas.length,
                            textos_abaixo_de_12px: pequenos.length,
                            exemplos_texto_pequeno: pequenos.slice(0,6).map(n => (n.className||n.tagName)+' '+
                                getComputedStyle(n).fontSize+' "'+(n.textContent||'').trim().slice(0,28)+'"'),
                            alvos_toque_abaixo_44: alvos.length,
                            exemplos_alvo_pequeno: alvos.slice(0,6).map(n => n.tagName+' '+
                                Math.round(n.getBoundingClientRect().height)+'px "'+(n.textContent||'').trim().slice(0,22)+'"'),
                            charts_no_dom: document.querySelectorAll('.chart').length,
                            charts_inicializados: [...document.querySelectorAll('.chart')]
                                .filter(n => window.echarts && echarts.getInstanceByDom(n)).length,
                            linhas_tabela: document.querySelectorAll('#t_score tbody tr').length,
                            tem_busca: !!document.querySelector('#t_score input, [data-busca]'),
                            tem_paginacao: !!document.querySelector('.paginacao, [data-pagina]'),
                            tem_chips_filtro: !!document.querySelector('.chips, [data-chip]'),
                            tem_resumo_executivo: !!document.querySelector('[data-resumo], #resumo'),
                            tem_dossie: !!document.querySelector('[data-dossie], #dossie'),
                            tem_estado_vazio: !!document.querySelector('.vazio, [data-vazio]'),
                        };
                    }"""
                ),
                "erros_console": erros,
            }

            # first contentful paint
            rel["performance"][vp["nome"]] = pg.evaluate(
                """() => {
                    const fcp = performance.getEntriesByName('first-contentful-paint')[0];
                    const nav = performance.getEntriesByType('navigation')[0];
                    return {fcp_ms: fcp ? Math.round(fcp.startTime) : null,
                            dom_ready_ms: nav ? Math.round(nav.domContentLoadedEventEnd) : null,
                            load_ms: nav ? Math.round(nav.loadEventEnd) : null,
                            js_heap_mb: performance.memory ? Math.round(performance.memory.usedJSHeapSize/1048576) : null};
                }"""
            )

            # latência de troca de aba (aba 1) e de filtro
            abas = pg.query_selector_all("#tabs button")
            latencia = pg.evaluate(
                """(i) => {
                    const btns = [...document.querySelectorAll('#tabs button')];
                    const t0 = performance.now();
                    btns[i].click();
                    document.body.offsetHeight;           // força layout
                    const t1 = performance.now();
                    return Math.round(t1 - t0);
                }""",
                1,
            )
            pg.wait_for_timeout(300)
            lat_filtro = pg.evaluate(
                """() => {
                    const sel = document.getElementById('f_fam');
                    sel.value = sel.options[1].value;
                    const t0 = performance.now();
                    sel.dispatchEvent(new Event('change'));
                    document.body.offsetHeight;
                    return Math.round(performance.now() - t0);
                }"""
            )
            pg.evaluate("() => { document.getElementById('f_fam').value=''; document.getElementById('f_fam').dispatchEvent(new Event('change')); }")
            pg.wait_for_timeout(200)

            rel["performance"][vp["nome"]].update({"troca_aba_ms": latencia, "filtro_ms": lat_filtro})

            # axe-core (aba Decisão e aba Preços)
            if AXE.exists():
                pg.add_script_tag(path=str(AXE))
                viol: dict[str, Any] = {}
                for aba_idx, aba_nome in ((0, "decisao"), (5, "precos")):
                    pg.query_selector_all("#tabs button")[aba_idx].click()
                    pg.wait_for_timeout(600)
                    v = pg.evaluate(
                        """async () => {
                            const r = await axe.run(document, {runOnly: {type:'tag', values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});
                            const conta = s => r.violations.filter(x => x.impact === s).length;
                            return {critical: conta('critical'), serious: conta('serious'),
                                    moderate: conta('moderate'), minor: conta('minor'),
                                    total: r.violations.length,
                                    regras: r.violations.slice(0,8).map(x => x.id+' ['+x.impact+'] x'+x.nodes.length),
                                    nodes: r.violations.reduce((a,x)=>a+x.nodes.length,0)};
                        }"""
                    )
                    viol[aba_nome] = v
                rel["viewports"][vp["nome"]]["axe"] = viol
            else:
                rel["viewports"][vp["nome"]]["axe"] = "axe-core ausente"

            pg.screenshot(path=str(SHOTS / f'{vp["nome"]}_decisao.png'), full_page=False)
            pg.query_selector_all("#tabs button")[0].click()
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(SHOTS / f'{vp["nome"]}_topo.png'), full_page=False)
            ctx.close()

        # ---- dívidas estruturais independentes de viewport (desktop) ----
        ctx = nav.new_context(viewport={"width": 1440, "height": 900})
        pg = ctx.new_page()
        pg.goto(html, wait_until="load")
        pg.wait_for_timeout(2000)
        rel["estrutura"] = pg.evaluate(
            """() => {
                const cards = [...document.querySelectorAll('.niche')];
                const primeiro = cards[0];
                const score = primeiro ? primeiro.querySelector('.score') : null;
                const h3 = primeiro ? primeiro.querySelector('h3') : null;
                const fs = n => n ? parseFloat(getComputedStyle(n).fontSize) : null;
                const rotulos = [...document.querySelectorAll('.q, .hint, th, .dim span')].slice(0,400);
                const caixaAlta = rotulos.filter(n => {
                    const t = (n.textContent||'').trim();
                    return t.length > 6 && t === t.toUpperCase() && /[A-ZÀ-Ú]/.test(t);
                });
                return {
                    score_font_px: fs(score), familia_font_px: fs(h3),
                    razao_score_familia: (fs(score) && fs(h3)) ? +(fs(score)/fs(h3)).toFixed(2) : null,
                    familia_texto: h3 ? h3.textContent.slice(0,40) : null,
                    rotulos_em_caixa_alta: caixaAlta.length,
                    exemplos_caixa_alta: caixaAlta.slice(0,5).map(n => (n.textContent||'').trim().slice(0,40)),
                    card_tem_faixa_rank: primeiro ? /1–\\d|1-\\d|faixa/.test(primeiro.textContent) : null,
                    card_tem_cta: primeiro ? !!primeiro.querySelector('button, a') : null,
                    filtros_chips: document.querySelectorAll('.chips .chip, [data-chip]').length,
                    url_tem_estado: location.search.length > 1 || location.hash.length > 1,
                    aba_decisao_primeiro_elemento: document.querySelector('#tab0 .card .q') ?
                        document.querySelector('#tab0 .card .q').textContent.trim().slice(0,60) : null,
                    abas: [...document.querySelectorAll('#tabs button')].map(b => b.textContent.trim()),
                    graficos: document.querySelectorAll('.chart').length,
                    fontes_distintas: [...new Set([...document.querySelectorAll('body *')]
                        .slice(0,600).map(n => getComputedStyle(n).fontFamily))].length,
                    raios_distintos: [...new Set([...document.querySelectorAll('body *')]
                        .slice(0,600).map(n => getComputedStyle(n).borderRadius))].length,
                    espacos_distintos: [...new Set([...document.querySelectorAll('body *')]
                        .slice(0,600).map(n => getComputedStyle(n).paddingTop))].length,
                    tem_print_css: [...document.styleSheets].some(s => {
                        try { return [...s.cssRules].some(r => r.media && String(r.media.mediaText).includes('print')); }
                        catch(e) { return false; } }),
                };
            }"""
        )
        pg.screenshot(path=str(SHOTS / "desktop_decisao_full.png"), full_page=True)
        ctx.close()
        nav.close()

    (SAIDA / "audit.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- resumo no console ----
    print("=== viewports ===")
    for nome, v in rel["viewports"].items():
        print(f"{nome:8s} {v['viewport']:9s} carga={v['carga_ms']}ms overflow={v['overflow_x']} "
              f"textos<12px={v['textos_abaixo_de_12px']} alvos<44px={v['alvos_toque_abaixo_44']} "
              f"charts={v['charts_inicializados']}/{v['charts_no_dom']} linhas={v['linhas_tabela']} "
              f"busca={v['tem_busca']} chips={v['tem_chips_filtro']}")
        for aba, ax in (v.get("axe") or {}).items():
            if isinstance(ax, dict):
                print(f"         axe[{aba}]: critical={ax['critical']} serious={ax['serious']} "
                      f"moderate={ax['moderate']} nos={ax['nodes']} {ax['regras'][:4]}")
    print("=== performance ===")
    for nome, p in rel["performance"].items():
        print(f"{nome:8s} fcp={p.get('fcp_ms')}ms dom={p.get('dom_ready_ms')}ms load={p.get('load_ms')}ms "
              f"aba={p.get('troca_aba_ms')}ms filtro={p.get('filtro_ms')}ms heap={p.get('js_heap_mb')}MB")
    print("=== estrutura ===")
    for k, v in rel["estrutura"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
