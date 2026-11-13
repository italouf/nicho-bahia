# SPEC.md — especificação do projeto nicho-bahia

Versão 1.0 · 2026-11-12 · derivada do Gate G1 (aprovado) · insumo do Gate G2

---

## 1. Objetivo

Escolher **1 a 3 nichos de material** (`FAMILIA CATÁLOGO`) para o primeiro ataque comercial de uma
startup baiana de 3 sócios, com CAPEX limitado, sem atestados técnicos e base em Feira de Santana.
Para cada nicho escolhido a entrega é: itens-âncora, órgãos-alvo, regiões, calendário de ataque,
faixa de preço praticada, riscos e critérios de abandono.

O painel responde Q1–Q8 da missão (§9) e cada gráfico existe para responder uma dessas perguntas.

## 2. Contrato de camadas

```
XLSX brutos (somente leitura)
   └─ staging  data/_meta/staging/raw_<ano>.parquet    872.257 linhas, 4 + 77 colunas
        └─ treated   data/treated/compras_tratadas.parquet
             └─ aggregates data/aggregates/*.parquet
                  └─ panel_data.json  (único insumo do painel)
                       └─ output/painel_decisao.html
```

Regra bloqueante: **o painel lê exclusivamente `panel_data.json`**. Nenhum acesso a parquet, XLSX ou
rede a partir do HTML. Nenhuma visualização é construída antes dos gates G3 e G4 verdes.

## 3. Camada tratada — colunas derivadas

Além das 77 colunas de staging (todas preservadas), a tabela tratada cria:

| Coluna | Tipo | Regra |
|---|---|---|
| `linha_id` | text | `_src_year + ':' + _src_row` — chave técnica única da linha |
| `data` | date | `data_geracao_afm_aps` (nunca nula após filtro de escopo) |
| `ano`, `mes` | int | extraídos de `data` |
| `ano_mes` | text | `YYYY-MM` |
| `valor_total_nominal` | double | `valor_total` |
| `valor_total_real` | double | `valor_total × deflator(ano)` (§4) |
| `valor_unitario_real` | double | `valor_unitario × deflator(ano)` |
| `valor_estimado_real` | double | `valor_estimado × deflator(ano)` |
| `is_material` | bool | `tipo_do_item IN ('Material','MATERIAL')` |
| `is_pandemia` | bool | qualquer flag COVID = `Sim` **ou** `contrato_emergencial_cgst = 'Sim'` |
| `is_regulado` | bool | regra de §5.2 (lista editável em `config.yaml`) |
| `is_pf` | bool | identificador (só dígitos) com 11 dígitos = pessoa física |
| `cnpj14` | text | 14 dígitos extraídos de `cnpj`; nulo se não tiver 14 dígitos |
| `fornecedor_id` | text | `cnpj14` quando existir; senão `PF:<11 dígitos>`; senão `INVALIDO:<valor>` |
| `canal` | text | normalização de `forma_contratacao` (§5.3) |
| `is_dispensa` | bool | `canal IN ('dispensa_eletronica','dispensa_tradicional')` |
| `is_dispensa_eletronica` | bool | `canal = 'dispensa_eletronica'` |
| `is_pce` | bool | `pce_pedido_cotacao` não vazio |
| `is_via_ata` | bool | `canal = 'registro_precos'` (compra via ata de RP) |
| `familia_key` | text | `familia_catalogo` em caixa alta sem acento, espaços colapsados |
| `grupo_key` | text | idem para `grupo_catalogo` |
| `item_key` | text | `familia_key + '|' + norm(nome_basico) + '|' + norm(um)` |
| `nome_key` | text | `familia_key + '|' + norm(nome_basico)` |
| `secretaria_key`, `ug_key`, `municipio_key`, `regiao_key` | text | normalização de caixa/acento |
| `regiao_key` tem também `regiao_raio` | text | `dentro`/`fora` do raio de 200 km (§5.4) |
| `prazo_entrega_dias` | int | inteiro de `prazo_entrega`; `NULL` se > 365 (cauda inválida) |
| `preco_outlier` | bool | `valor_unitario_real` fora de [p1, p99] do seu `item_key` |

Normalizações de texto: `NFKD` sem acentos → caixa alta → espaços colapsados → `trim`.
A tabela tratada mantém também as colunas originais em texto (para drill-down e prova).

## 4. Deflação (R$ de dez/2025)

```
deflator(ano) = Π_{y = ano..2025} (1 + ipca_y/100)
```

