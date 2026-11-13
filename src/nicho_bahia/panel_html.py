"""Template do painel HTML único (offline, ECharts embutido, dados embutidos).

Placeholders substituídos por `render()`: __DATA__, __ECHARTS__, __GERADO__, __VERSAO__.
Sem nenhuma referência externa: nada de CDN, fontes, imagens ou fetch.
"""

from __future__ import annotations

import json
from typing import Any

CSS = """
:root{
 --bg:#f6f7f9; --card:#fff; --ink:#16202b; --muted:#5d6b7a; --line:#dfe4ea;
 --accent:#0a6c74; --accent2:#c2410c; --ok:#0f766e; --warn:#b45309; --bad:#b91c1c;
 --shadow:0 1px 2px rgba(16,24,40,.06),0 1px 3px rgba(16,24,40,.10);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
 font-size:14px;line-height:1.45}
header{position:sticky;top:0;z-index:20;background:var(--card);border-bottom:1px solid var(--line);
 box-shadow:var(--shadow);padding:10px 18px 8px}
h1{font-size:16px;margin:0 0 2px;letter-spacing:-.01em}
h1 span{color:var(--accent)}
.sub{color:var(--muted);font-size:11.5px}
.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:8px}
.bar label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
select{font:inherit;font-size:12px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;
 background:#fff;color:var(--ink);max-width:230px}
.toggle{display:inline-flex;border:1px solid var(--line);border-radius:7px;overflow:hidden}
.toggle button{font:inherit;font-size:12px;padding:5px 11px;border:0;background:#fff;color:var(--muted);cursor:pointer}
.toggle button.on{background:var(--accent);color:#fff;font-weight:600}
nav{display:flex;gap:2px;overflow-x:auto;padding:0 14px;background:var(--card);
 border-bottom:1px solid var(--line);position:sticky;top:0;z-index:19}
nav button{font:inherit;font-size:12.5px;white-space:nowrap;padding:9px 12px;border:0;background:none;
 color:var(--muted);cursor:pointer;border-bottom:2px solid transparent}
nav button.on{color:var(--ink);font-weight:600;border-bottom-color:var(--accent)}
main{padding:16px 18px 60px;max-width:1560px;margin:0 auto}
.panel{display:none}
.panel.on{display:block}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(440px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);
 padding:12px 14px 8px;min-width:0}
.card.full{grid-column:1/-1}
.q{font-size:13.5px;font-weight:650;margin:0 0 2px}
.hint{font-size:11.5px;color:var(--muted);margin:0 0 6px}
.chart{width:100%;height:300px}
.chart.tall{height:430px}
.chart.short{height:230px}
footer.src{border-top:1px dashed var(--line);margin-top:8px;padding-top:5px;
 font-size:10.5px;color:var(--muted);display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
footer.src code{font-size:10.5px;background:#eef2f5;padding:1px 5px;border-radius:4px}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{padding:5px 7px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);
 cursor:pointer;user-select:none;white-space:nowrap;background:#fbfcfd;position:sticky;top:0}
th:hover{color:var(--accent)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr:hover td{background:#f8fafb}
.tag{display:inline-block;font-size:10px;padding:1px 6px;border-radius:99px;border:1px solid var(--line);background:#f8fafb}
.tag.ok{color:var(--ok);border-color:#99f6e4;background:#f0fdfa}
.tag.bad{color:var(--bad);border-color:#fecaca;background:#fef2f2}
.tag.warn{color:var(--warn);border-color:#fed7aa;background:#fffbeb}
.cards{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.niche{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;box-shadow:var(--shadow)}
.niche h3{margin:0 0 2px;font-size:13.5px;line-height:1.3}
.score{font-size:26px;font-weight:700;color:var(--accent);line-height:1}
.rank{font-size:11px;color:var(--muted)}
.dims{margin:8px 0 6px;display:grid;gap:3px}
.dim{display:grid;grid-template-columns:112px 1fr 30px;gap:6px;align-items:center;font-size:10.5px;color:var(--muted)}
.dim .track{height:5px;background:#eef2f5;border-radius:3px;overflow:hidden}
.dim .fill{height:100%;background:var(--accent)}
.kv{font-size:11.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 12px;margin:2px 0}
.kv b{color:var(--ink);font-weight:600}
.risco{font-size:11px;color:var(--warn);margin-top:4px}
.btn{font:inherit;font-size:11.5px;padding:5px 10px;border:1px solid var(--line);border-radius:6px;
 background:#fff;cursor:pointer}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.note{font-size:11.5px;color:var(--muted);background:#fbfcfd;border:1px dashed var(--line);
 border-radius:8px;padding:8px 10px;margin:6px 0}
.legend-src{font-size:10.5px;color:var(--muted)}
.escopo{font-size:11.5px;margin-top:6px;padding:5px 9px;border-radius:7px;background:#eef6f7;
 border:1px solid #cfe3e5;color:#0a4f55;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.escopo .tag{margin-left:auto}
.marca{font-size:10.5px;padding:3px 8px;border-radius:6px;margin:2px 0 6px;display:none}
.marca.alerta{display:block;color:#92400e;background:#fffbeb;border:1px solid #fed7aa}
.marca.neutra{display:block;color:#5d6b7a;background:#f6f8f9;border:1px solid var(--line)}
ol.assump{margin:0;padding-left:18px;font-size:12px}
ol.assump li{margin-bottom:5px}
ol.assump .st{font-size:10px;font-weight:600;padding:1px 5px;border-radius:4px;margin-left:4px}
.st.VALIDADA{background:#f0fdfa;color:#0f766e}
.st.PREMISSA{background:#fffbeb;color:#b45309}
.st.A-VALIDAR{background:#fef2f2;color:#b91c1c}
.avoid{font-size:12px}
.avoid td:first-child{max-width:340px}
@media(max-width:900px){.grid{grid-template-columns:1fr}.chart{height:260px}}
"""

