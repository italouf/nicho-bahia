"""CLI do pipeline: run.py --stage <estagio>.

Estágios disponíveis (ordem de execução): inventory, ingest, profile, treat, validate,
analyze, score, build, qa, all.
Cada estágio é idempotente e pode ser reexecutado do zero.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Callable
from datetime import UTC, datetime

from . import paths
from .logging_utils import RunLog, configure_stdout

StageFn = Callable[[RunLog], object]

STAGE_ORDER: tuple[str, ...] = (
    "inventory",
    "ingest",
    "profile",
    "treat",
    "validate",
    "analyze",
    "score",
    "build",
    "qa",
)


def load_stage(name: str) -> StageFn:
    """Importa o módulo do estágio sob demanda (estágios ainda não implementados falham claro)."""
    if name == "inventory":
        from .stages import inventory

        return inventory.run
    if name == "ingest":
        from .stages import ingest

        return ingest.run
    if name == "profile":
        from .stages import profile

        return profile.run
    if name == "treat":
        from .stages import treat

        return treat.run
    if name == "validate":
        from .stages import validate

        return validate.run
    if name == "analyze":
        from .stages import analyze

        return analyze.run
    if name == "score":
        from .stages import score

        return score.run
    if name == "build":
        from .stages import build

        return build.run
    if name == "qa":
        from .stages import qa

        return qa.run
    raise SystemExit(f"estágio desconhecido: {name!r} (disponíveis: {', '.join(STAGE_ORDER)})")


def run_stages(stages: list[str]) -> int:
    configure_stdout()
    paths.ensure_dirs()
    started = datetime.now(UTC)
    log = RunLog("run")
    log(f"# nicho-bahia — execução {started.isoformat()}")
    log(f"# workspace: {paths.WORKSPACE}")
    try:
        for st in stages:
            log.section(f">>> ESTÁGIO: {st}")
            load_stage(st)(log)
        log.section("RESUMO")
        log(f"estágios executados: {', '.join(stages)}")
        log(f"início: {started.isoformat()}")
        log(f"fim:    {datetime.now(UTC).isoformat()}")
        log(f"duracao_s: {(datetime.now(UTC) - started).total_seconds():.1f}")
        return 0
    except NotImplementedError as exc:
        log(f"\n[NAO IMPLEMENTADO] {exc}")
        log("O pipeline parou neste ponto de propósito (estágio futuro).")
        return 3
    except Exception:
        log("\n[ERRO] estágio falhou:")
        log(traceback.format_exc())
        return 1
    finally:
        log.close()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="run.py", description="Pipeline de seleção de nicho — compras públicas BA")
    p.add_argument(
        "--stage",
        default="all",
        choices=(*STAGE_ORDER, "all"),
        help="estágio a executar (default: all)",
    )
    p.add_argument(
        "--from",
        dest="from_stage",
        default=None,
        choices=STAGE_ORDER,
        help="executa a partir deste estágio (inclusive) até o fim",
    )
    args = p.parse_args(argv)

    if args.from_stage:
        idx = STAGE_ORDER.index(args.from_stage)
        stages = list(STAGE_ORDER[idx:])
    elif args.stage == "all":
        stages = list(STAGE_ORDER)
    else:
        stages = [args.stage]
    return run_stages(stages)


if __name__ == "__main__":
    sys.exit(main())
