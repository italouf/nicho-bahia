# DATA_PROFILE.md — perfilamento da base SIMPAS (BA, 2021–2025)

Gerado por `run.py --stage profile` em 2026-11-12T17:46:22.724580+00:00.
Fonte: `data/_meta/staging/raw_<ano>.parquet` (camada de staging, 1 linha = 1 linha da planilha).

## 0. Achados críticos (leia primeiro)

1. **A base tem 4 linhas que não são dados** (rodapé de observações no fim da planilha de 2025, arquivo `SIMPAS_VOLUME_DE_COMPRAS_ANO_2025 1 (1).xlsx`, linhas 198083–198086). Elas não têm AFM/APS nem valor e serão removidas na camada tratada, com log de conservação.
2. **No escopo de MATERIAL, `VALOR TOTAL` é exatamente `QTD × VALOR UNITÁRIO`**: 0 linhas incoerentes em 560.934 (Σ TOTAL = R$ 12.597.609.650,96 e Σ QTD×UNIT = R$ 12.597.609.774,41, idênticas). Toda a incoerência global vem de **serviços (APS)**, onde 34.449 de 311.317 linhas divergem porque o VALOR TOTAL é o valor do contrato inteiro (12 ou 60 meses) e o VALOR UNITÁRIO é o valor mensal, com QTD CONTRATADA = 1. **Consequência: para materiais, VALOR TOTAL é confiável; a análise de serviço não é o escopo deste projeto.**
3. **`VALOR ESTIMADO` é unitário, não total**: igual ao VALOR UNITÁRIO em 85,94% dos casos e ao VALOR TOTAL em apenas 5,29%. Razão UNITÁRIO/ESTIMADO: p50 = 1. A métrica 'desconto vs. estimado' será calculada **por unidade**, não por linha.
4. **O eixo temporal é sólido**: `DATA GERAÇÃO da AFM/APS` cobre 872.253 linhas entre 2021-01-04 e 2025-12-30, sem divergência com ANO/MÊS GERAÇÃO (0 divergências de ano, 0 de mês). `Assinatura da AFM/APS` é suja e não deve ser usada como eixo (44,185% das linhas sem assinatura; datas fora da faixa 2019–2026 e anteriores à geração).
5. **Não há sobreposição entre os 5 arquivos** (0 chaves repetidas entre arquivos), logo não há dupla contagem entre anos. A chave candidata com melhor unicidade é `afm_aps + codigo + item + valor_unitario` com 99,9443% (486 excedentes). Os excedentes têm valores diferentes entre si (são linhas distintas da mesma AFM), então **não serão descartados**: a chave de trabalho é a linha (`_src_file` + `_src_row`).
6. **4.665 linhas (2.618 fornecedores) têm identificador de 11 dígitos — CPF, ou seja, pessoa física**, e 47 fornecedores têm identificador de 10 dígitos (formato inválido). Para concorrência de materiais, o universo de referência é o de pessoa jurídica (CNPJ de 14 dígitos).
7. **`FORMA DE CONTRATAÇÃO` mistura dois vocabulários**: rótulos por modalidade (`E - Dispensa Eletrônica`, `D - Dispensa Tradicional`, `C - Licitação`...) e o rótulo `Registro de Preços`, que indica compra **via ata de RP** (procedimento, não modalidade). `PCE` só aparece em `E - Dispensa Eletrônica` (100,0% dos casos), confirmando ser o marcador da cotação eletrônica. O canal de entrada da startup será modelado com os dois campos.
8. **Ticket e teto da dispensa**: no material, 406.634 de 422.041 AFM/APS (96,35%) têm valor total ≤ R$ 65.492,11 (mediana por AFM/APS = R$ 1.330,20). Ou seja, o teto legal da dispensa eletrônica cobre quase todo o universo de materiais — mas atenção: o teto é por contratação/objeto de mesma natureza por UG/ano, então o valor por AFM/APS é apenas **proxy**.
9. **`CLASSIFICAÇÃO FAMÍLIA` não separa material de serviço** (97,2% das linhas são `Outros`). O discriminador correto é `TIPO DO ITEM` (Material/Serviço), coerente com `TIPO FORNECIMENTO` (AFM/APS).
10. **A hierarquia de catálogo não é árvore estrita**: 1.242 nomes básicos aparecem sob mais de uma família. Chaves de análise serão `(familia_catalogo, nome_basico)`.

## 1. Visão geral

- Linhas: **872.257**
- CNPJs distintos: **15.216** | AFM/APS distintas: **449.967**
- Famílias de catálogo: **726** | Nomes básicos: **6.360** | Códigos: **52.876** | Itens (descrições): **52.600**
- Secretarias: **41** | Unidades: **1.917** | Municípios de entrega: **418**
- Σ VALOR TOTAL: **R$ 87.368.466.271** | Σ VALOR ESTIMADO: **R$ 85.285.509.979,35**

### Por arquivo de origem

| Arquivo | Linhas | AFM/APS | CNPJs | Σ VALOR TOTAL | TOTAL nulo | Data nula |
|---|---|---|---|---|---|---|
| 2021 | 90.058 | 55.311 | 4.463 | 11.597.672.979,19 | 0 | 0 |
| 2022 | 177.068 | 86.094 | 6.095 | 19.081.152.418,79 | 0 | 0 |
| 2023 | 217.918 | 100.695 | 6.897 | 12.154.881.363,15 | 0 | 0 |
| 2024 | 189.127 | 102.472 | 6.845 | 24.557.777.346,53 | 0 | 0 |
| 2025 | 198.086 | 105.395 | 7.361 | 19.976.982.163,34 | 4 | 4 |

