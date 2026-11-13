# ASSUMPTIONS.md — premissas e hipóteses

> Toda premissa vive aqui e é exibida na aba **Método** do painel.
> Status: **VALIDADA** (testada contra os dados em F1) · **PREMISSA** (aceita sem teste conclusivo) ·
> **A VALIDAR** (depende de decisão no gate ou de fonte externa).

## A. Eixo temporal e grão

| id | Premissa | Status | Evidência |
|---|---|---|---|
| A1 | O eixo temporal é `DATA GERAÇÃO da AFM/APS`; `ANO/MÊS GERAÇÃO` é fallback redundante | **VALIDADA** | 872.253 de 872.257 linhas com data; 0 divergências entre ano(data) e ANO GERAÇÃO; 0 de mês; faixa 2021-01-04 a 2025-12-30 (`profile.json:temporal`) |
| A2 | O grão da base é **1 linha = 1 item de uma AFM/APS** | **VALIDADA** | (afm_aps, codigo, item) tem 99,9439% de unicidade; não há repetição entre arquivos |
| A3 | Cada arquivo cobre exatamente o seu ano, sem sobreposição | **VALIDADA** | matriz arquivo × ano é diagonal; 0 chaves em mais de um arquivo |
| A4 | `Assinatura da AFM/APS` não serve como eixo temporal | **VALIDADA** | 44,19% nula; 133 datas anteriores a 2019; 281 anteriores à geração |
| A5 | 2021–2022 contêm distorção pandêmica e devem ser segmentados, não misturados | **PREMISSA** | flags COVID concentradas em 2021 (4.551 linhas, R$ 1,11 bi) |

## B. Escopo: o que é "material"

| id | Premissa | Status | Evidência |
|---|---|---|---|
| A6 | O escopo padrão da análise é `TIPO DO ITEM = 'Material'` | **VALIDADA** | equivale a `TIPO FORNECIMENTO = 'AFM'` em 99,999% das linhas; 560.934 linhas; R$ 12,60 bi em 5 anos |
| A7 | `CLASSIFICAÇÃO FAMÍLIA` não discrimina material de serviço | **VALIDADA** | 97,2% das linhas são `Outros`; as 3 categorias não separam AFM de APS |
| A8 | `VALOR TOTAL` é confiável para materiais | **VALIDADA** | para material, `QTD × UNIT` = `VALOR TOTAL` em 100% das linhas (0 incoerentes em 560.934) |
| A9 | A incoerência `QTD × UNIT ≠ VALOR TOTAL` em serviços decorre de contrato plurimensal | **VALIDADA** | razão concentra-se em 12 e 60; serviços são 100% da incoerência global |
| A10 | `VALOR ESTIMADO` é **unitário** (referência da cotação), não total | **VALIDADA** | igual ao unitário em 85,94%; ao total em 5,29%; mediana da razão unitário/estimado = 1,00 |
| A11 | Serviços (APS) estão fora do escopo deste projeto | **PREMISSA** | decisão de negócio (startup de materiais); 311.318 linhas / R$ 74,77 bi ficam de fora e isso é declarado |

## C. Canal de compra (dispensa / PCE)

| id | Premissa | Status | Evidência |
|---|---|---|---|
| A12 | `PCE - Pedido de Cotação Eletrônica` preenchido é o marcador de **cotação eletrônica** | **VALIDADA** | PCE aparece em 100,0% das linhas de `E - Dispensa Eletrônica` e em 0,0% de todas as outras formas |
| A13 | `FORMA DE CONTRATAÇÃO` mistura modalidade (`E -`, `D -`, `C -`...) com procedimento (`Registro de Preços`) | **VALIDADA** | 23 rótulos distintos; `Registro de Preços` coexiste com todos os anos e representa compra via ata |
| A14 | Canal dispensa = `E - Dispensa Eletrônica` + `D - Dispensa Tradicional`; "dispensa eletrônica" = `E` + PCE | **PREMISSA** | decisão de modelagem; 150.453 linhas de material |
| A15 | O teto por AFM/APS é **proxy** do teto legal (que é por contratação/objeto de mesma natureza por UG/ano) | **PREMISSA** | limitação declarada; não é possível reconstruir o agrupamento legal com esta base |
| A16 | O teto de referência é R$ 65.492,11 (Decreto 12.807/2025, vigente em 2026), aplicado em termos reais a todos os anos | **A VALIDAR** | ver Q2 no Gate G1; o teto é reajustado por decreto a cada ano e era menor antes |