BODY = """
<header>
  <h1>Painel de decisão de nicho — compras públicas da Bahia <span>2021–2025</span></h1>
  <div class="sub">
    Base SIMPAS/FIPLAN · escopo: material, não regulado, não pandemia ·
    <span id="hdr_n"></span> nichos ranqueados · valores em R$ de dez/2025 quando “real” ·
    histórias não são previsão
  </div>
  <div class="bar">
    <label for="f_ano">Ano</label>
    <select id="f_ano"><option value="">todos</option></select>
    <label for="f_sec">Secretaria</label>
    <select id="f_sec"><option value="">todas</option></select>
    <label for="f_reg">Região de entrega</label>
    <select id="f_reg"><option value="">todas</option></select>
    <label for="f_fam">Família</label>
    <select id="f_fam"><option value="">todas</option></select>
    <span class="toggle" role="group" aria-label="nominal ou real">
      <button id="btn_real" class="on">R$ reais (dez/2025)</button>
      <button id="btn_nom">R$ nominais</button>
    </span>
    <button class="btn" id="btn_reset">limpar filtros</button>
  </div>
  <div class="escopo" id="escopo"></div>
</header>

<nav id="tabs">
  <button data-tab="0" class="on">0 · Decisão</button>
  <button data-tab="1">1 · Mercado</button>
  <button data-tab="2">2 · Sazonalidade</button>
  <button data-tab="3">3 · Compradores &amp; canal</button>
  <button data-tab="4">4 · Concorrência</button>
  <button data-tab="5">5 · Preços</button>
  <button data-tab="6">6 · Logística</button>
  <button data-tab="7">7 · Método</button>
</nav>

<main>
  <!-- ============================ ABA 0 ============================ -->
  <section class="panel on" id="tab0">
    <div class="card full">
      <p class="q">Quais nichos atacar primeiro?</p>
      <p class="hint">Top 5 por score (0–100). As barras mostram o percentil de cada dimensão; o risco aparece abaixo.</p>
      <div class="cards" id="cards"></div>
      <footer class="src"><span>Score decomposto em 7 dimensões (pesos 20/15/15/15/15/10/10)</span><code>A09 · A13</code></footer>
    </div>

    <div class="card full">
      <p class="q">A recomendação é estável? Como o ranking muda com ±20% nos pesos?</p>
      <p class="hint">Cada família foi reavaliada em 14 cenários de pesos. A barra mostra a faixa de posição; o ponto, a posição de referência.</p>
      <div id="c_sens" class="chart short"></div>
      <footer class="src"><span>Faixa de rank em 14 cenários · % = frequência no top-10</span><code>A13</code></footer>
    </div>

    <div class="card full">
      <p class="q">Compare os nichos — tabela ordenável</p>
      <p class="hint">Clique no cabeçalho para ordenar. “Exportar CSV” baixa exatamente os números exibidos.</p>
      <div style="max-height:420px;overflow:auto">
        <table id="t_score"><thead></thead><tbody></tbody></table>
      </div>
      <div style="margin-top:8px;display:flex;gap:8px;align-items:center">
        <button class="btn" id="btn_csv">Exportar CSV</button>
        <span class="hint" id="t_score_info" style="margin:0"></span>
      </div>
      <footer class="src"><span>Todos os nichos elegíveis</span><code>A09</code></footer>
    </div>

    <div class="card full">
      <p class="q">O que evitar?</p>
      <p class="hint">Famílias com barreira regulatória (registro sanitário, ANVISA, produto controlado) ou majoritariamente reguladas.</p>
      <table class="avoid" id="t_evitar"><thead></thead><tbody></tbody></table>
      <footer class="src"><span>Critério editável em config.yaml → regulados</span><code>A12</code></footer>
    </div>
  </section>

  <!-- ============================ ABA 1 ============================ -->
  <section class="panel" id="tab1">
    <div class="card full">
      <p class="q">Onde está o dinheiro e como ele evoluiu?</p>
      <p class="hint">Gasto anual por família (top 10 por score, ou a família selecionada).</p>
      <div id="c_serie" class="chart tall"></div>
      <footer class="src"><span>R$ milhões por ano · 2021–2025</span><code>A01</code></footer>
    </div>
    <div class="card">
      <p class="q">Qual a fatia de cada família no gasto?</p>
      <p class="hint">Participação no período (ou no ano selecionado).</p>
      <div id="c_treemap" class="chart tall"></div>
      <footer class="src"><span>Área = valor; clique para filtrar</span><code>A02</code></footer>
    </div>
    <div class="card">
      <p class="q">Quais famílias crescem de forma sustentada?</p>
      <p class="hint">CAGR real 2021–2025 — as 20 maiores em módulo.</p>
      <div id="c_cagr" class="chart tall"></div>
      <footer class="src"><span>% ao ano, valores reais</span><code>A03</code></footer>
    </div>
  </section>

  <!-- ============================ ABA 2 ============================ -->
  <section class="panel" id="tab2">
    <div class="card full">
      <p class="q">Quando o órgão compra? (sazonalidade por família)</p>
      <p class="hint">Índice = média do mês ÷ média geral. 1,0 = mês típico; acima de 1,2 = pico.</p>
      <div id="c_heat" class="chart tall"></div>
      <footer class="src"><span>Índice mensal médio 2021–2025 · top 12 famílias por score</span><code>A05</code></footer>
    </div>
    <div class="card full">
      <p class="q">Qual o calendário de ataque do nicho?</p>
      <p class="hint">Meses em que a família selecionada concentra compras — antecipe proposta e estoque.</p>
      <div id="c_cal" class="chart"></div>
      <footer class="src"><span>Índice mensal da família selecionada</span><code>A05</code></footer>
    </div>
  </section>

  <!-- ============================ ABA 3 ============================ -->
  <section class="panel" id="tab3">
    <div class="card full">
      <p class="q">Quem compra e quanto?</p>
      <p class="hint">Top 15 secretarias por valor, com o share do canal dispensa.</p>
      <div id="c_orgaos" class="chart tall"></div>
      <footer class="src"><span>R$ milhões · filtro de ano aplica-se aqui</span><code>A06</code></footer>
    </div>
    <div class="card">
      <p class="q">Por qual porta se entra: dispensa, ata ou licitação?</p>
      <p class="hint">Distribuição do valor por canal de compra.</p>
      <div id="c_canal" class="chart"></div>
      <footer class="src"><span>% do valor no período</span><code>A07</code></footer>
    </div>
    <div class="card">
      <p class="q">O ticket cabe na dispensa?</p>
      <p class="hint">Cada bolha é uma família: ticket mediano por AFM/APS × % de compras abaixo do teto. Bolha = valor.</p>
      <div id="c_ticket" class="chart"></div>
      <footer class="src"><span>Teto de dispensa R$ 65.492,11 (linha vertical)</span><code>A08</code></footer>
    </div>
  </section>

  <!-- ============================ ABA 4 ============================ -->
  <section class="panel" id="tab4">
    <div class="card full">
      <p class="q">A concorrência é fragmentada e há espaço para entrar?</p>
      <p class="hint">Crescimento × concentração (HHI). Bolha = valor. Quadrante superior esquerdo = mercado grande e fragmentado.</p>
      <div id="c_conc" class="chart tall"></div>
      <footer class="src"><span>HHI 0–10.000 (quanto menor, mais fragmentado) · bolha = R$ 2024–2025</span><code>A11</code></footer>
    </div>
    <div class="card">
      <p class="q">Estão entrando fornecedores novos?</p>
      <p class="hint">Novos fornecedores por ano (primeira aparição na base, a partir de 2022).</p>
      <div id="c_ent" class="chart"></div>
      <footer class="src"><span>Contagem de novos entrantes</span><code>A14</code></footer>
    </div>
    <div class="card">
      <p class="q">Quem são os incumbentes?</p>
      <p class="hint">Top fornecedores da família selecionada no período.</p>
      <div id="c_forn" class="chart"></div>
      <footer class="src"><span>R$ milhões por fornecedor</span><code>A15 · A10</code></footer>
    </div>
  </section>

  <!-- ============================ ABA 5 ============================ -->
  <section class="panel" id="tab5">
    <div class="card full">
      <p class="q">Qual a faixa de preço praticada por item-âncora?</p>
      <p class="hint">Mediana anual e faixa p25–p75 dos 3 itens mais comprados da família selecionada.</p>
      <div id="c_preco" class="chart tall"></div>
      <footer class="src"><span>R$ por unidade (reais/nominal conforme o toggle)</span><code>A16</code></footer>
    </div>
    <div class="card">
      <p class="q">O preço é estável?</p>
      <p class="hint">Coeficiente de variação do preço unitário por item (mediana da família).</p>
      <div id="c_cv" class="chart"></div>
      <footer class="src"><span>CV: quanto menor, mais previsível</span><code>A17</code></footer>
    </div>
    <div class="card">
      <p class="q">Quanto se desconta do valor estimado?</p>
      <p class="hint">Desconto mediano praticado sobre o valor estimado da cotação.</p>
      <div id="c_desc" class="chart"></div>
      <footer class="src"><span>% de desconto sobre o estimado</span><code>A18</code></footer>
    </div>
  </section>

  <!-- ============================ ABA 6 ============================ -->
  <section class="panel" id="tab6">
    <div class="card full">
      <p class="q">Onde entregar?</p>
      <p class="hint">Valor por região de entrega. Regiões dentro do raio de 200 km aparecem destacadas.</p>
      <div id="c_regiao" class="chart tall"></div>
      <footer class="src"><span>R$ milhões · raio a partir de Feira de Santana</span><code>A19</code></footer>
    </div>
    <div class="card">
      <p class="q">Em quanto tempo o órgão exige a entrega?</p>
      <p class="hint">Prazo mediano e p90 por família (top 12 por volume de compras).</p>
      <div id="c_prazo" class="chart"></div>
      <footer class="src"><span>Dias corridos</span><code>A20</code></footer>
    </div>
    <div class="card">
      <p class="q">Onde estão os compradores?</p>
      <p class="hint">Municípios de entrega com maior valor.</p>
      <div id="c_mun" class="chart"></div>
      <footer class="src"><span>Top 15 municípios no período</span><code>A21</code></footer>
    </div>
  </section>

  <!-- ============================ ABA 7 ============================ -->
  <section class="panel" id="tab7">
    <div class="card full">
      <p class="q">O que foi filtrado e qual o efeito?</p>
      <p class="hint">Pipeline de exclusão com contagens e reconciliação de valor.</p>
      <table id="t_filtros"><thead></thead><tbody></tbody></table>
      <div id="recon" class="note"></div>
      <footer class="src"><span>Conservação de dados — nada descartado em silêncio</span><code>A22</code></footer>
    </div>
    <div class="card">
      <p class="q">Quais premissas sustentam os números?</p>
      <p class="hint">Todas as premissas de ASSUMPTIONS.md, com status de validação.</p>
      <ol class="assump" id="l_assump"></ol>
      <footer class="src"><span>Premissas também em ASSUMPTIONS.md</span><code>—</code></footer>
    </div>
    <div class="card">
      <p class="q">Quais são as limitações?</p>
      <div id="l_limites" style="font-size:12px"></div>
      <footer class="src"><span>—</span><code>—</code></footer>
    </div>
    <div class="card full">
      <p class="q">Dicionário de indicadores e origem dos dados</p>
      <table id="t_dict"><thead></thead><tbody></tbody></table>
      <footer class="src"><span>Id do agregado no rodapé de cada gráfico</span><code>meta.ids</code></footer>
    </div>
  </section>
</main>
"""

