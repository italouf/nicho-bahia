"""Digest compacto do profile.json para leitura no chat (sem despejar a base)."""
from __future__ import annotations

import json
import sys

P = r"C:\Users\Micro\source\repos\PL\nicho-bahia\data\_meta\profile.json"


def show(title: str, obj: object, limit: int = 40) -> None:
    print(f"\n### {title}")
    if isinstance(obj, list):
        for r in obj[:limit]:
            print("  ", r)
        if len(obj) > limit:
            print(f"   ... ({len(obj)} itens)")
    elif isinstance(obj, dict):
        for k, v in list(obj.items())[:limit]:
            print(f"  {k}: {v}")
    else:
        print("  ", obj)


def main() -> None:
    p = json.load(open(P, encoding="utf-8"))
    show("TOTAIS", p["totais"])
    show("POR ARQUIVO", p["por_arquivo"])
    print("\n### CHAVE")
    for k, v in p["chave"]["candidatos"].items():
        print(f"  {k}: linhas={v['linhas']:,} chaves={v['chaves_distintas']:,} unid={v['unicidade_pct']}% dup={v['duplicatas_pct']}%")
    show("SOBREPOSICAO", p["chave"]["sobreposicao_entre_arquivos"])
    show("EXEMPLOS DUP", p["chave"]["exemplos_duplicata_chave_completa"])
    show("COERENCIA", p["coerencia"])
    print("\n### TEMPORAL por_ano")
    for r in p["temporal"]["por_ano"]:
        print("  ", r)
    print("\n### MATRIZ arquivo x ano")
    for r in p["temporal"]["matriz_arquivo_x_ano"]:
        print("  ", r)
    show("ADERENCIA", p["temporal"]["aderencia"])
    show("LIMITES", p["temporal"]["limites"])
    show("CNPJ", p["cnpj"])
    print("\n### ESCOPO")
    for r in p["cruzamentos"]["escopo_tipo_fornecimento_x_tipo_item"]:
        print("  ", r)
    print("\n### CANAL")
    for r in p["cruzamentos"]["canal_forma_contratacao"]:
        print("  ", r)
    print("\n### COVID")
    for r in p["cruzamentos"]["flags_covid"]:
        print("  ", r)
    print("\n### SRD/LID")
    for r in p["cruzamentos"]["srd_lid"]:
        print("  ", r)
    show("ORGAO GERENCIADOR", p["cruzamentos"]["orgao_gerenciador"])
    show("NUMERICAS DISFARCADAS", p["numericas_disfarcadas"])
    show("ENTIDADES", p["entidades"])
    print("\n### CATEGORICAS (n_distinct)")
    for k, v in p["categoricas"].items():
        print(f"  {k}: {v['n_distinct']} distintos{' (truncado)' if v['truncado'] else ''}")
    print("\n### COLUNAS com nulos > 20%")
    for c in p["colunas"]:
        if c["pct_null"] and c["pct_null"] > 20:
            print(f"  {c['coluna']}: {c['pct_null']}% nulos ({c['n_null']:,})")
    print("\n### COLUNAS numericas: min/max/neg/zero")
    for c in p["colunas"]:
        if c["tipo_staging"] in ("num", "int"):
            print(f"  {c['coluna']}: min={c['min']} max={c['max']} neg={c['n_negativos']} zero={c['n_zeros']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