## D. Fornecedores e concorrência

| id | Premissa | Status | Evidência |
|---|---|---|---|
| A17 | `CATEGORIA` é o porte do fornecedor, não o tipo de objeto | **VALIDADA** | 7 valores: NO (7.765 CNPJs), EPP (2.825), ME (4.001), MEI (845), AF (29), ES (75), EC (16) |
| A18 | `NO` = não optante do Simples (empresa de médio/grande porte) | **A VALIDAR** | inferência pelo volume de valor (R$ 78,7 bi em 316 mil linhas); ver Q6 no Gate G1 |
| A19 | Fornecedores com identificador de 11 dígitos são **pessoa física (CPF)** e saem da análise de concorrência | **VALIDADA** | 4.665 linhas / 2.618 fornecedores; 47 fornecedores têm identificador de 10 dígitos (inválido) |
| A20 | "Novo entrante" = primeira aparição do CNPJ na base | **PREMISSA** | **truncamento à esquerda**: quem já vendia antes de 2021 aparece como "entrante" em 2021; por isso entrantes só serão contados a partir de 2022 |
| A21 | HHI calculado por participação no **valor** transacionado, por família, em base anual | **PREMISSA** | decisão de método; alternativa seria participação por número de linhas |

## E. Preço e deflação

| id | Premissa | Status | Evidência |
|---|---|---|---|
| A22 | Deflacionamento para R$ de dez/2025 por IPCA **anual** | **PREMISSA** | 2021: 10,06%; 2022: 5,79%; 2023: 4,62%; 2024: 4,83%; 2025: 4,26%. Limitação: granularidade anual, não mensal |
| A23 | A análise de preço usa o par `(Nome Básico, UM)` como item padronizado | **PREMISSA** | o catálogo tem 52.876 códigos e 6.360 nomes básicos; `(nome_basico, um)` reduz ruído de unidade |
| A24 | Outliers de preço são **mantidos**; winsorização p1/p99 só nas estatísticas de preço | **PREMISSA** | há valores unitários até R$ 1,42 bi; excluir perderia compras legítimas de grande porte |
| A25 | `VALOR TOTAL` zero ou negativo é mantido e sinalizado, não descartado | **PREMISSA** | 18 linhas com total zero; 2 com unitário negativo (material) |

## F. Logística e regiões

| id | Premissa | Status | Evidência |
|---|---|---|---|
| A26 | A entrega é estadual: 99,99% das linhas têm UF de entrega na BA | **VALIDADA** | BA 871.682 + `ba` 476 + DF 95 (95 linhas, provável erro de cadastro) |
| A27 | O raio de ~200 km a partir de Feira de Santana cobre RMS, Feira de Santana e Alagoinhas/Serrinha | **A VALIDAR** | ver Q4 no Gate G1 |
| A28 | `Regiao_Principal_Município` e `Região do Local de Entrega` têm rótulos sujos e serão normalizados | **VALIDADA** | há rótulos truncados (`Região SAJesus, Amargosa,Valença,SAmaro`) e inativos (`Região Merenda Escolar (Inativo)`) |
| A29 | `PRAZO DE ENTREGA` é numérico em dias, com cauda inválida | **VALIDADA** | 100% numérico; mediana 15–30 dias; 4.858 linhas acima de 365 dias, máximo 36.000 |

## G. Método e comunicação

| id | Premissa | Status | Evidência |
|---|---|---|---|
| A30 | Toda métrica do painel carrega o id do agregado que a originou | **PREMISSA** | requisito do projeto (anti-alucinação) |
| A31 | Histórico não é previsão: nenhuma projeção será apresentada como expectativa | **PREMISSA** | requisito do projeto |
| A32 | A base é **estadual** (Poder Executivo da BA), sem compras municipais | **PREMISSA** | nota de rodapé da própria planilha de 2025: "órgãos e entidades do Poder Executivo do Estado da Bahia" |
| A33 | Não há dados de pagamento/adimplência | **PREMISSA** | limitação da base, declarada no painel |
