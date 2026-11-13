"""Testes da camada tratada (T07): contrato pandera + asserções de regra.

Requisito A4: ≥ 15 asserções cobrindo tipos, domínios, datas, CNPJ amostral e não-negatividade.
Os testes leem apenas as colunas necessárias do parquet para não inflar memória.
"""

from __future__ import annotations

import re

import pandas as pd
import pandera as pa
import pytest
from pandera import Check, Column, DataFrameSchema

from nicho_bahia import paths
from nicho_bahia.config import load_config

# colunas carregadas do parquet tratado
COLS = [
    "linha_id",
    "data",
    "ano",
    "mes",
    "ano_mes",
    "tipo_do_item",
    "familia_catalogo",
    "familia_key",
    "nome_basico",
    "item_key",
    "um",
    "valor_total_nominal",
    "valor_total_real",
    "valor_unitario_nominal",
    "valor_unitario_real",
    "valor_estimado_nominal",
    "deflator",
    "cnpj",
    "cnpj14",
    "is_pf",
    "fornecedor_id",
    "canal",
    "is_dispensa",
    "is_dispensa_eletronica",
    "is_pce",
    "is_regulado",
    "is_pandemia",
    "preco_outlier",
    "prazo_entrega_dias",
    "regiao_raio",
    "qtd_contratada",
    "afm_aps",
]


@pytest.fixture(scope="session")
def df() -> pd.DataFrame:
    if not paths.TREATED_PARQUET.exists():
        pytest.skip(f"parquet tratado ausente: {paths.TREATED_PARQUET}")
    d = pd.read_parquet(paths.TREATED_PARQUET, columns=COLS)
    # o parquet guarda DATE (date32); pandas entrega datetime.date -> converte para datetime64
    d["data"] = pd.to_datetime(d["data"])
    return d


@pytest.fixture(scope="session")
def cfg():  # noqa: ANN201
    return load_config()


# ---------------------------------------------------------------------------------
# Contrato de esquema (pandera)
# ---------------------------------------------------------------------------------
SCHEMA = DataFrameSchema(
    {
        "linha_id": Column(str, nullable=False, unique=True),
        "data": Column(pa.DateTime, nullable=False),
        "ano": Column("int64", Check.isin([2021, 2022, 2023, 2024, 2025])),
        "mes": Column("int64", Check.in_range(1, 12)),
        "ano_mes": Column(str, Check.str_matches(r"^\d{4}-\d{2}$")),
        "tipo_do_item": Column(str, Check.isin(["Material", "MATERIAL", "material"])),
        "valor_total_nominal": Column(float, Check.ge(0)),
        "valor_total_real": Column(float, Check.ge(0)),
        "deflator": Column(float, Check.gt(0)),
        "is_regulado": Column("bool"),
        "is_pandemia": Column("bool"),
        "is_pf": Column("bool"),
        "preco_outlier": Column("bool"),
        "canal": Column(str, nullable=False),
        "familia_key": Column(str, nullable=False),
        "item_key": Column(str, nullable=False),
    },
    strict=False,
    coerce=False,
)


def test_schema_pandera(df: pd.DataFrame) -> None:
    """A4-01: o DataFrame respeita o contrato de tipos e domínios."""
    SCHEMA.validate(df, lazy=True)


def test_contagem_de_linhas(df: pd.DataFrame) -> None:
    """A4-02: o escopo tratado tem exatamente 560.934 linhas (E4 do log de conservação)."""
    assert len(df) == 560_934


def test_data_e_ano_coerentes(df: pd.DataFrame) -> None:
    """A4-03: ano e mês derivam da data, sem divergência."""
    assert (df["data"].dt.year == df["ano"]).all()
    assert (df["data"].dt.month == df["mes"]).all()


def test_sem_nulos_estruturais(df: pd.DataFrame) -> None:
    """A4-04: chaves e valor real não podem ser nulos."""
    for col in ("linha_id", "data", "familia_key", "item_key", "valor_total_real", "deflator"):
        assert df[col].notna().all(), f"{col} tem nulos"


def test_nao_negatividade(df: pd.DataFrame) -> None:
    """A4-05: valores totais (nominal e real) nunca negativos no escopo tratado."""
    assert (df["valor_total_nominal"] >= 0).all()
    assert (df["valor_total_real"] >= 0).all()


def test_qtd_positiva(df: pd.DataFrame) -> None:
    """A4-06: quantidade contratada sempre positiva em material."""
    assert (df["qtd_contratada"] > 0).all()


def test_deflator_por_ano_confere_com_config(df: pd.DataFrame, cfg) -> None:  # noqa: ANN001
    """A4-07: cada ano tem exatamente um deflator, igual ao calculado a partir do config."""
    do_config = cfg.get("deflacao.ipca_ano_pct")
    por_ano = df.groupby("ano")["deflator"].nunique()
    assert (por_ano == 1).all(), f"mais de um deflator no mesmo ano: {por_ano.to_dict()}"
    fatores = df.groupby("ano")["deflator"].first().to_dict()
    # na convenção inicio_ano, a razão entre anos consecutivos é (1 + IPCA do ano mais antigo)
    for ano in (2021, 2022, 2023, 2024):
        razao = fatores[ano] / fatores[ano + 1]
        esperado = 1.0 + float(do_config[ano]) / 100.0
        assert razao == pytest.approx(esperado, rel=1e-6), f"razão {ano}/{ano + 1} incorreta"


