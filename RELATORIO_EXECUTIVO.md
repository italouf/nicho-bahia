# RELATÓRIO EXECUTIVO — Seleção de nicho em compras públicas da Bahia (2021–2025)

**Para:** sócios da startup · **Base:** SIMPAS/FIPLAN-BA, 560.934 linhas de material (R$ 12,60 bi nominais) ·
**Escopo analítico:** material, não regulado, não pandemia — 352.537 linhas, R$ 10,16 bi (R$ de dez/2025).
**Data:** 12/11/2026 · todos os números são rastreáveis ao agregado indicado no rodapé do painel.

---

## 1. Recomendação

Atacar **três famílias de consumo recorrente**, nesta ordem de prioridade:

| # | Família (catálogo) | Score | R$ 2024–25/ano | Cresc. real | Ticket mediano/AFM | Nº forn. | HHI | % ≤ teto | % no raio |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **89.55 — Café, chá e chocolate** | 75,0 | R$ 4,02 mi | +42,2% a.a. | R$ 2.096 | 204 | 643 | 99,5% | 83,5% |
| 2 | **75.10 — Artigos de escritório** | 72,7 | R$ 3,30 mi | +21,9% a.a. | R$ 312 | 362 | 273 | 100,0% | 78,4% |
| 3 | **85.40 — Artigos de papel para higiene** | 66,7 | R$ 15,10 mi | +8,2% a.a. | R$ 4.464 | 333 | 871 | 97,2% | 87,1% |

Os três têm, em comum, o que a startup precisa: **compra todos os meses** (100% dos 60 meses), **ticket abaixo do
teto de dispensa**, **concorrência fragmentada** (HHI 273–871, top-3 com 22%–45%) e **entrega concentrada no raio
de 200 km**. Nenhum exige atestado técnico ou registro sanitário.

## 2. Por que estes três (e não os dois primeiros do score)

O ranking bruto coloca em 2º e 4º lugar `41.10 Equipamentos para refrigeração` (72,8) e `41.20 Equipamentos de ar
condicionado` (71,1). **Não recomendamos**: são bens duráveis (95%–99% do valor), com instalação e assistência
técnica, venda pontual por órgão e apenas 1,6%–5,2% do valor em dispensa. O score mede demanda, concorrência e
fit de canal; não mede o custo de pós-venda. O painel exibe esse rótulo (`perfil de uso`) ao lado do score
justamente para que essa decisão seja explícita.

O 3º colocado por score entre os consumíveis seria `84.15 Vestuário para fins especiais` (69,4). Ficou como
**alternativa**: 82% do valor está num único item (camisa/fardamento), o HHI é 2.359 e o top-3 concentra 65,5% —
mercado grande, mas com incumbentes fortes e necessidade de grade de tamanhos e estoque.

## 3. Como atacar

**Calendário.** Os três nichos concentram compras em **outubro e novembro** (índice 1,3–1,8× a média), com pico
secundário em junho–julho no papel higiênico (hospitais). Ação comercial deve começar em **agosto**, para estar
credenciado e com preço cadastrado antes da janela.

**Itens-âncora** (menor barreira: 99%–100% classificados como item **comum**, sem especificação fechada):

| Família | Item | UM | Valor no período | Preço mediano | Faixa p25–p75 | Fornecedores |
|---|---|---|---|---|---|---|
| 89.55 | Café | Pc | R$ 12,76 mi | R$ 8,63 | R$ 7,24–10,23 | 174 |
| 75.10 | Pasta | Un | R$ 5,98 mi | R$ 3,60 | R$ 2,03–8,41 | 230 |
| 75.10 | Caneta | Un | R$ 2,08 mi | R$ 0,87 | R$ 0,71–1,44 | 199 |
| 85.40 | Papel higiênico (Pc) | Pc | R$ 76,25 mi | R$ 24,59 | R$ 15,08–51,53 | 304 |

**Órgãos-alvo.** Priorizar quem já compra por dispensa e está no raio:

- **Café:** Diretoria Geral do FESBA/SESAB (R$ 823 mil, 23% em dispensa), IMA/Meio Ambiente (R$ 543 mil, 26%),
  Diretoria Geral da SAEB (R$ 496 mil, 24%).
- **Escritório:** UNEB (R$ 595 mil, **91% em dispensa**), Diretoria Geral da Educação (R$ 395 mil, 52%),
  NRE-26 Salvador (R$ 385 mil, 83%), UEFS (R$ 329 mil).
- **Papel higiênico:** aqui a porta **não** é a dispensa (2%–4%): são os hospitais (Roberto Santos, HGE, Ana Nery,
  Cleriston Andrade) abastecidos por ata de registro de preços. Encaixa na 2ª fase da estratégia (pregão com
  lotes ME/EPP), não no primeiro trimestre.

## 4. Alternativas e o que evitar

| Alternativa | Por que não é a 1ª aposta |
|---|---|
| 41.10 / 41.20 (refrigeração, ar-condicionado) | Bem durável, instalação e pós-venda; dispensa quase nula. |
| 84.15 Vestuário especial | HHI 2.359, top-3 65,5%, 82% do valor em um item. |
| 89.20 Panificação e cereais | R$ 1,2 mi/ano apenas — massa crítica baixa. |
| 81.05 Sacos e bolsas | Bom fit (HHI 862), mas demanda 3,7× menor e crescimento menor. |

**Evitar (regulados):** medicamentos e correlatos (65.02, R$ 1,78 bi), medicamentos para ação judicial (65.01,
R$ 1,72 bi), drogas e reagentes (65.05), OPME (65.50), munições (13.05) e combustíveis (91.30). Exigem registro
ANVISA, atestado de fabricante ou são produto controlado — barreira incompatível com a fase atual. A lista
completa está no painel (aba 0) e o critério é editável em `config.yaml`.

## 5. Riscos e critérios de abandono

**Riscos.** (i) *Concentração de canal*: no papel higiênico 86% do valor não passa por dispensa — depende de ata,
que tem prazo e adesão. (ii) *Preço*: café tem CV mediano de 31% e faixa p25–p75 larga (R$ 7,24–10,23), o que
exige controle de custo de reposição. (iii) *Institucional*: a base cobre o Estado, não os municípios — o mercado
endereçável real é uma fração do total. (iv) *Histórico não é previsão*: o crescimento de 42% a.a. do café é
passado, não garantia.

**Abandonar o nicho se, por 2 trimestres consecutivos:** não houver dispensa eletrônica da família na região;
o ticket mediano por AFM/APS subir acima de R$ 65.492,11 (obrigando pregão e atestados); o HHI ficar acima de
2.500 com top-3 acima de 70%; ou o preço mediano cair abaixo do custo de reposição em 2 medições.

## 6. Rastreabilidade e método

Pipeline reproduzível: `uv run python run.py --stage all` (inventário → perfilamento → tratamento → validação →
análise → score → painel → QA). Decisões de negócio em `config.yaml` (pesos, tetos, listas de exclusão,
convenção de deflação); premissas em `ASSUMPTIONS.md`; perguntas e respostas do gate em `QUESTIONS.md`.
Conservação de dados: 872.257 linhas brutas → 560.934 de material → 352.537 no escopo analítico, com log de
cada passo e reconciliação de valor em **0,000000%**. Todos os gates (G3, G4, QA) estão verdes.
O painel `output/painel_decisao.html` (2,3 MB, offline) abre por `file://`, tem 8 abas e 18 gráficos, e cada
gráfico traz no rodapé o id do agregado que o originou.
