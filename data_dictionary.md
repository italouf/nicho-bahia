# data_dictionary.md — dicionário de dados (original → canônico)

Gerado por `run.py --stage profile` em 2026-11-12T17:46:22.724580+00:00.

Regras de normalização aplicadas na camada de staging:

1. Rótulo original → `snake_case` ASCII (sem acento), sem espaços nas pontas e com espaços internos colapsados.
2. Valores de texto têm espaços nas pontas removidos; célula vazia vira `NULL`.
3. Datas: lidas como data nativa (o XLSX já traz data); textos em `dd/mm/aaaa` e `aaaa-mm-dd` também são aceitos.
4. Números: aceita `1.234,56` (BR) e `1234.56` (US). Conteúdo não numérico vira `NULL` e é contado em log.
5. Cabeçalhos em branco foram resolvidos por posição (ver seção 12 do DATA_PROFILE.md e o log de ingestão).

| # | Coluna original (planilha) | Coluna canônica | Tipo | Nulos | % nulos | Distintos | Semântica de trabalho |
|---|---|---|---|---|---|---|---|
| 0 | `COD. SECRETARIA` | `cod_secretaria` | int | 4 | 0,00% | 41 | Código da secretaria/órgão (dígito). |
| 1 | `SECRETARIA` | `secretaria` | text | 4 | 0,00% | 41 | Nome do órgão: 'NN - NOME'. |
| 2 | `UNIDADE` | `unidade` | text | 4 | 0,00% | 1.917 | Unidade orçamentária: 'NN.NNN - NOME'. |
| 3 | `UO FIPLAN` | `uo_fiplan` | text | 306.568 | 35,15% | 97 | Código UO FIPLAN + descrição. |
| 4 | `UG FIPLAN` | `ug_fiplan` | text | 308.972 | 35,42% | 400 | Código UG FIPLAN + descrição. |
| 5 | `TIPO FORNECIMENTO` | `tipo_fornecimento` | text | 4 | 0,00% | 2 | AFM (material) ou APS (serviço/prestação). |
| 6 | `GRUPO LICITAÇÃO` | `grupo_licitacao` | text | 4 | 0,00% | 147 | Grupo de licitação (rubrica de compra). |
| 7 | `GRUPO CATÁLOGO` | `grupo_catalogo` | text | 4 | 0,00% | 78 | Nível 1 da hierarquia de catálogo. |
| 8 | `FAMILIA CATÁLOGO` | `familia_catalogo` | text | 4 | 0,00% | 726 | Nível 2 da hierarquia (família de material/serviço). |
| 9 | `CÓDIGO` | `codigo` | text | 4 | 0,00% | 52.876 | Código do item de catálogo (com DV). |
| 10 | `Nome Básico` | `nome_basico` | text | 4 | 0,00% | 6.360 | Nome básico do item (nível 3). |
| 11 | `ITEM` | `item` | text | 4 | 0,00% | 52.600 | Descrição/ especificação do item (nível 4). |
| 12 | `TIPO ITEM (ESPECIFICO/COMUM)` | `tipo_item_especifico_comum` | text | 4 | 0,00% | 2 | Item específico ou comum. |
| 13 | `UM` | `um` | text | 4 | 0,00% | 53 | Unidade de medida. |
| 14 | `TIPO DO ITEM` | `tipo_do_item` | text | 4 | 0,00% | 2 | Material / Serviço / (outros). |
| 15 | `QTD CONTRATADA` | `qtd_contratada` | num | 4 | 0,00% | 14.542 | Quantidade contratada na linha. |
| 16 | `Tipo_Calculo` | `tipo_calculo` | text | 713.360 | 81,78% | 3 | Campo auxiliar de cálculo (majoritariamente vazio). |
| 17 | `VALOR DETALHE` | `valor_detalhe` | num | 713.360 | 81,78% | 989 | Campo auxiliar de valor (majoritariamente vazio). |
| 18 | `VALOR UNITÁRIO` | `valor_unitario` | num | 6 | 0,00% | 68.381 | Valor unitário contratado. |
| 19 | `VALOR TOTAL` | `valor_total` | num | 4 | 0,00% | 156.729 | Valor total da linha (QTD x UNIT). |
| 20 | `CNPJ` | `cnpj` | text | 4 | 0,00% | 15.216 | CNPJ do fornecedor (com máscara). |
| 21 | `cnae_codigo` | `cnae_codigo` | int | 5.097 | 0,58% | 681 | CNAE do fornecedor (Receita). |
| 22 | `cnae_descricao` | `cnae_descricao` | text | 4 | 0,00% | 672 | Descrição do CNAE. |
| 23 | `uf_receita` | `uf_receita` | text | 4 | 0,00% | 28 | UF do fornecedor na Receita. |
| 24 | `razao_social` | `razao_social` | text | 4 | 0,00% | 14.514 | Razão social (Receita). |
| 25 | `nome_fantasia` | `nome_fantasia` | text | 4 | 0,00% | 9.143 | Nome fantasia (Receita). |
| 26 | `FORNECEDOR` | `fornecedor` | text | 90.062 | 10,32% | 13.974 | Fornecedor conforme cadastro FIPLAN. AUSENTE em 2021. |
| 27 | `CATEGORIA` | `categoria` | text | 5 | 0,00% | 7 | Porte do fornecedor (ME/EPP/MEDIO/NO...). |
| 28 | `SITUAÇÃO FORNECEDOR` | `situacao_fornecedor` | text | 4 | 0,00% | 11 | Situação cadastral do fornecedor. |
| 29 | `UF FORNECEDOR` | `uf_fornecedor` | text | 203 | 0,02% | 29 | UF do fornecedor (FIPLAN). |
| 30 | `FORMA DE CONTRATAÇÃO` | `forma_contratacao` | text | 4 | 0,00% | 23 | Modalidade/instrumento (Registro de Preços, Dispensa...). |
| 31 | `Nº LICITAÇÃO` | `n_licitacao` | text | 438.694 | 50,29% | 17.123 | Número da licitação de origem. |
| 32 | `Requisição de Material - RM/Requisição de Serviços -RS` | `requisicao_rm_rs` | text | 4 | 0,00% | 454.382 | Número da requisição (RM/RS). |
| 33 | `Dotacao` | `dotacao` | text | 4 | 0,00% | 2 | Dotação orçamentária. |
| 34 | `AFM/APS` | `afm_aps` | text | 4 | 0,00% | 449.967 | Código da AFM (material) ou APS (serviço). |
| 35 | `AFM/APS_TIPO ITEM` | `afm_aps_tipo_item` | text | 4 | 0,00% | 492.933 | Rótulo composto 'tipo - número'. |
| 36 | `DATA GERAÇÃO da AFM/APS` | `data_geracao_afm_aps` | date | 4 | 0,00% | 1.552 | Eixo temporal principal (data de geração). |
| 37 | `Assinatura da AFM/APS` | `assinatura_afm_aps` | date | 385.405 | 44,19% | 1.796 | Data de assinatura/empenho. Vazio em 2021. |
| 38 | `Código Local de Entrega/Execução da AFM/APS` | `cod_local_entrega` | text | 4 | 0,00% | 6.774 | Código do local de entrega. |
| 39 | `Endereço Local de Entrega/Execução da AFM/APS` | `endereco_local_entrega` | text | 4 | 0,00% | 5.700 | Endereço de entrega. |
| 40 | `Bairro Local de Entrega/Execução da AFM/APS` | `bairro_local_entrega` | text | 4 | 0,00% | 521 | Bairro de entrega. |
| 41 | `Município Local de Entrega/Execução da AFM/APS` | `municipio_local_entrega` | text | 4 | 0,00% | 418 | Município de entrega. |
| 42 | `UF Local de Entrega/Execução da AFM/APS` | `uf_local_entrega` | text | 4 | 0,00% | 3 | UF de entrega. |
| 43 | `SRD (FIPLAN)` | `srd_fiplan` | text | 325.064 | 37,27% | 353.603 | Sigla interna FIPLAN (a inferir por coocorrência). |
| 44 | `LID (FIPLAN)` | `lid_fiplan` | text | 325.077 | 37,27% | 353.591 | Sigla interna FIPLAN (a inferir por coocorrência). |
| 45 | `PCE - Pedido de Cotação Eletrônica` | `pce_pedido_cotacao` | text | 757.870 | 86,89% | 53.488 | Pedido de Cotação Eletrônica (proxy do canal dispensa). |
| 46 | `VALOR ESTIMADO` | `valor_estimado` | num | 4 | 0,00% | 65.474 | Valor de referência da cotação. ATENÇÃO: aparenta ser unitário, não total. |
| 47 | `Regiao_Principal_Município` | `regiao_principal_municipio` | text | 4 | 0,00% | 18 | Região de planejamento do município principal. |
| 48 | `Digitalização de Contrato` | `digitalizacao_contrato` | text | 4 | 0,00% | 2 | Indicador Sim/Não. |
| 49 | `CLASSIFICAÇÃO FAMÍLIA` | `classificacao_familia` | text | 4 | 0,00% | 3 | Classificação da família (Outros, Materiais...). |
| 50 | `REGIAO_Registro_Precos` | `regiao_registro_precos` | text | 518.034 | 59,39% | 30 | Região do registro de preços. |
| 51 | `MARCAÇÃO COVID-19` | `marcacao_covid` | text | 4 | 0,00% | 2 | Flag COVID (Sim/Não). |
| 52 | `LIBERAÇÃO COVID-19` | `liberacao_covid` | text | 4 | 0,00% | 2 | Flag liberação COVID. |
| 53 | `MARCAÇÃO VACINA COVID-19` | `marcacao_vacina_covid` | text | 4 | 0,00% | 2 | Flag vacina COVID. |
| 54 | `LIBERAÇÃO VACINA COVID-19` | `liberacao_vacina_covid` | text | 4 | 0,00% | 1 | Flag liberação vacina COVID. |
| 55 | `Situação do Fornecedor na Geração LID` | `situacao_fornecedor_lid` | text | 870.120 | 99,75% | 14 | Situação do fornecedor quando da geração do LID. |
| 56 | `MODULO SERVIÇOS TERCEIRIZADOS` | `modulo_servicos_terceirizados` | text | 4 | 0,00% | 2 | Indicador do módulo de terceirizados. |
| 57 | `INSTRUMENTO` | `instrumento` | text | 4 | 0,00% | 2 | Instrumento (Contrato/Ata/...). |
| 58 | `Contrato_Emergencial_Cgst` | `contrato_emergencial_cgst` | text | 560.935 | 64,31% | 2 | Flag contrato emergencial (CGE/ST). |
| 59 | `Situacao_Contrato_Cgst` | `situacao_contrato_cgst` | text | 869.173 | 99,65% | 6 | Situação do contrato no CGE/ST. |
| 60 | `UNIDADE LICITANTE` | `unidade_licitante` | text | 438.694 | 50,29% | 232 | Unidade licitante. |
| 61 | `TIPO DA REQUISIÇÃO` | `tipo_da_requisicao` | text | 4 | 0,00% | 2 | Tipo da requisição (RM/RS). |
| 62 | `DELEGAÇÃO AUTOMATICA` | `delegacao_automatica` | text | 4 | 0,00% | 2 | Indicador de delegação automática. |
| 63 | `ANO GERAÇÃO da AFM/APS` | `ano_geracao_afm_aps` | int | 4 | 0,00% | 5 | Ano de geração (fallback do eixo temporal). |
| 64 | `MES GERAÇÃO da AFM/APS` | `mes_geracao_afm_aps` | int | 4 | 0,00% | 12 | Mês de geração (fallback do eixo temporal). |
| 65 | `Região do Local de Entrega` | `regiao_local_entrega` | text | 4 | 0,00% | 18 | Região de planejamento do local de entrega. |
| 66 | `Nº PROCESSO` | `n_processo` | text | 153.181 | 17,56% | 277.449 | Número do processo administrativo. |
| 67 | `Nº CONTRATO` | `n_contrato` | text | 569.273 | 65,26% | 18.694 | Número do contrato. |
| 68 | `PRAZO DE ENTREGA` | `prazo_entrega` | text | 18 | 0,00% | 521 | Prazo de entrega (texto/numérico - a classificar em F1). |
| 69 | `ORGAO GERENCIADOR DO Registro de Preços` | `orgao_gerenciador_registro_precos` | text | 518.033 | 59,39% | 53 | Órgão gerenciador do RP (coluna 1). |
| 70 | `RESSUPRIMENTO` | `ressuprimento` | text | 5 | 0,00% | 3 | Indicador de ressuprimento. AUSENTE em 2021. |
| 71 | `ORGAO GERENCIADOR DO RP` | `orgao_gerenciador_rp` | text | 518.033 | 59,39% | 51 | Órgão gerenciador do RP (coluna 2). |
| 72 | `DATA FIM CONTRATO` | `data_fim_contrato` | date | 385.418 | 44,19% | 2.494 | Data fim da vigência. |
| 73 | `ANO FIM CONTRATO` | `ano_fim_contrato` | int | 385.418 | 44,19% | 17 | Ano fim da vigência. |
| 74 | `Aviso/Edital PNCP` | `aviso_edital_pncp` | text | 5 | 0,00% | 4 | Link do aviso/edital no PNCP (enriquecimento futuro). |
| 75 | `Ata RP PNCP` | `ata_rp_pncp` | text | 4 | 0,00% | 2 | Link da ata de RP no PNCP. |
| 76 | `Contratos PNCP` | `contratos_pncp` | text | 4 | 0,00% | 2 | Link do contrato no PNCP. |