JS = r"""
'use strict';
const DATA = __DATA__;
const ANOS = DATA.meta.anos;
const F = DATA.familias;
const M = DATA.metricas;
const DIM = DATA.dim;
const SENS = DATA.sens;
const SERIE = DATA.serie;
const SAZ = DATA.saz;
const ORG = DATA.orgaos;        // [fam, sec, ano, valorReal, shareDispensa, valorNominal]
const REG = DATA.regiao;        // [fam, regiao, ano, valorReal, valorNominal]
const CAN = DATA.canal;         // [fam, canal, ano, valorReal, linhas, valorNominal]
const MUN = DATA.municipios;    // [fam, municipio, valorReal]
const CONC = DATA.concorrencia; // [fam, ano, hhi, nForn, top3, novos, ativos]

const MET = {v2425:0,vtotal:1,cagr:2,rec:3,afms:4,ticket:5,teto:6,nforn:7,hhi:8,top3:9,
             disp:10,raio:11,cv:12,desc:13,pand:14,penal:15,tetoHist:16,prazo:17,novos:18,linhas:19};
const DIMS = ['demanda','crescimento','recorrência','fit dispensa','fragmentação','estab. preço','logística'];
const CANAL_NOME = {dispensa_eletronica:'Dispensa eletrônica',dispensa_tradicional:'Dispensa tradicional',
  registro_precos:'Registro de preços (ata)',adesao_rp:'Adesão a ata',licitacao:'Licitação',
  contratacao_direta:'Contratação direta',credenciamento:'Credenciamento',alteracao:'Alteração',outros:'Outros'};

const state = {ano:null, sec:null, regiao:null, familia:null, real:true, tab:0, sortCol:null, sortDir:-1};
const charts = {};
const COLORS = ['#0a6c74','#c2410c','#7c3aed','#0369a1','#b45309','#0f766e','#be123c','#4d7c0f',
                '#9333ea','#0891b2','#a16207','#15803d','#9f1239','#4338ca'];

/* ============================ utilidades ============================ */
const nf0 = new Intl.NumberFormat('pt-BR',{maximumFractionDigits:0});
const nf1 = new Intl.NumberFormat('pt-BR',{maximumFractionDigits:1});
const brl  = v => (v==null||isNaN(v)) ? '—' : 'R$ ' + nf0.format(v);
const brlM = v => (v==null||isNaN(v)) ? '—' : 'R$ ' + nf1.format(v/1e6) + ' mi';
const pct  = (v,c=1) => (v==null||isNaN(v)) ? '—' : (v*100).toFixed(c).replace('.',',') + '%';
const num  = v => (v==null||isNaN(v)) ? '—' : nf0.format(v);
const short = n => { const p = String(n).split(' - '); return p.length>1 ? p[0]+' · '+p[1].slice(0,34) : n; };
const curta = n => String(n).replace(/^\d+\s*-\s*/,'').slice(0,52);
const nomeFam = i => F[i] ? F[i].n : '—';
const el = id => document.getElementById(id);
function pick(i){ const s = SERIE[i]; return s ? (state.real ? s.r : s.n) : []; }

/* ============================ cubos de recorte ============================ */
function buildCubo(arr, vRealPos, vNomPos){
  const c = new Map();               // alvo -> Map(fam -> {r:[],n:[]})
  for(const r of arr){
    const k = ANOS.indexOf(r[2]); if(k < 0) continue;
    let m = c.get(r[1]); if(!m){ m = new Map(); c.set(r[1], m); }
    let e = m.get(r[0]); if(!e){ e = {r:new Array(ANOS.length).fill(0), n:new Array(ANOS.length).fill(0)}; m.set(r[0], e); }
    e.r[k] += r[vRealPos]; e.n[k] += r[vNomPos];
  }
  return c;
}
const CUBO_SEC = buildCubo(ORG, 3, 5);
const CUBO_REG = buildCubo(REG, 3, 4);

function cuboAtivo(){
  if(state.sec != null) return {cubo:CUBO_SEC, alvo:state.sec, dim:'secretaria'};
  if(state.regiao != null) return {cubo:CUBO_REG, alvo:state.regiao, dim:'região'};
  return null;
}
const emRecorte = () => state.sec != null || state.regiao != null;

/* série de 5 anos de uma família sob o recorte ativo (null = não comprada no recorte) */
function serieFam(i){
  const c = cuboAtivo();
  if(!c){ const s = SERIE[i]; return s ? (state.real ? s.r.slice() : s.n.slice()) : ANOS.map(()=>null); }
  const e = (c.cubo.get(c.alvo) || new Map()).get(i);
  if(!e) return ANOS.map(()=>null);
  return (state.real ? e.r : e.n).slice();
}
function valorFam(i, ano){
  if(ano != null){
    const s = serieFam(i); const k = ANOS.indexOf(ano);
    const v = s ? s[k] : null;
    return (v == null || v === 0) ? null : v;
  }
  const s = serieFam(i);
  if(!s || s.every(v => v == null)) return null;
  const tot = s.reduce((a,b)=>a+(b||0),0);
  return tot > 0 ? tot : null;
}
function cagrFam(i){
  const s = serieFam(i);
  if(!s) return null;
  const v1 = s[0], v2 = s[s.length-1];
  if(!v1 || !v2 || v1 <= 0 || v2 <= 0) return null;
  return Math.pow(v2/v1, 1/(ANOS.length-1)) - 1;
}

/* famílias visíveis sob o recorte, ordenadas pelo valor do recorte (ou pelo rank global) */
function familiasVisiveis(){
  const base = F.filter(f => f.e);
  if(!emRecorte()) return base.slice().sort((a,b)=>a.r-b.r);
  const comValor = base.map(f => ({f, v: valorFam(f.i, state.ano) || 0})).filter(x => x.v > 0);
  comValor.sort((a,b)=> b.v - a.v);
  return comValor.map(x => x.f);
}
/* ordenação GLOBAL — usada nos gráficos que não conseguem abrir o recorte, para que os
   números exibidos batam com o aviso "escopo completo" */
function familiasGlobais(){
  return F.filter(f => f.e).sort((a,b)=>a.r-b.r);
}
function alvoFamilias(n){
  if(state.familia != null) return [state.familia];
  return familiasVisiveis().slice(0, n).map(f => f.i);
}
function alvoFamiliasGlobal(n){
  if(state.familia != null) return [state.familia];
  return familiasGlobais().slice(0, n).map(f => f.i);
}
function familiaAtual(){
  if(state.familia != null) return state.familia;
  const top = familiasVisiveis();
  return top.length ? top[0].i : (F[0] ? F[0].i : 0);
}
function familiaAtualGlobal(){
  if(state.familia != null) return state.familia;
  const top = familiasGlobais();
  return top.length ? top[0].i : (F[0] ? F[0].i : 0);
}
const filtroFamilia = i => state.familia == null || state.familia === i;

/* valor de uma família para exibição: média 24–25 ou o ano selecionado */
function valorAnoFam(i){
  if(state.ano == null) return M[i][MET.v2425];
  const s = SERIE[i]; if(!s) return null;
  return (state.real ? s.r : s.n)[ANOS.indexOf(state.ano)];
}

/* ============================ marcações de escopo ============================ */
/* Um gráfico pode acumular dois avisos (recorte não suportado + indicador do período).
   Guardamos por id para que uma chamada não apague a outra. */
const MARCAS = {};
function marca(id, texto, tipo){
  const node = el(id); if(!node) return;
  if(!MARCAS[id]) MARCAS[id] = {alerta:'', neutra:''};
  if(!texto && tipo === undefined){ MARCAS[id] = {alerta:'', neutra:''}; }
  else { MARCAS[id][tipo || 'alerta'] = texto || ''; }

  const card = node.closest('.card') || node.parentElement;
  let box = card.querySelector('.marca[data-alvo="'+id+'"]');
  if(!box){
    box = document.createElement('div');
    box.className = 'marca'; box.dataset.alvo = id;
    const hint = card.querySelector('.hint');
    if(hint) hint.after(box); else card.insertBefore(box, node);
  }
  const linhas = [];
  if(MARCAS[id].alerta) linhas.push(MARCAS[id].alerta);
  if(MARCAS[id].neutra) linhas.push(MARCAS[id].neutra);
  const tipoFinal = MARCAS[id].alerta ? 'alerta' : 'neutra';
  box.className = 'marca' + (linhas.length ? ' ' + tipoFinal : '');
  box.innerHTML = linhas.map(l=>`<div>${l}</div>`).join('');
  // dessatura em vez de escurecer: sinaliza "fora do recorte" sem parecer gráfico quebrado
  node.style.opacity = 1;
  node.style.filter = MARCAS[id].alerta ? 'saturate(0.25)' : '';
}
function naoSeAplica(id, quais){
  const ativos = [];
  if(quais.includes('sec') && state.sec != null) ativos.push('secretaria');
  if(quais.includes('regiao') && state.regiao != null) ativos.push('região');
  if(quais.includes('ano') && state.ano != null) ativos.push('ano');
  if(quais.includes('familia') && state.familia != null) ativos.push('família');
  return ativos;
}
/* aviso âmbar: filtro ativo que ESTE gráfico não consegue recortar */
function semRecorte(id, suporta){
  const nao = naoSeAplica(id, ['sec','regiao','ano','familia'].filter(k => !suporta.includes(k)));
  if(nao.length){
    marca(id, '⚠ Este gráfico não abre o recorte por ' + nao.join(' e ') +
      ' — os números são do escopo completo para não misturar bases.', 'alerta');
  } else {
    marca(id, '', 'alerta');
  }
}
/* nota neutra: indicador do período, ano não se aplica */
function notaPeriodo(id){
  if(state.ano != null){
    marca(id, 'Indicador do período completo (2021–2025); o filtro de ano não se aplica.', 'neutra');
  } else {
    marca(id, '', 'neutra');
  }
}

function chart(id){
  if(!charts[id]) charts[id] = echarts.init(el(id), null, {renderer:'canvas'});
  return charts[id];
}
function draw(id, option){ const c = chart(id); c.setOption(option, true); c.resize(); }
const AXIS = {axisLine:{lineStyle:{color:'#cfd6dd'}}, splitLine:{lineStyle:{color:'#eef2f5'}}};
const AXISL = {color:'#5d6b7a', fontSize:10};
const BASE_GRID = {left:8,right:14,top:26,bottom:8,containLabel:true};

/* ============================ filtros ============================ */
function updateEscopo(){
  const b = el('escopo'); const partes = [];
  if(state.ano != null) partes.push('ano ' + state.ano);
  if(state.sec != null) partes.push('secretaria: ' + curta(DATA.secretarias[state.sec]));
  if(state.regiao != null) partes.push('região: ' + curta(DATA.regioes[state.regiao]));
  if(state.familia != null) partes.push('família: ' + short(nomeFam(state.familia)));
  if(!partes.length){
    b.innerHTML = '<span>Sem filtro — visão do estado inteiro, 2021–2025.</span>' +
      '<span class="tag ok">' + DATA.meta.n_elegiveis + ' nichos ranqueados</span>';
  } else {
    b.innerHTML = '<b>Recorte ativo:</b> ' + partes.join(' · ') +
      '<span class="tag warn">o score é global e não é recalculado pelo filtro</span>';
    if(state.sec != null || state.regiao != null){
      b.innerHTML += '<span style="flex-basis:100%;font-size:10.5px;color:#5d6b7a">' +
        'Secretaria e região são recortes alternativos (o agregado não cruza os dois): ao escolher um, o outro é limpo.</span>';
    }
  }
}

function initFilters(){
  const sa = el('f_ano');
  ANOS.forEach(a => { const o=document.createElement('option'); o.value=a; o.textContent=a; sa.appendChild(o); });
  const ss = el('f_sec');
  DATA.secretarias.forEach((s,i) => { const o=document.createElement('option'); o.value=i;
    o.textContent = curta(s).slice(0,62); ss.appendChild(o); });
  const sr = el('f_reg');
  DATA.regioes.forEach((s,i) => { const o=document.createElement('option'); o.value=i;
    o.textContent = curta(s).slice(0,46); sr.appendChild(o); });
  const sf = el('f_fam');
  F.filter(f=>f.e).sort((a,b)=>a.r-b.r).forEach(f => { const o=document.createElement('option');
    o.value=f.i; o.textContent = '#' + f.r + ' ' + short(f.n).slice(0,50); sf.appendChild(o); });

  sa.onchange = e => { state.ano = e.target.value !== '' ? +e.target.value : null; renderTab(); };
  // secretaria e região são recortes ALTERNATIVOS: não existe cruzamento órgão×região no agregado,
  // então manter os dois ativos faria um gráfico ignorar o outro silenciosamente.
  ss.onchange = e => {
    state.sec = e.target.value !== '' ? +e.target.value : null;
    if(state.sec != null){ state.regiao = null; sr.value = ''; }
    renderTab();
  };
  sr.onchange = e => {
    state.regiao = e.target.value !== '' ? +e.target.value : null;
    if(state.regiao != null){ state.sec = null; ss.value = ''; }
    renderTab();
  };
  sf.onchange = e => { state.familia = e.target.value !== '' ? +e.target.value : null; renderTab(); };
  el('btn_real').onclick = () => { state.real=true; el('btn_real').classList.add('on'); el('btn_nom').classList.remove('on'); renderTab(); };
  el('btn_nom').onclick = () => { state.real=false; el('btn_nom').classList.add('on'); el('btn_real').classList.remove('on'); renderTab(); };
  el('btn_reset').onclick = () => { state.ano=state.sec=state.regiao=state.familia=null;
    el('f_ano').value=''; el('f_sec').value=''; el('f_reg').value=''; el('f_fam').value=''; renderTab(); };
  document.querySelectorAll('#tabs button').forEach(b => b.onclick = () => {
    state.tab = +b.dataset.tab;
    document.querySelectorAll('#tabs button').forEach(x=>x.classList.toggle('on', x===b));
    document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('on', p.id==='tab'+state.tab));
    renderTab();
  });
  window.addEventListener('resize', ()=>{ Object.values(charts).forEach(c=>c.resize()); });
}

/* ============================ ABA 0 ============================ */
function renderCards(){
  const top = state.familia != null
    ? [F[state.familia]].filter(f => f && f.e)
    : F.filter(f=>f.e).sort((a,b)=>a.r-b.r).slice(0,5);
  const box = el('cards'); box.innerHTML='';
  const nota = document.createElement('div');
  if(emRecorte()){
    nota.className = 'marca alerta';
    nota.textContent = '⚠ O score é global (todo o estado, 2021–2025) e não é recalculado pelo recorte de ' +
      (state.sec != null ? 'secretaria' : 'região') + '. Use as abas 1 e 3 (ou 6) para ver o recorte.';
    box.appendChild(nota);
  }
  top.forEach(f=>{
    const m = M[f.i] || [], d = DIM[f.i] || [], s = SENS[f.i] || [];
    const st = s[2]!=null ? Math.round(s[2]*100) : null;
    const div = document.createElement('div'); div.className='niche';
    const barras = DIMS.map((nome,k)=>{
      const v = d[k]||0;
      return `<div class="dim"><span>${nome}</span><span class="track"><span class="fill" style="width:${v}%"></span></span><span>${Math.round(v)}</span></div>`;
    }).join('');
    const risco = [];
    if(f.pu!=='consumo recorrente') risco.push('perfil: '+f.pu);
    if((m[MET.pand]||0)>0.3) risco.push('dependência de pandemia '+pct(m[MET.pand],0));
    if(m[MET.penal]) risco.push(m[MET.penal]);
    if(st!=null) risco.push('estabilidade no top-10: '+st+'% em 14 cenários');
    div.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
        <div><h3>${short(f.n)}</h3><div class="rank">#${f.r} · ${f.pu||''}</div></div>
        <div style="text-align:right"><div class="score">${(f.s||0).toFixed(1)}</div><div class="rank">score</div></div>
      </div>
      <div class="dims">${barras}</div>
      <div class="kv">
        <span><b>${brl(valorAnoFam(f.i))}</b>${state.ano != null ? ' em ' + state.ano : '/ano (24–25)'}</span>
        <span>ticket <b>${brl(m[MET.ticket])}</b></span>
        <span><b>${pct(m[MET.teto],0)}</b> ≤ teto</span>
        <span><b>${num(m[MET.nforn])}</b> fornecedores</span>
        <span>HHI <b>${num(m[MET.hhi])}</b></span>
      </div>
      <div class="risco">${risco.join(' · ')}</div>`;
    box.appendChild(div);
  });
  if(!top.length){
    const v = document.createElement('div'); v.className='niche';
    v.textContent = 'Nenhum nicho elegível neste recorte.'; box.appendChild(v);
  }
}

function renderSens(){
  const rows = (state.familia != null ? [F[state.familia]] : familiasVisiveis()).slice(0,12).filter(f=>f&&SENS[f.i]);
  draw('c_sens', {
    grid:{...BASE_GRID, left:8, right:60, top:20, bottom:34},
    tooltip:{trigger:'item', formatter: p => {
      const f = rows[p.dataIndex]; if(!f) return '';
      return `<b>${short(f.n)}</b><br>rank ref: ${SENS[f.i][3]} (faixa ${SENS[f.i][0]}–${SENS[f.i][1]})<br>
              top-10 em ${Math.round(SENS[f.i][2]*100)}% dos 14 cenários`;}},
    xAxis:{type:'value', name:'posição no ranking', nameLocation:'middle', nameGap:24,
           nameTextStyle:{fontSize:10,color:'#5d6b7a'}, ...AXIS, min:0, axisLabel:{...AXISL}},
    yAxis:{type:'category', inverse:true, data:rows.map(f=>short(f.n).slice(0,40)),
           axisLabel:{fontSize:9,...AXISL}, axisLine:AXIS.axisLine},
    series:[
      {type:'bar', data:rows.map(f=>[SENS[f.i][0], SENS[f.i][1]]), itemStyle:{color:'#bbd8da',borderRadius:3},
       barWidth:8, silent:true, name:'faixa'},
      {type:'scatter', data:rows.map((f,k)=>[SENS[f.i][3], k]), symbolSize:9,
       itemStyle:{color:'#0a6c74'}, name:'referência'}
    ]
  });
}

const COLS_SCORE = [
  ['r','#',f=>f.r,true], ['n','Família',f=>short(f.n),false], ['s','Score',f=>f.s,true],
  ['pu','Perfil',f=>f.pu,false], ['v','R$ por ano',f=>valorAnoFam(f.i),true],
  ['c','CAGR real',f=>M[f.i][MET.cagr],true], ['rec','Recorrência',f=>M[f.i][MET.rec],true],
  ['tk','Ticket med.',f=>M[f.i][MET.ticket],true], ['te','% ≤ teto',f=>M[f.i][MET.teto],true],
  ['nf','Nº forn.',f=>M[f.i][MET.nforn],true], ['hh','HHI',f=>M[f.i][MET.hhi],true],
  ['dp','% dispensa',f=>M[f.i][MET.disp],true], ['ra','% no raio',f=>M[f.i][MET.raio],true],
];
function renderTabela(){
  let rows = (state.familia != null ? [F[state.familia]] : familiasVisiveis()).filter(Boolean);
  if(state.sortCol){ const c = COLS_SCORE.find(x=>x[0]===state.sortCol);
    if(c) rows = rows.slice().sort((a,b)=>((c[2](a)||0)-(c[2](b)||0))*state.sortDir); }
  const fmt = {r:v=>'#'+v, n:v=>v, s:v=>(v||0).toFixed(1), pu:v=>v||'—', v:v=>brl(v), c:v=>pct(v,1),
               rec:v=>pct(v,0), tk:v=>brl(v), te:v=>pct(v,0), nf:v=>num(v), hh:v=>num(v),
               dp:v=>pct(v,0), ra:v=>pct(v,0)};
  const thead = el('t_score').tHead, tbody = el('t_score').tBodies[0];
  thead.innerHTML = '<tr>' + COLS_SCORE.map(c=>{
    const rotulo = (c[0]==='v' && state.ano != null) ? 'R$ ' + state.ano : c[1];
    return `<th class="${c[3]?'num':''}" data-k="${c[0]}">${rotulo}</th>`;
  }).join('') + '</tr>';
  tbody.innerHTML = rows.map(f=>'<tr>' + COLS_SCORE.map(c=>{
      const v = c[0]==='s' ? f.s : c[2](f);
      if(c[0]==='pu'){
        const clsTag = f.pu==='consumo recorrente' ? 'ok' : (f.pu==='misto' ? 'warn' : 'bad');
        return `<td><span class="tag ${clsTag}">${f.pu||'—'}</span></td>`;
      }
      return `<td class="${c[3]?'num':''}">${fmt[c[0]](v)}</td>`;
    }).join('') + '</tr>').join('');
  thead.querySelectorAll('th').forEach(th => th.onclick = () => {
    const k = th.dataset.k;
    if(state.sortCol===k){ state.sortDir *= -1; } else { state.sortCol=k; state.sortDir=-1; }
    renderTabela();
  });
  el('t_score_info').textContent = rows.length + ' nichos elegíveis' +
    (state.familia != null ? ' (família filtrada)' : '') +
    (emRecorte() ? ' · recorte por ' + (state.sec!=null?'secretaria':'região') + ' (score global)' : '');
  el('t_score').dataset.csv = rows.map(f=>COLS_SCORE.map(c=>{
    const v = c[0]==='s'?f.s:c[2](f);
    return c[0]==='n' ? '"'+short(f.n)+'"' : (v==null?'':String(v).replace('.',','));
  }).join(';')).join('\n');
}

function renderEvitar(){
  const th = el('t_evitar').tHead, tb = el('t_evitar').tBodies[0];
  th.innerHTML = '<tr><th>Família</th><th class="num">R$ no material</th><th class="num">% do total</th><th class="num">Linhas</th><th class="num">Fornecedores</th><th>Situação</th></tr>';
  const relevantes = DATA.evitar.filter(r => (r[1]||0) >= 1e6 || (r[2]||0) >= 0.01);
  const omitidas = DATA.evitar.length - relevantes.length;
  tb.innerHTML = relevantes.map(r=>`<tr><td>${short(r[0])}</td><td class="num">${brl(r[1])}</td>
    <td class="num">${(r[2]||0).toFixed(2).replace('.',',')}%</td><td class="num">${num(r[4])}</td>
    <td class="num">${num(r[5])}</td>
    <td>${r[3]?'<span class="tag bad">excluída do ranking</span>':'<span class="tag warn">parcialmente regulada</span>'}</td></tr>`).join('')
    + (omitidas ? `<tr><td colspan="6" style="color:#5d6b7a;font-size:11px">+ ${omitidas} famílias com valor irrelevante (&lt; R$ 1 mi e &lt; 0,01% do total), omitidas desta lista</td></tr>` : '');
}

/* ============================ ABA 1 ============================ */
function renderSerie(){
  const fams = alvoFamilias(10);
  draw('c_serie', {
    color: COLORS, grid:{...BASE_GRID, right:160},
    tooltip:{trigger:'axis', valueFormatter:v => brl(v)},
    legend:{type:'scroll', right:0, top:0, orient:'vertical', textStyle:{fontSize:10}, itemWidth:10, itemHeight:8},
    xAxis:{type:'category', data:ANOS, ...AXIS, axisLabel:{...AXISL}},
    yAxis:{type:'value', ...AXIS, axisLabel:{...AXISL, formatter:v=>v===0?'0':nf1.format(v/1e6)+' mi'}},
    series: fams.map(i=>({name:short(nomeFam(i)).slice(0,32), type:'line', smooth:true,
      symbolSize:5, lineStyle:{width:2}, data:serieFam(i), connectNulls:false,
      markLine: state.ano ? {silent:true, symbol:'none', lineStyle:{color:'#c2410c',type:'dashed'},
        label:{formatter:String(state.ano),fontSize:9}, data:[{xAxis:String(state.ano)}]} : undefined,
      endLabel:{show:fams.length<=5, formatter:p=>short(p.seriesName).slice(0,18), fontSize:9}}))
  });
  semRecorte('c_serie', ['ano','sec','regiao','familia']);
}
function renderTreemap(){
  const todos = familiasVisiveis().map(f=>({name:short(f.n), value:Math.round(valorFam(f.i, state.ano)||0), i:f.i}))
    .filter(d=>d.value>0).sort((a,b)=>b.value-a.value);
  const dados = todos.slice(0, 40);
  const tot = todos.reduce((a,b)=>a+b.value,0);
  if(todos.length > dados.length){
    marca('c_treemap', 'Exibindo as 40 maiores famílias de ' + todos.length + ' no recorte ' +
      '(' + pct(dados.reduce((a,b)=>a+b.value,0)/(tot||1),1) + ' do valor).', 'neutra');
  } else {
    marca('c_treemap', '', 'neutra');
  }
  draw('c_treemap', {
    tooltip:{formatter: p => `<b>${p.name}</b><br>${brl(p.value)} (${pct(p.value/(tot||1),1)})`},
    series:[{type:'treemap', roam:false, nodeClick:'false', breadcrumb:{show:false},
      label:{fontSize:10, color:'#fff', overflow:'truncate'}, upperLabel:{show:false},
      itemStyle:{borderColor:'#fff',borderWidth:1,gapWidth:1},
      levels:[{color:COLORS, colorMappingBy:'index'}], data:dados}]
  });
  semRecorte('c_treemap', ['ano','sec','regiao','familia']);
}
function renderCagr(){
  // sob recorte, CAGR de base minúscula é ruído: exige massa mínima (0,5% do recorte)
  let base = familiasVisiveis();
  if(emRecorte()){
    const totalRecorte = base.reduce((a,f)=>a + (valorFam(f.i, null)||0), 0);
    base = base.filter(f => (valorFam(f.i, null)||0) >= totalRecorte * 0.005);
  }
  const rows = base.map(f=>({f, c: emRecorte() ? cagrFam(f.i) : M[f.i][MET.cagr]}))
    .filter(x=>x.c!=null && isFinite(x.c))
    .sort((a,b)=>Math.abs(b.c)-Math.abs(a.c)).slice(0,20)
    .sort((a,b)=>a.c-b.c);
  if(!rows.length){ draw('c_cagr', {title:{text:'Sem série suficiente neste recorte', left:'center', top:'middle', textStyle:{fontSize:12,color:'#5d6b7a'}}}); }
  else draw('c_cagr', {
    grid:{...BASE_GRID, left:8, right:50, top:10, bottom:24},
    tooltip:{trigger:'item', formatter:p=>`<b>${p.name}</b><br>CAGR real: ${pct(p.value/100,1)}`},
    xAxis:{type:'value', ...AXIS, axisLabel:{...AXISL, formatter:v=>nf0.format(v)+'%'}},
    yAxis:{type:'category', data:rows.map(x=>short(x.f.n).slice(0,38)), axisLabel:{fontSize:9,...AXISL}},
    series:[{type:'bar', data:rows.map(x=>+(x.c*100).toFixed(1)),
      itemStyle:{color:p=>p.value>=0?'#0a6c74':'#b91c1c', borderRadius:2}, barWidth:9}]
  });
  semRecorte('c_cagr', ['ano','sec','regiao','familia']);
}

/* ============================ ABA 2 ============================ */
function renderHeat(){
  const fams = alvoFamiliasGlobal(12);
  const mes = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
  const dados = [];
  fams.forEach((i,r)=>{ const s = SAZ[i]||[]; for(let c=0;c<12;c++) dados.push([c,r,s[c]==null?null:s[c]]); });
  draw('c_heat', {
    grid:{...BASE_GRID, left:8, right:20, top:10, bottom:44},
    tooltip:{formatter:p=>`<b>${short(nomeFam(fams[p.value[1]])).slice(0,40)}</b><br>${mes[p.value[0]]}: índice ${p.value[2]}`},
    xAxis:{type:'category', data:mes, splitArea:{show:true}, axisLabel:{fontSize:10,...AXISL}},
    yAxis:{type:'category', data:fams.map(i=>short(nomeFam(i)).slice(0,38)), axisLabel:{fontSize:9,...AXISL}},
    visualMap:{min:0.5, max:2.0, calculable:false, orient:'horizontal', left:'center', bottom:0,
      itemHeight:90, itemWidth:12, textStyle:{fontSize:10},
      inRange:{color:['#f0f9fa','#a7d8db','#4fa3aa','#0a6c74','#084c52']}},
    series:[{type:'heatmap', data:dados, label:{show:true,fontSize:8,formatter:p=>p.value[2]==null?'':p.value[2].toFixed(1)},
      emphasis:{itemStyle:{borderColor:'#16202b',borderWidth:1}}}]
  });
  semRecorte('c_heat', ['familia']);
}
function renderCal(){
  const i = familiaAtualGlobal();
  const s = SAZ[i] || [];
  const mes = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
  draw('c_cal', {
    grid:{...BASE_GRID, top:16, bottom:20},
    tooltip:{formatter:p=>`${mes[p.dataIndex]}: índice ${s[p.dataIndex]}`},
    xAxis:{type:'category', data:mes, ...AXIS, axisLabel:{...AXISL}},
    yAxis:{type:'value', min:0, ...AXIS, axisLabel:{...AXISL}},
    series:[{type:'bar', data:s.map(v=>v==null?null:+v.toFixed(2)),
      itemStyle:{color:p=>p.value>=1.2?'#c2410c':(p.value>=1?'#0a6c74':'#bbd8da'), borderRadius:3},
      markLine:{silent:true, symbol:'none', lineStyle:{color:'#5d6b7a',type:'dashed'},
        label:{formatter:p=>p.value===1?'média':'pico 1,2', fontSize:9, position:'insideEndTop', color:'#5d6b7a'},
        data:[{yAxis:1},{yAxis:1.2}]}}]
  });
  semRecorte('c_cal', ['familia']);
}

/* ============================ ABA 3 ============================ */
function renderOrgaos(){
  if(emRecorte() && state.sec == null){
    semRecorte('c_orgaos', ['ano','familia']);   // região ativa: sem cruzamento órgão×região
    return;
  }
  semRecorte('c_orgaos', ['ano','sec','familia']);

  if(state.sec != null){
    // drill: o que esta secretaria compra
    const acc = new Map();
    ORG.forEach(r=>{
      if(r[1] !== state.sec) return;
      if(state.ano != null && r[2] !== state.ano) return;
      if(!filtroFamilia(r[0])) return;
      const cur = acc.get(r[0]) || {v:0, d:0};
      cur.v += r[3]; cur.d += r[3]*(r[4]||0); acc.set(r[0], cur);
    });
    const arr = [...acc.entries()].map(([fam,o])=>({fam, v:o.v, disp:o.v?o.d/o.v:0}))
      .sort((a,b)=>b.v-a.v).slice(0,15).reverse();
    if(!arr.length){
      draw('c_orgaos', {title:{text:'Nenhuma compra desta secretaria neste recorte', left:'center', top:'middle', textStyle:{fontSize:12,color:'#5d6b7a'}}});
      return;
    }
    draw('c_orgaos', {
      grid:{...BASE_GRID, left:8, right:70, top:8, bottom:8},
      tooltip:{trigger:'item', formatter:p=>{ const r=arr[p.dataIndex];
        return `<b>${short(nomeFam(r.fam))}</b><br>${brl(r.v)}<br>dispensa: ${pct(r.disp,0)}`;}},
      xAxis:{type:'value', ...AXIS, axisLabel:{...AXISL, formatter:v=>nf1.format(v/1e6)+' mi'}},
      yAxis:{type:'category', data:arr.map(r=>short(nomeFam(r.fam)).slice(0,42)), axisLabel:{fontSize:9,...AXISL}},
      series:[{type:'bar', data:arr.map(r=>({value:r.v, itemStyle:{color:'#0a6c74', borderRadius:2}})), barWidth:10,
        label:{show:true, position:'right', fontSize:9, formatter:p=>pct(arr[p.dataIndex].disp,0)+' disp.'}}]
    });
    return;
  }

  // visão padrão: top secretarias
  const acc = new Map();
  ORG.forEach(r=>{
    if(!filtroFamilia(r[0])) return;
    if(state.ano != null && r[2] !== state.ano) return;
    const cur = acc.get(r[1]) || {v:0, vd:0};
    cur.v += r[3]; cur.vd += r[3]*(r[4]||0); acc.set(r[1], cur);
  });
  const arr = [...acc.entries()].map(([sec,o])=>({sec, v:o.v, disp:o.v?o.vd/o.v:0}))
    .sort((a,b)=>b.v-a.v).slice(0,15).reverse();
  draw('c_orgaos', {
    grid:{...BASE_GRID, left:8, right:70, top:8, bottom:8},
    tooltip:{trigger:'item', formatter:p=>{ const r=arr[p.dataIndex];
      return `<b>${curta(DATA.secretarias[r.sec])}</b><br>${brl(r.v)}<br>dispensa: ${pct(r.disp,0)}`;}},
    xAxis:{type:'value', ...AXIS, axisLabel:{...AXISL, formatter:v=>nf1.format(v/1e6)+' mi'}},
    yAxis:{type:'category', data:arr.map(r=>curta(DATA.secretarias[r.sec]).slice(0,42)), axisLabel:{fontSize:9,...AXISL}},
    series:[{type:'bar', data:arr.map(r=>({value:r.v, itemStyle:{color:'#0a6c74', borderRadius:2}})), barWidth:10,
      label:{show:true, position:'right', fontSize:9, formatter:p=>pct(arr[p.dataIndex].disp,0)+' disp.'}}]
  });
}
function renderCanal(){
  semRecorte('c_canal', ['ano','familia']);
  const acc = new Map();
  CAN.forEach(r=>{
    if(!filtroFamilia(r[0])) return;
    if(state.ano != null && r[2] !== state.ano) return;
    const v = state.real ? r[3] : r[5];
    acc.set(r[1], (acc.get(r[1])||0) + v);
  });
  const dados = [...acc.entries()].map(([ci,v])=>({name:CANAL_NOME[DATA.canais[ci]]||DATA.canais[ci], value:Math.round(v)}))
    .filter(d=>d.value>0).sort((a,b)=>b.value-a.value);
  const tot = dados.reduce((a,b)=>a+b.value,0) || 1;
  draw('c_canal', {
    tooltip:{formatter:p=>`<b>${p.name}</b><br>${brl(p.value)} (${pct(p.value/tot,1)})`},
    legend:{bottom:0, textStyle:{fontSize:9}, itemWidth:9, itemHeight:8},
    series:[{type:'pie', radius:['42%','72%'], center:['50%','44%'], data:dados,
      label:{fontSize:9, formatter:p=>pct(p.value/tot,0)},
      itemStyle:{borderColor:'#fff',borderWidth:1}}]
  });
}
function renderTicket(){
  semRecorte('c_ticket', ['familia']);
  notaPeriodo('c_ticket');
  const rows = familiasGlobais().filter(f=>M[f.i][MET.ticket]>0);
  draw('c_ticket', {
    grid:{...BASE_GRID, top:16, bottom:28},
    tooltip:{formatter:p=>{const f=rows[p.dataIndex];
      return `<b>${short(f.n).slice(0,44)}</b><br>ticket mediano ${brl(M[f.i][MET.ticket])}<br>
      ${pct(M[f.i][MET.teto],0)} das AFM/APS ≤ teto<br>valor ${brlM(M[f.i][MET.v2425])}/ano`;}},
    xAxis:{type:'log', name:'ticket mediano por AFM/APS (escala log)', nameLocation:'middle', nameGap:22,
      nameTextStyle:{fontSize:9,color:'#5d6b7a'}, ...AXIS,
      axisLabel:{...AXISL, formatter:v=>v>=1e6?(v/1e6)+'mi':(v>=1e3?(v/1e3)+'k':v)}},
    yAxis:{type:'value', name:'% ≤ teto', max:1, ...AXIS, axisLabel:{...AXISL, formatter:v=>Math.round(v*100)+'%'}},
    series:[{type:'scatter', data:rows.map((f,k)=>[M[f.i][MET.ticket], M[f.i][MET.teto], M[f.i][MET.v2425], k]),
      symbolSize: d => Math.max(5, Math.min(34, Math.sqrt(d[2]||0)/260)),
      itemStyle:{color:p=>{ const r=rows[p.data[3]];
        return (state.familia!=null && r.i===state.familia) ? '#c2410c' : '#0a6c74'; }, opacity:.78},
      markLine:{silent:true, symbol:'none', lineStyle:{color:'#c2410c', type:'dashed'},
        label:{formatter:'teto', fontSize:9, position:'insideEndTop'}, data:[{xAxis:DATA.meta.teto}]}}]
  });
}

/* ============================ ABA 4 ============================ */
function renderConc(){
  semRecorte('c_conc', ['ano','familia']);
  notaPeriodo('c_conc');
  const ano = state.ano;
  const rows = familiasGlobais().filter(f=>M[f.i][MET.hhi]!=null);
  const dados = rows.map((f,k)=>{
    let hhi = M[f.i][MET.hhi], top3 = M[f.i][MET.top3], nf = M[f.i][MET.nforn];
    if(ano != null){
      const r = CONC.find(x=>x[0]===f.i && x[1]===ano);
      if(!r) return null;
      hhi = r[2]; top3 = r[4]; nf = r[3];
    }
    const cagr = M[f.i][MET.cagr];              // sempre global: este gráfico não abre recorte
    if(cagr == null || !isFinite(cagr)) return null;
    const val = M[f.i][MET.v2425];
    return [cagr, hhi, val||0, k, top3, nf];
  }).filter(Boolean);
  draw('c_conc', {
    grid:{...BASE_GRID, top:20, bottom:30},
    tooltip:{formatter:p=>{const d=p.data; const f=rows[d[3]];
      return `<b>${short(f.n).slice(0,46)}</b><br>CAGR ${pct(d[0],1)}<br>HHI ${num(d[1])}<br>
      ${num(d[5])} fornecedores · ${brlM(d[2])}/ano<br>top-3: ${pct(d[4],0)}`;}},
    xAxis:{type:'value', name:'CAGR real 2021–2025', nameLocation:'middle', nameGap:24,
      nameTextStyle:{fontSize:9,color:'#5d6b7a'}, ...AXIS, axisLabel:{...AXISL, formatter:v=>Math.round(v*100)+'%'}},
    yAxis:{type:'value', name:'HHI (concentração)', nameTextStyle:{fontSize:9,color:'#5d6b7a'}, ...AXIS,
      axisLabel:{...AXISL, formatter:v=>v>=1000?(v/1000)+'k':v},
      markLine:{silent:true, symbol:'none', lineStyle:{color:'#c2410c',type:'dashed'},
        label:{formatter:'1.500 (fragmentado)',fontSize:9}, data:[{yAxis:1500}]}},
    series:[{type:'scatter', data:dados,
      symbolSize: d => Math.max(5, Math.min(36, Math.sqrt(d[2]||0)/220)),
      itemStyle:{color:p=>{ const f=rows[p.data[3]]; return (state.familia!=null && f.i===state.familia)?'#c2410c':'#0a6c74'; }, opacity:.7},
      markLine:{silent:true, symbol:'none', lineStyle:{color:'#5d6b7a',type:'dotted'},
        label:{formatter:'0%',fontSize:9}, data:[{xAxis:0}]}}]
  });
}
function renderEntrantes(){
  semRecorte('c_ent', ['familia']);
  const acc = new Map();
  CONC.forEach(r=>{
    if(!filtroFamilia(r[0])) return;
    if(r[1] < 2022) return;
    const cur = acc.get(r[1]) || {novos:0, ativos:0};
    cur.novos += r[5]; cur.ativos += r[6]; acc.set(r[1], cur);
  });
  const anos = [...acc.keys()].sort();
  draw('c_ent', {
    grid:{...BASE_GRID, top:16, bottom:8, right:46},
    tooltip:{trigger:'axis'},
    legend:{top:0, textStyle:{fontSize:9}, itemWidth:9, itemHeight:8},
    xAxis:{type:'category', data:anos, ...AXIS, axisLabel:{...AXISL}},
    yAxis:[
      {type:'value', name:'novos', nameTextStyle:{fontSize:9,color:'#5d6b7a'}, ...AXIS,
       axisLabel:{...AXISL, formatter:v=>nf0.format(v)}},
      {type:'value', name:'ativos', nameTextStyle:{fontSize:9,color:'#5d6b7a'}, ...AXIS,
       splitLine:{show:false}, axisLabel:{...AXISL, formatter:v=>nf0.format(v)}}
    ],
    series:[
      {name:'novos fornecedores', type:'bar', yAxisIndex:0, data:anos.map(a=>acc.get(a).novos),
       itemStyle:{color:'#0a6c74',borderRadius:2}, barWidth:'46%'},
      {name:'fornecedores ativos', type:'line', yAxisIndex:1, data:anos.map(a=>acc.get(a).ativos),
       symbolSize:5, lineStyle:{color:'#c2410c'}, itemStyle:{color:'#c2410c'},
       markLine: state.ano ? {silent:true, symbol:'none', lineStyle:{color:'#c2410c',type:'dashed'},
         label:{formatter:String(state.ano),fontSize:9}, data:[{xAxis:String(state.ano)}]} : undefined}
    ]
  });
  notaPeriodo('c_ent');
}
function renderFornecedores(){
  semRecorte('c_forn', ['familia']);
  notaPeriodo('c_forn');
  const i = familiaAtualGlobal();
  const dados = (DATA.fornecedores[i]||[]).slice().sort((a,b)=>a[3]-b[3]);
  draw('c_forn', {
    grid:{...BASE_GRID, left:8, right:60, top:8, bottom:8},
    tooltip:{formatter:p=>{const r=dados[p.dataIndex];
      return `<b>${r[0]}</b><br>${brlM(r[3])} · share ${pct(r[4],1)}<br>${r[1]||'—'} · ${r[2]||'—'}`;}},
    xAxis:{type:'value', ...AXIS, axisLabel:{...AXISL, formatter:v=>nf1.format(v/1e6)+' mi'}},
    yAxis:{type:'category', data:dados.map(r=>String(r[0]).slice(0,34)), axisLabel:{fontSize:9,...AXISL}},
    series:[{type:'bar', data:dados.map(r=>r[3]), barWidth:11, itemStyle:{color:'#0a6c74', borderRadius:2},
      label:{show:true,position:'right',fontSize:9,formatter:p=>pct(dados[p.dataIndex][4],0)}}]
  });
}

/* ============================ ABA 5 ============================ */
function renderPreco(){
  semRecorte('c_preco', ['familia']);
  const i = familiaAtualGlobal();
  const itens = (DATA.preco[i]||[]);
  const series = [], legend = [];
  itens.forEach((it,k)=>{
    const nome = String(it[0]).slice(0,26) + ' (' + (it[1]||'un') + ')';
    const cor = COLORS[k%COLORS.length];
    const p25 = state.real ? it[2] : it[6];
    const p50 = state.real ? it[3] : it[7];
    const p75 = state.real ? it[4] : it[8];
    const faixa = p75.map((v,j)=> (v!=null && p25[j]!=null) ? +(v - p25[j]).toFixed(4) : null);
    legend.push(nome);
    series.push({name:nome+' base', type:'line', data:p25, stack:'band'+k, symbol:'none',
      lineStyle:{opacity:0}, areaStyle:{opacity:0}, silent:true, tooltip:{show:false}});
    series.push({name:nome+' faixa', type:'line', data:faixa, stack:'band'+k, symbol:'none',
      lineStyle:{opacity:0}, areaStyle:{color:cor, opacity:.16}, silent:true, tooltip:{show:false}});
    series.push({name:nome, type:'line', data:p50, smooth:true, symbolSize:5, z:5,
      lineStyle:{width:2.2, color:cor}, itemStyle:{color:cor}});
  });
  if(!series.length){
    draw('c_preco', {title:{text:'Selecione uma família no filtro acima para ver as bandas de preço',
      left:'center', top:'middle', textStyle:{fontSize:12,color:'#5d6b7a'}}});
    return;
  }
  draw('c_preco', {
    grid:{...BASE_GRID, top:16, right:170},
    tooltip:{trigger:'axis', valueFormatter:v=>v==null?'—':brl(v)},
    legend:{data:legend, type:'scroll', right:0, top:0, orient:'vertical', textStyle:{fontSize:9},
      itemWidth:12, itemHeight:8},
    xAxis:{type:'category', data:ANOS, ...AXIS, axisLabel:{...AXISL}},
    yAxis:{type:'value', scale:true, ...AXIS,
      axisLabel:{...AXISL, formatter:v=>v>=1000?nf1.format(v/1000)+'k':nf1.format(v)}},
    series: series
  });
}
function renderCv(){
  semRecorte('c_cv', ['familia']);
  notaPeriodo('c_cv');
  const rows = familiasGlobais().filter(f=>M[f.i][MET.cv]!=null)
    .sort((a,b)=>M[b.i][MET.cv]-M[a.i][MET.cv]).slice(0,15).reverse();
  draw('c_cv', {
    grid:{...BASE_GRID, left:8, right:40, top:8, bottom:8},
    tooltip:{trigger:'item', formatter:p=>`<b>${p.name}</b><br>CV: ${pct(p.value/100,1)}`},
    xAxis:{type:'value', ...AXIS, axisLabel:{...AXISL, formatter:v=>v+'%'}},
    yAxis:{type:'category', data:rows.map(f=>short(f.n).slice(0,34)), axisLabel:{fontSize:9,...AXISL}},
    series:[{type:'bar', data:rows.map(f=>+(M[f.i][MET.cv]*100).toFixed(1)), barWidth:9,
      itemStyle:{color:p=>p.value>60?'#b91c1c':(p.value>35?'#b45309':'#0a6c74'), borderRadius:2}}]
  });
}
function renderDesc(){
  semRecorte('c_desc', ['familia']);
  notaPeriodo('c_desc');
  const rows = familiasGlobais().filter(f=>M[f.i][MET.desc]!=null)
    .sort((a,b)=>M[b.i][MET.desc]-M[a.i][MET.desc]).slice(0,15).reverse();
  draw('c_desc', {
    grid:{...BASE_GRID, left:8, right:40, top:8, bottom:8},
    tooltip:{trigger:'item', formatter:p=>`<b>${p.name}</b><br>desconto mediano: ${pct(p.value/100,1)}`},
    xAxis:{type:'value', ...AXIS, axisLabel:{...AXISL, formatter:v=>v+'%'}},
    yAxis:{type:'category', data:rows.map(f=>short(f.n).slice(0,34)), axisLabel:{fontSize:9,...AXISL}},
    series:[{type:'bar', data:rows.map(f=>+(M[f.i][MET.desc]*100).toFixed(1)), barWidth:9,
      itemStyle:{color:'#0a6c74', borderRadius:2}}]
  });
}

/* ============================ ABA 6 ============================ */
function renderRegiao(){
  if(state.sec != null){ semRecorte('c_regiao', []); return; }   // sem cruzamento secretaria×região
  semRecorte('c_regiao', ['ano','regiao','familia']);

  if(state.regiao != null){
    // drill: o que esta região recebe
    const m = CUBO_REG.get(state.regiao) || new Map();
    const arr = [...m.entries()].map(([fam,e])=>{
      const v = (state.real ? e.r : e.n);
      const val = state.ano != null ? v[ANOS.indexOf(state.ano)] : v.reduce((a,b)=>a+b,0);
      return {fam, v: val||0};
    }).filter(x=>filtroFamilia(x.fam) && x.v>0).sort((a,b)=>b.v-a.v).slice(0,15).reverse();
    if(!arr.length){
      draw('c_regiao', {title:{text:'Nenhuma entrega registrada nesta região com os filtros atuais',
        left:'center', top:'middle', textStyle:{fontSize:12,color:'#5d6b7a'}}});
      return;
    }
    const tot = arr.reduce((a,b)=>a+b.v,0) || 1;
    marca('c_regiao', 'Recorte: famílias entregues em ' + curta(DATA.regioes[state.regiao]) +
      (state.ano != null ? ' em ' + state.ano : ' (2021–2025)') + '.', 'neutra');
    draw('c_regiao', {
      grid:{...BASE_GRID, left:8, right:80, top:8, bottom:8},
      tooltip:{formatter:p=>{const r=arr[p.dataIndex];
        return `<b>${short(nomeFam(r.fam))}</b><br>${brl(r.v)} (${pct(r.v/tot,1)} da região)`;}},
      xAxis:{type:'value', ...AXIS, axisLabel:{...AXISL, formatter:v=>nf1.format(v/1e6)+' mi'}},
      yAxis:{type:'category', data:arr.map(r=>short(nomeFam(r.fam)).slice(0,38)), axisLabel:{fontSize:9,...AXISL}},
      series:[{type:'bar', barWidth:11, itemStyle:{color:'#c2410c', borderRadius:2},
        data:arr.map(r=>r.v),
        label:{show:true, position:'right', fontSize:9, formatter:p=>pct(arr[p.dataIndex].v/tot,0)}}]
    });
    return;
  }

  const acc = new Map();
  REG.forEach(r=>{
    if(!filtroFamilia(r[0])) return;
    if(state.ano != null && r[2] !== state.ano) return;
    acc.set(r[1], (acc.get(r[1])||0) + (state.real ? r[3] : r[4]));
  });
  const arr = [...acc.entries()].map(([ri,v])=>({ri, v, raio:DATA.raio_regiao[ri]}))
    .sort((a,b)=>a.v-b.v).filter(x=>x.v>0);
  const tot = arr.reduce((a,b)=>a+b.v,0) || 1;
  draw('c_regiao', {
    grid:{...BASE_GRID, left:8, right:80, top:8, bottom:8},
    tooltip:{formatter:p=>{const r=arr[p.dataIndex];
      return `<b>${curta(DATA.regioes[r.ri])}</b><br>${brl(r.v)} (${pct(r.v/tot,1)}) · ${r.raio==='dentro'?'dentro do raio':'fora do raio'}`;}},
    xAxis:{type:'value', ...AXIS, axisLabel:{...AXISL, formatter:v=>nf1.format(v/1e6)+' mi'}},
    yAxis:{type:'category', data:arr.map(r=>curta(DATA.regioes[r.ri]).slice(0,38)), axisLabel:{fontSize:9,...AXISL}},
    series:[{type:'bar', barWidth:11, itemStyle:{borderRadius:2},
      data:arr.map(r=>({value:r.v, itemStyle:{color: r.raio==='dentro'?'#0a6c74':(r.raio==='indefinida'?'#b45309':'#cbd5db')}})),
      label:{show:true, position:'right', fontSize:9, formatter:p=>pct(arr[p.dataIndex].v/tot,0)}}]
  });
}
function renderPrazo(){
  semRecorte('c_prazo', ['familia']);
  notaPeriodo('c_prazo');
  const rows = familiasGlobais().sort((a,b)=>(M[b.i][MET.afms]||0)-(M[a.i][MET.afms]||0)).slice(0,12);
  draw('c_prazo', {
    grid:{...BASE_GRID, left:8, right:20, top:16, bottom:34},
    tooltip:{trigger:'axis', valueFormatter:v=>v+' dias'},
    legend:{top:0, textStyle:{fontSize:9}, itemWidth:9, itemHeight:8},    xAxis:{type:'category', data:rows.map(f=>short(f.n).slice(0,16)), axisLabel:{fontSize:8,rotate:38,...AXISL}},
    yAxis:{type:'value', ...AXIS, axisLabel:{...AXISL}},
    series:[
      {name:'mediana', type:'bar', data:rows.map(f=>(DATA.prazo[f.i]||[])[0]), barWidth:10,
       itemStyle:{color:'#0a6c74',borderRadius:2}},
      {name:'p90', type:'bar', data:rows.map(f=>(DATA.prazo[f.i]||[])[1]), barWidth:10,
       itemStyle:{color:'#f0a97a',borderRadius:2}}
    ]
  });
}
function renderMun(){
  semRecorte('c_mun', ['familia']);
  notaPeriodo('c_mun');
  const acc = new Map();
  MUN.forEach(r=>{ if(!filtroFamilia(r[0])) return; acc.set(r[1], (acc.get(r[1])||0) + r[2]); });
  const dados = [...acc.entries()].map(([m,v])=>({m, v})).sort((a,b)=>b.v-a.v).slice(0,15).reverse();
  draw('c_mun', {
    grid:{...BASE_GRID, left:8, right:60, top:8, bottom:8},
    tooltip:{formatter:p=>`<b>${p.name}</b><br>${brlM(p.value)}`},
    xAxis:{type:'value', ...AXIS, axisLabel:{...AXISL, formatter:v=>nf1.format(v/1e6)+' mi'}},
    yAxis:{type:'category', data:dados.map(d=>String(d.m).slice(0,26)), axisLabel:{fontSize:9,...AXISL}},
    series:[{type:'bar', data:dados.map(d=>d.v), barWidth:9, itemStyle:{color:'#0a6c74', borderRadius:2}}]
  });
}

/* ============================ ABA 7 ============================ */
function renderMetodo(){
  const q = DATA.qualidade;
  const th = el('t_filtros').tHead, tb = el('t_filtros').tBodies[0];
  th.innerHTML = '<tr><th>Passo</th><th>Descrição</th><th class="num">Linhas</th><th class="num">Δ linhas</th><th class="num">Valor (R$)</th><th>Motivo</th></tr>';
  tb.innerHTML = q.conservacao.map(p=>`<tr><td><b>${p.passo}</b></td><td>${p.descricao}</td>
    <td class="num">${num(p.linhas)}</td><td class="num">${num(p.delta_linhas)}</td>
    <td class="num">${brl(p.valor)}</td><td>${p.motivo}</td></tr>`).join('');
  const r = q.reconciliacao;
  el('recon').innerHTML = `<b>Reconciliação:</b> bruto material ${brl(r.soma_bruta_material)} ·
    tratado ${brl(r.soma_tratado)} · diferença ${brl(r.diferenca_abs)}
    (${(r.diferenca_rel*100).toFixed(6).replace('.',',')}%, tolerância ${(r.tolerancia*100).toFixed(2).replace('.',',')}%)
    <span class="tag ${r.status==='OK'?'ok':'bad'}">${r.status}</span><br>
    Deflação: convenção <b>${q.convencao}</b> — ${Object.entries(q.deflatores).map(([a,f])=>a+': '+Number(f).toFixed(4)).join(' · ')}`;

  el('l_assump').innerHTML = DATA.assumptions.map(a=>{
    const st = (a[2]||'').trim().replace(/\s+/g,'-');
    return `<li><b>${a[0]}</b> ${a[1]} <span class="st ${st}">${a[2]||''}</span></li>`;
  }).join('');

  el('l_limites').innerHTML = `
   <ul style="margin:0;padding-left:16px">
    <li><b>Cobertura estadual</b>: base SIMPAS/FIPLAN do Estado da Bahia — não inclui compras municipais.</li>
    <li><b>Sem dados de pagamento/adimplência</b>: medimos contratação, não fluxo de caixa.</li>
    <li><b>Ticket por AFM/APS é proxy</b> do teto legal, que é por contratação/objeto de mesma natureza por UG/ano.</li>
    <li><b>Deflação anual</b> (IPCA), não mensal — a série real é aproximada dentro do ano.</li>
    <li><b>Histórico não é previsão</b>: nenhum número aqui projeta demanda futura.</li>
    <li><b>Entrantes</b>: base começa em 2021; “novo” significa primeira aparição, contada só de 2022.</li>
    <li><b>Pandemia</b>: 2021–2022 têm distorção; linhas marcadas ficam fora do escopo padrão.</li>
    <li><b>Filtros</b>: recortes de secretaria/região recompõem valor, participação e CAGR. Indicadores que dependem
        de fornecedor, item ou prazo (HHI, preço, CV, desconto) não têm esse cruzamento no agregado e são
        sinalizados no gráfico em vez de exibir um número de outro escopo.</li>
   </ul>`;

  const dict = [
    ['valor_total_real','Valor da linha em R$ de dez/2025 (IPCA).'],
    ['score','0–100: média ponderada dos percentis das 7 dimensões, menos penalidades.'],
    ['recorrência','Meses com compra ÷ 60.'],
    ['ticket por AFM/APS','Soma das linhas de uma AFM/APS; mediana da família.'],
    ['% ≤ teto','AFM/APS com valor real ≤ R$ 65.492,11.'],
    ['HHI','Σ(share do fornecedor)² × 10.000; < 1.500 = fragmentado.'],
    ['CAGR real','(valor 2025 / valor 2021)^(1/4) − 1, em reais.'],
    ['estabilidade_top10','Frequência com que a família fica no top-10 nos 14 cenários de peso.'],
    ['perfil de uso','Consumo recorrente × bem durável, pelo vocabulário do nome básico (informativo).'],
  ];
  const dt = el('t_dict').tHead, db = el('t_dict').tBodies[0];
  dt.innerHTML = '<tr><th>Indicador</th><th>Definição</th></tr>';
  db.innerHTML = dict.map(d=>`<tr><td><code>${d[0]}</code></td><td>${d[1]}</td></tr>`).join('') +
    Object.entries(DATA.meta.ids).map(([k,v])=>`<tr><td><code>${k}</code></td><td>agregado <code>${v}.parquet</code></td></tr>`).join('');
}

/* ============================ orquestração ============================ */
const RENDER = {
  0: [renderCards, renderSens, renderTabela, renderEvitar],
  1: [renderSerie, renderTreemap, renderCagr],
  2: [renderHeat, renderCal],
  3: [renderOrgaos, renderCanal, renderTicket],
  4: [renderConc, renderEntrantes, renderFornecedores],
  5: [renderPreco, renderCv, renderDesc],
  6: [renderRegiao, renderPrazo, renderMun],
  7: [renderMetodo],
};
function renderTab(){
  updateEscopo();
  (RENDER[state.tab]||[]).forEach(fn=>{ try{ fn(); }catch(e){ console.error('chart fail', fn.name, e); } });
}
function exportCsv(){
  const csv = el('t_score').dataset.csv || '';
  const blob = new Blob(['\ufeff' + csv], {type:'text/csv;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'nicho_score.csv';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
}
window.addEventListener('DOMContentLoaded', ()=>{
  initFilters();
  el('btn_csv').onclick = exportCsv;
  renderTab();
});
window.addEventListener('error', e => console.error('erro global', e.message));
"""


def render(dados: dict[str, Any], echarts_js: str, *, versao: str = "1.0", gerado: str = "") -> str:
    """Monta o HTML final, com dados e biblioteca embutidos."""
    payload = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    js = JS.replace("__DATA__", payload)
    return (
        "<!DOCTYPE html>\n<html lang=\"pt-BR\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"<title>Painel de decisão de nicho — compras públicas BA 2021–2025</title>\n"
        f"<!-- versão {versao} · gerado em {gerado} · 100% offline, sem requisições externas -->\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n{BODY}\n"
        f"<script>{echarts_js}</script>\n"
        f"<script>{js}</script>\n</body>\n</html>\n"
    )