IPCA (% a.a.): 2021 = 10,06 · 2022 = 5,79 · 2023 = 4,62 · 2024 = 4,83 · 2025 = 4,26
(`config.yaml → deflacao.ipca_ano_pct`, editável).

Convenção `inicio_ano` (padrão): o valor anual é tratado como preço de início do ano e inflado até
dez/2025 — por isso o IPCA de 2025 entra no deflator. Alternativas implementadas e selecionáveis:
`fim_ano` (não usa o IPCA do próprio ano) e `meio_ano` (usa metade do IPCA do ano). A escolha muda o
nível dos valores, não a ordenação das famílias; o efeito é reportado em `logs/`.

**Limitação declarada**: granularidade anual, não mensal.

## 5. Filtros de escopo e conservação

### 5.1 Pipeline de exclusão (ordem fixa, cada passo logado)

| # | Passo | Critério | Esperado |
|---|---|---|---|
| E0 | Bruto | todas as linhas de staging | 872.257 |
| E1 | Fora de escopo | `is_material = false` (serviços/APS) | −311.319 |
| E2 | Rodapé | `tipo_do_item IS NULL` (4 linhas de observação) | −4 |
| E3 | Sem data | `data_geracao_afm_aps IS NULL` | 0 |
| E4 | **Escopo tratado** | material com data e valor | **560.934** |
| E5 | **Escopo analítico** | dentro de E4, `NOT is_regulado AND NOT is_pandemia` | **352.537** |

E1 e E2 são contados separadamente porque `NOT (NULL IN (...))` é `NULL` em SQL: as 4 linhas de
rodapé não têm `tipo_do_item`, então não entram na contagem de serviço. Somadas, E1 + E2 = 311.323.

Cada passo grava: linhas antes/depois, Δ de `Σ VALOR TOTAL` e motivo. Reconciliação obrigatória:
`Σ valor_total` do escopo tratado vs. bruto filtrado, tolerância **0,1%** (A2). Observado:
diferença R$ 0,00 (0,000000%).

### 5.2 `is_regulado` (lista EVITAR) — decisão do G1/Q3

Marcado como regulado **por família**:
`65.01` (medicamentos p/ ação judicial), `65.02` (medicamentos e correlatos), `65.05` (drogas,
produtos biológicos e reagentes), `65.50` (OPME), `13.05` (munições e explosivos).

Marcado **por keyword** em `familia_catalogo`/`nome_basico`/`item`: medicamento, vacina, hemoderivado,
hemoterápico, imunobiológico, reagente biológico, munição, explosivo, combustível, gasolina, óleo
diesel, etanol, perecível, hortifruti, carne, leite, pão, refeição, água mineral, oxigênio medicinal.

**Famílias de saúde que permanecem como OPORTUNIDADE** (com risco sinalizado, não excluídas):
`65.15` instrumentos e suprimentos médicos, `65.30` mobiliário hospitalar, `65.32` vestuário
hospitalar/cirúrgico, `66.40` materiais e equipamentos de laboratório.

### 5.3 Normalização de canal (`FORMA DE CONTRATAÇÃO`)

| Rótulo original | `canal` |
|---|---|
| `E - Dispensa Eletrônica` | `dispensa_eletronica` |
| `D - Dispensa Tradicional` | `dispensa_tradicional` |
| `Registro de Preços` | `registro_precos` (compra via ata) |
| `W - Adesão Registro de Preços` | `adesao_rp` |
| `C - Licitação`, `Y - Licitação Lei Fed 13.303/16`, `F - RDC` | `licitacao` |
| `I - Inexigibilidade`, `Q - Contratação Direta`, `P - Comparação de Preço` | `contratacao_direta` |
| `N - Credenciamento` | `credenciamento` |
| `T - Termo Aditivo`, `U - Apostila`, `L - Alteração de Fornecedor` | `alteracao` |
| demais / vazio | `outros` |

`share_dispensa` = valor de `canal ∈ {dispensa_eletronica, dispensa_tradicional}` / valor total.
`share_pce` = valor com `is_pce` / valor total.

### 5.4 Raio logístico (decisão G1/Q4)

`dentro` = `{Região Metropolitana de Salvador, Região Feira de Santana,
Região Alagoinhas e Serrinha, Região SAJesus, Amargosa, Valença, SAmaro}` (após normalização de
rótulo). Demais regiões = `fora`. Configurável em `config.yaml → logistica.regioes_prioritarias`.

## 6. Métricas (fórmulas exatas)