## Colunas ausentes em arquivos específicos

- `fornecedor` — **ausente no arquivo de 2021** (o esquema de 2021 tem 77 colunas, sem esta).
- `ressuprimento` — ausente no arquivo de 2021 (a coluna de 2021 na posição equivalente é o órgão gerenciador do RP).
- Em 2021, `valor_total` e `assinatura_afm_aps` têm cabeçalho em branco e foram mapeadas por posição.
- Em 2022, há uma coluna extra em branco no fim da planilha, descartada.

## Hierarquia de produto

`grupo_catalogo > familia_catalogo > nome_basico > item` (descrição). O `codigo` identifica o item de catálogo.
A hierarquia **não é árvore estrita**: há nomes básicos sob mais de uma família.

<!-- INICIO:COLUNAS-DERIVADAS -->
## Colunas derivadas (camada tratada)

Criadas no estágio `treat`; ver `SPEC.md §3`.

| Coluna | Tipo | Semântica |
|---|---|---|
| `linha_id` | text | chave técnica única da linha (ano:linha da planilha) |
| `data` | date | data de geração da AFM/APS (eixo temporal) |
| `ano / mes / ano_mes` | int/text | partições temporais derivadas de data |
| `secretaria_key / unidade_key / ug_key` | text | chaves normalizadas (sem acento, caixa alta) |
| `grupo_key / familia_key` | text | chaves normalizadas da hierarquia de catálogo |
| `nome_key / item_desc_key / um_key` | text | chaves normalizadas de nome básico, descrição e unidade |
| `item_key` | text | familia|nome_basico|um normalizados — chave de comparação de preço |
| `nome_item_key` | text | familia|nome_basico normalizados |
| `cnpj14` | text | CNPJ com 14 dígitos; nulo para CPF/inválido |
| `is_pf` | bool | fornecedor pessoa física (CPF de 11 dígitos) |
| `fornecedor_id` | text | identidade do fornecedor (CNPJ, PF:CPF ou INVALIDO:...) |
| `uf_fornecedor_norm` | text | UF do fornecedor em caixa alta |
| `canal` | text | canal normalizado a partir de FORMA DE CONTRATAÇÃO (SPEC §5.3) |
| `is_dispensa` | bool | canal em dispensa eletrônica ou tradicional |
| `is_dispensa_eletronica` | bool | canal = dispensa eletrônica |
| `is_pce` | bool | PCE - Pedido de Cotação Eletrônica preenchido |
| `is_via_ata` | bool | compra via ata de Registro de Preços |
| `municipio_key / regiao_key` | text | município e região de entrega normalizados |
| `regiao_raio` | text | dentro / fora / indefinida em relação ao raio de 200 km |
| `is_pandemia` | bool | qualquer flag COVID = Sim ou contrato emergencial = Sim |
| `is_regulado` | bool | família ou keyword da lista EVITAR (config.regulados) |
| `prazo_entrega_dias` | int | prazo em dias; nulo se > 365 (cauda inválida) |
| `deflator` | double | fator IPCA do ano para R$ de dez/2025 |
| `valor_total_nominal / valor_total_real` | double | valor da linha em R$ nominais e em R$ de dez/2025 |
| `valor_unitario_real / valor_estimado_real` | double | valor unitário e estimado em R$ de dez/2025 |
| `preco_outlier` | bool | preço unitário fora de [p1, p99] do item (sinaliza, não remove) |

<!-- FIM:COLUNAS-DERIVADAS -->
