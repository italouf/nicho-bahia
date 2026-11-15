"""Funções de renderização dos gráficos analíticos (V4 onward).

As 17 funções abaixo foram EXTRAÍDAS SEM ALTERAÇÃO do painel validado (pré-retrofit):
mesma lógica, mesmos campos, mesmos ids de container. É o que garante o AR-25
(paridade de números). Só o CSS e o contêiner mudam neste retrofit.
"""

from __future__ import annotations

JS_CHARTS = r"""
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

/* ============================ SENSIBILIDADE (A13) ============================ */
function renderSens(){
  const rows = (state.familia != null ? [F[state.familia]] : familiasVisiveis())
    .slice(0, 12).filter(f => f && SENS[f.i]);
  draw('c_sens', {
    grid:{...BASE_GRID, left:8, right:64, top:20, bottom:34},
    tooltip:{trigger:'item', formatter: p => {
      const f = rows[p.dataIndex]; if(!f) return '';
      const s = SENS[f.i];
      return `<b>${sentencaCase(f.n)}</b><br>posição de referência ${s[3]} (faixa ${s[0]}–${s[1]})<br>
              top-10 em ${Math.round(s[2]*100)}% dos 14 cenários`;}},
    xAxis:{type:'value', name:'posição no ranking (14 cenários)', nameLocation:'middle', nameGap:24,
           nameTextStyle:{fontSize:11, color:'#4a5764'}, ...AXIS, min:0, axisLabel:{...AXISL}},
    yAxis:{type:'category', inverse:true, data:rows.map(f=>sentencaCase(f.n).slice(0,38)),
           axisLabel:{fontSize:11, ...AXISL}, axisLine:AXIS.axisLine},
    series:[
      {type:'bar', data:rows.map(f=>[SENS[f.i][0], SENS[f.i][1]]),
       itemStyle:{color:'#bcd7d9', borderRadius:3}, barWidth:8, silent:true, name:'faixa'},
      {type:'scatter', data:rows.map((f,k)=>[SENS[f.i][3], k]), symbolSize:9,
       itemStyle:{color:'#0a6c74'}, name:'referência'}
    ]
  });
  semRecorte('c_sens', ['familia']);
}

/* ============================ orquestração ============================ */
const RENDER = {
  decisao: [renderVeredito, renderCards, renderSens, renderTabela, renderEvitar],
  dossie: [renderDossie],
  mercado: [renderSerie, renderTreemap, renderCagr],
  sazonalidade: [renderHeat, renderCal],
  compradores: [renderOrgaos, renderCanal, renderTicket],
  concorrencia: [renderConc, renderEntrantes, renderFornecedores],
  precos: [renderPreco, renderCv, renderDesc],
  logistica: [renderRegiao, renderPrazo, renderMun],
  metodo: [renderMetodo],
};

function renderTab(){
  setAba(state.tab);
  renderChips();
  escreverUrl();
  (RENDER[state.tab] || []).forEach(fn => {
    try { fn(); }
    catch (e) { console.error('chart fail', fn.name || fn, e); }
  });
}

window.addEventListener('DOMContentLoaded', () => {
  lerUrl();
  initFiltros();
  initAbas();
  initDossie();
  const busca = el('busca');
  if(busca) busca.addEventListener('input', e => {
    state.busca = e.target.value; state.pagina = 1; renderTabela();
  });
  const csv = el('btn_csv');
  if(csv) csv.addEventListener('click', exportCsv);
  window.addEventListener('resize', () => {
    Object.values(charts).forEach(c => { try { c.resize(); } catch(e){} });
  }, {passive:true});
  renderTab();
  document.body.dataset.pronto = '1';
});
window.addEventListener('error', e => console.error('erro global', e.message));

"""
