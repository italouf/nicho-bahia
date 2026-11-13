"""F6 — QA do painel com Playwright headless (A6, A7, A8, A9, A10).

Verifica, em `file://`:
- A6: zero erros de console e zero pageerror;
- A7: ≥ 12 gráficos renderizam;
- A7b: **cada** filtro global (ano, secretaria, região, família) altera de fato os gráficos —
       nenhum filtro pode ser inerte (regressão que passou despercebida na primeira versão);
- A8: o toggle nominal/real altera os valores exibidos;
- A9: a aba Método lista as premissas e os filtros com contagens;
- A10: nenhuma requisição externa e arquivo ≤ 15 MB.

Evidências: logs/qa_report.json + logs/qa_console.log + logs/diagnostico_filtros.json.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from .. import paths
from ..logging_utils import RunLog, write_json

ABAS = ("Decisão", "Mercado", "Sazonalidade", "Compradores", "Concorrência", "Preços", "Logística", "Método")

# filtros globais: (nome, seletor, valor de teste)
FILTROS = (
    ("ano", "#f_ano", "2023"),
    ("secretaria", "#f_sec", "1"),
    ("região", "#f_reg", "1"),
    ("família", "#f_fam", "2"),
)

# quantos itens cada filtro precisa alterar para ser considerado funcional
MIN_ITENS_POR_FILTRO = 3


def _snapshot(pg) -> dict[str, str]:  # noqa: ANN001
    """Estado observável: opções dos gráficos ECharts + blocos HTML da aba 0."""
    return pg.evaluate(
        """() => {
            const out = {};
            document.querySelectorAll('.chart').forEach(n => {
                const c = window.echarts && echarts.getInstanceByDom(n);
                if (!c) { out[n.id] = 'SEM_INSTANCIA'; return; }
                const o = c.getOption() || {};
                const s = (o.series || []).map(x => ({
                    t: x.type, n: x.name || '',
                    ml: x.markLine ? JSON.stringify(x.markLine.data) : '',
                    d: Array.isArray(x.data) ? x.data.map(v => (v && typeof v === 'object')
                        ? (v.value ?? v.name ?? JSON.stringify(v)) : v) : null
                }));
                out[n.id] = JSON.stringify({
                    s,
                    x: o.xAxis && o.xAxis[0] && o.xAxis[0].data,
                    y: o.yAxis && o.yAxis[0] && o.yAxis[0].data,
                    yml: o.yAxis && o.yAxis[0] && o.yAxis[0].markLine ? JSON.stringify(o.yAxis[0].markLine.data) : ''
                });
            });
            out['__cards'] = (document.getElementById('cards') || {}).textContent || '';
            out['__tabela'] = (document.getElementById('t_score') || {}).textContent || '';
            out['__escopo'] = (document.getElementById('escopo') || {}).textContent || '';
            return out;
        }"""
    )


def _snapshot_todas_abas(pg, abas) -> dict[str, dict[str, str]]:  # noqa: ANN001
    out: dict[str, dict[str, str]] = {}
    for i, aba in enumerate(abas):
        aba.click()
        pg.wait_for_timeout(350)
        out[str(i)] = _snapshot(pg)
    return out


def run(log: RunLog) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    paths.ensure_dirs()
    log.section("F6 — QA DO PAINEL (headless)")
    html = paths.WORKSPACE / "output" / "painel_decisao.html"
    if not html.exists():
        raise FileNotFoundError(f"painel não encontrado: {html} (rode --stage build)")
    url = html.as_uri()
    log(f"abrindo {url}")

    console: list[dict[str, str]] = []
    erros: list[str] = []
    requisicoes: list[str] = []

    with sync_playwright() as pw:
        navegador = pw.chromium.launch(args=["--allow-file-access-from-files"])
        contexto = navegador.new_context(viewport={"width": 1600, "height": 1000})
        pagina = contexto.new_page()

        pagina.on("console", lambda m: console.append({"tipo": m.type, "texto": m.text}))
        pagina.on("pageerror", lambda e: erros.append(str(e)))
        pagina.on("request", lambda r: requisicoes.append(r.url))

        pagina.goto(url, wait_until="load")
        pagina.wait_for_timeout(2500)
        erros_console = [c for c in console if c["tipo"] == "error"]
        log(f"console: {len(console)} mensagens ({len(erros_console)} de erro), {len(erros)} pageerror")

        abas = pagina.query_selector_all("#tabs button")
        log(f"abas encontradas: {len(abas)}")
        if len(abas) != len(ABAS):
            raise RuntimeError(f"esperava {len(ABAS)} abas, encontrei {len(abas)}")

        # ---------- A7: todos os gráficos renderizam ao percorrer as abas ----------
        base = _snapshot_todas_abas(pagina, abas)
        graficos_com_canvas = pagina.evaluate(
            """() => [...document.querySelectorAll('.chart')]
                 .filter(n => { const c = n.querySelector('canvas'); return c && c.width > 0; }).length"""
        )
        total_graficos = pagina.evaluate("() => document.querySelectorAll('.chart').length")
        # gráfico com canvas mas SEM dados = bug silencioso (foi o caso do prazo, chave errada no JSON)
        sem_dados = pagina.evaluate(
            """() => {
                 const temDado = v => {
                   if (v === null || v === undefined || v === '') return false;
                   if (Array.isArray(v)) return v.some(x => x !== null && x !== undefined && !Number.isNaN(x));
                   if (typeof v === 'object') return v.value != null || v.name != null;
                   return true;
                 };
                 return [...document.querySelectorAll('.chart')].filter(n => {
                   const c = window.echarts && echarts.getInstanceByDom(n); if(!c) return true;
                   const o = c.getOption() || {};
                   return !(o.series || []).some(s => Array.isArray(s.data) && s.data.some(temDado));
                 }).map(n => n.id);
               }"""
        )
        log(f"gráficos na página: {total_graficos}; com canvas: {graficos_com_canvas}; sem dados: {sem_dados}")

        # ---------- A7b: reatividade de CADA filtro ----------
        reatividade: dict[str, Any] = {}
        for nome, seletor, valor in FILTROS:
            pagina.select_option(seletor, valor)
            pagina.wait_for_timeout(600)
            depois = _snapshot_todas_abas(pagina, abas)
            mudancas: dict[str, list[str]] = {}
            for k in base:
                mudancas[k] = [item for item in depois[k] if base[k].get(item) != depois[k][item]]
            todos = sorted({x for v in mudancas.values() for x in v})
            graficos = [x for x in todos if not x.startswith("__")]
            reatividade[nome] = {
                "itens_alterados": len(todos),
                "graficos_alterados": graficos,
                "por_aba": mudancas,
                "escopo_atualizado": "__escopo" in todos,
            }
            log(f"  filtro {nome:11s}: {len(todos):2d} itens, {len(graficos):2d} gráficos -> {graficos}")
            # limpa e refaz a base (o reset pode mudar o estado renderizado)
            pagina.select_option(seletor, "")
            pagina.wait_for_timeout(400)
            base = _snapshot_todas_abas(pagina, abas)

        (paths.LOGS / "diagnostico_filtros.json").write_text(
            json.dumps({"filtros": {k: v["por_aba"] for k, v in reatividade.items()},
                        "resumo": {k: {"itens": v["itens_alterados"], "graficos": v["graficos_alterados"]}
                                   for k, v in reatividade.items()}},
                       ensure_ascii=False, indent=1),
            encoding="utf-8",
        )

        # ---------- A8: toggle nominal/real ----------
        # antes: secretaria e região são mutuamente exclusivas
        pagina.select_option("#f_sec", "1")
        pagina.wait_for_timeout(300)
        pagina.select_option("#f_reg", "2")
        pagina.wait_for_timeout(400)
        exclusao = pagina.evaluate("""() => ({sec: document.getElementById('f_sec').value,
                                            reg: document.getElementById('f_reg').value})""")
        exclusivo = exclusao["sec"] == "" and exclusao["reg"] == "2"
        log(f"recortes mutuamente exclusivos: {exclusivo} (sec={exclusao['sec']!r}, reg={exclusao['reg']!r})")
        pagina.select_option("#f_reg", "")
        pagina.wait_for_timeout(300)

        pagina.query_selector_all("#tabs button")[1].click()
        pagina.wait_for_timeout(500)
        real_antes = pagina.evaluate(
            """() => echarts.getInstanceByDom(document.getElementById('c_serie')).getOption().series[0].data.slice()"""
        )
        pagina.click("#btn_nom")
        pagina.wait_for_timeout(700)
        nom_depois = pagina.evaluate(
            """() => echarts.getInstanceByDom(document.getElementById('c_serie')).getOption().series[0].data.slice()"""
        )
        conferencia = pagina.evaluate(
            """() => { const i = DATA.familias.filter(f => f.e).sort((a,b)=>a.r-b.r)[0].i;
                 return {i, real: DATA.serie[i].r, nom: DATA.serie[i].n}; }"""
        )
        toggle_ok = real_antes != nom_depois
        # confere contra o agregado embutido
        real_confere = all(abs(float(a) - float(b)) < 1.0 for a, b in zip(real_antes, conferencia["real"], strict=True) if a is not None)
        pagina.click("#btn_real")
        pagina.wait_for_timeout(400)
        log(f"toggle nominal/real alterou valores: {toggle_ok} (confere com o agregado: {real_confere})")

        # ---------- A9: aba Método ----------
        pagina.query_selector_all("#tabs button")[7].click()
        pagina.wait_for_timeout(700)
        metodo = pagina.evaluate(
            """() => ({
                assump: document.querySelectorAll('#l_assump li').length,
                filtros: document.querySelectorAll('#t_filtros tbody tr').length,
                dict: document.querySelectorAll('#t_dict tbody tr').length,
                recon: (document.getElementById('recon')||{}).textContent || ''
            })"""
        )
        log(f"aba método: {metodo['assump']} premissas, {metodo['filtros']} filtros, {metodo['dict']} itens")

        # ---------- A10 ----------
        externas = [u for u in requisicoes if not u.startswith("file://") and not u.startswith("data:")]
        tamanho_mb = html.stat().st_size / 1024 / 1024
        log(f"requisições: {len(requisicoes)} (externas: {len(externas)}); arquivo {tamanho_mb:.2f} MB")

        pagina.screenshot(path=str(paths.LOGS / "qa_aba7.png"), full_page=False)
        navegador.close()

    # ---------- veredito ----------
    checks: list[dict[str, Any]] = []

    def add(id_: str, descricao: str, ok: bool, evidencia: str) -> None:
        checks.append({"id": id_, "descricao": descricao, "status": "OK" if ok else "FALHA", "evidencia": evidencia})

    add("A6", "zero erros de console", not erros_console and not erros,
        f"{len(erros_console)} erros de console, {len(erros)} pageerror")
    add("A7", "≥ 12 gráficos renderizam", graficos_com_canvas >= 12, f"{graficos_com_canvas} gráficos com canvas")
    add("A7c", "todo gráfico tem dados (nenhum vazio)", not sem_dados,
        f"sem dados: {sem_dados or 'nenhum'}")
    add("A7d", "secretaria e região são exclusivas", exclusivo,
        f"sec={exclusao['sec']!r} reg={exclusao['reg']!r}")
    for nome, _sel, _val in FILTROS:
        r = reatividade[nome]
        ok = r["itens_alterados"] >= MIN_ITENS_POR_FILTRO and len(r["graficos_alterados"]) >= 1
        add(f"A7b-{nome}", f"filtro '{nome}' é funcional",
            ok, f"{r['itens_alterados']} itens / {len(r['graficos_alterados'])} gráficos alterados")
    add("A8", "toggle nominal/real altera valores", toggle_ok and real_confere,
        f"real={conferencia['real'][:2]} nom={conferencia['nom'][:2]}")
    add("A9", "aba Método completa", metodo["assump"] >= 20 and metodo["filtros"] >= 4,
        f"{metodo['assump']} premissas / {metodo['filtros']} filtros")
    add("A10", "zero requisições externas", not externas, f"{len(externas)} externas")
    add("A10b", "arquivo ≤ 15 MB", tamanho_mb <= 15.0, f"{tamanho_mb:.2f} MB")

    falhas = [c for c in checks if c["status"] != "OK"]
    report = {
        "gerado_em": datetime.now(UTC).isoformat(),
        "arquivo": str(html),
        "status": "VERDE" if not falhas else "VERMELHO",
        "checks": checks,
        "reatividade_filtros": {
            k: {"itens": v["itens_alterados"], "graficos": v["graficos_alterados"]}
            for k, v in reatividade.items()
        },
        "n_graficos": graficos_com_canvas,
        "console": console,
        "pageerrors": erros,
        "requisicoes": {"total": len(requisicoes), "externas": externas},
        "metodo": metodo,
        "tamanho_mb": round(tamanho_mb, 2),
    }
    write_json(paths.LOGS / "qa_report.json", report)
    with (paths.LOGS / "qa_console.log").open("w", encoding="utf-8") as fh:
        for c in console:
            fh.write(f"[{c['tipo']}] {c['texto']}\n")
        for e in erros:
            fh.write(f"[pageerror] {e}\n")

    log("")
    for r in checks:
        log(f"  [{r['status']:5s}] {r['id']:14s} {r['descricao']:38s} {r['evidencia']}")
    log(f"[{'VERDE' if not falhas else 'VERMELHO'}] QA — {len(checks) - len(falhas)}/{len(checks)} verificações OK")
    log(f"[ok] {paths.relative(paths.LOGS / 'qa_report.json')}")

    if falhas:
        raise RuntimeError("QA VERMELHO: " + ", ".join(r["id"] for r in falhas))
    return report
