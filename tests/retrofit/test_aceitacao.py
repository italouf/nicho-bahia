"""Critérios de aceitação do retrofit (AR-01…AR-23), verificados por Playwright.

Cada teste corresponde a um AR do SPEC_RETROFIT. Não substituem A1–A12 nem a paridade
(`test_paridade.py`): somam-se a eles.
"""

from __future__ import annotations

import pytest

from nicho_bahia import paths

from .painel import abrir

pytestmark = pytest.mark.retrofit

AXE = paths.WORKSPACE / "tmp" / "axe" / "axe.min.js"


# ---------------------------------------------------------------- US-01 decisão
def test_ar01_veredito_antes_de_qualquer_grafico() -> None:
    with abrir() as s:
        ok = s.page.evaluate("""() => {
            const v = document.querySelector('[data-veredito]');
            const c = document.querySelector('canvas');
            const antes = !!(v && c && (v.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING));
            const frase = (document.querySelector('[data-veredito-frase]')||{}).textContent || '';
            const tempo = (document.querySelector('[data-tempo-leitura]')||{}).textContent || '';
            return {antes, frase: frase.trim(), tempo: tempo.trim()};
        }""")
        assert ok["antes"], "o bloco de veredito precisa vir antes do primeiro canvas"
        assert len(ok["frase"]) > 20
        assert "5 min" in ok["tempo"]


def test_ar02_exatamente_tres_cards() -> None:
    with abrir() as s:
        n = s.page.eval_on_selector_all(".niche", "ns => ns.length")
        assert n == 3, f"esperava 3 cards de destaque, achei {n}"


# ---------------------------------------------------------------- US-02 hierarquia
def test_ar03_ar04_codigo_e_metadado_score_e_protagonista() -> None:
    with abrir() as s:
        d = s.page.evaluate("""() => {
            const c = document.querySelector('.niche');
            const px = sel => parseFloat(getComputedStyle(c.querySelector(sel)).fontSize);
            const txt = sel => (c.querySelector(sel).textContent || '').trim();
            return {score: px('[data-score]'), nome: px('[data-nome]'), codigo: px('[data-codigo-valor]'),
                    codigoTxt: txt('[data-codigo-valor]'), nomeTxt: txt('[data-nome]'),
                    temRotuloScore: /score/i.test(c.textContent)};
        }""")
        assert d["codigo"] <= 12, "código da família deve ser metadado (≤12px)"
        assert d["score"] >= 2.0 * d["nome"], "score deve dominar tipograficamente o nome"
        assert d["codigoTxt"] and d["codigoTxt"][0].isdigit(), "código deve estar identificável"
        assert d["temRotuloScore"], "o número precisa do rótulo 'score' ao lado"


# ---------------------------------------------------------------- US-03 incerteza
def test_ar05_faixa_de_rank_e_estabilidade() -> None:
    with abrir() as s:
        d = s.page.evaluate("""() => {
            const c = document.querySelector('.niche');
            const faixa = (c.querySelector('[data-faixa-rank]')||{}).textContent || '';
            const est = (c.querySelector('[data-estabilidade]')||{}).textContent || '';
            const score = (c.querySelector('[data-score]')||{}).textContent || '';
            return {faixa, est, score};
        }""")
        assert "14 cenários" in d["faixa"] and "posição" in d["faixa"]
        assert "%" in d["est"]
        assert len(d["score"].split(",")[-1]) == 1, "score com 1 decimal (sem falsa precisão)"


def test_ar06_flag_com_texto_e_icone() -> None:
    with abrir() as s:
        badges = s.page.eval_on_selector_all(
            ".niche .badge", "ns => ns.map(n => ({txt: n.textContent.trim(), icone: n.querySelector('span') !== null}))"
        )
        assert badges, "cards devem ter badges de risco"
        for b in badges:
            assert b["txt"], "badge sem texto"
            assert b["icone"], "badge sem ícone (cor não pode ser o único canal)"


# ---------------------------------------------------------------- US-04 tese
def test_ar07_tese_curta_com_verbo_e_dois_riscos() -> None:
    with abrir() as s:
        d = s.page.evaluate("""() => {
            const c = document.querySelector('.niche');
            return {tese: (c.querySelector('[data-tese]')||{}).textContent.trim(),
                    riscos: c.querySelectorAll('.badge').length};
        }""")
        assert len(d["tese"]) <= 140, f"tese com {len(d['tese'])} caracteres"
        assert d["tese"].split()[0] in ("Atacar", "Disputar", "Entrar"), "tese deve iniciar por verbo"
        assert d["riscos"] == 2, "exatamente dois riscos por card"


