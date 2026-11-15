# SPEC_RETROFIT.md — Retrofit de UI/UX do painel nicho-bahia

Versão 1.0 (aprovado no gate R1 em 2026-11-15) · **delta do SPEC.md §9 — não o substitui**
Base: `logs/retrofit/R0_AUDITORIA.md` + `logs/retrofit/audit.json`
Decisões do gate: **Q11 (a)** destacar os 3 nichos do relatório via `config.yaml → recomendados`;
**Q12** interface ≥ 12px e eixos de gráfico ≥ 11px (exceção declarada).

---

## 1. Problema e objetivo

O painel hoje é um **instrumento de análise** competente (18 gráficos, rastreabilidade, filtros,
zero dependências) mas não é um **instrumento de decisão**. A auditoria R0 mostra por quê, com medida:

- não existe camada executiva: o primeiro elemento da aba Decisão é o gráfico de sensibilidade;
- o cartão de nicho mistura código de catálogo e score no mesmo plano visual (razão tipográfica 1,93);
- a incerteza existe no dado (A13, 14 cenários) mas não aparece no cartão;
- a tabela exige rolar 155 linhas sem busca;
- em 360px o layout transborda (1.632 elementos fora da tela).

**Objetivo:** um sócio leigo em dados deve, em **≤ 5 minutos**, (a) entender os 3 nichos
recomendados, (b) entender por quê e com quais riscos, (c) saber o próximo passo concreto.

**Não-objetivo:** mudar qualquer número. O retrofit é de apresentação e interação (invariante I1).

## 2. Personas

| id | Persona | Contexto | Precisa em | Sucesso é |
|---|---|---|---|---|
| P1 | **Sócio-decisor** | celular, entre reuniões, não lê gráfico | 5 min | sair sabendo onde atacar e por quê |
| P2 | **Sócio-operador** | desktop, vai montar a proposta | 20 min | órgãos, calendário, faixa de preço, prazo |
| P3 | **Analista/auditor** | desktop, confere método | 10 min | rastrear cada número até o agregado |

P1 é o público do **nível 1** da interface. P2 do **nível 2** (dossiê). P3 do **nível 3** (método).

## 3. Jornada (decidir → comparar → aprofundar → agir)

| Etapa | Pergunta do sócio | Onde | Tempo-alvo | Entrega |
|---|---|---|---|---|
| **Decidir** | "onde ataco?" | aba 0, acima da dobra | 30 s | veredito + 3 nichos com score, faixa e 2 riscos |
| **Comparar** | "por que esse e não aquele?" | aba 0, tabela | 2 min | tabela com busca/ordenação + faixa de rank |
| **Aprofundar** | "como é esse mercado?" | aba 1 Dossiê | 2 min | 7 blocos do nicho numa página |
| **Agir** | "o que faço segunda-feira?" | aba 1, bloco de ação | 30 s | próximos passos datados + export |

## 4. Princípios de design (valem como critério de aceitação)

1. **Decisão antes de dado.** Nenhuma tela abre com gráfico; abre com a conclusão.
2. **Incerteza é informação.** Todo score aparece com faixa de rank (14 cenários) e flags.
3. **Um número, um dono.** O id do agregado no rodapé é mantido em 100% dos gráficos.
4. **Filtra ou declara.** Regra do SPEC §9.1 preservada e reforçada por chips visíveis.
5. **Mobile não é desktop encolhido.** Em ≤ 600px a tabela vira cartões e os gráficos simplificam.
6. **Nada de falsa precisão.** Score com 1 decimal; percentuais arredondados na leitura rápida.

## 5. Arquitetura de informação proposta (9 abas)

| # | Aba | Natureza | Mudança |
|---|---|---|---|
| 0 | **Decisão** | executiva | **reestruturada** (veredito + 3 cards + tabela + evitar + como ler) |
| 1 | **Dossiê** | operacional | **nova** (consolida A05/A06/A15/A16/A19/A20 + critérios de abandono) |
| 2–8 | Mercado, Sazonalidade, Compradores, Concorrência, Preços, Logística, Método | analítica | preservadas, com legenda/`13px` e títulos inalterados |

Motivo de inserir o Dossiê como aba 1: a jornada "aprofundar" precisa de deep-link e de impressão;
modal não é imprimível nem testável por URL. As abas analíticas continuam existindo para P3.

## 6. Histórias priorizadas (MoSCoW) e critérios de aceitação

> Formato AR: **DADO** (estado) **QUANDO** (ação) **ENTÃO** (resultado observável).
> Todas verificáveis por Playwright/screenshot, sem julgamento humano.

### US-01 · Must · Camada de decisão em 5 minutos
Como sócio sem tempo, quero abrir o painel e sair sabendo onde atacar, sem interpretar 18 gráficos.

- **AR-01** DADO o painel em 1440×900 sem filtro, QUANDO a aba Decisão renderiza, ENTÃO existe
  `[data-veredito]` **antes de qualquer `<canvas>` na ordem do DOM**, contendo: frase de recomendação,
  os 3 nichos e o tempo estimado de leitura ("≈ 5 min").
