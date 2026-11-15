"""AR-25 / I1 — nenhum número muda com o retrofit.

Compara a impressão digital numérica de cada gráfico com o *golden snapshot* congelado
antes das mudanças (`golden_series.json`) e o CSV exportado pela tabela.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from nicho_bahia import paths

from .painel import abrir, fingerprint_graficos, numeros

GOLDEN = paths.TESTS / "retrofit" / "golden_series.json"

pytestmark = pytest.mark.retrofit


@pytest.fixture(scope="module")
def golden() -> dict:
    if not GOLDEN.exists():
        pytest.skip("golden_series.json ausente — rode tmp/congela_golden.py antes do retrofit")
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def atual() -> dict[str, list[float]]:
    """Estado do painel atual: percorre todas as abas e captura os gráficos."""
    with abrir() as s:
        for aba in s.abas():
            s.ir_para(aba)
        return fingerprint_graficos(s.page)


def _fingerprint_golden(golden: dict) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for aba in golden["abas"].values():
        for cid, dados in aba.items():
            if not dados:
                continue
            out[cid] = numeros([s["data"] for s in dados["series"]])
    return out


def test_nenhum_numero_mudou(golden: dict, atual: dict[str, list[float]]) -> None:
    esperado = _fingerprint_golden(golden)
    comparados, divergentes = 0, []
    for cid, nums in esperado.items():
        if cid not in atual:
            divergentes.append(f"{cid}: gráfico ausente no painel novo")
            continue
        comparados += 1
        if len(nums) != len(atual[cid]):
            divergentes.append(f"{cid}: {len(nums)} números antes, {len(atual[cid])} depois")
        elif nums != atual[cid]:
            dif = [(i, a, b) for i, (a, b) in enumerate(zip(nums, atual[cid], strict=True)) if a != b][:3]
            divergentes.append(f"{cid}: valores diferentes em {len(dif)} posições (ex.: {dif})")
    assert comparados >= 18, f"só {comparados} gráficos comparados"
    assert not divergentes, "divergência de números:\n" + "\n".join(divergentes)


def test_contagem_de_graficos(golden: dict, atual: dict[str, list[float]]) -> None:
    ids_golden = set(_fingerprint_golden(golden))
    assert ids_golden <= set(atual), f"faltam gráficos: {sorted(ids_golden - set(atual))}"


def test_csv_exporta_todas_as_linhas() -> None:
    """O CSV do recorte completo precisa manter as 155 linhas de antes (independente da paginação)."""
    with abrir() as s:
        s.ir_para("Decisão")
        csv = s.page.evaluate("() => document.getElementById('tabela').dataset.csv || ''")
    linhas = [lin for lin in csv.split("\n") if lin.strip()]
    assert len(linhas) == 155, f"CSV com {len(linhas)} linhas; esperado 155"
    assert "89.55" in csv, "CSV sem o primeiro nicho"