# ---------------------------------------------------------------- US-05 dossiê
def test_ar08_cta_abre_dossie_com_sete_secoes() -> None:
    with abrir() as s:
        s.page.click(".niche [data-cta]")
        s.page.wait_for_timeout(700)
        d = s.page.evaluate("""() => ({
            aba: document.querySelector('#tabs [aria-selected=true]').textContent.trim(),
            secoes: document.querySelectorAll('[data-dossie-secao]').length,
            url: location.search,
            passos: document.querySelectorAll('[data-proximos-passos] li').length,
        })""")
        assert d["aba"] == "Dossiê"
        assert d["secoes"] == 7, f"esperava 7 seções, achei {d['secoes']}"
        assert "dossie=" in d["url"], "a URL deve registrar o dossiê aberto"
        assert d["passos"] >= 3, "próximos passos precisam existir"


def test_ar09_deep_link_do_dossie() -> None:
    with abrir() as s:
        s.page.goto(s.page.url.split("?")[0] + "?aba=dossie&dossie=75.10")
        s.page.wait_for_timeout(1600)
        d = s.page.evaluate("""() => ({
            aba: document.querySelector('#tabs [aria-selected=true]').textContent.trim(),
            selecionado: document.getElementById('dossie-select').value,
            nome: (document.getElementById('dossie-resumo')||{}).textContent || '',
        })""")
        assert d["aba"] == "Dossiê", "URL deve abrir na aba Dossiê"
        assert "escrit" in d["nome"].lower(), "URL deve selecionar o nicho 75.10"


# ---------------------------------------------------------------- US-06 tabela
def test_ar10_busca_filtra_e_atualiza_contador() -> None:
    with abrir() as s:
        s.page.fill("#busca", "caf")
        s.page.wait_for_timeout(350)
        d = s.page.evaluate("""() => ({
            linhas: [...document.querySelectorAll('#tabela tbody tr')].map(t => t.textContent).join(' '),
            contador: document.getElementById('contador').textContent})""")
        assert "caf" in d["linhas"].lower()
        assert "de 155" in d["contador"] and not d["contador"].startswith("155 de"), d["contador"]


def test_ar11_csv_exporta_recorte_completo_nao_a_pagina() -> None:
    with abrir() as s:
        csv = s.page.evaluate("() => document.getElementById('tabela').dataset.csv || ''")
        linhas = [lin for lin in csv.split("\n") if lin.strip()]
        assert len(linhas) == 155, f"CSV com {len(linhas)} linhas (paginação mostra 25)"
        # com busca, o CSV deve refletir o recorte
        s.page.fill("#busca", "caf")
        s.page.wait_for_timeout(300)
        csv2 = s.page.evaluate("() => document.getElementById('tabela').dataset.csv || ''")
        linhas2 = [lin for lin in csv2.split("\n") if lin.strip()]
        assert 0 < len(linhas2) < 155, "CSV deve seguir o recorte da busca"


def test_ar12_tabela_focavel_e_cabecalho_fixo() -> None:
    with abrir() as s:
        d = s.page.evaluate("""() => {
            const sc = document.getElementById('tabela-scroll');
            return {tabindex: sc.getAttribute('tabindex'), role: sc.getAttribute('role'),
                    sticky: getComputedStyle(document.querySelector('#tabela th')).position};
        }""")
        assert d["tabindex"] == "0", "região rolável precisa ser focável (axe)"
        assert d["role"] == "region"
        assert d["sticky"] == "sticky", "cabeçalho deve ficar fixo"


# ---------------------------------------------------------------- US-07 filtros
def test_ar13_chips_do_recorte() -> None:
    with abrir() as s:
        s.page.select_option("#f_ano", "2023")
        s.page.wait_for_timeout(400)
        d = s.page.evaluate("""() => ({chips: document.querySelectorAll('[data-chip]').length,
                                       remover: document.querySelectorAll('[data-chip-remover]').length,
                                       texto: (document.querySelector('[data-chip]')||{}).textContent || ''})""")
        assert d["chips"] == 1 and d["remover"] == 1
        assert "2023" in d["texto"]
        s.page.click("[data-chip-remover]")
        s.page.wait_for_timeout(300)
        assert s.page.eval_on_selector_all("[data-chip]", "n => n.length") == 0


def test_ar14_url_reproduz_recorte() -> None:
    with abrir() as s:
        s.page.select_option("#f_ano", "2024")
        s.page.wait_for_timeout(400)
        url = s.page.url
        assert "ano=2024" in url, url
        s.page.goto(url)
        s.page.wait_for_timeout(1500)
        assert s.page.eval_on_selector("#f_ano", "n => n.value") == "2024"