## 2. Cobertura temporal

| Ano do dado | Linhas | AFM/APS | Σ VALOR TOTAL |
|---|---|---|---|
| 2021 | 90.058 | 55.311 | 11.597.672.979,19 |
| 2022 | 177.068 | 86.094 | 19.081.152.418,79 |
| 2023 | 217.918 | 100.695 | 12.154.881.363,15 |
| 2024 | 189.127 | 102.472 | 24.557.777.346,53 |
| 2025 | 198.082 | 105.395 | 19.976.982.163,34 |
| — | 4 | 0 | — |

**Matriz arquivo × ano do dado** (revela sobreposição entre arquivos):

| Arquivo | Ano do dado | Linhas |
|---|---|---|
| 2021 | 2021 | 90.058 |
| 2022 | 2022 | 177.068 |
| 2023 | 2023 | 217.918 |
| 2024 | 2024 | 189.127 |
| 2025 | 2025 | 198.082 |
| 2025 | — | 4 |

- Linhas com data e ano preenchidos: **872.253**; ano divergente da data: **0**; mês divergente: **0**
- Linhas sem data de geração: **4** (destas, 0 têm ANO preenchido)
- Faixa de datas de geração: **2021-01-04 00:00:00** a **2025-12-30 00:00:00**; assinatura: 1900-01-01 00:00:00 a 2026-05-29 00:00:00; fim de contrato: 1900-01-08 00:00:00 a 2039-09-10 00:00:00

## 3. Teste de chave candidata

Linhas: **872.257**

| Chave candidata | Chaves distintas | Excedente | Unicidade % | Duplicatas % |
|---|---|---|---|---|
| afm_aps + codigo + item | 871.768 | 489 | 99,94 | 0,06 |
| afm_aps + codigo + item + data_geracao | 871.768 | 489 | 99,94 | 0,06 |
| afm_aps + codigo + item + valor_unitario | 871.771 | 486 | 99,94 | 0,06 |
| afm_aps + afm_aps_tipo_item + codigo + item | 871.768 | 489 | 99,94 | 0,06 |

- Chaves (afm_aps, codigo, item) presentes em mais de um arquivo: **0** de 871.768.

## 4. Coerência de valores

- QTD × UNIT vs TOTAL: **872.251** linhas completas; **34.449** incoerentes (3.9494%), desvio absoluto somado R$ 60.756.146.299,02.
- Nulos: TOTAL 4, UNIT 6, QTD 4, ESTIMADO 4.
- Negativos: TOTAL 0, UNIT 2, QTD 0. TOTAL zero: 18.
- **VALOR ESTIMADO**: igual ao UNITÁRIO em 85.938% e ao TOTAL em 5.288% dos casos → tratar como **valor unitário de referência**.
- Razão UNITÁRIO/ESTIMADO: p10=0.8935, p50=1.0, p90=1.0.

## 5. Escopo: material vs serviço, pandemia e canal

**TIPO FORNECIMENTO × TIPO DO ITEM**

| TIPO FORNECIMENTO | TIPO DO ITEM | Linhas | Σ VALOR TOTAL |
|---|---|---|---|
| AFM | Material | 560.930 | 12.597.491.113,12 |
| APS | Serviço | 311.318 | 74.770.730.214,88 |
| — | — | 4 | — |
| APS | Material | 4 | 118.537,84 |
| AFM | Serviço | 1 | 126.405,16 |

**FORMA DE CONTRATAÇÃO (canal)**

| Forma | Linhas | Σ Valor | Com PCE | % PCE | Ticket mediano |
|---|---|---|---|---|---|
| Registro de Preços | 354.223 | 10.129.994.132,37 | 0 | 0 | 1.150 |
| N - Credenciamento | 216.612 | 3.922.681.222,89 | 0 | 0 | 1.472,63 |
| E - Dispensa Eletrônica | 114.388 | 266.374.539,70 | 114.387 | 100 | 600 |
| C - Licitação | 78.833 | 27.297.763.904,54 | 0 | 0 | 1.574,70 |
| D - Dispensa Tradicional | 68.702 | 10.336.969.488,62 | 0 | 0 | 1.760 |
| T - Termo Aditivo | 17.145 | 8.856.427.241,76 | 0 | 0 | 12.396 |
| I - Inexigibilidade | 17.126 | 6.453.094.612,46 | 0 | 0 | 50.000 |
| W - Adesão Registro de Preços | 1.963 | 1.908.596.045,51 | 0 | 0 | 70.000 |
| Y - Licitação Lei Fed 13.303/16 | 935 | 15.565.748.994,86 | 0 | 0 | 822.133,21 |
| Q - Contratação Direta | 724 | 991.775.350,63 | 0 | 0 | 23.988 |
| U - Apostila | 649 | 130.981.080,15 | 0 | 0 | 3.912,41 |
| R - Concurso | 451 | 10.144.400 | 0 | 0 | 15.000 |
| S - Shopping | 208 | 11.793.174,27 | 0 | 0 | 11.790 |
| L - Alteração de Fornecedor | 146 | 1.245.264.321,69 | 0 | 0 | 19.070 |
| P - Comparação de Preço | 84 | 61.532.936,34 | 0 | 0 | 1.000 |
| G - Seleção de Consultores Individuais (SCI) | 23 | 15.734.916,03 | 0 | 0 | 831.600 |
| M - Manifestação de Interesse | 10 | 6.152.900,73 | 0 | 0 | 325.500 |
| O - Seleção Baseada nas Qualificações do Consultor (SQC) | 9 | 12.738.111,51 | 0 | 0 | 772.012 |
| H - Seleção Baseada na Qualidade (SBQ) | 8 | 8.194.000,17 | 0 | 0 | 962.232 |
| B - Seleção Baseada na Qualidade e Custo (SBQC) | 7 | 43.480.427,24 | 0 | 0 | 1.261.529,68 |
| F - RDC | 5 | 91.401.914,74 | 0 | 0 | 15.746.370,30 |
| — | 4 | — | 0 | 0 | — |
| V - Convênio | 1 | 80.584,99 | 0 | 0 | 80.584,99 |
| J - Seleção com Orçamento Fixo (SOF) | 1 | 1.541.969,80 | 0 | 0 | 1.541.969,80 |

