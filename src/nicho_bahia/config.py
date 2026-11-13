"""Carregamento e validação do config.yaml.

Todo parâmetro de negócio (pesos, thresholds, listas de exclusão) vem daqui — nunca do código.
A validação falha cedo e com mensagem explícita, para não rodar o pipeline com configuração inválida.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from . import paths

_MISSING = object()


class ConfigError(ValueError):
    """Configuração inválida."""


# caminhos obrigatórios (dotted path)
_OBRIGATORIOS: tuple[str, ...] = (
    "meta.versao",
    "negocio.sede.municipio",
    "tempo.anos_analise",
    "deflacao.ipca_ano_pct",
    "deflacao.convencao",
    "escopo.valores_material",
    "pandemia.colunas_flag",
    "regulados.familias",
    "regulados.keywords",
    "dispensa.teto_2026",
    "dispensa.mapa_canal",
    "dispensa.canais_dispensa",
    "logistica.regioes_dentro_raio",
    "metricas.minimo_afm_para_ranking",
    "metricas.minimo_valor_real_para_ranking",
    "score.pesos",
    "score.penalidades",
    "painel.arquivo",
    "execucao.tolerancia_reconciliacao",
)

_CONVENCOES = frozenset({"inicio_ano", "meio_ano", "fim_ano"})

_PESOS_ESPERADOS = frozenset(
    {
        "demanda",
        "crescimento",
        "recorrencia",
        "fit_dispensa",
        "fragmentacao",
        "estabilidade_preco",
        "logistica",
    }
)


class Config:
    """Acesso à configuração por caminho pontuado (`cfg.get("score.pesos.demanda")`)."""

    def __init__(self, data: dict[str, Any], source: Path | None = None) -> None:
        self._data = data
        self.source = source

    @property
    def raw(self) -> dict[str, Any]:
        return self._data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, dotted: str, default: Any = _MISSING) -> Any:
        """Busca por caminho pontuado. Sem default, levanta KeyError explicativo."""
        node: Any = self._data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                if default is not _MISSING:
                    return default
                raise ConfigError(f"config.yaml: caminho ausente {dotted!r}")
            node = node[part]
        return node

    # atalhos usados com frequência ------------------------------------------------
    @property
    def anos(self) -> list[int]:
        return [int(a) for a in self.get("tempo.anos_analise")]

    @property
    def pesos(self) -> dict[str, float]:
        return {k: float(v) for k, v in self.get("score.pesos").items()}

    @property
    def tolerancia_reconciliacao(self) -> float:
        return float(self.get("execucao.tolerancia_reconciliacao"))


def _validar(cfg: Config) -> None:
    for caminho in _OBRIGATORIOS:
        cfg.get(caminho)  # levanta ConfigError se ausente

    conv = cfg.get("deflacao.convencao")
    if conv not in _CONVENCOES:
        raise ConfigError(f"deflacao.convencao inválida: {conv!r} (use {sorted(_CONVENCOES)})")

    anos = cfg.anos
    if not anos:
        raise ConfigError("tempo.anos_analise está vazio")
    ipca = cfg.get("deflacao.ipca_ano_pct")
    faltando = [a for a in anos if a not in ipca and str(a) not in ipca]
    if faltando:
        raise ConfigError(f"deflacao.ipca_ano_pct sem os anos {faltando}")

    pesos = cfg.pesos
    if set(pesos) != _PESOS_ESPERADOS:
        raise ConfigError(
            f"score.pesos deve ter exatamente {sorted(_PESOS_ESPERADOS)}; veio {sorted(pesos)}"
        )
    soma = sum(pesos.values())
    if abs(soma - 100.0) > 1e-6:
        raise ConfigError(f"score.pesos deve somar 100; soma = {soma}")

    teto = float(cfg.get("dispensa.teto_2026"))
    if teto <= 0:
        raise ConfigError("dispensa.teto_2026 deve ser positivo")
    if not cfg.get("dispensa.mapa_canal"):
        raise ConfigError("dispensa.mapa_canal está vazio")
    canais = set(cfg.get("dispensa.mapa_canal").values())
    for c in cfg.get("dispensa.canais_dispensa"):
        if c not in canais:
            raise ConfigError(f"dispensa.canais_dispensa cita canal não mapeado: {c!r}")

    if not cfg.get("regulados.familias") and not cfg.get("regulados.keywords"):
        raise ConfigError("regulados: informe ao menos uma família ou keyword")
    if not cfg.get("logistica.regioes_dentro_raio"):
        raise ConfigError("logistica.regioes_dentro_raio está vazio")

    tol = cfg.tolerancia_reconciliacao
    if not (0.0 < tol < 1.0):
        raise ConfigError(f"execucao.tolerancia_reconciliacao fora de (0,1): {tol}")


@lru_cache(maxsize=4)
def _load_cached(path: Path) -> Config:
    if not path.exists():
        raise ConfigError(f"config.yaml não encontrado em {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError("config.yaml não é um mapeamento YAML")
    cfg = Config(data, source=path)
    _validar(cfg)
    return cfg


def load_config(path: Path | None = None) -> Config:
    """Carrega e valida o config.yaml (cacheado por caminho)."""
    return _load_cached(Path(path) if path is not None else paths.CONFIG_PATH)
