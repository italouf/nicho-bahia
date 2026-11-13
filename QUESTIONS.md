# QUESTIONS.md — ambiguidades e decisões pendentes

> Cada pergunta tem uma **recomendação** e o **impacto** de escolher outra opção.
> As marcadas com **[G1]** bloqueiam a especificação (F2) e foram levadas ao gate.

## Q1 [G1] — O escopo é só material, medido por `VALOR TOTAL` da linha?

- **Contexto**: `TIPO DO ITEM = 'Material'` = 560.934 linhas e R$ 12,60 bi (2021–2025). Serviços (APS) são
  311.318 linhas e R$ 74,77 bi, mas neles `VALOR TOTAL` é o valor do contrato plurimensal — a linha não
  é comparável entre órgãos.
- **Recomendação**: sim. Escopo = material; demanda medida por `VALOR TOTAL` da linha (validado: é
  exatamente `QTD × UNIT` em 100% das linhas de material).
- **Impacto de mudar**: incluir serviços contamina ticket, preço unitário e concorrência (fornecedores
  de serviço não são comparáveis a fornecedores de material).

## Q2 [G1] — Qual teto de dispensa usar na métrica "% de compras ≤ teto"?

- **Contexto**: o teto de 2026 é R$ 65.492,11 (Decreto 12.807/2025, art. 75, II da Lei 14.133/2021 —
  confirmado em fonte oficial). Esse valor é **reajustado anualmente por decreto**, logo nos anos
  anteriores ele era menor. Usar um teto único superestima o "fit dispensa" dos anos antigos.
- **Recomendação**: (a) usar **R$ 65.492,11 em termos reais para todos os anos** como métrica principal
  (comparável e orientada ao futuro, que é o que a startup enfrentará) **e** (b) publicar, como métrica
  secundária, o % abaixo do teto histórico de cada ano — a série histórica será levantada em F2 a partir
  dos decretos anuais, se você quiser essa métrica.
- **Impacto de mudar**: com teto histórico, o fit dispensa de 2021–2023 cai e famílias com ticket entre
  o teto antigo e R$ 65 mil mudam de posição no ranking.

## Q3 [G1] — O que entra na lista EVITAR por barreira regulatória?

- **Contexto**: a lista é editável em `config.yaml`. Candidatos óbvios: medicamentos (65.01, 65.02),
  drogas/reagentes (65.05), munições/explosivos (13.05), combustíveis, perecíveis e alimentação.
  **Dúvida real**: materiais médico-hospitalares (65.15 instrumentos e suprimentos, 65.30 mobiliário
  hospitalar, 65.32 vestuário hospitalar, 65.50 OPME) são **regulados** (ANVISA/atestados) ou são
  **oportunidade** (são materiais de uso recorrente, ticket médio, alta fragmentação)?
- **Recomendação**: EVITAR apenas o que exige registro sanitário/anvisa ou atestado técnico do
  fabricante: medicamentos (65.01, 65.02, 65.05), OPME (65.50) e munições (13.05). **Manter como
  oportunidade** 65.15, 65.30, 65.32 e 66.40, sinalizando a barreira como risco (não como exclusão).
- **Impacto de mudar**: 65.15 (R$ 1,35 bi, 684 CNPJs, ticket mediano R$ 2.700) é a 4ª maior família de
  material; excluí-la remove um dos nichos mais promissores.

## Q4 [G1] — Quais regiões de entrega compõem o "raio de ~200 km"?

- **Contexto**: a base tem 18 rótulos de região, alguns truncados ou inativos. Distâncias rodoviárias
  aproximadas de Feira de Santana: RMS ~110 km, Alagoinhas ~85 km, Serrinha ~160 km,
  Santo Antônio de Jesus ~130 km, Valença ~200 km, Ilhéus ~430 km, Vitória da Conquista ~500 km.