Todas as métricas por **família** (nível 1), com drill para **nome_base** e **item_key**.
Universo de ranqueamento (decisão G1/Q5): família com `n_afm ≥ 30` **e** `valor_total_real ≥ 1.000.000`
no período. As demais não são ranqueadas e aparecem com motivo "massa crítica insuficiente".

### 6.1 Demanda
- `valor_ano_real[a]` = Σ `valor_total_real` das linhas com `ano = a`
- `valor_ano_nominal[a]` = Σ `valor_total_nominal`
- `afm_ano[a]` = `COUNT(DISTINCT afm_aps)` com `ano = a`
- `ug_ano[a]` = `COUNT(DISTINCT ug_fiplan)` (nulo vira `ug_key` do órgão)
- `valor_2024_2025_real` = média dos `valor_ano_real` de 2024 e 2025 → **entrada do score**

### 6.2 Tendência
- `cagr_real` = `(valor_ano_real[2025] / valor_ano_real[2021])^(1/4) − 1`, se ambos > 0; senão `NULL`
  e a família é sinalizada como "série incompleta".
- `yoy[a]` = `valor_ano_real[a] / valor_ano_real[a−1] − 1`
- `dir_2_ultimos` = `+1` se `yoy[2024] > 0` **e** `yoy[2025] > 0`; `−1` se ambos < 0; `0` caso contrário.

### 6.3 Recorrência
- `meses_com_compra` = `COUNT(DISTINCT ano_mes)`; `recorrencia` = `meses_com_compra / 60`
- `intervalo_mediano_entre_compras_dias`: por UG, ordenar as AFM/APS por data e calcular a diferença
  em dias entre compras consecutivas; tomar a mediana das medianas das UGs com ≥ 2 compras.

### 6.4 Fit dispensa
- `ticket_afm_p25/p50/p75` = quantis do valor total **por AFM/APS** (soma das linhas de material da AFM)
- `pct_afm_ate_teto` = `COUNT(afm com valor_afm_real ≤ 65.492,11) / COUNT(afm)`
  (valor em reais de dez/2025; teto único de 2026 — decisão G1/Q2)
- `pct_afm_ate_teto_hist` = mesma conta, mas por ano: valor **nominal** da AFM vs. teto **nominal** do
  ano (`2021-2023: 50.000,00 · 2024: 59.906,02 · 2025: 62.725,59`). Métrica secundária.
- `fit_dispensa_raw` = `0,6 × pct_afm_ate_teto + 0,4 × share_dispensa` (0–1)
- **Limitação declarada**: o teto legal é por contratação/objeto de mesma natureza por UG/ano; o valor
  por AFM/APS é **proxy**.

### 6.5 Concorrência
- `n_fornecedores` = `COUNT(DISTINCT fornecedor_id)` com `is_pf = false` e `cnpj14` válido
- `hhi` = `Σ (share_i × 100)²` em que `share_i` = valor do fornecedor i / valor da família (0–10.000)
- `share_top3` = Σ dos 3 maiores shares
- `pct_valor_uf_nao_ba` = valor de fornecedores com `uf_fornecedor ≠ 'BA'` / valor total
- `novos_entrantes[a]` = fornecedores cuja **primeira aparição na base** é o ano `a`, contados só de
  **2022 em diante** (decisão G1/Q7), dividido pelo total de fornecedores ativos no ano
- `share_me_epp` = valor de `categoria ∈ {ME, EPP, MEI}` / valor total (`AF`, `ES`, `EC`, `NO` ficam fora)

### 6.6 Preço
- Por `item_key` e ano: `preco_mediano_real`, `preco_p25_real`, `preco_p75_real`, `n_linhas`
- `cv_preco` = desvio-padrão / média do preço real do item, ponderado; agregado da família = mediana
  dos CVs dos itens com `n_linhas ≥ 20`
- `tendencia_preco` = `(preco_mediano_real[2025] / preco_mediano_real[2021])^(1/4) − 1`
- `desconto_vs_estimado` = `1 − valor_unitario / valor_estimado` (por linha, quando
  `valor_estimado > 0`); reportar mediana por família
- Winsorização p1/p99 **apenas** nas estatísticas de preço; as linhas não são removidas.

### 6.7 Compradores
- `top_ug` / `top_secretaria` por valor real, com `share_dispensa` de cada um
- `concentracao_comprador` = share do maior comprador (UG) no valor da família

