"""Screenshots do painel por aba, para inspeção visual dirigida."""
from __future__ import annotations

import sys

from playwright.sync_api import sync_playwright

from nicho_bahia import paths

ABAS = {0: "decisao", 1: "mercado", 2: "sazonalidade", 3: "compradores",
        4: "concorrencia", 5: "precos", 6: "logistica"}


def main() -> None:
    html = (paths.WORKSPACE / "output" / "painel_decisao.html").as_uri()
    destino = paths.LOGS / "shots"
    destino.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        ctx = nav.new_context(viewport={"width": 1680, "height": 1150}, device_scale_factor=1)
        pg = ctx.new_page()
        pg.goto(html, wait_until="load")
        pg.wait_for_timeout(2200)
        for idx, nome in ABAS.items():
            pg.query_selector_all("#tabs button")[idx].click()
            pg.wait_for_timeout(1100)
            pg.screenshot(path=str(destino / f"aba{idx}_{nome}.png"), full_page=True)
            print("ok", idx, nome)
        nav.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
