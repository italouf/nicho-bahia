"""Esqueleto HTML do painel (V3–V7): 9 abas, header em 2 linhas, chips, tabela, dossiê.

Os ids dos 18 gráficos existentes são preservados para o teste de paridade (AR-25).
Componentes dinâmicos são preenchidos pelo JS; aqui fica só a estrutura e os textos de decisão.
"""

from __future__ import annotations

BODY = r"""
<a class="skip" href="#conteudo">Ir para o conteúdo</a>

<header class="topo">
  <div class="topo__linha">
    <div class="topo__marca">
      <h1>Painel de decisão de nicho — compras públicas da Bahia <span>2021–2025</span></h1>
      <p class="topo__sub">
        Base SIMPAS/FIPLAN · material, não regulado, não pandemia ·
        <b id="hdr_n">—</b> nichos ranqueados ·
        <span id="base-preco">valores em R$ de dez/2025</span> ·
        histórico não é previsão
      </p>
    </div>
    <div class="topo__acoes">
      <span class="toggle" role="group" aria-label="Base de preços exibida">
        <button id="btn_real" class="on" aria-pressed="true">R$ reais</button>
        <button id="btn_nom" aria-pressed="false">R$ nominais</button>
      </span>
    </div>
  </div>

  <div class="filtros">
    <button class="btn filtros__toggle" id="filtros-toggle" aria-expanded="true" aria-controls="filtros-campos">
      Filtros
    </button>
    <div class="filtros__campos" id="filtros-campos">
      <span class="campo"><label for="f_ano">Ano</label><select id="f_ano"><option value="">todos</option></select></span>
      <span class="campo"><label for="f_sec">Secretaria</label><select id="f_sec"><option value="">todas</option></select></span>
      <span class="campo"><label for="f_reg">Região de entrega</label><select id="f_reg"><option value="">todas</option></select></span>
      <span class="campo"><label for="f_fam">Família</label><select id="f_fam"><option value="">todas</option></select></span>
      <button class="btn" id="btn_reset">limpar filtros</button>
    </div>
  </div>

  <div class="chips" id="chips" data-chips aria-live="polite"></div>
</header>

<nav class="nav" id="tabs" role="tablist" aria-label="Seções do painel">
  <button role="tab" id="tabbtn-decisao" aria-controls="tab-decisao" aria-selected="true" tabindex="0">Decisão</button>
  <button role="tab" id="tabbtn-dossie" aria-controls="tab-dossie" aria-selected="false" tabindex="-1">Dossiê</button>
  <button role="tab" id="tabbtn-mercado" aria-controls="tab-mercado" aria-selected="false" tabindex="-1">Mercado</button>
  <button role="tab" id="tabbtn-sazonalidade" aria-controls="tab-sazonalidade" aria-selected="false" tabindex="-1">Sazonalidade</button>
  <button role="tab" id="tabbtn-compradores" aria-controls="tab-compradores" aria-selected="false" tabindex="-1">Compradores</button>
  <button role="tab" id="tabbtn-concorrencia" aria-controls="tab-concorrencia" aria-selected="false" tabindex="-1">Concorrência</button>
  <button role="tab" id="tabbtn-precos" aria-controls="tab-precos" aria-selected="false" tabindex="-1">Preços</button>
  <button role="tab" id="tabbtn-logistica" aria-controls="tab-logistica" aria-selected="false" tabindex="-1">Logística</button>
  <button role="tab" id="tabbtn-metodo" aria-controls="tab-metodo" aria-selected="false" tabindex="-1">Método</button>
</nav>

<main id="conteudo">

  <!-- ======================= DECISÃO ======================= -->
  <section class="painel on" id="tab-decisao" role="tabpanel" aria-labelledby="tabbtn-decisao" tabindex="0">
    <section class="veredito" data-veredito aria-labelledby="veredito-titulo">
      <h2 id="veredito-titulo" data-veredito-frase>Carregando recomendação…</h2>
      <p class="veredito__meta">
        <span>Leitura em <b data-tempo-leitura>≈ 5 min</b></span>
        <span>Score é global e não é recalculado pelos filtros</span>
        <span><b data-n-elegiveis>—</b> nichos elegíveis de <b data-n-total>—</b> famílias</span>
      </p>
      <div class="veredito__nichos" data-veredito-nichos></div>
      <details class="veredito__como">
        <summary>Como ler este painel</summary>
        <ul>
          <li><b>Score 0–100</b>: média ponderada de 7 dimensões (demanda, crescimento, recorrência,
              fit de dispensa, fragmentação, estabilidade de preço e logística), menos penalidades.
              Quanto maior, melhor o encaixe com a estratégia da startup.</li>
          <li><b>Faixa de posição</b>: o nicho foi reavaliado em 14 cenários com ±20% nos pesos do score.
              Faixa estreita perto do topo = recomendação estável.</li>
          <li><b>Perfil de uso</b>: “consumo recorrente” é o alvo; “bem durável” exige instalação e
              assistência técnica e não é recomendado para o primeiro ataque.</li>
          <li><b>Cores e selos</b>: o selo de alerta traz sempre texto e ícone — a cor nunca é a única
              informação.</li>
          <li><b>Rastreabilidade</b>: cada gráfico informa, no rodapé, o agregado que o originou.</li>
        </ul>
      </details>
    </section>

    <div class="cards" id="cards" data-cards aria-live="polite"></div>

    <div class="card full" style="margin-top:var(--s-3)">
      <h2>A recomendação é estável?</h2>
      <p class="card__hint">Cada família foi reavaliada em 14 cenários com ±20% nos pesos do score.
        Faixa estreita perto do topo significa recomendação robusta.</p>
      <div id="c_sens" class="chart short" role="img"
           aria-label="Faixa de posição das famílias nos 14 cenários de sensibilidade"></div>
      <footer class="rodape"><span>Posição no ranking por cenário · os 12 primeiros nichos</span><code>A13</code></footer>
    </div>

    <div class="card full" style="margin-top:var(--s-3)">
      <h2 id="tabela-titulo">Compare os nichos</h2>
      <p class="card__hint">Busque por nome ou código, ordene pelo cabeçalho. O CSV exporta todas as
        linhas do recorte atual, não apenas a página visível.</p>
      <div class="tabela__barra">
        <span class="campo tabela__busca">
          <label for="busca">Buscar nicho</label>
          <input type="search" id="busca" placeholder="ex.: café, papel, 75.10" autocomplete="off">
        </span>
        <span class="tabela__contador" id="contador" aria-live="polite">—</span>
        <button class="btn btn--primary" id="btn_csv">Exportar CSV</button>
      </div>
      <div class="tabela__scroll" id="tabela-scroll" tabindex="0" role="region"
           aria-labelledby="tabela-titulo" aria-describedby="tabela-ajuda">
        <table id="tabela"><thead></thead><tbody></tbody></table>
      </div>
      <p class="sr" id="tabela-ajuda">Tabela rolável. Use as setas para percorrer; o cabeçalho é fixo.</p>
      <div class="tabela__cartoes" id="tabela-cartoes"></div>
      <nav class="paginacao" id="paginacao" aria-label="Paginação da tabela"></nav>
      <footer class="rodape"><span>Todos os nichos elegíveis; a busca e a ordenação não alteram os valores</span><code>A09</code></footer>
    </div>

    <div class="card full">
      <h2>O que evitar</h2>
      <p class="card__hint">Famílias com barreira regulatória (registro sanitário, ANVISA, produto
        controlado) ou majoritariamente reguladas.</p>
      <div class="rolagem" tabindex="0" role="region" aria-label="Tabela com rolagem horizontal"><table id="t_evitar"><thead></thead><tbody></tbody></table></div>
      <footer class="rodape"><span>Critério editável em config.yaml → regulados</span><code>A12</code></footer>
    </div>
  </section>

  <!-- ======================= DOSSIÊ ======================= -->
  <section class="painel" id="tab-dossie" role="tabpanel" aria-labelledby="tabbtn-dossie" tabindex="0">
    <div class="dossie__topo">
      <span class="campo" style="min-width:320px">
        <label for="dossie-select">Nicho</label>
        <select id="dossie-select"></select>
      </span>
      <p class="card__hint" id="dossie-resumo" style="margin:0;flex:1 1 320px"></p>
      <button class="btn" id="btn_imprimir">Imprimir / PDF</button>
    </div>

    <div class="dossie__grid">
      <article class="card" data-dossie-secao="calendario">
        <h3>Quando comprar</h3>
        <p class="card__hint">Índice mensal: 1,0 = mês típico; acima de 1,2 = pico de compra.</p>
        <div id="c_dossie_cal" class="chart short" role="img" aria-label="Calendário de compras do nicho"></div>
        <footer class="rodape"><span>Índice mensal médio 2021–2025</span><code>A05</code></footer>
      </article>

      <article class="card" data-dossie-secao="orgaos">
        <h3>Quem compra</h3>
        <p class="card__hint">Órgãos com maior valor no período e quanto usam dispensa.</p>
        <div class="rolagem" tabindex="0" role="region" aria-label="Tabela com rolagem horizontal"><table id="t_dossie_orgaos"><thead></thead><tbody></tbody></table></div>
        <footer class="rodape"><span>Top 6 secretarias do nicho</span><code>A06</code></footer>
      </article>

      <article class="card" data-dossie-secao="itens">
        <h3>Itens-âncora</h3>
        <p class="card__hint">Itens de catálogo com maior valor, recorrência e menor barreira (item comum).</p>
        <div class="rolagem" tabindex="0" role="region" aria-label="Tabela com rolagem horizontal"><table id="t_dossie_itens"><thead></thead><tbody></tbody></table></div>
        <footer class="rodape"><span>Os 3 itens mais comprados do nicho</span><code>A16</code></footer>
      </article>

      <article class="card" data-dossie-secao="preco">
        <h3>Faixa de preço praticada</h3>
        <p class="card__hint">Mediana anual e faixa p25–p75 dos 3 itens mais comprados.</p>
        <div id="c_dossie_preco" class="chart" role="img" aria-label="Faixa de preço dos itens-âncora"></div>
        <footer class="rodape"><span>R$ por unidade</span><code>A16</code></footer>
      </article>

      <article class="card" data-dossie-secao="logistica">
        <h3>Onde entregar e em quanto tempo</h3>
        <div class="rolagem" tabindex="0" role="region" aria-label="Tabela com rolagem horizontal"><table id="t_dossie_logistica"><thead></thead><tbody></tbody></table></div>
        <footer class="rodape"><span>Regiões dentro do raio de 200 km</span><code>A19 · A20</code></footer>
      </article>

      <article class="card" data-dossie-secao="incumbentes">
        <h3>Quem já está lá</h3>
        <p class="card__hint">Fornecedores incumbentes e participação no valor do nicho.</p>
        <div class="rolagem" tabindex="0" role="region" aria-label="Tabela com rolagem horizontal"><table id="t_dossie_forn"><thead></thead><tbody></tbody></table></div>
        <footer class="rodape"><span>Top 6 fornecedores do período</span><code>A15</code></footer>
      </article>

      <article class="card full" data-dossie-secao="acao">
        <h3>Próximos passos e critérios de abandono</h3>
        <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(280px,1fr))">
          <div>
            <h4 style="font-size:var(--t-sm);color:var(--c-ink-2);margin-bottom:var(--s-2)">Ação sugerida</h4>
            <ol class="dossie__passos" data-proximos-passos></ol>
          </div>
          <div>
            <h4 style="font-size:var(--t-sm);color:var(--c-ink-2);margin-bottom:var(--s-2)">Abandonar se</h4>
            <ul class="dossie__lista">
              <li>não houver dispensa eletrônica da família na região por 2 trimestres consecutivos;</li>
              <li>o ticket mediano por AFM/APS passar de R$ <span data-teto>65.492,11</span>, exigindo pregão e atestados;</li>
              <li>o HHI ficar acima de 2.500 com top-3 acima de 70% do valor;</li>
              <li>o preço mediano cair abaixo do custo de reposição em 2 medições trimestrais.</li>
            </ul>
          </div>
        </div>
        <footer class="rodape"><span>Critérios do SPEC §1 e do relatório executivo</span><code>A09 · A13</code></footer>
      </article>
    </div>
  </section>

  <!-- ======================= MERCADO ======================= -->
  <section class="painel" id="tab-mercado" role="tabpanel" aria-labelledby="tabbtn-mercado" tabindex="0">
    <div class="grid">
      <div class="card full">
        <h2>Onde está o dinheiro e como ele evoluiu?</h2>
        <p class="card__hint">Gasto anual por família — top 10 por score, ou a família selecionada.</p>
        <div id="c_serie" class="chart tall" role="img" aria-label="Série anual de gasto por família"></div>
        <footer class="rodape"><span>R$ por ano · 2021–2025</span><code>A01</code></footer>
      </div>
      <div class="card">
        <h2>Qual a fatia de cada família no gasto?</h2>
        <p class="card__hint">Participação no período ou no ano selecionado.</p>
        <div id="c_treemap" class="chart tall" role="img" aria-label="Participação das famílias no gasto"></div>
        <footer class="rodape"><span>Área proporcional ao valor</span><code>A02</code></footer>
      </div>
      <div class="card">
        <h2>Quais famílias crescem de forma sustentada?</h2>
        <p class="card__hint">CAGR real 2021–2025 — as 20 maiores em módulo.</p>
        <div id="c_cagr" class="chart tall" role="img" aria-label="Crescimento anual composto por família"></div>
        <footer class="rodape"><span>% ao ano, valores reais</span><code>A03</code></footer>
      </div>
    </div>
  </section>

  <!-- ======================= SAZONALIDADE ======================= -->
  <section class="painel" id="tab-sazonalidade" role="tabpanel" aria-labelledby="tabbtn-sazonalidade" tabindex="0">
    <div class="grid">
      <div class="card full">
        <h2>Quando o órgão compra?</h2>
        <p class="card__hint">Índice = média do mês ÷ média geral. 1,0 é mês típico; acima de 1,2 é pico.</p>
        <div id="c_heat" class="chart tall" role="img" aria-label="Mapa de calor de sazonalidade por família"></div>
        <footer class="rodape"><span>Índice mensal médio · top 12 famílias por score</span><code>A05</code></footer>
      </div>
      <div class="card full">
        <h2>Qual o calendário de ataque do nicho?</h2>
        <p class="card__hint">Meses em que a família selecionada concentra compras.</p>
        <div id="c_cal" class="chart" role="img" aria-label="Calendário mensal da família selecionada"></div>
        <footer class="rodape"><span>Índice mensal da família selecionada</span><code>A05</code></footer>
      </div>
    </div>
  </section>

  <!-- ======================= COMPRADORES ======================= -->
  <section class="painel" id="tab-compradores" role="tabpanel" aria-labelledby="tabbtn-compradores" tabindex="0">
    <div class="grid">
      <div class="card full">
        <h2>Quem compra e quanto?</h2>
        <p class="card__hint">Top 15 secretarias por valor, com o share do canal dispensa.</p>
        <div id="c_orgaos" class="chart tall" role="img" aria-label="Valor por secretaria compradora"></div>
        <footer class="rodape"><span>R$ milhões · o filtro de ano se aplica aqui</span><code>A06</code></footer>
      </div>
      <div class="card">
        <h2>Por qual porta se entra?</h2>
        <p class="card__hint">Distribuição do valor por canal de compra.</p>
        <div id="c_canal" class="chart" role="img" aria-label="Distribuição do valor por canal de compra"></div>
        <footer class="rodape"><span>% do valor no período</span><code>A07</code></footer>
      </div>
      <div class="card">
        <h2>O ticket cabe na dispensa?</h2>
        <p class="card__hint">Cada bolha é uma família: ticket mediano por AFM/APS × % de compras abaixo do teto.</p>
        <div id="c_ticket" class="chart" role="img" aria-label="Ticket por AFM/APS contra o teto de dispensa"></div>
        <footer class="rodape"><span>Teto de dispensa R$ 65.492,11 (linha vertical)</span><code>A08</code></footer>
      </div>
    </div>
  </section>

  <!-- ======================= CONCORRÊNCIA ======================= -->
  <section class="painel" id="tab-concorrencia" role="tabpanel" aria-labelledby="tabbtn-concorrencia" tabindex="0">
    <div class="grid">
      <div class="card full">
        <h2>A concorrência é fragmentada e há espaço para entrar?</h2>
        <p class="card__hint">Crescimento × concentração (HHI). Bolha = valor. Canto superior esquerdo = mercado grande e fragmentado.</p>
        <div id="c_conc" class="chart tall" role="img" aria-label="Crescimento contra concentração de mercado"></div>
        <footer class="rodape"><span>HHI 0–10.000 (menor = mais fragmentado) · bolha = R$ 2024–2025</span><code>A11</code></footer>
      </div>
      <div class="card">
        <h2>Estão entrando fornecedores novos?</h2>
        <p class="card__hint">Novos fornecedores por ano (primeira aparição na base, a partir de 2022).</p>
        <div id="c_ent" class="chart" role="img" aria-label="Novos fornecedores por ano"></div>
        <footer class="rodape"><span>Contagem de novos entrantes</span><code>A14</code></footer>
      </div>
      <div class="card">
        <h2>Quem são os incumbentes?</h2>
        <p class="card__hint">Top fornecedores da família selecionada no período.</p>
        <div id="c_forn" class="chart" role="img" aria-label="Maiores fornecedores da família selecionada"></div>
        <footer class="rodape"><span>R$ milhões por fornecedor</span><code>A15 · A10</code></footer>
      </div>
    </div>
  </section>

  <!-- ======================= PREÇOS ======================= -->
  <section class="painel" id="tab-precos" role="tabpanel" aria-labelledby="tabbtn-precos" tabindex="0">
    <div class="grid">
      <div class="card full">
        <h2>Qual a faixa de preço praticada por item-âncora?</h2>
        <p class="card__hint">Mediana anual e faixa p25–p75 dos 3 itens mais comprados da família selecionada.</p>
        <div id="c_preco" class="chart tall" role="img" aria-label="Faixa de preço por item-âncora"></div>
        <footer class="rodape"><span>R$ por unidade</span><code>A16</code></footer>
      </div>
      <div class="card">
        <h2>O preço é estável?</h2>
        <p class="card__hint">Coeficiente de variação do preço unitário por item (mediana da família).</p>
        <div id="c_cv" class="chart" role="img" aria-label="Dispersão de preço por família"></div>
        <footer class="rodape"><span>CV: quanto menor, mais previsível</span><code>A17</code></footer>
      </div>
      <div class="card">
        <h2>Quanto se desconta do estimado?</h2>
        <p class="card__hint">Desconto mediano praticado sobre o valor estimado da cotação.</p>
        <div id="c_desc" class="chart" role="img" aria-label="Desconto sobre o valor estimado"></div>
        <footer class="rodape"><span>% de desconto sobre o estimado</span><code>A18</code></footer>
      </div>
    </div>
  </section>

  <!-- ======================= LOGÍSTICA ======================= -->
  <section class="painel" id="tab-logistica" role="tabpanel" aria-labelledby="tabbtn-logistica" tabindex="0">
    <div class="grid">
      <div class="card full">
        <h2>Onde entregar?</h2>
        <p class="card__hint">Valor por região de entrega. Regiões dentro do raio de 200 km aparecem destacadas.</p>
        <div id="c_regiao" class="chart tall" role="img" aria-label="Valor por região de entrega"></div>
        <footer class="rodape"><span>R$ milhões · raio a partir de Feira de Santana</span><code>A19</code></footer>
      </div>
      <div class="card">
        <h2>Em quanto tempo o órgão exige a entrega?</h2>
        <p class="card__hint">Prazo mediano e p90 por família (top 12 por volume de compras).</p>
        <div id="c_prazo" class="chart" role="img" aria-label="Prazo de entrega por família"></div>
        <footer class="rodape"><span>Dias corridos</span><code>A20</code></footer>
      </div>
      <div class="card">
        <h2>Onde estão os compradores?</h2>
        <p class="card__hint">Municípios de entrega com maior valor.</p>
        <div id="c_mun" class="chart" role="img" aria-label="Municípios de entrega por valor"></div>
        <footer class="rodape"><span>Top 15 municípios no período</span><code>A21</code></footer>
      </div>
    </div>
  </section>

  <!-- ======================= MÉTODO ======================= -->
  <section class="painel" id="tab-metodo" role="tabpanel" aria-labelledby="tabbtn-metodo" tabindex="0">
    <div class="grid">
      <div class="card full">
        <h2>O que foi filtrado e qual o efeito?</h2>
        <p class="card__hint">Pipeline de exclusão com contagens e reconciliação de valor.</p>
        <div class="rolagem" tabindex="0" role="region" aria-label="Tabela com rolagem horizontal"><table id="t_filtros"><thead></thead><tbody></tbody></table></div>
        <div id="recon" class="marca neutra" style="display:block;margin-top:var(--s-2)"></div>
        <footer class="rodape"><span>Conservação de dados — nada descartado em silêncio</span><code>A22</code></footer>
      </div>
      <div class="card">
        <h2>Quais premissas sustentam os números?</h2>
        <p class="card__hint">Todas as premissas de ASSUMPTIONS.md, com status de validação.</p>
        <ol class="dossie__lista" id="l_assump"></ol>
        <footer class="rodape"><span>Premissas também em ASSUMPTIONS.md</span><code>—</code></footer>
      </div>
      <div class="card">
        <h2>Quais são as limitações?</h2>
        <div id="l_limites" style="font-size:var(--t-sm)"></div>
        <footer class="rodape"><span>—</span><code>—</code></footer>
      </div>
      <div class="card full">
        <h2>Dicionário de indicadores e origem dos dados</h2>
        <div class="rolagem" tabindex="0" role="region" aria-label="Tabela com rolagem horizontal"><table id="t_dict"><thead></thead><tbody></tbody></table></div>
        <footer class="rodape"><span>Id do agregado no rodapé de cada gráfico</span><code>meta.ids</code></footer>
      </div>
    </div>
  </section>

</main>

<div class="sr" id="anuncio" aria-live="polite"></div>
"""