**Flags COVID / emergencial**

| MARC. COVID | LIB. COVID | MARC. VACINA | EMERGENCIAL | Linhas | Σ Valor |
|---|---|---|---|---|---|
| Não | Não | Não | — | 553.987 | 12.402.837.087,29 |
| Não | Não | Não | Não | 310.286 | 73.455.288.553,93 |
| Sim | Não | Não | — | 5.675 | 160.218.877,32 |
| Não | Não | Sim | — | 1.118 | 16.238.896,77 |
| Sim | Não | Não | Não | 461 | 725.230.618,11 |
| Não | Não | Sim | Não | 317 | 217.051.482,73 |
| Não | Não | Não | Sim | 165 | 56.018.186,14 |
| Sim | Sim | Não | — | 145 | 18.303.818,90 |
| Sim | Sim | Não | Não | 80 | 305.185.500,98 |
| Não | Sim | Não | Não | 13 | 12.074.410,83 |
| Não | Sim | Não | — | 6 | 18.838 |
| — | — | — | — | 4 | — |

**SRD / LID × forma de contratação** (inferência das siglas FIPLAN)

| SRD | LID | Forma | Linhas |
|---|---|---|---|
| — | — | N - Credenciamento | 199.984 |
| — | — | Registro de Preços | 106.656 |
| — | — | T - Termo Aditivo | 17.133 |
| — | — | U - Apostila | 646 |
| — | — | I - Inexigibilidade | 441 |
| 19.601.0003.22.0001567-9 | 19.601.0003.22.0001307-8 | C - Licitação | 307 |
| 19.601.0003.25.0000350-3 | 19.601.0003.25.0000273-1 | D - Dispensa Tradicional | 304 |
| 19.601.0003.22.0000988-1 | 19.601.0003.22.0001566-6 | C - Licitação | 284 |
| 22.202.0001.24.0000292-8 | 22.202.0001.24.0000297-4 | C - Licitação | 268 |
| 11.302.0001.22.0000057-2 | 11.302.0001.22.0000389-5 | C - Licitação | 249 |
| 11.301.0024.22.0000054-9 | 11.301.0024.22.0000044-7 | C - Licitação | 200 |
| 11.303.0001.22.0000752-1 | 11.303.0001.22.0000756-8 | C - Licitação | 177 |
| 11.303.0001.22.0000860-7 | 11.303.0001.22.0000816-5 | C - Licitação | 174 |
| 11.301.0004.23.0000032-1 | 11.301.0004.23.0000023-8 | C - Licitação | 169 |
| — | — | E - Dispensa Eletrônica | 167 |

## 6. Categóricas-chave (valores únicos)

### `tipo_fornecimento` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| AFM | 560.931 | 64,31 |
| APS | 311.322 | 35,69 |
| <NULL> | 4 | 0 |

### `tipo_do_item` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Material | 560.934 | 64,31 |
| Serviço | 311.319 | 35,69 |
| <NULL> | 4 | 0 |

### `tipo_item_especifico_comum` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| ESPECIFICO | 541.419 | 62,07 |
| COMUM | 330.834 | 37,93 |
| <NULL> | 4 | 0 |

### `classificacao_familia` — 3 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Outros | 848.150 | 97,24 |
| TIC | 19.327 | 2,22 |
| Serviços Terceirizados | 4.776 | 0,55 |
| <NULL> | 4 | 0 |

### `categoria` — 7 valores distintos

| Valor | Linhas | % |
|---|---|---|
| NO | 316.347 | 36,27 |
| EPP | 299.522 | 34,34 |
| ME | 238.048 | 27,29 |
| MEI | 16.331 | 1,87 |
| AF | 1.596 | 0,18 |
| ES | 340 | 0,04 |
| EC | 68 | 0,01 |
| <NULL> | 5 | 0,00 |

### `situacao_fornecedor` — 11 valores distintos

