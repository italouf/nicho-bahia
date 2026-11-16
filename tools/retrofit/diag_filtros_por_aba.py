"""Diagnóstico dirigido: aplicar filtro SEM trocar de aba e ver o que muda na aba atual.

O teste anterior (A7b) percorria todas as abas depois de filtrar, somando mudanças de abas
que o usuário nem está vendo. Aqui medimos a experiência real: parado numa aba, mexo no
filtro, vejo algo mudar?
"""
from __future__ import annotations

import json
import sys

from playwright.sync_api import sync_playwright

from nicho_bahia import paths

ABAS = ["Decisão", "Dossiê", "Mercado", "Sazonalidade", "Compradores",
        "Concorrência", "Preços", "Logística", "Método"]
FILTROS = [("ano", "#f_ano", "2023"), ("secretaria", "#f_sec", "1"),
           ("região", "#f_reg", "1"), ("família", "#f_fam", "2")]

SNAP = """() => {
    const out = {};
    document.querySelectorAll('.painel').forEach(p => {
        const visivel = p.classList.contains('on');
        const charts = [...p.querySelectorAll('.chart')].map(n => {
            const c = window.echarts && echarts.getInstanceByDom(n);
            if (!c) return null;
            const o = c.getOption() || {};
            return JSON.stringify((o.series||[]).map(s => s.data));
        }).join('|');
        out[p.id] = {
            visivel,
            charts,
            texto: p.textContent.replace(/\\s+/g,' ').trim(),
        };
    });
    out['__chips'] = (document.getElementById('chips')||{}).textContent || '';
    return out;
}"""


def main() -> None:
    url = (paths.WORKSPACE / "docs" / "index.html").as_uri()
    resultado: dict = {"por_aba": {}, "erros": []}

    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--allow-file-access-from-files"])
        ctx = nav.new_context(viewport={"width": 1440, "height": 900})
        pg = ctx.new_page()
        pg.on("console", lambda m: resultado["erros"].append(f"[{m.type}] {m.text}") if m.type == "error" else None)
        pg.on("pageerror", lambda e: resultado["erros"].append(f"[pageerror] {e}"))
        pg.goto(url, wait_until="load")
        pg.wait_for_timeout(1800)

        for aba in ABAS:
            pg.get_by_role("tab", name=aba, exact=False).first.click()
            pg.wait_for_timeout(450)
            base = pg.evaluate(SNAP)
            entrada: dict = {}
            for nome, sel, valor in FILTROS:
                pg.select_option(sel, valor)
                pg.wait_for_timeout(700)
                depois = pg.evaluate(SNAP)
                # compara só a aba visível
                chaves = [k for k in base if k.startswith("tab-")]
                mudou = [k for k in chaves if base[k]["charts"] != depois[k]["charts"] or base[k]["texto"] != depois[k]["texto"]]
                chips = depois["__chips"].strip()
                entrada[nome] = {"abas_que_mudaram": mudou, "chips": chips[:60]}
                pg.select_option(sel, "")
                pg.wait_for_timeout(400)
            resultado["por_aba"][aba] = entrada

        nav.close()

    (paths.LOGS / "retrofit" / "diagnostico_filtros_por_aba.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")

    print("aba            | ano | secretaria | região | família   (✓ = algo mudou na aba visível)")
    print("-" * 92)
    for aba, dados in resultado["por_aba"].items():
        marcas = []
        for nome, *_ in FILTROS:
            ok = "✓" if dados[nome]["abas_que_mudaram"] else "✗"
            marcas.append(f"{ok}")
        print(f"{aba:14s} |  {marcas[0]}  |     {marcas[1]}      |   {marcas[2]}   |   {marcas[3]}")

    print("\n=== detalhe ===")
    for aba, dados in resultado["por_aba"].items():
        inertes = [n for n, *_ in FILTROS if not dados[n]["abas_que_mudaram"]]
        if inertes:
            print(f"{aba}: inertes -> {', '.join(inertes)}")
    print(f"\nerros de console: {len(resultado['erros'])}")
    for e in resultado["erros"][:6]:
        print("  ", e)
    sys.exit(0 if not resultado["erros"] else 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
