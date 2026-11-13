"""Caminhos canônicos do projeto nicho-bahia.

Contrato de entrada/saída:
- RAW_DIR  : dados brutos, SOMENTE LEITURA (nunca escrever aqui).
- WORKSPACE: única área de escrita.
"""

from __future__ import annotations

from pathlib import Path

# --- diretórios -----------------------------------------------------------------
WORKSPACE: Path = Path(__file__).resolve().parents[2]
RAW_DIR: Path = Path(r"C:\Users\Micro\source\repos\PL\compras 2021-2025")

DATA: Path = WORKSPACE / "data"
META: Path = DATA / "_meta"
STAGING: Path = META / "staging"          # xlsx -> parquet (1:1 com a planilha)
TREATED: Path = DATA / "treated"          # camada tratada (contrato do painel)
AGGREGATES: Path = DATA / "aggregates"    # agregados + panel_data.json
LOGS: Path = WORKSPACE / "logs"
OUTPUT: Path = WORKSPACE / "output"
TESTS: Path = WORKSPACE / "tests"
TMP: Path = WORKSPACE / "tmp"

CONFIG_PATH: Path = WORKSPACE / "config.yaml"

# --- arquivos-chave -------------------------------------------------------------
STAGED_FILES: dict[int, Path] = {
    2021: STAGING / "raw_2021.parquet",
    2022: STAGING / "raw_2022.parquet",
    2023: STAGING / "raw_2023.parquet",
    2024: STAGING / "raw_2024.parquet",
    2025: STAGING / "raw_2025.parquet",
}
TREATED_PARQUET: Path = TREATED / "compras_tratadas.parquet"
PANEL_DATA_JSON: Path = AGGREGATES / "panel_data.json"

ALL_DIRS: tuple[Path, ...] = (
    DATA,
    META,
    STAGING,
    TREATED,
    AGGREGATES,
    LOGS,
    OUTPUT,
    TESTS,
    TMP,
)


def ensure_dirs() -> None:
    """Cria a árvore de diretórios de escrita (idempotente)."""
    for d in ALL_DIRS:
        d.mkdir(parents=True, exist_ok=True)


def relative(path: Path) -> str:
    """Caminho relativo ao workspace quando possível (para logs portáveis)."""
    try:
        return str(Path(path).resolve().relative_to(WORKSPACE))
    except ValueError:
        return str(path)
