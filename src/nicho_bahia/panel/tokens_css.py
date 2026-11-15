"""Design tokens e folha de estilo única do painel (V2).

Regra (AR-22): nenhum valor literal de cor/raio/espaço fora de `:root`.
Tipografia (AR-21): interface ≥ 12px; rótulos de eixo de gráfico ≥ 11px (exceção declarada).
"""

from __future__ import annotations

CSS = r"""
/* ============================== tokens ============================== */
:root{
  /* cor — pares texto/fundo ≥ 4.5:1 */
  --c-bg:#f5f7f9; --c-surface:#ffffff; --c-sunken:#f0f3f6;
  --c-ink:#141c25; --c-ink-2:#48545f; --c-ink-3:#57616c;
  --c-line:#d5dce3; --c-line-2:#e6ebf0;
  --c-accent:#0a6c74; --c-accent-ink:#08545a; --c-accent-soft:#e6f2f3;
  --c-ok:#0f766e; --c-ok-soft:#e6f5f2;
  --c-warn:#8a4b06; --c-warn-soft:#fdf3e4;
  --c-bad:#a31414; --c-bad-soft:#fbeaea;
  --c-focus:#0a6c74; --c-focus-ring:#7cc3c9;
  /* séries categóricas — ordenadas para funcionar em deuteranopia */
  --c-s1:#0a6c74; --c-s2:#c2410c; --c-s3:#7c3aed; --c-s4:#0369a1;
  --c-s5:#a16207; --c-s6:#0f766e; --c-s7:#9f1239; --c-s8:#4d7c0f;
  /* tipografia */
  --f-base:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --f-mono:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace;
  --t-xs:12px; --t-sm:13px; --t-md:14px; --t-lg:17px;
  --t-xl:22px; --t-2xl:30px; --t-hero:36px;
  --lh-tight:1.25; --lh:1.5;
  /* espaço — escala de 4, 6 degraus */
  --s-1:4px; --s-2:8px; --s-3:12px; --s-4:16px; --s-5:24px; --s-6:32px;
  /* raio — 3 degraus */
  --r-1:6px; --r-2:10px; --r-3:14px;
  /* sombra — 2 degraus */
  --sh-1:0 1px 2px rgba(16,24,40,.06);
  --sh-2:0 2px 10px rgba(16,24,40,.10);
  /* alvos e largura */
  --touch:44px; --w-max:1560px; --chart-h:300px; --chart-h-tall:420px; --chart-h-short:230px;
}

/* ============================== base ============================== */
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--c-bg);color:var(--c-ink);font:var(--t-md)/var(--lh) var(--f-base)}
h1,h2,h3,h4{margin:0;line-height:var(--lh-tight);font-weight:650}
p{margin:0}
a{color:var(--c-accent-ink)}
:focus-visible{outline:3px solid var(--c-focus);outline-offset:2px;border-radius:var(--r-1)}
.sr{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
.skip{position:absolute;left:var(--s-3);top:-100px;z-index:99;background:var(--c-accent);color:#fff;
  min-height:var(--touch);display:inline-flex;align-items:center;padding:var(--s-2) var(--s-4);
  border-radius:var(--r-1);font-size:var(--t-sm);text-decoration:none}
.skip:focus{top:var(--s-2)}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;scroll-behavior:auto!important}}

/* ============================== topo ============================== */
.topo{position:sticky;top:0;z-index:20;background:var(--c-surface);border-bottom:1px solid var(--c-line);
  box-shadow:var(--sh-1);padding:var(--s-3) var(--s-4) var(--s-2)}
.topo__linha{display:flex;gap:var(--s-4);align-items:flex-start;justify-content:space-between;flex-wrap:wrap}
.topo__marca{min-width:0}
.topo h1{font-size:var(--t-lg)}
.topo h1 span{color:var(--c-accent);font-weight:650}
.topo__sub{color:var(--c-ink-2);font-size:var(--t-sm);margin-top:var(--s-1)}
.topo__sub b{color:var(--c-ink)}
.topo__acoes{display:flex;gap:var(--s-2);align-items:center}

/* filtros: linha no desktop, colapsáveis no mobile */
.filtros{display:flex;gap:var(--s-3);align-items:flex-end;flex-wrap:wrap;margin-top:var(--s-3)}
.filtros__toggle{display:none}
.filtros__campos{display:flex;gap:var(--s-3);align-items:flex-end;flex-wrap:wrap}
.campo{display:flex;flex-direction:column;gap:var(--s-1);min-width:0}
.campo label{font-size:var(--t-xs);color:var(--c-ink-2);font-weight:600}
select,.btn{font:inherit;font-size:var(--t-sm);color:var(--c-ink);background:var(--c-surface);
  border:1px solid var(--c-line);border-radius:var(--r-1);padding:var(--s-2) var(--s-3);min-height:var(--touch)}
select{max-width:260px}
.btn{cursor:pointer}
.btn:hover{border-color:var(--c-accent);color:var(--c-accent-ink)}
.btn--primary{background:var(--c-accent);border-color:var(--c-accent);color:#fff}
.btn--primary:hover{background:var(--c-accent-ink);color:#fff}
.toggle{display:inline-flex;border:1px solid var(--c-line);border-radius:var(--r-1);overflow:hidden}
.toggle button{font:inherit;font-size:var(--t-sm);padding:var(--s-2) var(--s-3);border:0;background:var(--c-surface);
  color:var(--c-ink-2);cursor:pointer;min-height:var(--touch)}
.toggle button.on{background:var(--c-accent);color:#fff;font-weight:650}

/* chips de recorte */
.chips{display:flex;gap:var(--s-2);align-items:center;flex-wrap:wrap;margin-top:var(--s-2);min-height:0}
.chips:empty{display:none}
.chip{display:inline-flex;align-items:center;gap:var(--s-2);background:var(--c-accent-soft);
  color:var(--c-accent-ink);border:1px solid var(--c-focus-ring);border-radius:999px;
  padding:2px var(--s-2) 2px var(--s-3);font-size:var(--t-xs);font-weight:600}
.chip button{border:0;background:none;color:inherit;cursor:pointer;font-size:var(--t-md);line-height:1;
  padding:var(--s-1);border-radius:999px}
.chip button:hover{background:#cfe6e8}
.chips__limpar{margin-left:auto}

/* ============================== navegação ============================== */
.nav{display:flex;gap:var(--s-1);overflow-x:auto;scroll-snap-type:x proximity;background:var(--c-surface);
  border-bottom:1px solid var(--c-line);padding:0 var(--s-3)}
.nav::-webkit-scrollbar{height:3px}
.nav button{scroll-snap-align:start;font:inherit;font-size:var(--t-sm);white-space:nowrap;
  padding:var(--s-3) var(--s-3);border:0;border-bottom:3px solid transparent;background:none;
  color:var(--c-ink-2);cursor:pointer;min-height:var(--touch)}
.nav button[aria-selected="true"]{color:var(--c-ink);font-weight:700;border-bottom-color:var(--c-accent)}

/* ============================== conteúdo ============================== */
main{padding:var(--s-4) var(--s-4) var(--s-6);max-width:var(--w-max);margin:0 auto}
.painel{display:none}
.painel.on{display:block}
.grid{display:grid;gap:var(--s-3);grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
.card{background:var(--c-surface);border:1px solid var(--c-line);border-radius:var(--r-2);
  box-shadow:var(--sh-1);padding:var(--s-3) var(--s-4) var(--s-2);min-width:0}
.card.full{grid-column:1/-1}
.card h2,.card h3{font-size:var(--t-md);font-weight:650}
.card__hint{font-size:var(--t-sm);color:var(--c-ink-2);margin:var(--s-1) 0 var(--s-2)}
.chart{width:100%;height:var(--chart-h)}
.chart.tall{height:var(--chart-h-tall)}
.chart.short{height:var(--chart-h-short)}
.rodape{border-top:1px dashed var(--c-line);margin-top:var(--s-2);padding-top:var(--s-1);
  font-size:var(--t-xs);color:var(--c-ink-3);display:flex;justify-content:space-between;gap:var(--s-2);flex-wrap:wrap}
.rodape code{font-family:var(--f-mono);font-size:var(--t-xs);background:var(--c-sunken);padding:0 var(--s-1);border-radius:var(--r-1)}
.marca{font-size:var(--t-xs);padding:var(--s-1) var(--s-2);border-radius:var(--r-1);margin:var(--s-1) 0 var(--s-2);display:none}
.marca.alerta{display:block;color:var(--c-warn);background:var(--c-warn-soft);border:1px solid #f0d9b5}
.marca.neutra{display:block;color:var(--c-ink-2);background:var(--c-sunken);border:1px solid var(--c-line-2)}

/* ============================== veredito ============================== */
.veredito{background:linear-gradient(180deg,var(--c-surface),var(--c-accent-soft));
  border:1px solid var(--c-focus-ring);border-radius:var(--r-3);padding:var(--s-4);box-shadow:var(--sh-1);
  margin-bottom:var(--s-3)}
.veredito h2{font-size:var(--t-xl)}
.veredito__meta{color:var(--c-ink-2);font-size:var(--t-sm);margin-top:var(--s-2);display:flex;gap:var(--s-3);flex-wrap:wrap;align-items:center}
.veredito__meta b{color:var(--c-ink)}
.veredito__nichos{display:flex;gap:var(--s-2);flex-wrap:wrap;margin-top:var(--s-3)}
.veredito__nicho{background:var(--c-surface);border:1px solid var(--c-line);border-radius:999px;
  padding:var(--s-1) var(--s-3);font-size:var(--t-sm);display:inline-flex;gap:var(--s-2);align-items:center}
.veredito__nicho b{font-variant-numeric:tabular-nums}
.veredito__como{margin-top:var(--s-3)}
.veredito__como summary{cursor:pointer;font-size:var(--t-sm);color:var(--c-accent-ink);font-weight:600}
.veredito__como ul{margin:var(--s-2) 0 0;padding-left:var(--s-5);font-size:var(--t-sm);color:var(--c-ink-2)}

/* ============================== cards de nicho ============================== */
.cards{display:grid;gap:var(--s-3);grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.niche{background:var(--c-surface);border:1px solid var(--c-line);border-radius:var(--r-2);
  padding:var(--s-4);box-shadow:var(--sh-1);display:flex;flex-direction:column;gap:var(--s-2)}
.niche__topo{display:flex;justify-content:space-between;align-items:flex-start;gap:var(--s-3)}
.niche__nome{font-size:var(--t-lg);font-weight:700;line-height:var(--lh-tight)}
.niche__codigo{display:block;font-family:var(--f-mono);font-size:var(--t-xs);color:var(--c-ink-3);
  font-weight:500;margin-top:var(--s-1)}
.niche__codigo::before{content:"família "}
.niche__score{text-align:right;flex:none}
.niche__score b{display:block;font-size:var(--t-hero);line-height:1;color:var(--c-accent);font-variant-numeric:tabular-nums}
.niche__score span{font-size:var(--t-xs);color:var(--c-ink-2);font-weight:600}
.niche__faixa{font-size:var(--t-sm);color:var(--c-ink-2);margin-top:var(--s-1)}
.niche__faixa b{color:var(--c-ink)}
.niche__tese{font-size:var(--t-sm);color:var(--c-ink);margin:var(--s-1) 0}
.niche__riscos{display:flex;flex-wrap:wrap;gap:var(--s-2);margin:0;padding:0;list-style:none}
.badge{display:inline-flex;gap:var(--s-1);align-items:center;font-size:var(--t-xs);
  background:var(--c-warn-soft);color:var(--c-warn);border:1px solid #f0d9b5;border-radius:var(--r-1);
  padding:2px var(--s-2);font-weight:600}
.badge--bad{background:var(--c-bad-soft);color:var(--c-bad);border-color:#f0c9c9}
.badge--ok{background:var(--c-ok-soft);color:var(--c-ok);border-color:#bfe3dc}
.niche__metricas{display:grid;grid-template-columns:repeat(2,1fr);gap:var(--s-1) var(--s-3);
  font-size:var(--t-sm);color:var(--c-ink-2);margin-top:auto}
.niche__metricas b{color:var(--c-ink);font-variant-numeric:tabular-nums}
.niche__cta{margin-top:var(--s-2)}
.spark{width:100%;height:34px;display:block}

/* ============================== tabela ============================== */
.tabela__barra{display:flex;gap:var(--s-3);align-items:flex-end;flex-wrap:wrap;margin-bottom:var(--s-2)}
.tabela__busca{flex:1 1 240px;min-width:0}
input[type="search"]{font:inherit;font-size:var(--t-sm);width:100%;padding:var(--s-2) var(--s-3);
  border:1px solid var(--c-line);border-radius:var(--r-1);min-height:var(--touch);background:var(--c-surface);color:var(--c-ink)}
.tabela__contador{font-size:var(--t-sm);color:var(--c-ink-2);font-variant-numeric:tabular-nums}
.tabela__scroll{max-height:460px;overflow:auto;border:1px solid var(--c-line-2);border-radius:var(--r-1)}
table{width:100%;border-collapse:collapse;font-size:var(--t-sm)}
th,td{padding:var(--s-2) var(--s-2);border-bottom:1px solid var(--c-line-2);text-align:left;vertical-align:top}
th{position:sticky;top:0;z-index:1;background:var(--c-sunken);font-size:var(--t-xs);
  text-transform:none;letter-spacing:0;color:var(--c-ink-2);cursor:pointer;white-space:nowrap}
th[aria-sort="ascending"],th[aria-sort="descending"]{color:var(--c-accent-ink)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tbody tr:hover td{background:#fbfcfd}
.paginacao{display:flex;gap:var(--s-2);align-items:center;justify-content:flex-end;margin-top:var(--s-2);font-size:var(--t-sm)}
.paginacao button{min-height:var(--touch);min-width:var(--touch);padding:0 var(--s-2)}
.rolagem{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
summary{min-height:var(--touch);display:flex;align-items:center;gap:var(--s-2)}

/* ============================== dossiê ============================== */
.dossie__topo{display:flex;gap:var(--s-3);align-items:flex-end;flex-wrap:wrap;margin-bottom:var(--s-3)}
.dossie__grid{display:grid;gap:var(--s-3);grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}
.dossie__grid .full{grid-column:1/-1}
.dossie__lista{margin:0;padding-left:var(--s-5);font-size:var(--t-sm);color:var(--c-ink-2)}
.dossie__lista li{margin-bottom:var(--s-1)}
.dossie__passos{counter-reset:p;margin:0;padding:0;list-style:none;font-size:var(--t-sm)}
.dossie__passos li{counter-increment:p;padding-left:var(--s-6);position:relative;margin-bottom:var(--s-2)}
.dossie__passos li::before{content:counter(p);position:absolute;left:0;top:0;width:22px;height:22px;
  border-radius:999px;background:var(--c-accent);color:#fff;font-size:var(--t-xs);font-weight:700;
  display:grid;place-items:center}

/* ============================== estados ============================== */
.estado-vazio{display:grid;place-items:center;gap:var(--s-2);height:var(--chart-h);
  border:1px dashed var(--c-line);border-radius:var(--r-2);background:var(--c-sunken);
  color:var(--c-ink-2);font-size:var(--t-sm);text-align:center;padding:var(--s-3)}
.estado-vazio strong{color:var(--c-ink);display:block;font-size:var(--t-md)}
.skeleton{height:var(--chart-h);border-radius:var(--r-2);
  background:linear-gradient(90deg,var(--c-sunken) 25%,#e9eef3 37%,var(--c-sunken) 63%);
  background-size:400% 100%;animation:sk 1.2s ease infinite}
@keyframes sk{0%{background-position:100% 50%}100%{background-position:0 50%}}

/* ============================== responsivo ============================== */
@media (max-width:1023px){
  .grid{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
  main{padding:var(--s-3)}
}
@media (max-width:599px){
  :root{--chart-h:220px; --chart-h-tall:260px; --chart-h-short:190px}
  .topo{padding:var(--s-2) var(--s-3)}
  .topo h1{font-size:var(--t-md)}
  .topo__sub{font-size:var(--t-xs)}
  .filtros__toggle{display:inline-flex}
  .filtros__campos{display:none}
  .filtros__campos.on{display:flex;width:100%}
  .filtros__campos .campo{flex:1 1 100%}
  select{max-width:none;width:100%}
  .grid,.cards,.dossie__grid{grid-template-columns:1fr}
  .veredito{padding:var(--s-3)}
  .veredito h2{font-size:var(--t-lg)}
  .niche__score b{font-size:var(--t-2xl)}
  .tabela__scroll{display:none}      /* em mobile a tabela vira cartões */
  .tabela__cartoes{display:block}
  .nav button{padding:var(--s-2) var(--s-2);font-size:var(--t-xs)}
}
.tabela__cartoes{display:none}
.tabela__cartao{border:1px solid var(--c-line-2);border-radius:var(--r-2);padding:var(--s-3);margin-bottom:var(--s-2);
  background:var(--c-surface)}
.tabela__cartao h4{font-size:var(--t-md);margin-bottom:var(--s-1)}
.tabela__cartao dl{display:grid;grid-template-columns:auto 1fr;gap:var(--s-1) var(--s-2);margin:0;font-size:var(--t-sm)}
.tabela__cartao dt{color:var(--c-ink-2)}
.tabela__cartao dd{margin:0;text-align:right;font-variant-numeric:tabular-nums}

/* ============================== impressão ============================== */
@media print{
  :root{--chart-h:200px; --chart-h-tall:220px; --chart-h-short:170px}
  body{background:#fff;font-size:11pt}
  .topo,.nav,.chips,.filtros,.paginacao,.tabela__barra,.niche__cta,.btn,footer.rodape{display:none!important}
  main{padding:0;max-width:none}
  .painel{display:none!important}
  .painel.on{display:block!important}
  .card,.niche,.veredito{box-shadow:none;border-color:#999;break-inside:avoid}
  .dossie__grid{grid-template-columns:1fr 1fr}
  a[href]::after{content:""}
  @page{margin:12mm}
}
"""