### 6.8 Logística
- `pct_valor_no_raio` = valor entregue em `regiao_raio = 'dentro'` / valor total
- `prazo_mediano_dias`, `pct_prazo_ate_30d` (sobre linhas com prazo válido)
- `n_municipios_entrega`

### 6.9 Sazonalidade
- `indice_mes[m]` = `média(valor_real do mês m em 2021..2025) / média(geral dos 60 meses)`
- `meses_pico` = meses com `indice_mes ≥ 1,2`

## 7. Modelo de score (0–100)

### 7.1 Normalização
Cada dimensão é convertida em **percentil** (0–100) entre as famílias elegíveis (massa crítica).
Empates recebem o **posto máximo** (`method='max'`), para que o melhor da dimensão receba 100 —
com o posto médio, famílias empatadas em 60/60 meses ficavam em 84,5 e a dimensão perdia parte
do seu peso. `NULL` recebe percentil 0 e a família é sinalizada.

### 7.2 Dimensões e pesos (editáveis em `config.yaml → score.pesos`)

| Dimensão | Peso | Variável de entrada | Direção |
|---|---|---|---|
| `demanda` | 20 | `valor_2024_2025_real` | maior é melhor |
| `crescimento` | 15 | `cagr_real` | maior é melhor |
| `recorrencia` | 15 | `recorrencia` (meses com compra / 60) | maior é melhor |
| `fit_dispensa` | 15 | `fit_dispensa_raw` | maior é melhor |
| `fragmentacao` | 15 | `1 − hhi/10000` (com bônus de `n_fornecedores`) | maior é melhor |
| `estabilidade_preco` | 10 | `1 − min(cv_preco, 1)` | maior é melhor |
| `logistica` | 10 | `pct_valor_no_raio` | maior é melhor |

`fragmentacao_raw = 0,7 × (1 − hhi/10000) + 0,3 × percentil(log1p(n_fornecedores))`

```
score_bruto = Σ (peso_dim × percentil_dim) / Σ pesos          # 0..100
```

### 7.3 Penalidades e flags

| Regra | Efeito |
|---|---|
| família com ≥ 50% do valor material em linhas `is_regulado` | **fora do ranking** e na lista **EVITAR**; as linhas reguladas também já estão fora do escopo analítico (E5) |
| família parcialmente regulada (< 50%) | **permanece** no ranking, calculada apenas sobre as linhas não reguladas |
| `dependencia_pandemia` = valor `is_pandemia` / valor total > 30% | `−20` pontos e flag (as linhas de pandemia já estão fora do escopo analítico) |
| `dir_2_ultimos = −1` (queda nos 2 últimos anos) | `−15` pontos e flag |
| `cagr_real IS NULL` (série incompleta) | flag, sem penalidade |
| `n_afm < 30` ou `valor_total_real < 1.000.000` | fora do ranking (motivo declarado) |

`score_final = max(0, score_bruto + penalidades)`. As penalidades são reaplicadas em **todos** os
cenários de sensibilidade — caso contrário os ranks não seriam comparáveis.

### 7.4 Sensibilidade (A11)
Reexecutar o score com cada peso × `(1 ± 0,20)` (14 cenários) e reportar para cada família:
`score_min`, `score_max`, `rank_min`, `rank_max`, `estabilidade` = fração dos cenários em que a
família permanece no top-10. Publicar a matriz no painel (aba 0) e em `nicho_score.csv`.

## 8. Agregados (ids usados no rodapé de cada gráfico)