| Valor | Linhas | % |
|---|---|---|
| 1 - Ativo | 431.913 | 49,52 |
| 2 - Ativo com ocorrência | 256.422 | 29,40 |
| 6 - Cancelado | 57.937 | 6,64 |
| 7 - Candidato | 50.478 | 5,79 |
| 12 - Cancelado com Ocorrência | 19.203 | 2,20 |
| 4 - Suspenso determinado | 18.547 | 2,13 |
| 3 - Vencido | 13.425 | 1,54 |
| 5 - Suspenso indeterminado | 11.061 | 1,27 |
| 13 - Candidato com Ocorrência | 8.907 | 1,02 |
| 8 - Vencido com Ocorrência | 4.240 | 0,49 |
| 10 - Solicitado | 120 | 0,01 |
| <NULL> | 4 | 0 |

### `forma_contratacao` — 23 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Registro de Preços | 354.223 | 40,61 |
| N - Credenciamento | 216.612 | 24,83 |
| E - Dispensa Eletrônica | 114.388 | 13,11 |
| C - Licitação | 78.833 | 9,04 |
| D - Dispensa Tradicional | 68.702 | 7,88 |
| T - Termo Aditivo | 17.145 | 1,97 |
| I - Inexigibilidade | 17.126 | 1,96 |
| W - Adesão Registro de Preços | 1.963 | 0,23 |
| Y - Licitação Lei Fed 13.303/16 | 935 | 0,11 |
| Q - Contratação Direta | 724 | 0,08 |
| U - Apostila | 649 | 0,07 |
| R - Concurso | 451 | 0,05 |
| S - Shopping | 208 | 0,02 |
| L - Alteração de Fornecedor | 146 | 0,02 |
| P - Comparação de Preço | 84 | 0,01 |
| G - Seleção de Consultores Individuais (SCI) | 23 | 0,00 |
| M - Manifestação de Interesse | 10 | 0,00 |
| O - Seleção Baseada nas Qualificações do Consultor (SQC) | 9 | 0,00 |
| H - Seleção Baseada na Qualidade (SBQ) | 8 | 0,00 |
| B - Seleção Baseada na Qualidade e Custo (SBQC) | 7 | 0,00 |
| F - RDC | 5 | 0,00 |
| <NULL> | 4 | 0 |
| J - Seleção com Orçamento Fixo (SOF) | 1 | 0 |
| V - Convênio | 1 | 0 |

### `instrumento` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Não | 602.878 | 69,12 |
| Sim | 269.375 | 30,88 |
| <NULL> | 4 | 0 |

### `modulo_servicos_terceirizados` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Não | 869.169 | 99,65 |
| Sim | 3.084 | 0,35 |
| <NULL> | 4 | 0 |

### `srd_fiplan` — 353603 valores distintos (top 25; coluna de alta cardinalidade)

| Valor | Linhas | % |
|---|---|---|
| <NULL> | 325.064 | 37,27 |
| 19.601.0003.22.0001567-9 | 307 | 0,04 |
| 19.601.0003.25.0000350-3 | 304 | 0,04 |
| 19.601.0003.22.0000988-1 | 284 | 0,03 |
| 22.202.0001.24.0000292-8 | 268 | 0,03 |
| 11.302.0001.22.0000057-2 | 249 | 0,03 |
| 11.301.0024.22.0000054-9 | 200 | 0,02 |
| 11.303.0001.22.0000752-1 | 177 | 0,02 |
| 11.303.0001.22.0000860-7 | 174 | 0,02 |
| 11.301.0004.23.0000032-1 | 169 | 0,02 |
| 11.301.0016.23.0000073-8 | 166 | 0,02 |
| 11.302.0001.22.0000611-2 | 160 | 0,02 |
| 11.302.0001.22.0000084-1 | 145 | 0,02 |
| 11.303.0001.25.0000525-7 | 136 | 0,02 |
| 19.601.0003.24.0000762-6 | 135 | 0,01 |
| 19.601.0003.25.0001464-5 | 135 | 0,01 |
| 11.303.0001.22.0000484-9 | 127 | 0,01 |
| 11.302.0001.22.0000615-5 | 125 | 0,01 |
| 19.601.0003.22.0000835-4 | 125 | 0,01 |
| 20.801.0010.21.0000051-0 | 125 | 0,01 |
| 11.303.0001.24.0000679-6 | 124 | 0,01 |
| 19.601.0003.22.0001645-4 | 123 | 0,01 |
| 20.801.0010.23.0000008-2 | 122 | 0,01 |
| 11.303.0001.24.0000426-2 | 118 | 0,01 |
| 11.302.0001.24.0000214-2 | 115 | 0,01 |

### `lid_fiplan` — 353591 valores distintos (top 25; coluna de alta cardinalidade)

