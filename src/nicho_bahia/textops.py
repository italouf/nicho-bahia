"""Normalizações de texto, identificadores e deflação.

As funções aqui espelham exatamente as expressões SQL usadas no estágio `treat`
(`upper(strip_accents(x))` + colapso de espaços + trim), de modo que chaves calculadas
em Python e em SQL coincidam. Há teste unitário garantindo a equivalência.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final, Literal

TipoDocumento = Literal["cnpj", "cpf", "invalido"]

_WS = re.compile(r"\s+")
_NAO_DIGITO = re.compile(r"\D")


def normalize_key(value: str | None) -> str | None:
    """Normaliza texto para uso como chave: sem acento, caixa alta, espaços colapsados.

    Equivalente SQL: `trim(regexp_replace(upper(strip_accents(x)), '\\s+', ' ', 'g'))`.
    """
    if value is None:
        return None
    s = unicodedata.normalize("NFKD", str(value))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("\u00a0", " ").replace("\n", " ").replace("\r", " ").replace("\t", " ")
    s = _WS.sub(" ", s).strip()
    return s.upper()


def only_digits(value: str | None) -> str:
    """Remove tudo que não é dígito."""
    if value is None:
        return ""
    return _NAO_DIGITO.sub("", str(value))


def classificar_documento(value: str | None) -> tuple[TipoDocumento, str | None]:
    """Classifica o identificador do fornecedor em CNPJ (14), CPF (11) ou inválido.

    Regra validada em F1: 12.551 CNPJs de 14 dígitos, 2.618 CPFs de 11 dígitos e
    47 identificadores de 10 dígitos (formato não reconhecido).
    """
    d = only_digits(value)
    if len(d) == 14:
        return "cnpj", d
    if len(d) == 11:
        return "cpf", d
    return "invalido", None


def validar_cnpj(cnpj: str) -> bool:
    """Valida os dois dígitos verificadores de um CNPJ de 14 dígitos."""
    if len(cnpj) != 14 or not cnpj.isdigit() or len(set(cnpj)) == 1:
        return False
    pesos1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    pesos2 = (6, *pesos1)
    d1 = sum(int(a) * b for a, b in zip(cnpj[:12], pesos1, strict=True)) % 11
    d1 = 0 if d1 < 2 else 11 - d1
    d2 = sum(int(a) * b for a, b in zip(cnpj[:13], pesos2, strict=True)) % 11
    d2 = 0 if d2 < 2 else 11 - d2
    return cnpj[12] == str(d1) and cnpj[13] == str(d2)


def deflator_fatores(
    ipca_pct: dict[int | str, float],
    *,
    ano_base: int = 2025,
    convencao: str = "inicio_ano",
) -> dict[int, float]:
    """Fator de correção para levar valores nominais de cada ano a R$ do ano-base.

    Convenções (ver SPEC.md §4):
    - `inicio_ano`: o valor anual é preço de início do ano  -> Π(k = ano..base)(1+i_k)
    - `meio_ano`  : metade da inflação do próprio ano      -> Π(k = ano+1..base)(1+i_k) × (1+i_ano)^0,5
    - `fim_ano`   : o valor já está a preços de fim do ano -> Π(k = ano+1..base)(1+i_k)
    """
    taxas = {int(k): float(v) / 100.0 for k, v in ipca_pct.items()}
    if ano_base not in taxas:
        raise ValueError(f"ano-base {ano_base} sem IPCA informado")
    anos = sorted(taxas)
    if convencao not in {"inicio_ano", "meio_ano", "fim_ano"}:
        raise ValueError(f"convenção desconhecida: {convencao!r}")

    fatores: dict[int, float] = {}
    for ano in anos:
        if ano > ano_base:
            continue
        f = 1.0
        for k in anos:
            if k <= ano:
                continue
            if k > ano_base:
                break
            f *= 1.0 + taxas[k]
        if convencao == "inicio_ano":
            f *= 1.0 + taxas[ano]
        elif convencao == "meio_ano":
            f *= (1.0 + taxas[ano]) ** 0.5
        fatores[ano] = f
    return fatores


def brl(valor: float | None) -> str:
    """Formata em reais (usado em logs, não no painel)."""
    if valor is None:
        return "—"
    s = f"{valor:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor:.{casas}f}".replace(".", ",") + "%"


MAX_PRAZO_DIAS: Final[int] = 365