- **AR-02** DADO qualquer viewport, QUANDO conto os cards de destaque, ENTÃO são exatamente **3**
  (os recomendados) e cada um tem ≤ 200 palavras.

### US-02 · Must · Hierarquia código × score
Como leitor, quero que o código da família não pareça a nota.

- **AR-03** DADO um card, QUANDO inspeciono, ENTÃO `[data-codigo]` tem font-size ≤ 12px e opacidade
  menor que o nome; `[data-score]` tem font-size ≥ 2,0× o font-size do nome.
- **AR-04** DADO o card, QUANDO leio, ENTÃO o número do score tem o rótulo textual "score" adjacente
  e o código tem o rótulo "família" (nunca `89.55 · CAFE` antes de `75.0` sem rótulo).

### US-03 · Must · Incerteza visível nos cards
Como decisor, quero saber se o 1º lugar é estável.

- **AR-05** DADO um card, QUANDO inspeciono, ENTÃO existe `[data-faixa-rank]` com o texto
  "posição N–M em 14 cenários" e `[data-estabilidade]` com "X% no top-10"; o score tem 1 decimal.
  *Nota de execução (Δ):* os 14 cenários do A13 ranqueiam as **348** famílias do escopo analítico;
  o ranking da tabela mostra as **155** elegíveis. O card declara a faixa na base dos 348 e a aba
  Método explica a diferença. Não se alterou o agregado (invariante I1).
- **AR-06** DADO família com penalidade (pandemia > 30% ou queda nos 2 últimos anos), QUANDO aparece
  em card ou tabela, ENTÃO há `[data-flag]` com texto do motivo **e** ícone (cor não é canal único).

### US-04 · Must · Tese e riscos em 1 frase
- **AR-07** DADO um card, QUANDO leio, ENTÃO a tese tem ≤ 140 caracteres e inicia por verbo;
  e há exatamente 2 riscos, derivados de campos já existentes (`perfil_uso`, `dependencia_pandemia`,
  `hhi`, `share_top3`, `penalidades`) — **nenhuma métrica nova é calculada**.

### US-05 · Must · Dossiê do nicho (jornada "agir")
- **AR-08** DADO um card, QUANDO clico "Abrir dossiê", ENTÃO a aba Dossiê abre nesse nicho, a URL
  recebe `#dossie=<código>` e o dossiê contém 7 seções com id de agregado: calendário (A05),
  órgãos (A06), itens-âncora (A16), faixa de preço (A16), logística (A19/A20), incumbentes (A15),
  critérios de abandono (SPEC §1).
- **AR-09** DADO `#dossie=89.55` na URL, QUANDO recarrego, ENTÃO o dossiê abre no mesmo nicho.

### US-06 · Must · Tabela utilizável
- **AR-10** DADO a tabela, QUANDO digito "caf" em `#busca`, ENTÃO restam só linhas com "caf" no
  nome ou código e o contador mostra "N de 155".
- **AR-11** DADO busca/filtro ativos, QUANDO clico "Exportar CSV", ENTÃO o arquivo contém **todas**
  as linhas do recorte (não só as visíveis), com os mesmos valores de `nicho_score.csv` (A5).
- **AR-12** DADO a tabela em 1440px, QUANDO rolo o corpo, ENTÃO o `thead` permanece visível e o
  container rolável é focável por teclado (corrige `scrollable-region-focusable`).

### US-07 · Must · Filtros visíveis e compartilháveis
- **AR-13** DADO um filtro aplicado, QUANDO olho o topo, ENTÃO há chip removível `[data-chip]` por
  filtro ativo e um "limpar tudo"; o X remove só aquele filtro.
- **AR-14** DADO filtros ativos, QUANDO recarrego a URL, ENTÃO o estado é reproduzido
  (`?ano=&familia=...`); secretaria e região continuam exclusivas **e a UI explica por texto**.

### US-08 · Must · Responsivo 360/768/1440
- **AR-15** DADO 360×800, QUANDO carrego, ENTÃO `scrollWidth <= clientWidth`, 0 elementos fora da
  tela e todo `select`/`button` com altura ≥ 44px.
- **AR-16** DADO 360px, QUANDO abro a aba Decisão, ENTÃO a tabela é apresentada como cartões
  (sem rolagem horizontal) e os gráficos usam altura reduzida.

### US-09 · Must · Acessibilidade WCAG 2.1 AA
- **AR-17** DADO os 3 viewports, QUANDO rodo axe-core (wcag2a/2aa/21a/21aa), ENTÃO
  **0 critical e 0 serious**.
- **AR-18** DADO navegação por teclado, QUANDO tabulo a partir do topo, ENTÃO todos os controles são
  alcançáveis, com foco visível (contraste ≥ 3:1) e ordem de leitura preservada.

