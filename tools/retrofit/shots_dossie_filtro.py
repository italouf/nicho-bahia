"""Screenshots do dossiê com filtro aplicado (para conferir o aviso "filtra ou declara")."""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

from nicho_bahia import paths


def main() -> None:
    url = (paths.WORKSPACE / "docs" / "index.html").as_uri()
    shots = paths.LOGS / "retrofit" / "r4"
    shots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--allow-file-access-from-files"])
        pg = nav.new_context(viewport={"width": 1440, "height": 1000}).new_page()
        pg.goto(url, wait_until="load")
        pg.wait_for_timeout(1600)

        # 1) Dossiê com recorte de secretaria → deve avisar que não se aplica
        pg.select_option("#f_sec", "1")
        pg.wait_for_timeout(500)
        pg.get_by_role("tab", name="Dossiê", exact=False).first.click()
        pg.wait_for_timeout(900)
        pg.screenshot(path=str(shots / "dossie_com_secretaria.png"), full_page=False)
        aviso = pg.evaluate("() => (document.getElementById('dossie-aviso')||{}).textContent || ''")
        print("aviso:", aviso.strip()[:140])

        # 2) Dossiê com filtro de família → deve trocar o nicho exibido
        pg.select_option("#f_sec", "")
        pg.wait_for_timeout(300)
        pg.select_option("#f_fam", "2")
        pg.wait_for_timeout(800)
        resumo = pg.evaluate("() => (document.getElementById('dossie-resumo')||{}).textContent || ''")
        sel = pg.evaluate("() => document.getElementById('dossie-select').value")
        print("família filtrada ->", resumo.strip()[:90])
        print("seletor sincronizado:", sel)
        pg.screenshot(path=str(shots / "dossie_com_familia.png"), full_page=False)

        # 3) Método com filtro ativo → declaração permanente
        pg.get_by_role("tab", name="Método", exact=False).first.click()
        pg.wait_for_timeout(600)
        nota = pg.evaluate("() => (document.getElementById('metodo-aviso')||{}).textContent || ''")
        print("nota método:", nota.strip()[:110])
        nav.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