| Valor | Linhas | % |
|---|---|---|
| <NULL> | 325.077 | 37,27 |
| 19.601.0003.22.0001307-8 | 307 | 0,04 |
| 19.601.0003.25.0000273-1 | 304 | 0,04 |
| 19.601.0003.22.0001566-6 | 284 | 0,03 |
| 22.202.0001.24.0000297-4 | 268 | 0,03 |
| 11.302.0001.22.0000389-5 | 249 | 0,03 |
| 11.301.0024.22.0000044-7 | 200 | 0,02 |
| 11.303.0001.22.0000756-8 | 177 | 0,02 |
| 11.303.0001.22.0000816-5 | 174 | 0,02 |
| 11.301.0004.23.0000023-8 | 169 | 0,02 |
| 11.301.0016.23.0000087-5 | 166 | 0,02 |
| 11.302.0001.22.0000581-2 | 160 | 0,02 |
| 11.302.0001.22.0000046-2 | 145 | 0,02 |
| 11.303.0001.25.0000446-9 | 136 | 0,02 |
| 19.601.0003.24.0000631-5 | 135 | 0,01 |
| 19.601.0003.25.0001192-7 | 135 | 0,01 |
| 11.303.0001.22.0000424-0 | 127 | 0,01 |
| 11.302.0001.22.0000583-9 | 125 | 0,01 |
| 19.601.0003.22.0000674-8 | 125 | 0,01 |
| 20.801.0010.21.0000045-1 | 125 | 0,01 |
| 11.303.0001.24.0000591-4 | 124 | 0,01 |
| 19.601.0003.22.0001378-7 | 123 | 0,01 |
| 20.801.0010.23.0000010-1 | 122 | 0,01 |
| 11.303.0001.24.0000562-0 | 118 | 0,01 |
| 11.302.0001.24.0000147-8 | 115 | 0,01 |

### `marcacao_covid` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Não | 865.892 | 99,27 |
| Sim | 6.361 | 0,73 |
| <NULL> | 4 | 0 |

### `liberacao_covid` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Não | 872.009 | 99,97 |
| Sim | 244 | 0,03 |
| <NULL> | 4 | 0 |

### `marcacao_vacina_covid` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Não | 870.818 | 99,83 |
| Sim | 1.435 | 0,17 |
| <NULL> | 4 | 0 |

### `liberacao_vacina_covid` — 1 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Não | 872.253 | 100 |
| <NULL> | 4 | 0 |

### `contrato_emergencial_cgst` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| <NULL> | 560.935 | 64,31 |
| Não | 311.157 | 35,67 |
| Sim | 165 | 0,02 |

### `situacao_contrato_cgst` — 6 valores distintos

| Valor | Linhas | % |
|---|---|---|
| <NULL> | 869.173 | 99,65 |
| Vencido | 1.488 | 0,17 |
| Aditado | 724 | 0,08 |
| Vigente | 494 | 0,06 |
| Encerrado | 343 | 0,04 |
| Apostilado | 23 | 0,00 |
| Cancelado | 12 | 0,00 |

### `ressuprimento` — 3 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Não | 872.239 | 100,00 |
| 19.004 - FUNDO ESTADUAL DE SAUDE - DIRETORIA GERAL | 11 | 0,00 |
| <NULL> | 5 | 0,00 |
| 09.021 - SUPERINTENDENCIA DE RECURSOS LOGISTICOS | 2 | 0 |

### `delegacao_automatica` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Não | 719.276 | 82,46 |
| SIM | 152.977 | 17,54 |
| <NULL> | 4 | 0 |

### `digitalizacao_contrato` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| Não | 486.816 | 55,81 |
| Sim | 385.437 | 44,19 |
| <NULL> | 4 | 0 |

### `tipo_da_requisicao` — 2 valores distintos

| Valor | Linhas | % |
|---|---|---|
| RM | 560.931 | 64,31 |
| RS | 311.322 | 35,69 |
| <NULL> | 4 | 0 |

### `uf_fornecedor` — 29 valores distintos

| Valor | Linhas | % |
|---|---|---|
| BA | 708.057 | 81,17 |
| SP | 39.121 | 4,49 |
| MG | 26.919 | 3,09 |
| PR | 16.928 | 1,94 |
| PE | 13.341 | 1,53 |
| DF | 9.457 | 1,08 |
| GO | 9.301 | 1,07 |
| CE | 9.225 | 1,06 |
| ES | 9.031 | 1,03 |
| SC | 6.946 | 0,80 |
| RS | 6.358 | 0,73 |
| RJ | 5.732 | 0,66 |
| SE | 3.529 | 0,41 |
| AL | 2.841 | 0,33 |
| RN | 1.703 | 0,20 |
| PB | 1.028 | 0,12 |
| AM | 638 | 0,07 |
| TO | 553 | 0,06 |
| MS | 497 | 0,06 |
| EE | 329 | 0,04 |
| MT | 303 | 0,04 |
| <NULL> | 203 | 0,02 |
| RO | 80 | 0,01 |
| MA | 72 | 0,01 |
| PI | 36 | 0,00 |
| PA | 18 | 0,00 |
| Ba | 6 | 0,00 |
| AP | 2 | 0 |
| RR | 2 | 0 |
| AC | 1 | 0 |

### `uf_local_entrega` — 3 valores distintos

| Valor | Linhas | % |
|---|---|---|
| BA | 871.682 | 99,93 |
| ba | 476 | 0,06 |
| DF | 95 | 0,01 |
| <NULL> | 4 | 0 |

### `afm_aps_tipo_item` — 492933 valores distintos (top 25; coluna de alta cardinalidade)

