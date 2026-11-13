"""Screenshots com filtros aplicados, para inspeção do recorte e dos avisos."""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

from nicho_bahia import paths


def main() -> None:
    url = (paths.WORKSPACE / "output" / "painel_decisao.html").as_uri()
    destino = paths.LOGS / "shots"
    destino.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        ctx = nav.new_context(viewport={"width": 1680, "height": 1150})
        pg = ctx.new_page()
        pg.goto(url, wait_until="load")
        pg.wait_for_timeout(2200)

        # 1) recorte por secretaria na aba Mercado
        pg.select_option("#f_sec", "1")
        pg.wait_for_timeout(900)
        pg.query_selector_all("#tabs button")[1].click()
        pg.wait_for_timeout(900)
        pg.screenshot(path=str(destino / "filtro_secretaria_mercado.png"), full_page=True)
        print("ok secretaria/mercado")

        # 2) mesmo recorte na aba de Preços (deve avisar que não se aplica)
        pg.query_selector_all("#tabs button")[5].click()
        pg.wait_for_timeout(900)
        pg.screenshot(path=str(destino / "filtro_secretaria_precos.png"), full_page=True)
        print("ok secretaria/precos")

        # 3) recorte por região na aba Logística (drill)
        pg.select_option("#f_sec", "")
        pg.wait_for_timeout(500)
        pg.select_option("#f_reg", "3")
        pg.wait_for_timeout(900)
        pg.query_selector_all("#tabs button")[6].click()
        pg.wait_for_timeout(900)
        pg.screenshot(path=str(destino / "filtro_regiao_logistica.png"), full_page=True)
        print("ok regiao/logistica")

        nav.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
