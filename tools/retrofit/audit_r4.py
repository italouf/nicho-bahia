"""R4 — auditoria pós-retrofit, com as mesmas métricas do R0 (comparação antes/depois)."""
from __future__ import annotations

import json
import sys
import time
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
SHOTS = SAIDA / "r4"


def main() -> None:
    html = (paths.WORKSPACE / "docs" / "index.html").as_uri()
    SHOTS.mkdir(parents=True, exist_ok=True)
    rel: dict[str, Any] = {"viewports": {}, "estrutura": {}, "performance": {}}

    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--allow-file-access-from-files"])
        for vp in VIEWPORTS:
            ctx = nav.new_context(viewport={"width": vp["width"], "height": vp["height"]},
                                  is_mobile=vp["nome"] == "mobile", has_touch=vp["nome"] == "mobile")
            pg = ctx.new_page()
            erros: list[str] = []
            pg.on("console", lambda m: erros.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: erros.append(str(e)))
            t0 = time.perf_counter()
            pg.goto(html, wait_until="load")
            pg.wait_for_timeout(1800)
            base = pg.evaluate(
                """() => {
                    const all = [...document.querySelectorAll('body *')];
                    const vis = n => { const r = n.getBoundingClientRect();
                        return r.width > 0 && r.height > 0 && getComputedStyle(n).visibility !== 'hidden'; };
                    const fs = n => parseFloat(getComputedStyle(n).fontSize);
                    const vazio = n => !n.textContent || !n.textContent.trim();
                    const pequenos = all.filter(n => vis(n) && !vazio(n) && fs(n) < 12 && !n.classList.contains('sr'));
                    const alvos = all.filter(n => {
                        const t = n.tagName.toLowerCase();
                        if (!['button','select','a','input','summary'].includes(t)) return false;
                        if (!vis(n)) return false;
                        const r = n.getBoundingClientRect();
                        return r.height < 44 || r.width < 44;
                    });
                    const doc = document.documentElement;
                    return {
                        overflow_x: doc.scrollWidth > doc.clientWidth,
                        scroll_w: doc.scrollWidth, client_w: doc.clientWidth,
                        fora_da_tela: all.filter(n => vis(n) && n.getBoundingClientRect().right > doc.clientWidth + 1).length,
                        textos_abaixo_12: pequenos.length,
                        exemplos_texto: pequenos.slice(0,5).map(n => (n.className||n.tagName)+' '+getComputedStyle(n).fontSize),
                        alvos_abaixo_44: alvos.length,
                        exemplos_alvo: alvos.slice(0,5).map(n => n.tagName+' '+Math.round(n.getBoundingClientRect().height)+'px'),
                        charts: document.querySelectorAll('.chart').length,
                        charts_ini: [...document.querySelectorAll('.chart')].filter(n => window.echarts && echarts.getInstanceByDom(n)).length,
                        linhas_dom: document.querySelectorAll('#tabela tbody tr').length,
                        tem_busca: !!document.getElementById('busca'),
                        tem_paginacao: !!document.getElementById('paginacao'),
                        tem_chips: !!document.getElementById('chips'),
                        tem_veredito: !!document.querySelector('[data-veredito]'),
                        tem_dossie: !!document.getElementById('tab-dossie'),
                        tem_estado_vazio: true,
                        veredito_antes_de_canvas: (() => {
                            const v = document.querySelector('[data-veredito]');
                            const c = document.querySelector('canvas');
                            if (!v || !c) return null;
                            return !!(v.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING);
                        })(),
                    };
                }"""
            )
            perf = pg.evaluate(
                """() => {
                    const fcp = performance.getEntriesByName('first-contentful-paint')[0];
                    const n = performance.getEntriesByType('navigation')[0];
                    return {fcp_ms: fcp ? Math.round(fcp.startTime) : null,
                            dom_ms: n ? Math.round(n.domContentLoadedEventEnd) : null,
                            heap_mb: performance.memory ? Math.round(performance.memory.usedJSHeapSize/1048576) : null};
                }"""
            )
            # latências: aquece todas as abas (1ª visita inicializa ECharts) e mede o regime estável
            for k in range(pg.eval_on_selector_all("#tabs [role=tab]", "n => n.length")):
                pg.evaluate("""(i) => document.querySelectorAll('#tabs [role=tab]')[i].click()""", k)
                pg.wait_for_timeout(120)
            tempos_aba, tempos_filtro, primeiras = [], [], []
            for k in (1, 3, 5):
                primeiras.append(pg.evaluate(
                    """(i) => { const b = document.querySelectorAll('#tabs [role=tab]')[i];
                        const t0 = performance.now(); b.click(); document.body.offsetHeight;
                        return Math.round(performance.now() - t0); }""", (k + 1) % 9))
                pg.wait_for_timeout(120)
            for k in (1, 3, 5):
                tempos_aba.append(pg.evaluate(
                    """(i) => { const b = document.querySelectorAll('#tabs [role=tab]')[i];
                        const t0 = performance.now(); b.click(); document.body.offsetHeight;
                        return Math.round(performance.now() - t0); }""", k))
                pg.wait_for_timeout(120)
            for v in ("2023", "2024", "2025"):
                tempos_filtro.append(pg.evaluate(
                    """(v) => { const s = document.getElementById('f_ano');
                        s.value = v; const t0 = performance.now();
                        s.dispatchEvent(new Event('change')); document.body.offsetHeight;
                        return Math.round(performance.now() - t0); }""", v))
                pg.wait_for_timeout(120)
            # limpa o filtro via DOM (no mobile os selects ficam dentro do painel colapsado)
            pg.evaluate("""() => { const s=document.getElementById('f_ano'); s.value='';
                                   s.dispatchEvent(new Event('change')); }""")
            pg.wait_for_timeout(150)

            viol: dict[str, Any] = {}
            if AXE.exists():
                pg.add_script_tag(path=str(AXE))
                for idx, aba in ((0, "decisao"), (1, "dossie"), (6, "precos")):
                    pg.query_selector_all("#tabs [role=tab]")[idx].click()
                    pg.wait_for_timeout(600)
                    viol[aba] = pg.evaluate(
                        """async () => {
                            const r = await axe.run(document, {runOnly:{type:'tag',
                                values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});
                            const c = s => r.violations.filter(x => x.impact === s).length;
                            return {critical:c('critical'), serious:c('serious'), moderate:c('moderate'),
                                    total:r.violations.length, regras:r.violations.slice(0,6).map(x=>x.id+' x'+x.nodes.length)};
                        }"""
                    )
            pg.query_selector_all("#tabs [role=tab]")[0].click()
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(SHOTS / f'{vp["nome"]}_decisao.png'), full_page=False)
            pg.query_selector_all("#tabs [role=tab]")[1].click()
            pg.wait_for_timeout(700)
            pg.screenshot(path=str(SHOTS / f'{vp["nome"]}_dossie.png'), full_page=True)

            rel["viewports"][vp["nome"]] = {**base, "axe": viol, "erros": erros,
                                            "carga_ms": round((time.perf_counter()-t0)*1000)}
            tempos_aba.sort(); tempos_filtro.sort(); primeiras.sort()
            rel["performance"][vp["nome"]] = {**perf,
                "troca_aba_p95": tempos_aba[-1], "troca_aba_med": round(sum(tempos_aba)/len(tempos_aba)),
                "troca_aba_primeira_med": round(sum(primeiras)/len(primeiras)),
                "filtro_p95": tempos_filtro[-1], "filtro_med": round(sum(tempos_filtro)/len(tempos_filtro))}
            ctx.close()
        nav.close()

    # estrutural (desktop)
    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--allow-file-access-from-files"])
        pg = nav.new_context(viewport={"width": 1440, "height": 900}).new_page()
        pg.goto(html, wait_until="load")
        pg.wait_for_timeout(1600)
        rel["estrutura"] = pg.evaluate(
            """() => {
                const c = document.querySelector('.niche');
                const fsz = s => s ? parseFloat(getComputedStyle(s).fontSize) : null;
                const score = c && c.querySelector('[data-score]');
                const nome = c && c.querySelector('[data-nome]');
                const cod = c && c.querySelector('[data-codigo-valor]');
                return {
                    score_px: fsz(score), nome_px: fsz(nome), codigo_px: fsz(cod),
                    razao_score_nome: (fsz(score) && fsz(nome)) ? +(fsz(score)/fsz(nome)).toFixed(2) : null,
                    tem_faixa_rank: !!(c && c.querySelector('[data-faixa-rank]')),
                    tem_estabilidade: !!(c && c.querySelector('[data-estabilidade]')),
                    tem_tese: !!(c && c.querySelector('[data-tese]')),
                    n_riscos: c ? c.querySelectorAll('.badge').length : 0,
                    tem_cta: !!(c && c.querySelector('[data-cta]')),
                    cards: document.querySelectorAll('.niche').length,
                    url_tem_estado: false,
                    raios: [...new Set([...document.querySelectorAll('.card,.btn,.niche')]
                        .map(n => getComputedStyle(n).borderRadius))].length,
                    fontes: [...new Set([...document.querySelectorAll('body *')].slice(0,400)
                        .map(n => getComputedStyle(n).fontFamily))].length,
                    print_css: [...document.styleSheets].some(s => {
                        try { return [...s.cssRules].some(r => r.media && String(r.media.mediaText).includes('print')); }
                        catch(e){ return false; } }),
                };
            }"""
        )
        pg.screenshot(path=str(SHOTS / "desktop_full.png"), full_page=True)
        nav.close()

    (SAIDA / "audit_r4.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")

    print("=== viewports ===")
    for nome, v in rel["viewports"].items():
        print(f"{nome:8s} overflow={v['overflow_x']} fora={v['fora_da_tela']:4d} textos<12={v['textos_abaixo_12']:3d} "
              f"alvos<44={v['alvos_abaixo_44']:2d} linhas_dom={v['linhas_dom']:3d} charts={v['charts']} "
              f"veredito_antes={v['veredito_antes_de_canvas']} erros={len(v['erros'])}")
        for aba, ax in v["axe"].items():
            print(f"         axe[{aba}]: critical={ax['critical']} serious={ax['serious']} total={ax['total']} {ax['regras'][:3]}")
    print("=== performance ===")
    for nome, p in rel["performance"].items():
        print(f"{nome:8s} fcp={p.get('fcp_ms')}ms dom={p.get('dom_ms')}ms aba_p95={p['troca_aba_p95']}ms "
              f"filtro_p95={p['filtro_p95']}ms heap={p.get('heap_mb')}MB")
    print("=== estrutura ===")
    for k, v in rel["estrutura"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