| Valor | Linhas | % |
|---|---|---|
| APS - 19.004.00089/2022 | 307 | 0,04 |
| APS - 19.004.00017/2025 | 304 | 0,04 |
| APS - 19.004.00097/2022 | 284 | 0,03 |
| AFM - 11.620.00168/2022 | 249 | 0,03 |
| AFM - 11.271.00037/2022 | 200 | 0,02 |
| AFM - 11.630.00456/2022 | 174 | 0,02 |
| AFM - 11.229.00178/2022 | 169 | 0,02 |
| AFM - 11.241.00067/2023 | 166 | 0,02 |
| AFM - 11.620.00237/2022 | 160 | 0,02 |
| AFM - 11.630.00428/2022 | 159 | 0,02 |
| AFM - 11.620.00029/2022 | 145 | 0,02 |
| APS - 11.630.00169/2025 | 136 | 0,02 |
| APS - 19.004.00025/2024 | 135 | 0,01 |
| APS - 19.004.00085/2025 | 135 | 0,01 |
| AFM - 22.710.00232/2024 | 134 | 0,01 |
| AFM - 22.710.00233/2024 | 134 | 0,01 |
| APS - 70.245.00002/2021 | 131 | 0,01 |
| APS - 11.630.00135/2022 | 127 | 0,01 |
| AFM - 11.620.00239/2022 | 125 | 0,01 |
| AFM - 20.062.00031/2021 | 125 | 0,01 |
| APS - 19.004.00040/2022 | 125 | 0,01 |
| APS - 11.630.00202/2024 | 124 | 0,01 |
| APS - 19.004.00090/2022 | 123 | 0,01 |
| APS - 70.245.00005/2024 | 123 | 0,01 |
| AFM - 20.062.00003/2023 | 122 | 0,01 |

### `tipo_calculo` — 3 valores distintos

| Valor | Linhas | % |
|---|---|---|
| <NULL> | 713.360 | 81,78 |
| Multiplicação | 156.997 | 18,00 |
| Valor Final do Item | 1.325 | 0,15 |
| Diárias | 575 | 0,07 |

### `prazo_entrega` — 521 valores distintos (top 25; coluna de alta cardinalidade)

| Valor | Linhas | % |
|---|---|---|
| 15 | 187.152 | 21,46 |
| 30 | 170.872 | 19,59 |
| 7 | 106.189 | 12,17 |
| 365 | 58.281 | 6,68 |
| 10 | 48.181 | 5,52 |
| 270 | 34.289 | 3,93 |
| 90 | 33.233 | 3,81 |
| 240 | 28.830 | 3,31 |
| 5 | 27.202 | 3,12 |
| 60 | 25.323 | 2,90 |
| 210 | 25.200 | 2,89 |
| 180 | 23.985 | 2,75 |
| 150 | 13.706 | 1,57 |
| 120 | 12.993 | 1,49 |
| 300 | 11.203 | 1,28 |
| 8 | 9.671 | 1,11 |
| 20 | 9.481 | 1,09 |
| 12 | 4.916 | 0,56 |
| 3 | 4.806 | 0,55 |
| 40 | 3.651 | 0,42 |
| 1 | 3.408 | 0,39 |
| 45 | 2.809 | 0,32 |
| 360 | 2.652 | 0,30 |
| 1095 | 2.076 | 0,24 |
| 330 | 2.056 | 0,24 |

### `pce_pedido_cotacao` — 53488 valores distintos (top 25; coluna de alta cardinalidade)

| Valor | Linhas | % |
|---|---|---|
| <NULL> | 757.870 | 86,89 |
| 1127320250010 | 130 | 0,01 |
| 2007220230006 | 118 | 0,01 |
| 2007220240002 | 117 | 0,01 |
| 2007220240039 | 112 | 0,01 |
| 1123020240030 | 104 | 0,01 |
| 2007220240046 | 97 | 0,01 |
| 2007220250038 | 94 | 0,01 |
| 2023120230027 | 89 | 0,01 |
| 2006620230008 | 85 | 0,01 |
| 2001920250011 | 82 | 0,01 |
| 1123020240036 | 79 | 0,01 |
| 2010020240009 | 79 | 0,01 |
| 2078020250004 | 79 | 0,01 |
| 2006320230009 | 77 | 0,01 |
| 2078920240002 | 75 | 0,01 |
| 2017020240002 | 72 | 0,01 |
| 2022320250025 | 72 | 0,01 |
| 1123220250022 | 71 | 0,01 |
| 2007220230017 | 71 | 0,01 |
| 2023120240003 | 71 | 0,01 |
| 1123320240057 | 70 | 0,01 |
| 1123620240121 | 69 | 0,01 |
| 2007220220004 | 69 | 0,01 |
| 2007220220033 | 69 | 0,01 |

## 7. Higiene de CNPJ

- CNPJs distintos: **15.216**; com máscara: 100.0%; 14 dígitos: 82.486%.
- Validação de DV em amostra de 2.000 CNPJs distintos: **100.0%** válidos.

## 8. Colunas de texto que podem conter números

| Coluna | Preenchidos | Numéricos | % numérico | Mín | Máx |
|---|---|---|---|---|---|
| prazo_entrega | 872.239 | 872.239 | 100 | 1 | 36.000 |
| cnae_codigo | 867.160 | 867.160 | 100 | 111.302 | 9.900.800 |
| n_processo | 719.076 | 0 | 0 | — | — |
| cod_local_entrega | 872.253 | 872.253 | 100 | 10.010.001 | 722.370.001 |