### US-10 · Must · Performance
- **AR-19** DADO 1440px, QUANDO carrego, ENTÃO FCP ≤ 2 s; DADO mobile emulado (CPU 4×), FCP ≤ 4 s.
- **AR-20** DADO troca de aba e aplicação de filtro, QUANDO mensuro handler + layout, ENTÃO p95
  ≤ 200 ms nos 3 viewports (baseline atual: 418 ms no tablet).

### US-11 · Should · Legibilidade e design tokens
- **AR-21** DADO qualquer viewport, QUANDO conto textos de **interface** < 12px, ENTÃO 0
  (rótulos de eixo de gráfico: ≥ 11px — exceção declarada em ASSUMPTIONS).
- **AR-22** DADO o CSS, QUANDO conto valores distintos, ENTÃO ≤ 4 raios e ≤ 6 espaçamentos,
  todos vindos de custom properties.

### US-12 · Should · Export executivo (impressão)
- **AR-23** DADO o dossiê aberto, QUANDO imprimo (`@media print`), ENTÃO o PDF tem 1–2 páginas com
  cabeçalho, nicho, tese, riscos e 3 próximos passos, sem controles de filtro.

### US-13 · Could · Estados vazio/carregando/erro
- **AR-24** DADO um recorte que zera um gráfico, ENTÃO há estado vazio padronizado com explicação e
  ação "limpar filtros", no lugar de canvas em branco.

### US-14 · Must (invariante) · Nenhum número muda
- **AR-25** DADO o painel antes e depois do retrofit, QUANDO comparo as séries de dados dos 18
  gráficos e o CSV exportado, ENTÃO são **idênticos** (mesmos valores, mesma ordem); só o layout muda.

### Fora de escopo (Won't)
Reescrever em React/Vue; backend; novas fontes de dados; alterar pesos, limiares ou score;
redesenhar marca; internacionalização.

## 7. Métricas de sucesso (baseline R0 → meta R4)

| Métrica | Baseline | Meta |
|---|---|---|
| Overflow horizontal em 360px | sim (1.632 fora da tela) | **não (0)** |
| Textos de interface < 12px | 389 | **0** |
| Alvos de toque < 44px | 29 | **0** |
| Violações axe critical+serious | 1 | **0** |
| Troca de aba p95 | 418 ms (tablet) | **≤ 200 ms** |
| Cliques até o dossiê | não existe | **1** |
| Busca na tabela | ausente | **presente** |
| Estado na URL | ausente | **reprodutível** |
| Linhas no DOM (tabela) | 155 | **≤ 40** (virtualização) |
| CSS de impressão | ausente | **1–2 páginas** |
| Paridade de números (AR-25) | — | **100% idêntica** |

## 8. Riscos

| Risco | Mitigação |
|---|---|
| Retrofit mexer em número sem querer | AR-25 compara séries e CSV antes/depois; I1 no checklist |
| Virtualizar a tabela quebrar o export CSV | export lê o array completo do recorte, não o DOM (AR-11) |
| Inserir aba 1 quebrar testes por índice | testes passam a clicar por rótulo (`get_by_role`), não por índice |
| Responsivo "resolve" escondendo informação | em 360px a tabela vira cartões com os mesmos campos essenciais |
| Dossiê virar tela nova de dados | só consome agregados existentes; sem cálculo novo no cliente |
| Ganhar acessibilidade perdendo densidade | contraste e 12px aplicados a texto de leitura, não a eixos |

## 9. Rastreabilidade (matriz completa vai no PLAN_RETROFIT)

| US | AR | Arquivo afetado | Teste |
|---|---|---|---|
| US-01 | AR-01, AR-02 | `panel_html.py` (BODY aba 0, JS `renderVeredito`) | `tests/retrofit/test_decisao.py` |
| US-02 | AR-03, AR-04 | `panel_html.py` (CSS+JS cards) | idem |
| US-03 | AR-05, AR-06 | JS cards | idem |
| US-04 | AR-07 | JS `tese()` | idem |
| US-05 | AR-08, AR-09 | BODY nova aba + JS `renderDossie` | `test_dossie.py` |
| US-06 | AR-10..12 | JS tabela | `test_tabela.py` |
| US-07 | AR-13, AR-14 | JS filtros/URL | `test_filtros.py` |
| US-08 | AR-15, AR-16 | CSS responsivo | `test_responsivo.py` |
| US-09 | AR-17, AR-18 | CSS/HTML | `test_a11y.py` (axe) |
| US-10 | AR-19, AR-20 | JS lazy/render | `test_perf.py` |
| US-11 | AR-21, AR-22 | CSS tokens | `test_tipografia.py` |
| US-12 | AR-23 | CSS `@media print` | `test_print.py` |
| US-13 | AR-24 | JS estados | `test_estados.py` |
| US-14 | AR-25 | — | `test_paridade.py` |

## 10. O que este spec NÃO decide

Não decide qual nicho recomendar (isso vem do score, congelado); não muda pesos; não altera o
`config.yaml` de negócio; não define identidade visual nova além de tokens e hierarquia.