- **Recomendação**: raio = `Região Metropolitana de Salvador` + `Região Feira de Santana` +
  `Região Alagoinhas e Serrinha` + `Região SAJesus, Amargosa, Valença, SAmaro`. As demais regiões entram
  como "expansão futura".
- **Impacto de mudar**: o raio define o score de logística (peso 10) e a lista de órgãos-alvo.

## Q5 [G1] — Escopo de análise: todas as 726 famílias ou só as com massa crítica?

- **Contexto**: 77 famílias têm menos de 10 linhas no período — estatística inútil e ruído no ranking.
- **Recomendação**: ranquear apenas famílias com **≥ 30 AFM/APS e ≥ R$ 1 milhão** no período
  (aprox. 190 famílias), declarando as excluídas e o motivo no painel. As demais continuam no drill-down.
- **Impacto de mudar**: incluir todas diluirá o top-10 com nichos de 5 compras.

## Q6 [G1] — `NO` na coluna `CATEGORIA` significa "não optante do Simples" (empresa média/grande)?

- **Contexto**: 7 valores: `NO` (316.347 linhas, 7.765 CNPJs, R$ 78,7 bi), `EPP` (299.522), `ME` (238.048),
  `MEI` (16.331), `AF` (1.596), `ES` (340), `EC` (68). `AF`, `ES` e `EC` são siglas não documentadas.
- **Recomendação**: tratar `NO` = não optante do Simples; `AF`/`ES`/`EC` = "outros/desconhecido" (0,2% das
  linhas) e não usar no cálculo de share ME/EPP. Se você souber o significado, corrija em `config.yaml`.
- **Impacto de mudar**: afeta o share ME/EPP na análise de concorrência (Q3 do projeto).

## Q7 — Como tratar "novos entrantes" com base começando em 2021?

- **Contexto**: um fornecedor cuja primeira compra registrada é 2021 pode ser antigo. Chamá-lo de
  "entrante" é erro de truncamento à esquerda.
- **Recomendação**: contar entrantes apenas de **2022 em diante**, e rotular como "primeira aparição na
  base", não "empresa nova".
- **Impacto**: sem isso, 2021 apareceria artificialmente como o ano de maior entrada de fornecedores.

## Q8 — Pessoa física (CPF) entra na análise de concorrência?

- **Contexto**: 2.618 fornecedores são pessoa física (4.665 linhas), sobretudo em serviços.
- **Recomendação**: excluir PF da análise de concorrência de materiais (não são concorrentes relevantes
  para uma startup B2G) e manter MEI.
- **Impacto**: pequeno (0,5% das linhas); afeta apenas a contagem de fornecedores.

## Q9 — O que fazer com `Nº PROCESSO`, `Nº CONTRATO`, `SRD`, `LID` e os 3 links do PNCP?

- **Contexto**: as 3 colunas de PNCP são links (enriquecimento futuro); `SRD`/`LID` são códigos internos
  FIPLAN de documento (353 mil valores distintos) e não classificam nada; `Nº CONTRATO` cobre 34,7% das
  linhas.
- **Recomendação**: manter no parquet tratado como texto, exibir `Nº CONTRATO` no drill-down e **não**
  usar como filtro. Links do PNCP ficam reservados para uma fase de enriquecimento.
- **Impacto**: nenhum no ranking; melhora a rastreabilidade.

## Q10 — A base é só do Poder Executivo estadual?

- **Contexto**: a própria planilha de 2025 traz a nota "Critérios: Registro das compras e contratações
  realizado pelos órgãos e entidades do Poder Executivo do Estado da Bahia no ano de 2025". Mas há
  41 secretarias/órgãos, incluindo Assembleia Legislativa e Tribunal de Contas — que não são Executivo.
- **Recomendação**: declarar a limitação como "base estadual (SIMPAS/FIPLAN), cobertura declarada do
  Poder Executivo, com presença de órgãos de outros poderes"; **não** filtrar por poder.
- **Impacto**: se filtrarmos só Executivo, perdemos ~? das linhas — a decidir em F2 se você quiser.