## 9. Hierarquia de catálogo por grupo (top 30 por valor)

| GRUPO CATÁLOGO | Famílias | Nomes básicos | Linhas | Σ Valor |
|---|---|---|---|---|
| 07 - OBRAS E CONSTRUCOES | 26 | 131 | 3.826 | 29.629.538.373,07 |
| 02 - SERVICOS TECNICOS E ESPECIALIZADOS | 76 | 630 | 13.190 | 22.210.713.762,17 |
| 01 - SERVICOS GERAIS E ADMINISTRATIVOS | 81 | 526 | 244.989 | 14.022.815.015,67 |
| 65 - EQUIPAMENTOS E ARTIGOS DE USO MEDICO, DENTARIO E VETERINARIO | 18 | 1.574 | 268.292 | 5.564.295.434,72 |
| 09 - SERVICOS MEDICOS E ODONTOLOGICOS | 20 | 67 | 1.037 | 2.462.108.783,76 |
| 04 - SERVICOS DE MANUTENCAO E ASSISTENCIA TECNICA | 55 | 678 | 25.048 | 2.351.308.975,93 |
| 03 - SERVICOS DE SUPORTE A ADMINISTRACAO DE PREDIOS E AREAS PUBLICAS | 28 | 433 | 10.559 | 2.210.814.212,44 |
| 23 - VEICULOS | 4 | 29 | 682 | 1.897.960.664,41 |
| 08 - INSTALACOES E MONTAGENS | 40 | 376 | 8.371 | 1.085.090.409,58 |
| 70 - EQUIP. DE PROCSS. AUTOM. DE DADOS DE USO GERAL, PROG. SUPR. E EQUIP DE SUPORTE | 18 | 331 | 13.344 | 912.812.118,45 |
| 05 - SERVICOS DE TRANSPORTES | 11 | 20 | 2.367 | 542.775.688,10 |
| 71 - MOBILIARIOS | 4 | 65 | 9.115 | 520.164.008,28 |
| 24 - TRATORES | 1 | 3 | 200 | 394.402.833,33 |
| 41 - EQUIPAMENTOS DE REFRIGERACAO, CIRCULACAO E CONDICIONAMENTO DE AR | 4 | 44 | 7.414 | 294.868.772,10 |
| 66 - INSTRUMENTOS E EQUIPAMENTOS DE LABORATORIO | 16 | 304 | 9.069 | 277.236.958,66 |
| 06 - ESTUDOS E PROJETOS | 30 | 37 | 1.932 | 255.691.399,32 |
| 84 - VESTUARIOS E EQUIPAMENTOS INDIVIDUAIS E INSIGNIAS | 15 | 108 | 6.164 | 237.479.174,26 |
| 56 - MATERIAIS PARA CONSTRUCAO | 8 | 79 | 4.976 | 221.080.991,46 |
| 76 - LIVROS, MAPAS E OUTRAS PUBLICACOES | 5 | 51 | 6.190 | 200.765.524,90 |
| 37 - MAQUINARIA E EQUIPAMENTOS AGRICOLAS | 6 | 166 | 2.051 | 191.356.343,54 |
| 89 - ALIMENTOS | 14 | 167 | 28.552 | 172.385.357,51 |
| 47 - CANOS, TUBOS, MANGUEIRAS E ACESSORIOS | 3 | 38 | 6.117 | 126.778.584,44 |
| 85 - ARTIGOS PARA HIGIENE PESSOAL | 3 | 56 | 12.331 | 126.107.461,15 |
| 15 - AERONAVES SEUS COMPONENTES ESTRUTURAIS | 1 | 3 | 88 | 112.744.263,83 |
| 78 - EQUIPAMENTOS PARA RECREACAO E DESPORTO | 3 | 190 | 5.064 | 102.328.090,40 |
| 13 - MUNICOES E EXPLOSIVOS | 1 | 16 | 218 | 89.982.810,89 |
| 42 - EQUIPAMENTOS PARA COMBATE A INCENDIO, RESGATE E SEGURANCA | 4 | 126 | 3.634 | 87.761.736,73 |
| 10 - ARMAMENTOS | 3 | 14 | 71 | 72.002.749,56 |
| 75 - UTENSILIOS DE ESCRITORIO E MATERIAL DE EXPEDIENTE | 4 | 115 | 42.869 | 71.562.389,84 |
| 81 - RECIPIENTES E MATERIAIS DE ACONDICIONAMENTO E EMBALAGEM | 6 | 24 | 9.672 | 68.231.382,82 |

## 11. Universo de MATERIAL (escopo padrão da análise)

Filtro: `TIPO DO ITEM = 'Material'` (coerente com `TIPO FORNECIMENTO = 'AFM'` em 99,999% das linhas).

| Ano | Linhas | AFM/APS | CNPJs | Famílias | Σ VALOR TOTAL | Ticket mediano/linha |
|---|---|---|---|---|---|---|
| 2021 | 73.263 | 53.395 | 1.847 | 283 | 1.999.740.528,41 | 924 |
| 2022 | 113.033 | 81.103 | 2.334 | 305 | 2.308.241.623,95 | 899 |
| 2023 | 126.263 | 94.541 | 2.613 | 318 | 2.256.950.625,80 | 864 |
| 2024 | 121.468 | 95.246 | 2.516 | 315 | 2.940.344.318,21 | 1.016 |
| 2025 | 126.907 | 97.756 | 2.486 | 317 | 3.092.332.554,59 | 1.053 |

