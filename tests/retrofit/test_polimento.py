"""AR-23 (impressão) e AR-24 (estado vazio) — os dois critérios que faltavam."""

from __future__ import annotations

import pytest

from .painel import abrir

pytestmark = pytest.mark.retrofit


def test_ar23_impressao_mostra_so_o_conteudo() -> None:
    """Em @media print, navegação/filtros somem e o conteúdo da aba ativa permanece."""
    with abrir() as s:
        s.page.get_by_role("tab", name="Dossiê", exact=False).first.click()
        s.page.wait_for_timeout(600)
        s.page.emulate_media(media="print")
        s.page.wait_for_timeout(250)
        d = s.page.evaluate("""() => {
            const disp = sel => { const n = document.querySelector(sel); return n ? getComputedStyle(n).display : 'ausente'; };
            return {
                nav: disp('.nav'), topo: disp('.topo'), filtros: disp('.filtros'),
                painelAtivo: disp('#tab-dossie'),
                secoesVisiveis: [...document.querySelectorAll('[data-dossie-secao]')]
                    .filter(n => getComputedStyle(n).display !== 'none').length,
                printCss: [...document.styleSheets].some(sh => {
                    try { return [...sh.cssRules].some(r => r.media && String(r.media.mediaText).includes('print')); }
                    catch(e) { return false; } }),
            };
        }""")
        assert d["printCss"], "não há regra @media print"
        assert d["nav"] == "none" and d["topo"] == "none" and d["filtros"] == "none"
        assert d["painelAtivo"] != "none", "o conteúdo precisa continuar visível na impressão"
        assert d["secoesVisiveis"] == 7, f"{d['secoesVisiveis']} seções visíveis na impressão"
        s.page.emulate_media(media="screen")


def test_ar24_estado_vazio_quando_o_grafico_nao_tem_dados() -> None:
    with abrir() as s:
        s.page.get_by_role("tab", name="Concorrência", exact=False).first.click()
        s.page.wait_for_timeout(600)
        # força um gráfico sem dados pelo próprio caminho de render
        # (opção cartesiana completa: o ECharts exige eixos para montar a série)
        s.page.evaluate(
            """() => draw('c_forn', {xAxis:{type:'value'}, yAxis:{type:'category', data:[]},
                                    series:[{type:'bar', data:[]}]})"""
        )
        s.page.wait_for_timeout(250)
        d = s.page.evaluate("""() => {
            const box = document.querySelector('.estado-vazio[data-para="c_forn"]');
            const chart = document.getElementById('c_forn');
            return {temCaixa: !!box, texto: box ? box.textContent : '',
                    chartOculto: chart ? getComputedStyle(chart).display === 'none' : null};
        }""")
        assert d["temCaixa"], "estado vazio não apareceu"
        assert "Sem dados" in d["texto"] and "limpar os filtros" in d["texto"]
        assert d["chartOculto"], "o canvas vazio deveria ficar oculto"
        # ao voltar a ter dados, o aviso desaparece
        s.page.get_by_role("tab", name="Decisão", exact=False).first.click()
        s.page.get_by_role("tab", name="Concorrência", exact=False).first.click()
        s.page.wait_for_timeout(600)
        d2 = s.page.evaluate("""() => {
            const box = document.querySelector('.estado-vazio[data-para="c_forn"]');
            return {visivel: box ? getComputedStyle(box).display !== 'none' : false};
        }""")
        assert not d2["visivel"], "o aviso deveria sumir quando há dados"
