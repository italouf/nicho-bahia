"""Núcleo do painel (V3–V7): estado, cubos, filtros, URL, chips, decisão, tabela e dossiê."""

from __future__ import annotations

JS_CORE = r"""
'use strict';
/* ============================ dados ============================ */
const DATA = JSON.parse(document.getElementById("dados").textContent);
const META = DATA.meta;
const ANOS = META.anos;
const F = DATA.familias;
const M = DATA.metricas;
const DIM = DATA.dim;
const SENS = DATA.sens;
const SERIE = DATA.serie;
const SAZ = DATA.saz;
const ORG = DATA.orgaos;         /* [fam, sec, ano, valorReal, shareDispensa, valorNominal] */
const REG = DATA.regiao;         /* [fam, regiao, ano, valorReal, valorNominal] */
const CAN = DATA.canal;          /* [fam, canal, ano, valorReal, linhas, valorNominal] */
const MUN = DATA.municipios;     /* [fam, municipio, valorReal] */
const CONC = DATA.concorrencia;  /* [fam, ano, hhi, nForn, top3, novos, ativos] */

const MET = {v2425:0, vtotal:1, cagr:2, rec:3, afms:4, ticket:5, teto:6, nforn:7, hhi:8, top3:9,
             disp:10, raio:11, cv:12, desc:13, pand:14, penal:15, tetoHist:16, prazo:17, novos:18, linhas:19};
const DIMS = ['demanda','crescimento','recorrência','fit dispensa','fragmentação','estab. preço','logística'];
const CANAL_NOME = {dispensa_eletronica:'Dispensa eletrônica', dispensa_tradicional:'Dispensa tradicional',
  registro_precos:'Registro de preços (ata)', adesao_rp:'Adesão a ata', licitacao:'Licitação',
  contratacao_direta:'Contratação direta', credenciamento:'Credenciamento', alteracao:'Alteração', outros:'Outros'};
const ABAS = ['decisao','dossie','mercado','sazonalidade','compradores','concorrencia','precos','logistica','metodo'];

const state = {ano:null, sec:null, regiao:null, familia:null, real:true,
               tab:'decisao', dossie:null, busca:'', pagina:1, sortCol:'r', sortDir:1};
const charts = {};
const cssVar = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const COLORS = ['--c-s1','--c-s2','--c-s3','--c-s4','--c-s5','--c-s6','--c-s7','--c-s8']
  .map(cssVar).filter(Boolean);

/* ============================ utilidades ============================ */
const nf0 = new Intl.NumberFormat('pt-BR', {maximumFractionDigits:0});
const nf1 = new Intl.NumberFormat('pt-BR', {maximumFractionDigits:1});
const brl  = v => (v==null||isNaN(v)) ? '—' : 'R$ ' + nf0.format(v);
const brlM = v => (v==null||isNaN(v)) ? '—' : 'R$ ' + nf1.format(v/1e6) + ' mi';
const pct  = (v,c=1) => (v==null||isNaN(v)) ? '—' : (v*100).toFixed(c).replace('.',',') + '%';
const num  = v => (v==null||isNaN(v)) ? '—' : nf0.format(v);
const dec1 = v => (v==null||isNaN(v)) ? '—' : Number(v).toFixed(1).replace('.',',');
const el = id => document.getElementById(id);
const curta = n => String(n).replace(/^\d+\s*-\s*/,'').slice(0,60);
const codigoFam = s => String(s).split(' - ')[0].trim();
const nomeFam = i => F[i] ? F[i].n : '—';
/* rótulo curto "código · nome em sentence case" — usado nas legendas e eixos */
const short = n => { const c = codigoFam(n); return c + ' · ' + sentencaCase(n).slice(0, 34); };
function sentencaCase(s){
  const t = String(s).split(' - ').slice(1).join(' - ') || String(s);
  const m = t.toLowerCase();
  return m.charAt(0).toUpperCase() + m.slice(1);
}
function pick(i){ const s = SERIE[i]; return s ? (state.real ? s.r : s.n) : []; }

/* ============================ cubos de recorte ============================ */
function buildCubo(arr, vRealPos, vNomPos){
  const c = new Map();
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

function serieFam(i){
  const c = cuboAtivo();
  if(!c){ const s = SERIE[i]; return s ? (state.real ? s.r.slice() : s.n.slice()) : ANOS.map(()=>null); }
  const e = (c.cubo.get(c.alvo) || new Map()).get(i);
  if(!e) return ANOS.map(()=>null);
  return (state.real ? e.r : e.n).slice();
}
function valorFam(i, ano){
  if(ano != null){
    const s = serieFam(i); const k = ANOS.indexOf(ano); const v = s ? s[k] : null;
    return (v == null || v === 0) ? null : v;
  }
  const s = serieFam(i);
  if(!s || s.every(v => v == null)) return null;
  const tot = s.reduce((a,b)=>a+(b||0), 0);
  return tot > 0 ? tot : null;
}
function cagrFam(i){
  const s = serieFam(i); if(!s) return null;
  const v1 = s[0], v2 = s[s.length-1];
  if(!v1 || !v2 || v1 <= 0 || v2 <= 0) return null;
  return Math.pow(v2/v1, 1/(ANOS.length-1)) - 1;
}
function familiasVisiveis(){
  const base = F.filter(f => f.e);
  if(!emRecorte()) return base.slice().sort((a,b)=>a.r-b.r);
  const comValor = base.map(f => ({f, v: valorFam(f.i, state.ano) || 0})).filter(x => x.v > 0);
  comValor.sort((a,b)=> b.v - a.v);
  return comValor.map(x => x.f);
}
function familiasGlobais(){ return F.filter(f => f.e).sort((a,b)=>a.r-b.r); }
function alvoFamilias(n){ return state.familia != null ? [state.familia] : familiasVisiveis().slice(0,n).map(f=>f.i); }
function alvoFamiliasGlobal(n){ return state.familia != null ? [state.familia] : familiasGlobais().slice(0,n).map(f=>f.i); }
function familiaAtual(){ if(state.familia != null) return state.familia; const t = familiasVisiveis(); return t.length ? t[0].i : (F[0]?F[0].i:0); }
function familiaAtualGlobal(){ if(state.familia != null) return state.familia; const t = familiasGlobais(); return t.length ? t[0].i : (F[0]?F[0].i:0); }
const filtroFamilia = i => state.familia == null || state.familia === i;
function valorAnoFam(i){
  if(state.ano == null) return M[i][MET.v2425];
  const s = SERIE[i]; if(!s) return null;
  return (state.real ? s.r : s.n)[ANOS.indexOf(state.ano)];
}

/* ============================ marcações de escopo ============================ */
const MARCAS = {};
function marca(id, texto, tipo){
  const node = el(id); if(!node) return;
  if(!MARCAS[id]) MARCAS[id] = {alerta:'', neutra:''};
  if(!texto && tipo === undefined){ MARCAS[id] = {alerta:'', neutra:''}; }
  else { MARCAS[id][tipo || 'alerta'] = texto || ''; }
  const card = node.closest('.card') || node.parentElement;
  let box;
  if(node.classList.contains('marca') && !node.dataset.alvo){
    // o próprio elemento já é o aviso (ex.: #dossie-aviso, #metodo-aviso)
    box = node;
    box.dataset.alvo = id;
  } else {
    box = card.querySelector('.marca[data-alvo="'+id+'"]');
    if(!box){
      box = document.createElement('div');
      box.className = 'marca'; box.dataset.alvo = id;
      const hint = card.querySelector('.card__hint');
      if(hint) hint.after(box); else card.insertBefore(box, node);
    }
  }
  const linhas = [];
  if(MARCAS[id].alerta) linhas.push(MARCAS[id].alerta);
  if(MARCAS[id].neutra) linhas.push(MARCAS[id].neutra);
  box.className = 'marca' + (linhas.length ? ' ' + (MARCAS[id].alerta ? 'alerta' : 'neutra') : '');
  box.innerHTML = linhas.map(l=>`<div>${l}</div>`).join('');
  node.style.opacity = 1;
  node.style.filter = MARCAS[id].alerta ? 'saturate(0.25)' : '';
}
function naoSeAplica(quais){
  const ativos = [];
  if(quais.includes('sec') && state.sec != null) ativos.push('secretaria');
  if(quais.includes('regiao') && state.regiao != null) ativos.push('região');
  if(quais.includes('ano') && state.ano != null) ativos.push('ano');
  if(quais.includes('familia') && state.familia != null) ativos.push('família');
  return ativos;
}
function semRecorte(id, suporta){
  const nao = naoSeAplica(['sec','regiao','ano','familia'].filter(k => !suporta.includes(k)));
  if(nao.length){
    marca(id, '⚠ Este gráfico não abre o recorte por ' + nao.join(' e ') +
      ' — os números são do escopo completo para não misturar bases.', 'alerta');
  } else marca(id, '', 'alerta');
}
function notaPeriodo(id){
  if(state.ano != null) marca(id, 'Indicador do período completo (2021–2025); o filtro de ano não se aplica.', 'neutra');
  else marca(id, '', 'neutra');
}

/* ============================ charts ============================ */
function chart(id){
  if(!charts[id]) charts[id] = echarts.init(el(id), null, {renderer:'canvas'});
  return charts[id];
}
function draw(id, option){
  if(!el(id)) return;
  const node = el(id);
  const c = chart(id); c.setOption(option, true); c.resize();
  // estado vazio padronizado (AR-24): se nenhuma série trouxe valor, avisa em vez de mostrar canvas vazio
  const temDado = (option.series || []).some(s =>
    Array.isArray(s.data) && s.data.some(v => v !== null && v !== undefined && v !== ''));
  let box = node.parentElement.querySelector('.estado-vazio[data-para="' + id + '"]');
  if(!temDado){
    if(!box){
      box = document.createElement('div');
      box.className = 'estado-vazio';
      box.dataset.para = id;
      box.innerHTML = '<strong>Sem dados neste recorte</strong>Tente limpar os filtros ou escolher outro nicho.';
      node.after(box);
    }
    box.style.display = 'grid';
    node.style.display = 'none';
  } else {
    if(box) box.style.display = 'none';
    node.style.display = '';
  }
}
const AXIS = {axisLine:{lineStyle:{color:'#cfd6dd'}}, splitLine:{lineStyle:{color:'#eef2f5'}}};
const AXISL = {color:'#4a5764', fontSize:11};
const BASE_GRID = {left:8, right:14, top:26, bottom:8, containLabel:true};

/* ============================ URL ============================ */
function escreverUrl(){
  const p = new URLSearchParams();
  if(state.ano) p.set('ano', state.ano);
  if(state.sec != null) p.set('sec', state.sec);
  if(state.regiao != null) p.set('regiao', state.regiao);
  if(state.familia != null) p.set('familia', codigoFam(F[state.familia].n));
  if(state.tab !== 'decisao') p.set('aba', state.tab);
  if(state.tab === 'dossie' && state.dossie != null) p.set('dossie', codigoFam(F[state.dossie].n));
  const q = p.toString();
  history.replaceState(null, '', q ? '?' + q : location.pathname);
}
function lerUrl(){
  const p = new URLSearchParams(location.search);
  const num = k => (p.get(k) != null && p.get(k) !== '') ? +p.get(k) : null;
  if(num('ano')) state.ano = num('ano');
  if(num('sec') != null) state.sec = num('sec');
  if(p.get('regiao') != null && p.get('regiao') !== '') state.regiao = +p.get('regiao');
  const fam = p.get('familia');
  if(fam){
    const f = F.find(x => codigoFam(x.n) === fam || x.k === fam);
    if(f) state.familia = f.i;
  }
  const aba = p.get('aba'); if(aba && ABAS.includes(aba)) state.tab = aba;
  const dos = p.get('dossie');
  if(dos){ const f = F.find(x => codigoFam(x.n) === dos); if(f){ state.dossie = f.i; state.tab = 'dossie'; } }
}

/* ============================ chips ============================ */
function renderChips(){
  const box = el('chips'); if(!box) return;
  const itens = [];
  if(state.ano != null) itens.push(['ano', String(state.ano)]);
  if(state.sec != null) itens.push(['sec', curta(DATA.secretarias[state.sec])]);
  if(state.regiao != null) itens.push(['regiao', curta(DATA.regioes[state.regiao])]);
  if(state.familia != null) itens.push(['familia', sentencaCase(F[state.familia].n)]);
  box.innerHTML = itens.length
    ? itens.map(([k,txt])=>`<span class="chip" data-chip="${k}">${txt}
         <button type="button" data-chip-remover="${k}" aria-label="Remover filtro ${txt}">×</button></span>`).join('')
      + '<button class="btn chips__limpar" id="chips-limpar">limpar tudo</button>'
    : '';
  box.querySelectorAll('[data-chip-remover]').forEach(b => b.onclick = () => {
    const k = b.dataset.chipRemover;
    if(k==='ano'){ state.ano=null; el('f_ano').value=''; }
    if(k==='sec'){ state.sec=null; el('f_sec').value=''; }
    if(k==='regiao'){ state.regiao=null; el('f_reg').value=''; }
    if(k==='familia'){ state.familia=null; el('f_fam').value=''; }
    renderTab();
  });
  const limpar = el('chips-limpar');
  if(limpar) limpar.onclick = () => { limparFiltros(); renderTab(); };
}
function limparFiltros(){
  state.ano = state.sec = state.regiao = state.familia = null;
  ['f_ano','f_sec','f_reg','f_fam'].forEach(id => { const n = el(id); if(n) n.value = ''; });
}

/* ============================ abas ============================ */
function setAba(nome, {focar=false} = {}){
  if(!ABAS.includes(nome)) nome = 'decisao';
  state.tab = nome;
  document.querySelectorAll('#tabs [role="tab"]').forEach(b => {
    const on = b.getAttribute('aria-controls') === 'tab-' + nome;
    b.setAttribute('aria-selected', on ? 'true' : 'false');
    b.tabIndex = on ? 0 : -1;
    if(on && focar) b.focus();
  });
  document.querySelectorAll('.painel').forEach(p => p.classList.toggle('on', p.id === 'tab-' + nome));
}
function initAbas(){
  const tabs = [...document.querySelectorAll('#tabs [role="tab"]')];
  tabs.forEach(b => {
    b.onclick = () => { setAba(b.getAttribute('aria-controls').replace('tab-','')); renderTab(); };
    b.onkeydown = ev => {
      const i = tabs.indexOf(b);
      if(ev.key === 'ArrowRight'){ ev.preventDefault(); const n = tabs[(i+1)%tabs.length];
        setAba(n.getAttribute('aria-controls').replace('tab-',''), {focar:true}); renderTab(); }
      if(ev.key === 'ArrowLeft'){ ev.preventDefault(); const n = tabs[(i-1+tabs.length)%tabs.length];
        setAba(n.getAttribute('aria-controls').replace('tab-',''), {focar:true}); renderTab(); }
      if(ev.key === 'Home'){ ev.preventDefault(); setAba('decisao',{focar:true}); renderTab(); }
      if(ev.key === 'End'){ ev.preventDefault(); setAba('metodo',{focar:true}); renderTab(); }
    };
  });
}

/* ============================ filtros ============================ */
function initFiltros(){
  const sa = el('f_ano'); ANOS.forEach(a => { const o=document.createElement('option'); o.value=a; o.textContent=a; sa.appendChild(o); });
  const ss = el('f_sec'); DATA.secretarias.forEach((s,i) => { const o=document.createElement('option'); o.value=i; o.textContent = curta(s); ss.appendChild(o); });
  const sr = el('f_reg'); DATA.regioes.forEach((s,i) => { const o=document.createElement('option'); o.value=i; o.textContent = curta(s); sr.appendChild(o); });
  const sf = el('f_fam'); familiasGlobais().forEach(f => { const o=document.createElement('option'); o.value=f.i;
    o.textContent = '#' + f.r + ' ' + sentencaCase(f.n); sf.appendChild(o); });

  if(state.ano) sa.value = String(state.ano);
  if(state.sec != null) ss.value = String(state.sec);
  if(state.regiao != null) sr.value = String(state.regiao);
  if(state.familia != null) sf.value = String(state.familia);

  sa.onchange = e => { state.ano = e.target.value !== '' ? +e.target.value : null; state.pagina = 1; renderTab(); };
  ss.onchange = e => { state.sec = e.target.value !== '' ? +e.target.value : null;
    if(state.sec != null){ state.regiao = null; el('f_reg').value = ''; } state.pagina = 1; renderTab(); };
  sr.onchange = e => { state.regiao = e.target.value !== '' ? +e.target.value : null;
    if(state.regiao != null){ state.sec = null; el('f_sec').value = ''; } state.pagina = 1; renderTab(); };
  sf.onchange = e => { state.familia = e.target.value !== '' ? +e.target.value : null; state.pagina = 1; renderTab(); };

  el('btn_real').onclick = () => { state.real = true; el('btn_real').classList.add('on');
    el('btn_real').setAttribute('aria-pressed','true'); el('btn_nom').classList.remove('on');
    el('btn_nom').setAttribute('aria-pressed','false'); el('base-preco').textContent = 'valores em R$ de dez/2025'; renderTab(); };
  el('btn_nom').onclick = () => { state.real = false; el('btn_nom').classList.add('on');
    el('btn_nom').setAttribute('aria-pressed','true'); el('btn_real').classList.remove('on');
    el('btn_real').setAttribute('aria-pressed','false'); el('base-preco').textContent = 'valores nominais (como pagos no ano)'; renderTab(); };
  el('btn_reset').onclick = () => { limparFiltros(); state.pagina = 1; renderTab(); };

  // filtros colapsáveis no mobile
  const toggle = el('filtros-toggle');
  if(toggle){
    const compacto = () => window.matchMedia('(max-width:599px)').matches;
    const aplicar = () => {
      const aberto = !compacto();
      toggle.setAttribute('aria-expanded', String(aberto));
      el('filtros-campos').classList.toggle('on', aberto);
      toggle.style.display = compacto() ? 'inline-flex' : 'none';
    };
    aplicar();
    toggle.onclick = () => {
      const aberto = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!aberto));
      el('filtros-campos').classList.toggle('on', !aberto);
    };
    window.addEventListener('resize', aplicar, {passive:true});
  }
  el('hdr_n').textContent = META.n_elegiveis;
  const nTot = document.querySelector('[data-n-total]'); if(nTot) nTot.textContent = F.length;
  const nEl = document.querySelector('[data-n-elegiveis]'); if(nEl) nEl.textContent = META.n_elegiveis;
  const teto = document.querySelector('[data-teto]'); if(teto) teto.textContent = nf0.format(META.teto) + ',11';
}

/* ============================ VEREDITO ============================ */
function recomendados(){
  const lista = (META.recomendados || []).map(c => F.find(f => codigoFam(f.n) === c)).filter(Boolean);
  if(lista.length) return lista;
  return familiasGlobais().slice(0, 3);
}
function renderVeredito(){
  const recs = recomendados();
  const frase = el('veredito-titulo');
  const primeiro = recs[0];
  if(frase){
    frase.textContent = primeiro
      ? 'Atacar ' + recs.length + ' nichos de consumo recorrente — nesta ordem de prioridade.'
      : 'Sem nichos elegíveis no recorte atual.';
  }
  const box = document.querySelector('[data-veredito-nichos]');
  if(box){
    box.innerHTML = recs.map(f => {
      const m = M[f.i];
      return `<span class="veredito__nicho">${sentencaCase(f.n)}
        <b>${dec1(f.s)}</b> <span style="color:var(--c-ink-3)">score</span></span>`;
    }).join('');
  }
  const tempo = document.querySelector('[data-tempo-leitura]'); if(tempo) tempo.textContent = '≈ 5 min';
}

/* ============================ CARDS ============================ */
function teseDe(f){
  const m = M[f.i]; const nome = sentencaCase(f.n).toLowerCase();
  if(f.pu === 'bem durável')
    return `Disputar ${nome} exige instalação e pós-venda: ticket de ${brl(m[MET.ticket])} e só ${pct(m[MET.teto],0)} abaixo do teto.`;
  const v = brlM(m[MET.v2425]);
  return `Atacar ${nome} por dispensa: ${v}/ano, ${pct(m[MET.teto],0)} das compras abaixo do teto e ${num(m[MET.nforn])} fornecedores.`;
}
function riscosDe(f){
  const m = M[f.i]; const out = [];
  if((m[MET.pand]||0) > 0.3) out.push(['bad','⚠','dependência de pandemia ' + pct(m[MET.pand],0)]);
  if(f.pu !== 'consumo recorrente') out.push(['','⚠','exige assistência técnica']);
  if(m[MET.penal]) out.push(['bad','▼', m[MET.penal]]);
  if((m[MET.hhi]||0) > 1500) out.push(['','▲','concentração HHI ' + num(m[MET.hhi])]);
  if((m[MET.top3]||0) > 0.6) out.push(['','▲','top-3 concentra ' + pct(m[MET.top3],0)]);
  if((m[MET.disp]||0) < 0.15) out.push(['','▼','só ' + pct(m[MET.disp],0) + ' em dispensa']);
  if((m[MET.cv]||0) > 0.3) out.push(['','⚠','preço volátil (CV ' + pct(m[MET.cv],0) + ')']);
  if((m[MET.desc]||0) <= 0.01) out.push(['','▼','sem desconto sobre o estimado']);
  if(!out.length) out.push(['ok','✓','sem risco relevante nos indicadores']);
  if(out.length === 1) out.push(['','·','ticket ' + brl(m[MET.ticket]) + ' por AFM/APS']);
  return out.slice(0,2);
}
function sparkline(vals){
  const v = vals.filter(x => x != null);
  if(v.length < 2) return '';
  const min = Math.min(...v), max = Math.max(...v), w = 100, h = 30;
  const stepX = w / (v.length - 1);
  const pts = v.map((y,i) => `${(i*stepX).toFixed(1)},${(h - ((y-min)/((max-min)||1))*h).toFixed(1)}`).join(' ');
  return `<svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none" aria-hidden="true" focusable="false">
      <polyline points="${pts}" fill="none" stroke="var(--c-accent)" stroke-width="1.6"/></svg>`;
}
function renderCards(){
  const box = el('cards'); if(!box) return;
  const recs = recomendados();
  box.innerHTML = recs.map(f => {
    const m = M[f.i], s = SENS[f.i] || [];
    const faixa = s.length ? `${s[0]}–${s[1]}` : '—';
    const estab = s.length ? Math.round(s[2]*100) : null;
    const riscos = riscosDe(f).map(([t,i,txt]) =>
      `<li class="badge ${t==='bad'?'badge--bad':(t==='ok'?'badge--ok':'')}"><span aria-hidden="true">${i}</span>${txt}</li>`).join('');
    return `<article class="niche" data-codigo="${codigoFam(f.n)}">
      <div class="niche__topo">
        <div>
          <h3 class="niche__nome" data-nome>${sentencaCase(f.n)}</h3>
          <span class="niche__codigo" data-codigo-valor>${codigoFam(f.n)}</span>
        </div>
        <div class="niche__score"><b data-score>${dec1(f.s)}</b><span>score</span></div>
      </div>
      <p class="niche__faixa" data-faixa-rank>posição <b>${faixa}</b> em 14 cenários${estab!=null?` · <b data-estabilidade>${estab}%</b> no top-10`:''}</p>
      <p class="niche__tese" data-tese>${teseDe(f)}</p>
      <ul class="niche__riscos" data-riscos>${riscos}</ul>
      ${sparkline(pick(f.i))}
      <div class="niche__metricas">
        <span>${state.ano != null ? 'R$ em ' + state.ano : 'R$/ano (24–25)'} <b>${brl(valorAnoFam(f.i))}</b></span>
        <span>ticket/AFM <b>${brl(m[MET.ticket])}</b></span>
        <span>% ≤ teto <b>${pct(m[MET.teto],0)}</b></span>
        <span>fornecedores <b>${num(m[MET.nforn])}</b></span>
        <span>HHI <b>${num(m[MET.hhi])}</b></span>
        <span>no raio <b>${pct(m[MET.raio],0)}</b></span>
      </div>
      <div class="niche__cta">
        <button class="btn btn--primary" data-cta="${codigoFam(f.n)}">Abrir dossiê</button>
      </div>
    </article>`;
  }).join('') || '<div class="estado-vazio"><strong>Sem nichos elegíveis neste recorte</strong>Tente limpar os filtros.</div>';
  box.querySelectorAll('[data-cta]').forEach(b => b.onclick = () => {
    const f = F.find(x => codigoFam(x.n) === b.dataset.cta);
    if(!f) return;
    state.dossie = f.i;
    setAba('dossie'); renderTab();
    el('tab-dossie').scrollIntoView({block:'start', behavior:'smooth'});
  });
}

/* ============================ TABELA ============================ */
const COLUNAS = [
  {k:'r',   t:'#',            num:true,  v:f=>f.r},
  {k:'n',   t:'Família',      num:false, v:f=>sentencaCase(f.n)},
  {k:'s',   t:'Score',        num:true,  v:f=>f.s},
  {k:'fx',  t:'Faixa em 14 cenários', num:false, v:f=>{ const s=SENS[f.i]||[]; return s.length?`${s[0]}–${s[1]} (${Math.round(s[2]*100)}%)`:'—'; }},
  {k:'pu',  t:'Perfil',       num:false, v:f=>f.pu||'—'},
  {k:'v',   t:'R$ no ano',    num:true,  v:f=>valorAnoFam(f.i)},
  {k:'c',   t:'CAGR real',    num:true,  v:f=>M[f.i][MET.cagr]},
  {k:'rec', t:'Recorrência',  num:true,  v:f=>M[f.i][MET.rec]},
  {k:'tk',  t:'Ticket/AFM',   num:true,  v:f=>M[f.i][MET.ticket]},
  {k:'te',  t:'% ≤ teto',     num:true,  v:f=>M[f.i][MET.teto]},
  {k:'nf',  t:'Nº forn.',     num:true,  v:f=>M[f.i][MET.nforn]},
  {k:'hh',  t:'HHI',          num:true,  v:f=>M[f.i][MET.hhi]},
  {k:'dp',  t:'% dispensa',   num:true,  v:f=>M[f.i][MET.disp]},
  {k:'ra',  t:'% no raio',    num:true,  v:f=>M[f.i][MET.raio]},
];
const POR_PAGINA = 25;

function fmtCol(k, v){
  if(v == null || v === '') return '—';
  if(['s'].includes(k)) return dec1(v);
  if(['v','tk'].includes(k)) return brl(v);
  if(['c'].includes(k)) return pct(v,1);
  if(['rec','te','dp','ra'].includes(k)) return pct(v,0);
  if(['nf','hh'].includes(k)) return num(v);
  if(k === 'r') return '#' + v;
  return String(v);
}
function linhasFiltradas(){
  const q = state.busca.trim().toLowerCase();
  let rows = (state.familia != null ? [F[state.familia]] : familiasVisiveis()).filter(Boolean);
  if(q){
    rows = rows.filter(f => (f.n + ' ' + codigoFam(f.n)).toLowerCase().includes(q));
  }
  const col = COLUNAS.find(c => c.k === state.sortCol) || COLUNAS[0];
  rows = rows.slice().sort((a,b)=>{
    const va = col.v(a), vb = col.v(b);
    if(va == null && vb == null) return 0;
    if(va == null) return 1;
    if(vb == null) return -1;
    if(typeof va === 'number' && typeof vb === 'number') return (va - vb) * state.sortDir;
    return String(va).localeCompare(String(vb), 'pt-BR') * state.sortDir;
  });
  return rows;
}
function renderTabela(){
  const rows = linhasFiltradas();
  const totalPag = Math.max(1, Math.ceil(rows.length / POR_PAGINA));
  state.pagina = Math.min(Math.max(1, state.pagina), totalPag);
  const ini = (state.pagina - 1) * POR_PAGINA;
  const pagina = rows.slice(ini, ini + POR_PAGINA);

  const thead = el('tabela').tHead, tbody = el('tabela').tBodies[0];
  thead.innerHTML = '<tr>' + COLUNAS.map(c => {
    const ativo = state.sortCol === c.k;
    const ordem = ativo ? (state.sortDir === 1 ? 'ascending' : 'descending') : 'none';
    return `<th class="${c.num?'num':''}" data-k="${c.k}" scope="col" aria-sort="${ordem}"
      tabindex="0" role="columnheader">${c.t}${ativo?(state.sortDir===1?' ▲':' ▼'):''}</th>`;
  }).join('') + '</tr>';
  thead.querySelectorAll('th').forEach(th => {
    const ord = () => {
      const k = th.dataset.k;
      if(state.sortCol === k) state.sortDir *= -1; else { state.sortCol = k; state.sortDir = 1; }
      state.pagina = 1; renderTabela();
    };
    th.onclick = ord;
    th.onkeydown = e => { if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); ord(); } };
  });

  tbody.innerHTML = pagina.map(f => '<tr>' + COLUNAS.map(c =>
    `<td class="${c.num?'num':''}">${fmtCol(c.k, c.v(f))}</td>`).join('') + '</tr>').join('');

  // versão mobile em cartões
  const cartoes = el('tabela-cartoes');
  if(cartoes){
    cartoes.innerHTML = pagina.map(f => `<article class="tabela__cartao">
      <h4>${sentencaCase(f.n)} <span class="niche__codigo" style="display:inline">${codigoFam(f.n)}</span></h4>
      <dl>
        <dt>Score</dt><dd>${dec1(f.s)}</dd>
        <dt>Faixa</dt><dd>${fmtCol('fx', COLUNAS[3].v(f))}</dd>
        <dt>Perfil</dt><dd>${f.pu||'—'}</dd>
        <dt>R$ no ano</dt><dd>${fmtCol('v', valorAnoFam(f.i))}</dd>
        <dt>Ticket/AFM</dt><dd>${fmtCol('tk', M[f.i][MET.ticket])}</dd>
        <dt>% ≤ teto</dt><dd>${fmtCol('te', M[f.i][MET.teto])}</dd>
      </dl></article>`).join('');
  }

  const cont = el('contador');
  if(cont) cont.textContent = rows.length
    ? `${rows.length} de ${familiasVisiveis().length} nichos`
    : 'nenhum nicho com esse termo';

  const pag = el('paginacao');
  if(pag){
    pag.innerHTML = `<button class="btn" data-pag="1" ${state.pagina===1?'disabled':''} aria-label="Primeira página">«</button>
      <button class="btn" data-pag="${state.pagina-1}" ${state.pagina===1?'disabled':''} aria-label="Página anterior">‹</button>
      <span aria-live="polite">página ${state.pagina} de ${totalPag}</span>
      <button class="btn" data-pag="${state.pagina+1}" ${state.pagina===totalPag?'disabled':''} aria-label="Próxima página">›</button>
      <button class="btn" data-pag="${totalPag}" ${state.pagina===totalPag?'disabled':''} aria-label="Última página">»</button>`;
    pag.querySelectorAll('[data-pag]').forEach(b => b.onclick = () => {
      state.pagina = +b.dataset.pag; renderTabela();
    });
  }
  el('tabela').dataset.csv = rows.map(f => COLUNAS.map(c => {
    const v = c.k === 's' ? f.s : c.v(f);
    if(c.k === 'n') return '"' + sentenciaCsv(f.n) + '"';
    if(v == null || v === '') return '';
    return typeof v === 'number' ? String(v).replace('.', ',') : '"' + String(v).replace(/"/g,'""') + '"';
  }).join(';')).join('\n');
}
function sentenciaCsv(s){ return String(s).replace(/"/g,'""'); }

function renderEvitar(){
  const th = el('t_evitar').tHead, tb = el('t_evitar').tBodies[0];
  th.innerHTML = '<tr><th scope="col">Família</th><th scope="col" class="num">R$ no material</th>' +
    '<th scope="col" class="num">% do total</th><th scope="col" class="num">Fornecedores</th><th scope="col">Situação</th></tr>';
  const rel = DATA.evitar.filter(r => (r[1]||0) >= 1e6 || (r[2]||0) >= 0.01);
  const om = DATA.evitar.length - rel.length;
  tb.innerHTML = rel.map(r => `<tr><td>${sentencaCase(r[0])} <span class="niche__codigo" style="display:inline">${codigoFam(r[0])}</span></td>
      <td class="num">${brl(r[1])}</td><td class="num">${(r[2]||0).toFixed(2).replace('.',',')}%</td>
      <td class="num">${num(r[5])}</td>
      <td>${r[3]?'<span class="badge badge--bad"><span aria-hidden="true">■</span>excluída do ranking</span>'
                :'<span class="badge"><span aria-hidden="true">▲</span>parcialmente regulada</span>'}</td></tr>`).join('')
    + (om ? `<tr><td colspan="5" style="color:var(--c-ink-3);font-size:var(--t-xs)">+ ${om} famílias com valor irrelevante omitidas</td></tr>` : '');
}

/* ============================ DOSSIÊ ============================ */
function initDossie(){
  const sel = el('dossie-select'); if(!sel) return;
  sel.innerHTML = familiasGlobais().map(f =>
    `<option value="${f.i}">#${f.r} · ${sentencaCase(f.n)}</option>`).join('');
  sel.onchange = () => { state.dossie = +sel.value; renderTab(); };
  const imp = el('btn_imprimir');
  if(imp) imp.onclick = () => window.print();
}
function renderDossie(){
  const sel = el('dossie-select'); if(!sel) return;
  // a família filtrada manda no dossiê; sem ela, vale o nicho escolhido ou o líder GLOBAL
  // (não usar familiasVisiveis aqui: sob recorte ela mudaria o nicho e contradiria o aviso)
  const i = (state.familia != null) ? state.familia
          : ((state.dossie != null && F[state.dossie]) ? state.dossie : familiaAtualGlobal());
  state.dossie = i;
  sel.value = String(i);
  const f = F[i], m = M[i], s = SENS[i] || [];
  const anoIdx = state.ano != null ? ANOS.indexOf(state.ano) : null;

  // regra "filtra ou declara": o dossiê consolida o nicho no estado inteiro
  if(emRecorte()){
    marca('dossie-aviso',
      '⚠ O dossiê consolida o nicho em todo o estado (2021–2025): o recorte por ' +
      (state.sec != null ? 'secretaria' : 'região') + ' não se aplica aqui. ' +
      'Para ver esse recorte, use as abas Compradores (secretaria) e Logística (região).', 'alerta');
  } else if(state.familia != null){
    marca('dossie-aviso', 'Mostrando o nicho escolhido no filtro de família.', 'neutra');
  } else {
    marca('dossie-aviso', '', 'neutra');
  }

  el('dossie-resumo').innerHTML =
    `<b>${sentencaCase(f.n)}</b> · score <b>${dec1(f.s)}</b> · faixa ${s.length?s[0]+'–'+s[1]:'—'} em 14 cenários ·
     ${brlM(m[MET.v2425])}/ano · ${pct(m[MET.teto],0)} abaixo do teto · ${num(m[MET.nforn])} fornecedores · ${pct(m[MET.disp],0)} em dispensa`;

  // calendário
  const s12 = SAZ[i] || [];
  const mes = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
  if(state.ano != null){
    marca('c_dossie_cal', 'Índice mensal médio de 2021–2025; o filtro de ano não se aplica aqui.', 'neutra');
  } else marca('c_dossie_cal', '', 'neutra');
  draw('c_dossie_cal', {
    grid:{...BASE_GRID, top:14, bottom:18},
    tooltip:{formatter:p=>`${mes[p.dataIndex]}: índice ${s12[p.dataIndex]}`},
    xAxis:{type:'category', data:mes, ...AXIS, axisLabel:{...AXISL}},
    yAxis:{type:'value', min:0, ...AXIS, axisLabel:{...AXISL}},
    series:[{type:'bar', data:s12.map(v=>v==null?null:+v.toFixed(2)),
      itemStyle:{color:p=>p.value>=1.2?'var(--c-s2)':(p.value>=1?'var(--c-s1)':'#c7dadd'), borderRadius:2},
      markLine:{silent:true, symbol:'none', lineStyle:{color:'#8a97a3',type:'dashed'},
        label:{formatter:'1,0', fontSize:10, position:'insideEndTop'}, data:[{yAxis:1}]}}]
  });

  // preço
  const itens = DATA.preco[i] || [];
  const series = [], legend = [];
  itens.forEach((it,k)=>{
    const nome = String(it[0]).slice(0,24) + ' (' + (it[1]||'un') + ')';
    const p25 = state.real ? it[2] : it[6], p50 = state.real ? it[3] : it[7], p75 = state.real ? it[4] : it[8];
    const faixa = p75.map((v,j)=> (v!=null && p25[j]!=null) ? +(v - p25[j]).toFixed(4) : null);
    legend.push(nome);
    series.push({name:nome+' base', type:'line', data:p25, stack:'b'+k, symbol:'none', lineStyle:{opacity:0}, areaStyle:{opacity:0}, silent:true});
    series.push({name:nome+' faixa', type:'line', data:faixa, stack:'b'+k, symbol:'none', lineStyle:{opacity:0},
      areaStyle:{color:COLORS[k%COLORS.length], opacity:.16}, silent:true});
    series.push({name:nome, type:'line', data:p50, smooth:true, symbolSize:4, z:5,
      lineStyle:{width:2, color:COLORS[k%COLORS.length]}, itemStyle:{color:COLORS[k%COLORS.length]}});
  });
  draw('c_dossie_preco', series.length ? {
    grid:{...BASE_GRID, top:10, right:8, bottom:18},
    tooltip:{trigger:'axis', valueFormatter:v=>v==null?'—':brl(v)},
    legend:{show:false},
    xAxis:{type:'category', data:ANOS, ...AXIS, axisLabel:{...AXISL}},
    yAxis:{type:'value', scale:true, ...AXIS, axisLabel:{...AXISL, formatter:v=>v>=1000?nf1.format(v/1000)+'k':nf1.format(v)}},
    series
  } : {title:{text:'Sem itens no recorte', left:'center', top:'middle', textStyle:{fontSize:12,color:'#4a5764'}}});

  // órgãos
  const acc = new Map();
  ORG.forEach(r => {
    if(r[0]!==i) return;
    if(state.ano != null && r[2] !== state.ano) return;
    acc.set(r[1], (acc.get(r[1])||0) + r[3]);
  });
  const org = [...acc.entries()].map(([sec,v])=>({sec,v})).sort((a,b)=>b.v-a.v).slice(0,6);
  const totOrg = org.reduce((a,b)=>a+b.v,0) || 1;
  el('t_dossie_orgaos').tHead.innerHTML = '<tr><th scope="col">Secretaria</th><th scope="col" class="num">R$</th><th scope="col" class="num">%</th></tr>';
  el('t_dossie_orgaos').tBodies[0].innerHTML = org.map(o =>
    `<tr><td>${curta(DATA.secretarias[o.sec]).slice(0,44)}</td><td class="num">${brlM(o.v)}</td>
     <td class="num">${pct(o.v/totOrg,0)}</td></tr>`).join('') ||
    '<tr><td colspan="3">sem compras no recorte</td></tr>';

  // itens (preço do ano selecionado, quando houver)
  const kAno = anoIdx != null ? anoIdx : 4;
  const rotuloAno = anoIdx != null ? `Preço em ${state.ano}` : 'Preço mediano (2025)';
  el('t_dossie_itens').tHead.innerHTML =
    `<tr><th scope="col">Item</th><th scope="col">UM</th><th scope="col" class="num">${rotuloAno}</th>` +
    '<th scope="col" class="num">p25–p75</th><th scope="col" class="num">Nº</th></tr>';
  el('t_dossie_itens').tBodies[0].innerHTML = itens.map(it => {
    const p50 = state.real ? it[3] : it[7], p25 = state.real ? it[2] : it[6], p75 = state.real ? it[4] : it[8];
    const lin = (it[5]||[]).reduce((a,b)=>a+b,0);
    const eh = x => x == null ? '—' : brl(x);
    return `<tr><td>${String(it[0]).slice(0,26)}</td><td>${it[1]||'—'}</td>
      <td class="num">${eh(p50[kAno])}</td>
      <td class="num">${p25[kAno]==null?'—':brl(p25[kAno])+' – '+brl(p75[kAno])}</td>
      <td class="num">${num(lin)}</td></tr>`;
  }).join('') || '<tr><td colspan="5">sem itens no recorte</td></tr>';

  // logística
  const accR = new Map();
  REG.forEach(r => { if(r[0]!==i) return; if(state.ano && r[2]!==state.ano) return;
    accR.set(r[1], (accR.get(r[1])||0) + (state.real ? r[3] : r[4])); });
  const regs = [...accR.entries()].map(([ri,v])=>({ri,v})).sort((a,b)=>b.v-a.v).slice(0,5);
  const totR = regs.reduce((a,b)=>a+b.v,0) || 1;
  const pz = DATA.prazo[i] || [];
  el('t_dossie_logistica').tHead.innerHTML =
    '<tr><th scope="col">Região</th><th scope="col" class="num">R$</th><th scope="col" class="num">%</th></tr>';
  el('t_dossie_logistica').tBodies[0].innerHTML = regs.map(r =>
    `<tr><td>${curta(DATA.regioes[r.ri]).slice(0,40)}${DATA.raio_regiao[r.ri]==='dentro'?' <span class="badge badge--ok"><span aria-hidden="true">✓</span>raio</span>':''}</td>
     <td class="num">${brlM(r.v)}</td><td class="num">${pct(r.v/totR,0)}</td></tr>`).join('')
    + (pz.length ? `<tr><td><b>prazo mediano</b></td><td class="num">${num(pz[0])} d</td><td class="num">p90 ${num(pz[1])} d</td></tr>` : '');

  // incumbentes
  const forn = (DATA.fornecedores[i] || []);
  el('t_dossie_forn').tHead.innerHTML =
    '<tr><th scope="col">Fornecedor</th><th scope="col">UF</th><th scope="col" class="num">R$</th><th scope="col" class="num">share</th></tr>';
  el('t_dossie_forn').tBodies[0].innerHTML = forn.map(r =>
    `<tr><td>${String(r[0]).slice(0,38)}</td><td>${r[1]||'—'}</td><td class="num">${brlM(r[3])}</td>
     <td class="num">${pct(r[4],1)}</td></tr>`).join('') ||
    '<tr><td colspan="4">sem fornecedores pessoa jurídica no recorte</td></tr>';

  // próximos passos (derivados do calendário e dos órgãos)
  const picos = s12.map((v,k)=>({mes:k+1, v})).filter(x=>x.v!=null).sort((a,b)=>b.v-a.v).slice(0,2);
  const orgTop = org[0];
  const passos = [];
  if(picos.length) passos.push(`Preparar proposta antes de <b>${mes[picos[0].mes-1]}</b> — mês de pico (índice ${picos[0].v.toFixed(2).replace('.',',')}× a média).`);
  if(orgTop) passos.push(`Começar pelo órgão <b>${curta(DATA.secretarias[orgTop.sec]).slice(0,48)}</b> (${brlM(orgTop.v)} no período).`);
  passos.push(`Disputar por dispensa: ${pct(m[MET.teto],0)} das AFM/APS ficam abaixo de R$ ${nf0.format(META.teto)}.`);
  passos.push(`Cadastrar preço na faixa mediana de <b>${brl(m[MET.ticket])}</b> por AFM/APS e revisar a cada cotação.`);
  document.querySelector('[data-proximos-passos]').innerHTML = passos.map(p=>`<li>${p}</li>`).join('');
}

/* ============================ MÉTODO ============================ */
function renderMetodo(){
  const q = DATA.qualidade;
  el('t_filtros').tHead.innerHTML = '<tr><th scope="col">Passo</th><th scope="col">Descrição</th>' +
    '<th scope="col" class="num">Linhas</th><th scope="col" class="num">Δ linhas</th><th scope="col" class="num">Valor</th><th scope="col">Motivo</th></tr>';
  el('t_filtros').tBodies[0].innerHTML = q.conservacao.map(p =>
    `<tr><td><b>${p.passo}</b></td><td>${p.descricao}</td><td class="num">${num(p.linhas)}</td>
     <td class="num">${num(p.delta_linhas)}</td><td class="num">${brl(p.valor)}</td><td>${p.motivo}</td></tr>`).join('');
  const r = q.reconciliacao;
  el('recon').innerHTML = `<b>Reconciliação:</b> bruto material ${brl(r.soma_bruta_material)} ·
    tratado ${brl(r.soma_tratado)} · diferença ${brl(r.diferenca_abs)}
    (${(r.diferenca_rel*100).toFixed(6).replace('.',',')}%, tolerância ${(r.tolerancia*100).toFixed(2).replace('.',',')}%)
    <span class="badge badge--ok"><span aria-hidden="true">✓</span>${r.status}</span><br>
    Deflação: convenção <b>${q.convencao}</b> — ${Object.entries(q.deflatores).map(([a,f])=>a+': '+Number(f).toFixed(4)).join(' · ')}`;

  el('l_assump').innerHTML = DATA.assumptions.map(a => {
    const st = (a[2]||'').trim().replace(/\s+/g,'-');
    return `<li><b>${a[0]}</b> ${a[1]} <span class="badge ${st==='VALIDADA'?'badge--ok':''}">${a[2]||''}</span></li>`;
  }).join('');

  el('l_limites').innerHTML = `<ul class="dossie__lista">
    <li><b>Cobertura estadual</b>: base SIMPAS/FIPLAN do Estado da Bahia — não inclui compras municipais.</li>
    <li><b>Sem dados de pagamento/adimplência</b>: medimos contratação, não fluxo de caixa.</li>
    <li><b>Ticket por AFM/APS é proxy</b> do teto legal, que é por contratação/objeto de mesma natureza por UG/ano.</li>
    <li><b>Deflação anual</b> (IPCA), não mensal.</li>
    <li><b>Histórico não é previsão</b>: nenhum número projeta demanda futura.</li>
    <li><b>Entrantes</b>: base começa em 2021; “novo” = primeira aparição, contado de 2022 em diante.</li>
    <li><b>Pandemia</b>: 2021–2022 têm distorção; linhas marcadas ficam fora do escopo padrão.</li>
    <li><b>Filtros</b>: recortes de secretaria/região recompõem valor, participação e CAGR. Indicadores que dependem
        de fornecedor, item ou prazo (HHI, preço, CV, desconto) não têm esse cruzamento e são sinalizados no gráfico.</li>
    <li><b>Faixa de posição</b>: os 14 cenários de sensibilidade ranqueiam as ${F.length} famílias do escopo analítico;
        o ranking da tabela mostra as ${META.n_elegiveis} elegíveis. São bases diferentes, declaradas em cada tela.</li>
  </ul>`;

  const dict = [
    ['valor_total_real','Valor da linha em R$ de dez/2025 (IPCA).'],
    ['score','0–100: média ponderada dos percentis de 7 dimensões, menos penalidades.'],
    ['recorrência','Meses com compra ÷ 60.'],
    ['ticket por AFM/APS','Soma das linhas de uma AFM/APS; mediana da família.'],
    ['% ≤ teto','AFM/APS com valor real ≤ R$ 65.492,11.'],
    ['HHI','Σ(share do fornecedor)² × 10.000; abaixo de 1.500 = fragmentado.'],
    ['CAGR real','(valor 2025 / valor 2021)^(1/4) − 1, em reais.'],
    ['estabilidade_top10','Frequência com que a família fica no top-10 nos 14 cenários de peso.'],
    ['perfil de uso','Consumo recorrente × bem durável, pelo vocabulário do nome básico (informativo).'],
  ];
  el('t_dict').tHead.innerHTML = '<tr><th scope="col">Indicador</th><th scope="col">Definição</th></tr>';
  el('t_dict').tBodies[0].innerHTML = dict.map(d=>`<tr><td><code>${d[0]}</code></td><td>${d[1]}</td></tr>`).join('')
    + Object.entries(META.ids).map(([k,v])=>`<tr><td><code>${k}</code></td><td>agregado <code>${v}.parquet</code></td></tr>`).join('');
}

/* ============================ export ============================ */
function exportCsv(){
  const csv = el('tabela').dataset.csv || '';
  const blob = new Blob(['\ufeff' + csv], {type:'text/csv;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'nicho_score.csv';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  const an = el('anuncio'); if(an) an.textContent = 'CSV exportado com ' +
    (csv ? csv.split('\n').length : 0) + ' linhas do recorte atual.';
}
"""