- Ticket por AFM/APS: p50 = R$ 1.330,20, p75 = R$ 5.220; 96,35% das AFM/APS ≤ R$ 65.492,11.

**Material por forma de contratação**

| Forma | Linhas | % linhas | Σ Valor | Ticket mediano | CNPJs |
|---|---|---|---|---|---|
| Registro de Preços | 338.724 | 60,39 | 7.449.649.360,54 | 1.086 | 1.767 |
| C - Licitação | 63.102 | 11,25 | 1.638.131.200 | 939,40 | 2.206 |
| W - Adesão Registro de Preços | 1.479 | 0,26 | 1.552.892.045,94 | 73.500 | 282 |
| D - Dispensa Tradicional | 42.295 | 7,54 | 1.060.780.114,36 | 980 | 2.234 |
| I - Inexigibilidade | 3.562 | 0,64 | 462.338.363,86 | 2.100,08 | 174 |
| E - Dispensa Eletrônica | 108.158 | 19,28 | 239.519.403,76 | 576,80 | 2.248 |
| T - Termo Aditivo | 1.399 | 0,25 | 94.587.920,21 | 2.310 | 171 |
| Q - Contratação Direta | 232 | 0,04 | 40.145.355,66 | 9.540 | 44 |
| Y - Licitação Lei Fed 13.303/16 | 222 | 0,04 | 32.652.870,69 | 3.268,38 | 25 |
| N - Credenciamento | 1.531 | 0,27 | 23.882.405 | 7.700 | 13 |
| S - Shopping | 78 | 0,01 | 1.700.541,08 | 11.199,32 | 6 |
| L - Alteração de Fornecedor | 82 | 0,01 | 1.168.780,86 | 15.150,50 | 9 |
| P - Comparação de Preço | 70 | 0,01 | 161.289 | 595 | 2 |

## 12. Anomalias, limpeza e mapeamentos

**Identificador do fornecedor (dígitos em `CNPJ`)** — 4.665 linhas são CPF (pessoa física).

| Dígitos | Linhas | Fornecedores |
|---|---|---|
| 10 | 428 | 47 |
| 11 | 4.665 | 2.618 |
| 14 | 867.160 | 12.551 |

**Datas e prazos suspeitos por arquivo**

| Arquivo | Assinatura < 2019 | Assinatura > 2026 | Assinatura < geração | Ano fim fora de faixa | Prazo > 365 d |
|---|---|---|---|---|---|
| 2021 | 0 | 0 | 0 | 0 | 530 |
| 2022 | 0 | 0 | 6 | 0 | 650 |
| 2023 | 0 | 0 | 71 | 0 | 766 |
| 2024 | 8 | 0 | 133 | 8 | 1.013 |
| 2025 | 125 | 0 | 281 | 100 | 1.899 |

**Escala**: 3.700 linhas com valor unitário ≥ R$ 1 mi; 102 linhas com valor total ≥ R$ 100 mi; valor unitário máximo R$ 1.418.231.801; valor total máximo R$ 1.418.231.801. Outliers serão mantidos e sinalizados; winsorização (p1/p99) só nas estatísticas de preço.

**UF de entrega** (evidência de que a base é estadual e a entrega é quase toda na BA)

| UF de entrega | Linhas |
|---|---|
| BA | 871.682 |
| ba | 476 |
| DF | 95 |
| (nulo) | 4 |

**Regiões de entrega** (rótulos originais — exigem normalização)

| Região (rótulo original) | Linhas | Σ Valor |
|---|---|---|
| Região Metropolitana de Salvador | 414.525 | 81.583.118.354,81 |
| Região Itapetinga e Vitória da Conquista | 51.399 | 637.067.845,15 |
| Região Feira de Santana | 45.015 | 1.763.370.098,28 |
| Região Alagoinhas e Serrinha | 42.611 | 298.796.067,89 |
| Região SAJesus, Amargosa,Valença,SAmaro | 39.136 | 398.762.112,82 |
| Região Jequié | 38.305 | 328.099.463,07 |
| Região Brumado, Caetité e Guanambi | 33.540 | 199.292.215,72 |
| Região Ilhéus e Itabuna | 29.845 | 507.089.129,73 |
| Região Ribeira do Pombal e Paulo Afonso | 28.959 | 312.838.503,11 |
| Região Juazeiro e Senhor do Bonfim | 27.174 | 263.994.753,58 |
| Região Eunápolis e Teixeira de Freitas | 27.118 | 192.544.607,70 |
| Região Jacobina, Piritiba e Itaberaba | 26.982 | 347.108.678,17 |
| Região Seabra e Irecê | 23.078 | 179.220.790,56 |
| Região Barreiras | 20.484 | 165.358.933,44 |
| Região B. Jesus Lapa e Macaúbas | 18.307 | 155.512.373,09 |
| Região SAEB/SAC Interior | 5.413 | 30.996.200,71 |
| Região Merenda Escolar (Inativo) | 267 | 5.100.085,07 |
| Região Centro Oeste do Brasil | 95 | 196.058,10 |
| (nulo) | 4 | — |
