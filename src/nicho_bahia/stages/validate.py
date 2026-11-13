"""F3/G3 — Validação automática da camada tratada.

Roda uma bateria de verificações independentes (não as mesmas do pytest, para não
mascarar erro comum) e o pytest. Grava evidência em logs/gate_g3.json e logs/pytest_f3.log.

Gate G3 fica VERDE apenas se todas as verificações passarem e o pytest sair com 0.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any

import duckdb

from .. import paths
from ..config import load_config
from ..logging_utils import RunLog, write_json


def _sha256(path) -> str:  # noqa: ANN001
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Check:
    __slots__ = ("id", "descricao", "esperado", "obtido", "status")

    def __init__(self, id_: str, descricao: str, esperado: Any, obtido: Any, ok: bool) -> None:
        self.id = id_
        self.descricao = descricao
        self.esperado = esperado
        self.obtido = obtido
        self.status = "OK" if ok else "FALHA"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "descricao": self.descricao,
            "esperado": self.esperado,
            "obtido": self.obtido,
            "status": self.status,
        }


def _run_pytest(log: RunLog) -> dict[str, Any]:
    """Executa o pytest no venv corrente e guarda a saída.

    O ambiente é herdado de propósito: no Windows, um env mínimo quebra `asyncio`
    (`_overlapped` / Winsock) e o pytest aborta com erro interno (exit 3).
    """
    destino = paths.LOGS / "pytest_f3.log"
    env = {
        **os.environ,
        "DISABLE_PANDERA_IMPORT_WARNING": "True",
        "PYTHONIOENCODING": "utf-8",
    }
    env.pop("PYTEST_ADDOPTS", None)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(paths.WORKSPACE),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    saida = (proc.stdout or "") + (proc.stderr or "")
    destino.write_text(saida, encoding="utf-8")
    # a última linha do pytest -q é algo como "42 passed in 4.44s"
    resumo = ""
    for linha in reversed(saida.strip().splitlines()):
        if "passed" in linha or "failed" in linha or "error" in linha:
            resumo = linha.strip()
            break
    return {"exit_code": proc.returncode, "resumo": resumo, "log": paths.relative(destino)}


def run(log: RunLog) -> dict[str, Any]:
    paths.ensure_dirs()
    log.section("F3/G3 — VALIDAÇÃO DA CAMADA TRATADA")
    cfg = load_config()

    if not paths.TREATED_PARQUET.exists():
        raise FileNotFoundError(f"parquet tratado ausente: {paths.TREATED_PARQUET} (rode --stage treat)")

    con = duckdb.connect()
    con.execute("SET threads TO 4")
    con.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{paths.TREATED_PARQUET.as_posix()}')")

    def one(sql: str) -> dict[str, Any]:
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, cur.fetchone(), strict=True))

    checks: list[Check] = []

    # C01 — contagem
    n = int(one("SELECT count(*) AS n FROM t")["n"])
    checks.append(Check("C01", "linhas no escopo tratado", 560934, n, n == 560934))

    # C02 — reconciliação registrada no tratamento
    trat = json.loads((paths.META / "tratamento.json").read_text(encoding="utf-8"))
    rec = trat["reconciliacao"]
    checks.append(
        Check(
            "C02",
            "reconciliação Σ valor (bruto material vs tratado)",
            f"<= {cfg.tolerancia_reconciliacao * 100:.2f}%",
            f"{rec['diferenca_rel'] * 100:.6f}%",
            rec["status"] == "OK" and rec["diferenca_rel"] <= cfg.tolerancia_reconciliacao,
        )
    )

    # C03 — chave técnica única
    dup = int(one("SELECT count(*) - count(DISTINCT linha_id) AS d FROM t")["d"])
    checks.append(Check("C03", "linha_id única", "0 duplicatas", dup, dup == 0))

    # C04 — nulos estruturais
    nul = one(
        """
        SELECT count(*) FILTER (WHERE data IS NULL) AS data,
               count(*) FILTER (WHERE familia_key IS NULL) AS familia,
               count(*) FILTER (WHERE item_key IS NULL) AS item_key,
               count(*) FILTER (WHERE valor_total_real IS NULL) AS valor
        FROM t
        """
    )
    checks.append(Check("C04", "nulos estruturais", "0 em data/familia/item_key/valor", nul, all(v == 0 for v in nul.values())))

    # C05 — deflator por ano bate com o config
    from ..textops import deflator_fatores

    esperado = deflator_fatores(
        cfg.get("deflacao.ipca_ano_pct"),
        ano_base=int(cfg.get("meta.ano_base_deflacao")),
        convencao=str(cfg.get("deflacao.convencao")),
    )
    obtido = {
        int(r["ano"]): round(float(r["d"]), 6)
        for r in con.execute("SELECT ano, min(deflator) AS d FROM t GROUP BY 1 ORDER BY 1").fetch_df().to_dict("records")
    }
    ok_defl = all(abs(obtido.get(a, -1) - round(f, 6)) < 1e-6 for a, f in esperado.items())
    checks.append(Check("C05", "deflator por ano = config", {k: round(v, 6) for k, v in esperado.items()}, obtido, ok_defl))

    # C06 — soma nominal = bruto material
    soma = float(one("SELECT sum(valor_total_real) AS v FROM t")["v"])
    soma_nom = float(one("SELECT sum(valor_total_nominal) AS v FROM t")["v"])
    checks.append(
        Check(
            "C06",
            "Σ valor nominal do tratado",
            f"{rec['soma_bruta_material']:.2f}",
            f"{soma_nom:.2f}",
            abs(soma_nom - rec["soma_bruta_material"]) <= 0.01,
        )
    )
    log(f"Σ nominal = R$ {soma_nom:,.2f} | Σ real (dez/2025) = R$ {soma:,.2f}")

    # C07 — famílias reguladas 100% marcadas
    prefixos = [str(f).upper() for f in cfg.get("regulados.familias")]
    cond = " OR ".join(f"familia_key LIKE '{p}%'" for p in prefixos)
    reg = one(f"SELECT count(*) AS n, count(*) FILTER (WHERE is_regulado) AS r FROM t WHERE {cond}")
    ok_reg = int(reg["n"]) > 0 and int(reg["r"]) == int(reg["n"])
    checks.append(Check("C07", "famílias reguladas 100% marcadas", "100%", f"{reg['r']}/{reg['n']}", ok_reg))

    # C08 — famílias de saúde mantidas como oportunidade não podem estar majoritariamente reguladas
    pref_op = [str(f).upper() for f in cfg.get("regulados.saude_oportunidade")]
    cond_op = " OR ".join(f"familia_key LIKE '{p}%'" for p in pref_op)
    op = con.execute(
        f"""
        SELECT familia_catalogo,
               round(100.0*sum(valor_total_real) FILTER (WHERE is_regulado)/nullif(sum(valor_total_real),0),2) AS pct
        FROM t WHERE {cond_op} GROUP BY 1
        """
    ).fetch_df()
    pior = float(op["pct"].fillna(0).max()) if len(op) else 0.0
    checks.append(
        Check("C08", "saúde-oportunidade não majoritariamente regulada", "< 50% do valor", f"máx {pior:.2f}%", pior < 50.0)
    )

    # C09 — canal mapeado
    canal = one(
        """
        SELECT count(*) AS n, count(*) FILTER (WHERE canal_mapeado) AS m,
               count(*) FILTER (WHERE NOT canal_mapeado) AS nm
        FROM t
        """
    )
    checks.append(Check("C09", "rótulos de canal reconhecidos", "0 não mapeados", canal["nm"], int(canal["nm"]) == 0))

    # C10 — cobertura temporal e de entidades
    cob = one(
        """
        SELECT count(DISTINCT ano) AS anos, count(DISTINCT ano_mes) AS meses,
               count(DISTINCT familia_key) AS familias, count(DISTINCT item_key) AS itens,
               count(DISTINCT fornecedor_id) AS fornecedores
        FROM t
        """
    )
    ok_cob = int(cob["anos"]) == 5 and int(cob["meses"]) == 60
    checks.append(Check("C10", "cobertura temporal (5 anos / 60 meses)", "5 / 60", f"{cob['anos']} / {cob['meses']}", ok_cob))
    log(
        f"cobertura: famílias={cob['familias']:,} itens={cob['itens']:,} "
        f"fornecedores={cob['fornecedores']:,}"
    )

    # C11 — pytest
    pytest_res = _run_pytest(log)
    checks.append(
        Check("C11", "pytest (contrato pandera + regras)", "exit 0", f"exit {pytest_res['exit_code']}: {pytest_res['resumo']}", pytest_res["exit_code"] == 0)
    )

    # C12 — hash do parquet registrado
    sha = _sha256(paths.TREATED_PARQUET)
    checks.append(Check("C12", "sha256 do parquet registrado", sha[:16], sha[:16], sha == trat["parquet"]["sha256"]))

    # resumo
    falhas = [c for c in checks if c.status != "OK"]
    log("\nverificações:")
    for c in checks:
        log(f"  [{c.status:5s}] {c.id} {c.descricao:52s} esperado={c.esperado} obtido={c.obtido}")

    gate = {
        "gate": "G3",
        "gerado_em": datetime.now(UTC).isoformat(),
        "status": "VERDE" if not falhas else "VERMELHO",
        "checks": [c.as_dict() for c in checks],
        "pytest": pytest_res,
        "parquet": {
            "caminho": paths.relative(paths.TREATED_PARQUET),
            "sha256": sha,
            "linhas": n,
            "tamanho_mb": round(paths.TREATED_PARQUET.stat().st_size / 1024 / 1024, 2),
        },
    }
    write_json(paths.LOGS / "gate_g3.json", gate)
    log(f"\n[{'VERDE' if not falhas else 'VERMELHO'}] Gate G3 — {len(checks) - len(falhas)}/{len(checks)} verificações OK")
    log(f"[ok] {paths.relative(paths.LOGS / 'gate_g3.json')}")
    con.close()

    if falhas:
        raise RuntimeError("Gate G3 VERMELHO: " + ", ".join(f"{c.id} ({c.descricao})" for c in falhas))
    return gate
