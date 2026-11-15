"""Infra comum dos testes de retrofit: abre o painel e coleta erros de console."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from dataclasses import dataclass, field

from playwright.sync_api import Page, sync_playwright

from nicho_bahia import paths

URL = (paths.WORKSPACE / "docs" / "index.html").as_uri()


@dataclass
class Sessao:
    page: Page
    console: list[str] = field(default_factory=list)

    def ir_para(self, aba: str) -> None:
        """Clica na aba pelo rótulo (teste não depende de índice)."""
        self.page.get_by_role("tab", name=aba, exact=False).first.click()
        self.page.wait_for_timeout(450)

    def abas(self) -> list[str]:
        return self.page.eval_on_selector_all(
            '#tabs [role="tab"]', "ns => ns.map(n => n.textContent.trim())"
        )


@contextlib.contextmanager
def abrir(width: int = 1440, height: int = 900, *, mobile: bool = False) -> Iterator[Sessao]:
    with sync_playwright() as pw:
        nav = pw.chromium.launch(args=["--allow-file-access-from-files"])
        ctx = nav.new_context(viewport={"width": width, "height": height},
                              is_mobile=mobile, has_touch=mobile)
        page = ctx.new_page()
        sess = Sessao(page=page)
        page.on("console", lambda m: sess.console.append(f"[{m.type}] {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: sess.console.append(f"[pageerror] {e}"))
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(1800)
        try:
            yield sess
        finally:
            nav.close()


def _valor(el) -> list[float]:
    """Extrai só o VALOR de cada elemento de dado, ignorando metadados de estilo/índice."""
    if isinstance(el, bool) or el is None:
        return []
    if isinstance(el, (int, float)):
        return [round(float(el), 6)]
    if isinstance(el, dict):
        for chave in ("value", "v"):          # `v` é a forma normalizada do golden
            v = el.get(chave)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return [round(float(v), 6)]
        return []
    if isinstance(el, (list, tuple)):
        out: list[float] = []
        for x in el:
            out.extend(_valor(x))
        return out
    return []


def numeros(no) -> list[float]:
    """Números de uma estrutura de dados de gráfico, em ordem, sem metadados.

    Comparar números (e não rótulos nem estilos) é o que o invariante I1 exige: o retrofit
    pode trocar 'CAFE' por 'Cafe' na legenda e a cor da barra, nunca o valor.
    """
    return _valor(no)


def fingerprint_graficos(page: Page, ids: list[str] | None = None) -> dict[str, list[float]]:
    """Imprime a impressão digital numérica de cada gráfico visível."""
    bruto = page.evaluate(
        """() => {
            const out = {};
            document.querySelectorAll('.chart').forEach(n => {
                const c = window.echarts && echarts.getInstanceByDom(n);
                if (!c) return;
                const o = c.getOption() || {};
                out[n.id] = (o.series || []).map(s => s.data === undefined ? null : s.data);
            });
            return out;
        }"""
    )
    alvo = set(ids) if ids else None
    return {
        k: numeros(v) for k, v in bruto.items()
        if (alvo is None or k in alvo) and v is not None
    }
