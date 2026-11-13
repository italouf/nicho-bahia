"""Testes unitários das normalizações e da deflação (T02/T04).

Cobrem: normalização de texto (acento, espaço, caixa), identificadores (CNPJ/CPF),
validação de DV e as três convenções de deflação.
"""

from __future__ import annotations

import pytest

from nicho_bahia.textops import (
    classificar_documento,
    deflator_fatores,
    normalize_key,
    only_digits,
    validar_cnpj,
)


class TestNormalizeKey:
    def test_remove_acento_e_sobe_caixa(self) -> None:
        assert normalize_key("Região Metropolitana de Salvador") == "REGIAO METROPOLITANA DE SALVADOR"

    def test_cedilha_e_til(self) -> None:
        assert normalize_key("São José da Conceição") == "SAO JOSE DA CONCEICAO"

    def test_colapsa_espacos_e_remove_pontas(self) -> None:
        assert normalize_key("  Região   Feira  de   Santana  ") == "REGIAO FEIRA DE SANTANA"

    def test_nbsp(self) -> None:
        assert normalize_key("A\u00a0B") == "A B"

    def test_none(self) -> None:
        assert normalize_key(None) is None

    def test_vazio(self) -> None:
        assert normalize_key("   ") == ""

    def test_idempotente(self) -> None:
        uma = normalize_key("Região SAJesus, Amargosa,Valença,SAmaro")
        assert normalize_key(uma) == uma

    def test_quebra_de_linha(self) -> None:
        assert normalize_key("A\nB") == "A B"


class TestIdentificadores:
    def test_only_digits(self) -> None:
        assert only_digits("12.345.678/0001-99") == "12345678000199"

    def test_only_digits_none(self) -> None:
        assert only_digits(None) == ""

    def test_classifica_cnpj(self) -> None:
        tipo, valor = classificar_documento("05.913.471/0001-04")
        assert tipo == "cnpj"
        assert valor == "05913471000104"

    def test_classifica_cpf(self) -> None:
        tipo, valor = classificar_documento("000.081.285-45")
        assert tipo == "cpf"
        assert valor == "00008128545"

    def test_classifica_invalido(self) -> None:
        tipo, valor = classificar_documento("2013.34563-6")
        assert tipo == "invalido"
        assert valor is None

    def test_cnpj_valido(self) -> None:
        assert validar_cnpj("05913471000104")

    def test_cnpj_dv_invalido(self) -> None:
        assert not validar_cnpj("05913471000105")

    def test_cnpj_repetido_invalido(self) -> None:
        assert not validar_cnpj("00000000000000")


class TestDeflator:
    IPCA = {2021: 10.06, 2022: 5.79, 2023: 4.62, 2024: 4.83, 2025: 4.26}

    def test_inicio_ano_2025(self) -> None:
        f = deflator_fatores(self.IPCA, ano_base=2025, convencao="inicio_ano")
        assert f[2025] == pytest.approx(1.0426, rel=1e-9)

    def test_inicio_ano_2021(self) -> None:
        f = deflator_fatores(self.IPCA, ano_base=2025, convencao="inicio_ano")
        esperado = 1.1006 * 1.0579 * 1.0462 * 1.0483 * 1.0426
        assert f[2021] == pytest.approx(esperado, rel=1e-9)
        assert f[2021] == pytest.approx(1.331350, abs=1e-5)

    def test_fim_ano_2025_e_um(self) -> None:
        f = deflator_fatores(self.IPCA, ano_base=2025, convencao="fim_ano")
        assert f[2025] == pytest.approx(1.0)

    def test_meio_ano_entre_as_duas(self) -> None:
        i = deflator_fatores(self.IPCA, ano_base=2025, convencao="inicio_ano")[2023]
        m = deflator_fatores(self.IPCA, ano_base=2025, convencao="meio_ano")[2023]
        fi = deflator_fatores(self.IPCA, ano_base=2025, convencao="fim_ano")[2023]
        assert fi < m < i

    def test_monotono_decrescente(self) -> None:
        f = deflator_fatores(self.IPCA, ano_base=2025, convencao="inicio_ano")
        anos = sorted(f)
        for a, b in zip(anos, anos[1:], strict=False):
            assert f[a] > f[b], "anos mais antigos devem ter fator maior"

    def test_convencao_invalida(self) -> None:
        with pytest.raises(ValueError):
            deflator_fatores(self.IPCA, convencao="mensal")