| id | arquivo | grão | conteúdo |
|---|---|---|---|
| `A01` | `agg_familia_ano.parquet` | família × ano | valor nominal/real, linhas, AFM, UGs, fornecedores |
| `A02` | `agg_familia_periodo.parquet` | família | totais do período, participação, ranking |
| `A03` | `agg_familia_tendencia.parquet` | família | CAGR, YoY, direção, série 2021–2025 |
| `A04` | `agg_familia_metricas.parquet` | família | todas as métricas de §6 |
| `A05` | `agg_sazonalidade.parquet` | família × mês | valor médio, índice mensal |
| `A06` | `agg_orgao_familia.parquet` | secretaria × UG × família × ano | valor, share dispensa |
| `A07` | `agg_canal_familia.parquet` | família × canal × ano | valor, linhas, ticket |
| `A08` | `agg_ticket_afm.parquet` | família | quantis de ticket por AFM, % ≤ teto |
| `A09` | `agg_score.parquet` | família | score, dimensões, penalidades, rank |
| `A10` | `agg_fornecedor_familia.parquet` | família × fornecedor × ano | valor, share, UF, porte, 1ª aparição |
| `A11` | `agg_concorrencia.parquet` | família × ano | HHI, top-3, n fornecedores, entrantes |
| `A12` | `agg_evitar.parquet` | família | motivo da exclusão, evidências |
| `A13` | `agg_sensibilidade.parquet` | família × cenário | score e rank por cenário |
| `A14` | `agg_entrantes.parquet` | família × ano | novos entrantes, base ativa |
| `A15` | `agg_top_fornecedores.parquet` | família × fornecedor | top 10 por valor, share |
| `A16` | `agg_preco_item.parquet` | item_key × ano | mediana, p25, p75, n, CV |
| `A17` | `agg_preco_dispersao.parquet` | família | CV mediano, amplitude, itens analisados |
| `A18` | `agg_desconto.parquet` | família × ano | desconto mediano vs estimado |
| `A19` | `agg_regiao_familia.parquet` | região × família × ano | valor, linhas, raio |
| `A20` | `agg_prazo.parquet` | família | prazo mediano, % ≤ 30 dias, distribuição |
| `A21` | `agg_municipio.parquet` | município × família | valor, linhas, concentração |
| `A22` | `agg_qualidade.parquet` | passo | filtros aplicados, contagens, Δ valor, reconciliação |

`panel_data.json` embute A01–A22 em formato colunar compacto (arrays sem chaves repetidas),
**meta ≤ 8 MB**, com `meta.gerado_em`, `meta.hash_agregados` e `meta.ids` para o rodapé.

## 9. Painel — 8 abas e 16 gráficos

Arquivo único `output/painel_decisao.html`, PT-BR, offline (`file://`), ECharts e JSON embutidos,
≤ 15 MB. Toggle global **nominal/real**. Filtros globais: **ano**, **secretaria**, **região**,
**família**. Cada gráfico tem título-pergunta, unidade, período e id do agregado no rodapé.

| Aba | # | Gráfico | Pergunta que responde | Agregado |
|---|---|---|---|---|
| 0 DECISÃO | 1 | Cards top-5 com score decomposto + tese + riscos + sensibilidade | "Onde atacar primeiro?" | A09, A13 |
| | 2 | Tabela ordenável com export CSV | "Compare os nichos" | A09 |
| | 3 | Lista EVITAR com motivo | "O que evitar?" | A12 |
| 1 MERCADO | 4 | Linhas de gasto real por família (top 10) | Q1 | A01 |
| | 5 | Treemap de participação no período | Q1 | A02 |
| | 6 | Barras de CAGR real por família | Q1 | A03 |
| 2 SAZONALIDADE | 7 | Heatmap família × mês (índice) | Q6 | A05 |
| | 8 | Calendário de ataque (meses-pico por nicho) | Q6 | A05 |
| 3 COMPRADORES & CANAL | 9 | Top 15 órgãos por valor (com share dispensa) | Q5 | A06 |
| | 10 | Mix de modalidade + share dispensa/PCE | Q2 | A07 |
| | 11 | Dispersão ticket por AFM vs. teto de dispensa | Q2 | A08 |
| 4 CONCORRÊNCIA | 12 | Scatter crescimento × HHI (bolha = volume) | Q3 | A11 |
| | 13 | Novos entrantes por ano | Q3 | A14 |
| | 14 | Top fornecedores por família (share) | Q3 | A15 |
| 5 PREÇOS | 15 | Bandas de preço por item-âncora (p25–p75 por ano) | Q7 | A16 |
| | 16 | Dispersão de preço (CV) e desconto vs. estimado | Q7 | A17, A18 |
| 6 LOGÍSTICA | 17 | Valor por região de entrega, destacando o raio | Q5 | A19 |
| | 18 | Distribuição de prazo de entrega | Q5 | A20 |
| | 19 | Concentração por município de entrega | Q5 | A21 |
| 7 MÉTODO | 20 | Filtros aplicados com contagens e reconciliação | Q8 | A22 |
| | 21 | Premissas (ASSUMPTIONS.md) e limitações | — | — |
| | 22 | Dicionário de dados e ids dos agregados | — | — |

Saídas de apoio: `nicho_score.csv`, `top_itens.csv`, `orgaos_alvo.csv`.

### 9.1 Filtros globais — regra "filtra ou declara"

