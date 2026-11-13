"""Esquema canônico da base SIMPAS (Volume de Compras) e mapeamento dos arquivos brutos.

Estratégia de mapeamento (validada em F0 — ver DATA_PROFILE.md):
1. O cabeçalho de cada planilha é lido e normalizado (caixa alta, sem acento, espaços
   colapsados).
2. Cada rótulo é resolvido via tabela de aliases -> nome canônico snake_case.
3. Cabeçalhos em branco são resolvidos por OVERRIDE POSICIONAL explícito, por arquivo,
   declarado em POSITIONAL_OVERRIDES. Nenhum override é silencioso: a etapa de ingestão
   grava em log qual coluna foi mapeada por posição.
4. Colunas não resolvidas são descartadas e listadas no log (não há descarte silencioso).

Fatos observados em F0 (2026-11):
- 2021: 77 colunas, SEM a coluna "FORNECEDOR" (todas as colunas a partir do índice 26
  deslocadas em -1). Cabeçalhos em branco nos índices 19, 36, 70 e 76.
  Índice 19 = VALOR TOTAL (dados numéricos presentes; QTD x UNIT confere)
  Índice 36 = Assinatura da AFM/APS (posicional: sucede DATA GERAÇÃO)
  Índice 70 = ORGAO GERENCIADOR DO RP (posicional: 2025 índice 71)
  Índice 76 = coluna extra em branco, sem dados -> descartada
- 2022: 78 colunas = esquema de 77 + 1 coluna final em branco -> descartada
- 2023/2024/2025: 77 colunas, esquema idêntico
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Final, Literal

Kind = Literal["text", "num", "int", "date"]


def norm_header(raw: str) -> str:
    """Normaliza rótulo de cabeçalho: sem acento, caixa alta, espaços colapsados."""
    s = unicodedata.normalize("NFKD", str(raw))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("\u00a0", " ").replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip().upper()


@dataclass(frozen=True, slots=True)
class Column:
    name: str            # nome canônico snake_case
    kind: Kind           # tipo no parquet de staging
    label: str           # rótulo original (como aparece na planilha, sem espaços extras)
    description: str     # semântica de trabalho (validar em F1)


# Ordem canônica = ordem das colunas nas planilhas 2023-2025 (77 colunas).
CANONICAL: Final[tuple[Column, ...]] = (
    Column("cod_secretaria", "int", "COD. SECRETARIA", "Código da secretaria/órgão (dígito)."),
    Column("secretaria", "text", "SECRETARIA", "Nome do órgão: 'NN - NOME'."),
    Column("unidade", "text", "UNIDADE", "Unidade orçamentária: 'NN.NNN - NOME'."),
    Column("uo_fiplan", "text", "UO FIPLAN", "Código UO FIPLAN + descrição."),
    Column("ug_fiplan", "text", "UG FIPLAN", "Código UG FIPLAN + descrição."),
    Column("tipo_fornecimento", "text", "TIPO FORNECIMENTO", "AFM (material) ou APS (serviço/prestação)."),
    Column("grupo_licitacao", "text", "GRUPO LICITAÇÃO", "Grupo de licitação (rubrica de compra)."),
    Column("grupo_catalogo", "text", "GRUPO CATÁLOGO", "Nível 1 da hierarquia de catálogo."),
    Column("familia_catalogo", "text", "FAMILIA CATÁLOGO", "Nível 2 da hierarquia (família de material/serviço)."),
    Column("codigo", "text", "CÓDIGO", "Código do item de catálogo (com DV)."),
    Column("nome_basico", "text", "Nome Básico", "Nome básico do item (nível 3)."),
    Column("item", "text", "ITEM", "Descrição/ especificação do item (nível 4)."),
    Column("tipo_item_especifico_comum", "text", "TIPO ITEM (ESPECIFICO/COMUM)", "Item específico ou comum."),
    Column("um", "text", "UM", "Unidade de medida."),
    Column("tipo_do_item", "text", "TIPO DO ITEM", "Material / Serviço / (outros)."),
    Column("qtd_contratada", "num", "QTD CONTRATADA", "Quantidade contratada na linha."),
    Column("tipo_calculo", "text", "Tipo_Calculo", "Campo auxiliar de cálculo (majoritariamente vazio)."),
    Column("valor_detalhe", "num", "VALOR DETALHE", "Campo auxiliar de valor (majoritariamente vazio)."),
    Column("valor_unitario", "num", "VALOR UNITÁRIO", "Valor unitário contratado."),
    Column("valor_total", "num", "VALOR TOTAL", "Valor total da linha (QTD x UNIT)."),
    Column("cnpj", "text", "CNPJ", "CNPJ do fornecedor (com máscara)."),
    Column("cnae_codigo", "int", "cnae_codigo", "CNAE do fornecedor (Receita)."),
    Column("cnae_descricao", "text", "cnae_descricao", "Descrição do CNAE."),
    Column("uf_receita", "text", "uf_receita", "UF do fornecedor na Receita."),
    Column("razao_social", "text", "razao_social", "Razão social (Receita)."),
    Column("nome_fantasia", "text", "nome_fantasia", "Nome fantasia (Receita)."),
    Column("fornecedor", "text", "FORNECEDOR", "Fornecedor conforme cadastro FIPLAN. AUSENTE em 2021."),
    Column("categoria", "text", "CATEGORIA", "Porte do fornecedor (ME/EPP/MEDIO/NO...)."),
    Column("situacao_fornecedor", "text", "SITUAÇÃO FORNECEDOR", "Situação cadastral do fornecedor."),
    Column("uf_fornecedor", "text", "UF FORNECEDOR", "UF do fornecedor (FIPLAN)."),
    Column("forma_contratacao", "text", "FORMA DE CONTRATAÇÃO", "Modalidade/instrumento (Registro de Preços, Dispensa...)."),
    Column("n_licitacao", "text", "Nº LICITAÇÃO", "Número da licitação de origem."),
    Column("requisicao_rm_rs", "text", "Requisição de Material - RM/Requisição de Serviços -RS", "Número da requisição (RM/RS)."),
    Column("dotacao", "text", "Dotacao", "Dotação orçamentária."),
    Column("afm_aps", "text", "AFM/APS", "Código da AFM (material) ou APS (serviço)."),
    Column("afm_aps_tipo_item", "text", "AFM/APS_TIPO ITEM", "Rótulo composto 'tipo - número'."),
    Column("data_geracao_afm_aps", "date", "DATA GERAÇÃO da AFM/APS", "Eixo temporal principal (data de geração)."),
    Column("assinatura_afm_aps", "date", "Assinatura da AFM/APS", "Data de assinatura/empenho. Vazio em 2021."),
    Column("cod_local_entrega", "text", "Código Local de Entrega/Execução da AFM/APS", "Código do local de entrega."),
    Column("endereco_local_entrega", "text", "Endereço Local de Entrega/Execução da AFM/APS", "Endereço de entrega."),
    Column("bairro_local_entrega", "text", "Bairro Local de Entrega/Execução da AFM/APS", "Bairro de entrega."),
    Column("municipio_local_entrega", "text", "Município Local de Entrega/Execução da AFM/APS", "Município de entrega."),
    Column("uf_local_entrega", "text", "UF Local de Entrega/Execução da AFM/APS", "UF de entrega."),
    Column("srd_fiplan", "text", "SRD (FIPLAN)", "Sigla interna FIPLAN (a inferir por coocorrência)."),
    Column("lid_fiplan", "text", "LID (FIPLAN)", "Sigla interna FIPLAN (a inferir por coocorrência)."),
    Column("pce_pedido_cotacao", "text", "PCE - Pedido de Cotação Eletrônica", "Pedido de Cotação Eletrônica (proxy do canal dispensa)."),
    Column("valor_estimado", "num", "VALOR ESTIMADO", "Valor de referência da cotação. ATENÇÃO: aparenta ser unitário, não total."),
    Column("regiao_principal_municipio", "text", "Regiao_Principal_Município", "Região de planejamento do município principal."),
    Column("digitalizacao_contrato", "text", "Digitalização de Contrato", "Indicador Sim/Não."),
    Column("classificacao_familia", "text", "CLASSIFICAÇÃO FAMÍLIA", "Classificação da família (Outros, Materiais...)."),
    Column("regiao_registro_precos", "text", "REGIAO_Registro_Precos", "Região do registro de preços."),
    Column("marcacao_covid", "text", "MARCAÇÃO COVID-19", "Flag COVID (Sim/Não)."),
    Column("liberacao_covid", "text", "LIBERAÇÃO COVID-19", "Flag liberação COVID."),
    Column("marcacao_vacina_covid", "text", "MARCAÇÃO VACINA COVID-19", "Flag vacina COVID."),
    Column("liberacao_vacina_covid", "text", "LIBERAÇÃO VACINA COVID-19", "Flag liberação vacina COVID."),
    Column("situacao_fornecedor_lid", "text", "Situação do Fornecedor na Geração LID", "Situação do fornecedor quando da geração do LID."),
    Column("modulo_servicos_terceirizados", "text", "MODULO SERVIÇOS TERCEIRIZADOS", "Indicador do módulo de terceirizados."),
    Column("instrumento", "text", "INSTRUMENTO", "Instrumento (Contrato/Ata/...)."),
    Column("contrato_emergencial_cgst", "text", "Contrato_Emergencial_Cgst", "Flag contrato emergencial (CGE/ST)."),
    Column("situacao_contrato_cgst", "text", "Situacao_Contrato_Cgst", "Situação do contrato no CGE/ST."),
    Column("unidade_licitante", "text", "UNIDADE LICITANTE", "Unidade licitante."),
    Column("tipo_da_requisicao", "text", "TIPO DA REQUISIÇÃO", "Tipo da requisição (RM/RS)."),
    Column("delegacao_automatica", "text", "DELEGAÇÃO AUTOMATICA", "Indicador de delegação automática."),
    Column("ano_geracao_afm_aps", "int", "ANO GERAÇÃO da AFM/APS", "Ano de geração (fallback do eixo temporal)."),
    Column("mes_geracao_afm_aps", "int", "MES GERAÇÃO da AFM/APS", "Mês de geração (fallback do eixo temporal)."),
    Column("regiao_local_entrega", "text", "Região do Local de Entrega", "Região de planejamento do local de entrega."),
    Column("n_processo", "text", "Nº PROCESSO", "Número do processo administrativo."),
    Column("n_contrato", "text", "Nº CONTRATO", "Número do contrato."),
    Column("prazo_entrega", "text", "PRAZO DE ENTREGA", "Prazo de entrega (texto/numérico - a classificar em F1)."),
    Column("orgao_gerenciador_registro_precos", "text", "ORGAO GERENCIADOR DO Registro de Preços", "Órgão gerenciador do RP (coluna 1)."),
    Column("ressuprimento", "text", "RESSUPRIMENTO", "Indicador de ressuprimento. AUSENTE em 2021."),
    Column("orgao_gerenciador_rp", "text", "ORGAO GERENCIADOR DO RP", "Órgão gerenciador do RP (coluna 2)."),
    Column("data_fim_contrato", "date", "DATA FIM CONTRATO", "Data fim da vigência."),
    Column("ano_fim_contrato", "int", "ANO FIM CONTRATO", "Ano fim da vigência."),
    Column("aviso_edital_pncp", "text", "Aviso/Edital PNCP", "Link do aviso/edital no PNCP (enriquecimento futuro)."),
    Column("ata_rp_pncp", "text", "Ata RP PNCP", "Link da ata de RP no PNCP."),
    Column("contratos_pncp", "text", "Contratos PNCP", "Link do contrato no PNCP."),
)

CANONICAL_NAMES: Final[tuple[str, ...]] = tuple(c.name for c in CANONICAL)
KIND_BY_NAME: Final[dict[str, Kind]] = {c.name: c.kind for c in CANONICAL}
LABEL_BY_NAME: Final[dict[str, str]] = {c.name: c.label for c in CANONICAL}

# --- aliases: rótulo normalizado -> nome canônico --------------------------------
_ALIASES: dict[str, str] = {norm_header(c.label): c.name for c in CANONICAL}
# variações observadas / previsíveis
_ALIASES.update(
    {
        norm_header("Nº  PROCESSO"): "n_processo",
        norm_header("Nº PROCESSO"): "n_processo",
        norm_header("DATA GERACAO DA AFM/APS"): "data_geracao_afm_aps",
        norm_header("TIPO ITEM (ESPECIFICO/COMUM)"): "tipo_item_especifico_comum",
        norm_header("ORGAO GERENCIADOR DO REGISTRO DE PRECOS"): "orgao_gerenciador_registro_precos",
        norm_header("ORGAO GERENCIADOR DO RP"): "orgao_gerenciador_rp",
        norm_header("CONTRATO_EMERGENCIAL_CGST"): "contrato_emergencial_cgst",
        norm_header("SITUACAO_CONTRATO_CGST"): "situacao_contrato_cgst",
        norm_header("REGIAO_REGISTRO_PRECOS"): "regiao_registro_precos",
        norm_header("REGIAO_PRINCIPAL_MUNICIPIO"): "regiao_principal_municipio",
        norm_header("TIPO_CALCULO"): "tipo_calculo",
        norm_header("CLASSIFICACAO FAMILIA"): "classificacao_familia",
        norm_header("MARCAÇÃO VACINA COVID-19"): "marcacao_vacina_covid",
    }
)
ALIASES: Final[dict[str, str]] = _ALIASES


@dataclass(frozen=True, slots=True)
class RawFile:
    """Descritor de um arquivo bruto e de suas particularidades de esquema."""

    year: int
    filename: str
    # índice da coluna (0-based) -> nome canônico, para cabeçalhos em branco
    positional_overrides: tuple[tuple[int, str], ...] = ()


RAW_FILES: Final[tuple[RawFile, ...]] = (
    RawFile(2021, "SIMPAS_VOLUME_DE_COMPRAS_GERAL_2021.xlsx", ((19, "valor_total"), (36, "assinatura_afm_aps"), (70, "orgao_gerenciador_rp"))),
    RawFile(2022, "SIMPAS_VOLUME_DE_COMPRAS_GERAL_2022.xlsx"),
    RawFile(2023, "SIMPAS_VOLUME_DE_COMPRAS_GERAL_2023 1.xlsx"),
    RawFile(2024, "SIMPAS_VOLUME_DE_COMPRAS_GERAL_2024 2.xlsx"),
    RawFile(2025, "SIMPAS_VOLUME_DE_COMPRAS_ANO_2025 1 (1).xlsx"),
)


def resolve_header(header: list[str], raw: RawFile) -> tuple[list[str | None], list[dict[str, object]]]:
    """Resolve cada posição do cabeçalho em um nome canônico (ou None).

    Retorna (mapping, events) onde events registra como cada coluna foi resolvida
    (alias, override posicional, descartada) para ser gravado no log.
    """
    overrides = dict(raw.positional_overrides)
    mapping: list[str | None] = []
    events: list[dict[str, object]] = []
    seen: dict[str, int] = {}

    for idx, raw_label in enumerate(header):
        key = norm_header(raw_label)
        canon: str | None = None
        how = "blank"
        if key in ALIASES:
            canon = ALIASES[key]
            how = "alias"
        elif idx in overrides:
            canon = overrides[idx]
            how = "posicional"
        elif key == "":
            canon = None
            how = "descartada_vazia"
        else:
            canon = None
            how = "descartada_desconhecida"

        if canon is not None:
            if canon in seen:
                raise ValueError(
                    f"{raw.filename}: coluna canônica duplicada {canon!r} nos índices "
                    f"{seen[canon]} e {idx} (rótulos {header[seen[canon]]!r} e {raw_label!r})"
                )
            seen[canon] = idx
        mapping.append(canon)
        events.append(
            {
                "index": idx,
                "raw_label": str(raw_label),
                "canonical": canon,
                "resolved_by": how,
            }
        )
    return mapping, events