def test_valor_real_eh_nominal_vezes_deflator(df: pd.DataFrame) -> None:
    """A4-08: valor_total_real = valor_total_nominal × deflator (tolerância de arredondamento)."""
    esperado = df["valor_total_nominal"] * df["deflator"]
    diff = (df["valor_total_real"] - esperado).abs()
    assert diff.max() <= 0.011, f"maior desvio: {diff.max()}"


def test_soma_nominal_reconcilia_com_staging(df: pd.DataFrame) -> None:
    """A4-09: Σ valor nominal fecha com o valor do escopo material (0,00% de desvio)."""
    assert df["valor_total_nominal"].sum() == pytest.approx(12_597_609_650.96, rel=1e-9)


def test_item_key_bem_formada(df: pd.DataFrame) -> None:
    """A4-10: item_key = familia_key|nome_key|um_key (dois separadores)."""
    assert (df["item_key"].str.count(r"\|") == 2).all()


def test_familia_key_sem_acento(df: pd.DataFrame) -> None:
    """A4-11: chaves normalizadas não contêm acento nem minúscula."""
    keys = df["familia_key"].dropna().unique()
    acento = re.compile(r"[ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç]")
    assert not any(acento.search(k) for k in keys)
    assert all(k == k.upper() for k in keys)


def test_canal_no_dominio(df: pd.DataFrame, cfg) -> None:  # noqa: ANN001
    """A4-12: canal pertence ao conjunto mapeado no config (+ 'outros')."""
    permitidos = set(cfg.get("dispensa.mapa_canal").values()) | {"outros"}
    assert set(df["canal"].unique()) <= permitidos


def test_pce_implica_dispensa_eletronica(df: pd.DataFrame) -> None:
    """A4-13: PCE preenchido só ocorre em dispensa eletrônica (validado em F1)."""
    com_pce = df[df["is_pce"]]
    assert com_pce["is_dispensa_eletronica"].all()


def test_is_pf_e_cnpj14_exclusivos(df: pd.DataFrame) -> None:
    """A4-14: pessoa física não tem cnpj14; cnpj14 só existe com 14 dígitos."""
    pf = df[df["is_pf"]]
    assert pf["cnpj14"].isna().all()
    com_cnpj = df[df["cnpj14"].notna()]
    assert com_cnpj["cnpj14"].str.len().eq(14).all()
    assert not com_cnpj["is_pf"].any()


def test_cnpj_amostral_dv_valido(df: pd.DataFrame) -> None:
    """A4-15: amostra de 500 CNPJs distintos do parquet tem DV válido."""
    from nicho_bahia.textops import validar_cnpj

    amostra = df["cnpj14"].dropna().drop_duplicates().head(500).tolist()
    assert len(amostra) > 0
    invalidos = [c for c in amostra if not validar_cnpj(c)]
    assert invalidos == [], f"{len(invalidos)} CNPJs com DV inválido na amostra"


def test_prazo_dentro_do_limite(df: pd.DataFrame, cfg) -> None:  # noqa: ANN001
    """A4-16: prazo de entrega nunca excede o limite configurado (cauda vira nulo)."""
    limite = int(cfg.get("logistica.prazo_maximo_valido_dias"))
    validos = df["prazo_entrega_dias"].dropna()
    assert validos.min() >= 0
    assert validos.max() <= limite


def test_regiao_raio_no_dominio(df: pd.DataFrame) -> None:
    """A4-17: classificação do raio pertence a {dentro, fora, indefinida}."""
    assert set(df["regiao_raio"].dropna().unique()) <= {"dentro", "fora", "indefinida"}


def test_regulados_por_familia(df: pd.DataFrame, cfg) -> None:  # noqa: ANN001
    """A4-18: toda linha das famílias reguladas do config está marcada como is_regulado."""
    prefixos = tuple(str(f).upper() for f in cfg.get("regulados.familias"))
    sel = df["familia_key"].str.startswith(prefixos)
    sub = df[sel]
    assert len(sub) > 0, "nenhuma linha das famílias reguladas — config ou dado inconsistente"
    assert sub["is_regulado"].all()


def test_linha_id_unica(df: pd.DataFrame) -> None:
    """A4-19: a chave técnica é única em 100% (A3)."""
    assert df["linha_id"].is_unique


def test_material_apenas(df: pd.DataFrame) -> None:
    """A4-20: a camada tratada contém apenas material (escopo aprovado no G1)."""
    assert df["tipo_do_item"].str.upper().eq("MATERIAL").all()