Nenhum filtro pode ser inerte e nenhum gráfico pode exibir um número de outro escopo sem avisar.
Cada gráfico **ou** recalcula com o recorte, **ou** mostra um aviso âmbar e dessaturação,
mantendo os números do escopo completo. A barra de recorte no topo sempre lista o que está ativo.

| Gráfico | ano | secretaria | região | família |
|---|---|---|---|---|
| `c_serie` (A01) | destaca ano | **recorta** | **recorta** | filtra |
| `c_treemap` (A02) | **recorta** | **recorta** | **recorta** | filtra |
| `c_cagr` (A03) | — | **recorta** | **recorta** | filtra |
| `c_orgaos` (A06) | **recorta** | **drill** (top famílias da secretaria) | — | filtra |
| `c_canal` (A07) | **recorta** | — | — | filtra |
| `c_conc` (A11) | **recorta** (HHI do ano) | — | — | destaca |
| `c_ent` (A14) | destaca ano | — | — | filtra |
| `c_regiao` (A19) | **recorta** | — | **drill** (top famílias da região) | filtra |
| `c_heat` / `c_cal` (A05) | — | — | — | filtra |
| `c_ticket` (A08) | período | — | — | filtra |
| `c_forn` (A15), `c_preco` (A16) | período | — | — | filtra |
| `c_cv`, `c_desc`, `c_prazo`, `c_mun` | período | — | — | filtra |
| cards / tabela / `c_sens` | valor do ano | nota (score é global) | nota | filtra/destaca |

"período" = indicador calculado sobre 2021–2025: aviso neutro quando o ano está ativo.
"recorta" = o valor, a participação e (quando aplicável) o CAGR são recalculados no recorte de
`secretaria × família × ano` ou `região × família × ano` (agregados A06 e A19).
"—" = o agregado não tem esse cruzamento; o gráfico é sinalizado e mantém o escopo completo.

O **score não é recalculado** por filtro (depende de HHI, preço e ticket, que não têm recorte por
órgão/região). Isso é dito na barra de recorte e na aba Método.

**Secretaria e região são mutuamente exclusivas**: o agregado não cruza órgão × região, então ao
escolher um o outro é limpo automaticamente (testado em A7d). O ano e a família combinam livremente
com qualquer um dos dois.

## 10. Testes de aceitação

| id | Teste | Como é verificado |
|---|---|---|
| A1 | Reexecução determinística | `run.py --stage all` duas vezes; comparar `sha256` de cada parquet de agregados e do `panel_data.json` (excluindo timestamp) |
| A2 | Reconciliação ≤ 0,1% | `Σ valor_total` tratado vs. bruto filtrado por material; gravação em `agg_qualidade` e `logs/conservacao.log` |
| A3 | Chave primária | `linha_id` única em 100%; e (afm_aps, codigo, item) ≥ 99,9% (99,9439% observado); duplicatas documentadas |
| A4 | pytest + pandera ≥ 15 asserções | tipos, domínios (`ano ∈ 2021..2025`, `valor ≥ 0` exceto 2 linhas sinalizadas), datas, CNPJ amostral (DV), não-negatividade |
| A5 | Score do painel = CSV | comparar `nicho_score.csv` com o objeto embutido no HTML |
| A6 | Zero erros de console | playwright headless em `file://`, captura de `console` e `pageerror` |
| A7 | ≥ 12 gráficos renderizam | contar instâncias ECharts no DOM e verificar `canvas` não vazio; aplicar filtros e conferir mudança |
| A8 | Toggle nominal/real | alternar e comparar valores com os agregados |
| A9 | Aba Método completa | toda linha de `ASSUMPTIONS.md` presente no HTML; todo filtro de E1–E4 com contagem |
| A10 | Arquivo único ≤ 15 MB e zero requests externos | `playwright.on('request')` — só `file://` |
| A11 | Estabilidade top-10 | `agg_sensibilidade` + tabela no painel |
| A12 | Relatório executivo ≤ 2 páginas | `RELATORIO_EXECUTIVO.md` |

## 11. Fora de escopo / riscos

- **Fora de escopo**: serviços (APS); compras municipais; pagamento/adimplência; previsão de demanda;
  enriquecimento por PNCP; análise de fornecedores pessoa física.
- **Riscos**: (a) `nº de UGs` e `secretaria` têm nulos de 35% em UO/UG FIPLAN → fallback pelo campo
  `secretaria`/`unidade`; (b) teto de dispensa é proxy; (c) deflação anual; (d) truncamento à esquerda
  na contagem de entrantes; (e) 2021–2022 com distorção pandêmica.
