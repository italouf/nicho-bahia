"""A1 — verificação de reprodutibilidade: hashes dos agregados antes/depois de `run.py --stage all`."""
from __future__ import annotations

import hashlib
import json
import sys

from nicho_bahia import paths

DEST = paths.LOGS / "hashes_agregados.json"


def coletar() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(paths.AGGREGATES.glob("*.parquet")):
        out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:32]
    for p in sorted(paths.TREATED.glob("*.parquet")):
        out["treated/" + p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:32]
    # panel_data.json: remove campos voláteis (timestamp) antes de hashear
    pj = paths.AGGREGATES / "panel_data.json"
    if pj.exists():
        d = json.loads(pj.read_text(encoding="utf-8"))
        d.get("meta", {}).pop("gerado_em", None)
        d["meta"].pop("hashes", None)
        out["panel_data.json(estavel)"] = hashlib.sha256(
            json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()[:32]
    for p in sorted(paths.WORKSPACE.glob("*.csv")):
        out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:32]
    return out


def main() -> None:
    acao = sys.argv[1] if len(sys.argv) > 1 else "save"
    if acao == "save":
        dados = coletar()
        DEST.write_text(json.dumps(dados, indent=1, sort_keys=True), encoding="utf-8")
        print(f"salvos {len(dados)} hashes em {DEST.name}")
        return
    if acao == "compare":
        antes = json.loads(DEST.read_text(encoding="utf-8"))
        depois = coletar()
        iguais = [k for k in antes if antes[k] == depois.get(k)]
        diferentes = [k for k in antes if antes[k] != depois.get(k)]
        faltando = [k for k in antes if k not in depois]
        print(f"arquivos comparados: {len(antes)}")
        print(f"idênticos: {len(iguais)}")
        print(f"diferentes: {len(diferentes)} -> {diferentes}")
        print(f"faltando: {faltando}")
        sys.exit(0 if not diferentes and not faltando else 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