# ---------------------------------------------------------------- US-08 responsivo
def test_ar15_sem_overflow_e_alvos_44_no_mobile() -> None:
    with abrir(width=360, height=800, mobile=True) as s:
        d = s.page.evaluate("""() => {
            const doc = document.documentElement;
            const alvos = [...document.querySelectorAll('button,select,a,input,summary')].filter(n => {
                const r = n.getBoundingClientRect();
                return r.width > 0 && r.height > 0 && (r.height < 44 || r.width < 44);
            }).length;
            return {scroll: doc.scrollWidth, client: doc.clientWidth, alvos};
        }""")
        assert d["scroll"] <= d["client"] + 1, f"overflow: {d['scroll']} > {d['client']}"
        assert d["alvos"] == 0, f"{d['alvos']} controles abaixo de 44px"


def test_ar16_tabela_vira_cartoes_no_mobile() -> None:
    with abrir(width=360, height=800, mobile=True) as s:
        d = s.page.evaluate("""() => ({
            cartoes: document.querySelectorAll('#tabela-cartoes .tabela__cartao').length,
            scrollVisivel: getComputedStyle(document.getElementById('tabela-scroll')).display,
        })""")
        assert d["cartoes"] > 0, "mobile deve mostrar a tabela como cartões"
        assert d["scrollVisivel"] == "none"


# ---------------------------------------------------------------- US-09 a11y
@pytest.mark.skipif(not AXE.exists(), reason="axe-core ausente")
def test_ar17_axe_sem_violacoes_critical_ou_serious() -> None:
    with abrir(width=360, height=800, mobile=True) as s:
        s.page.add_script_tag(path=str(AXE))
        for aba in ("Decisão", "Dossiê"):
            s.ir_para(aba)
            v = s.page.evaluate(
                """async () => {
                    const r = await axe.run(document, {runOnly:{type:'tag',
                        values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});
                    return {critical: r.violations.filter(x=>x.impact==='critical').length,
                            serious: r.violations.filter(x=>x.impact==='serious').length,
                            ids: r.violations.map(x=>x.id)};
                }"""
            )
            assert v["critical"] == 0 and v["serious"] == 0, f"{aba}: {v}"


def test_ar18_abas_navegaveis_por_teclado() -> None:
    with abrir() as s:
        s.page.focus("#tabbtn-decisao")
        s.page.keyboard.press("ArrowRight")
        s.page.wait_for_timeout(300)
        d = s.page.evaluate("""() => ({foco: document.activeElement.id,
            selecionada: document.querySelector('#tabs [aria-selected=true]').id})""")
        assert d["foco"] == "tabbtn-dossie" and d["selecionada"] == "tabbtn-dossie"


# ---------------------------------------------------------------- US-11 tipografia
def test_ar21_nenhum_texto_de_interface_abaixo_de_12px() -> None:
    for w, h, mob in ((360, 800, True), (1440, 900, False)):
        with abrir(width=w, height=h, mobile=mob) as s:
            n = s.page.evaluate("""() => [...document.querySelectorAll('body *')].filter(n => {
                const r = n.getBoundingClientRect();
                if (r.width === 0 || r.height === 0) return false;
                if (!n.textContent || !n.textContent.trim()) return false;
                if (n.classList.contains('sr') || n.closest('.chart')) return false;
                return parseFloat(getComputedStyle(n).fontSize) < 12;
            }).length""")
            assert n == 0, f"{n} textos de interface abaixo de 12px em {w}px"


def test_ar22_tokens_de_raio_e_espaco() -> None:
    with abrir() as s:
        d = s.page.evaluate("""() => {
            const nos = [...document.querySelectorAll('.card,.btn,.niche,.badge,.chip')];
            const raios = new Set(nos.map(n => getComputedStyle(n).borderRadius));
            const pads = new Set(nos.map(n => getComputedStyle(n).padding));
            return {raios: raios.size, pads: pads.size};
        }""")
        assert d["raios"] <= 4, f"{d['raios']} raios distintos"
        assert d["pads"] <= 8, f"{d['pads']} paddings distintos"


# ---------------------------------------------------------------- US-10 perf
def test_ar20_troca_de_aba_ate_200ms() -> None:
    with abrir() as s:
        n = s.page.eval_on_selector_all("#tabs [role=tab]", "ns => ns.length")
        for i in range(n):                      # aquece (1ª visita inicializa ECharts)
            s.page.evaluate("(i) => document.querySelectorAll('#tabs [role=tab]')[i].click()", i)
            s.page.wait_for_timeout(90)
        tempos = []
        for i in (1, 3, 5, 2):
            tempos.append(s.page.evaluate(
                """(i) => { const b = document.querySelectorAll('#tabs [role=tab]')[i];
                    const t0 = performance.now(); b.click(); document.body.offsetHeight;
                    return performance.now() - t0; }""", i))
            s.page.wait_for_timeout(90)
        mediana = sorted(tempos)[len(tempos)//2]
        assert mediana <= 200, f"mediana {mediana:.0f}ms (tempos: {[round(t) for t in tempos]})"
