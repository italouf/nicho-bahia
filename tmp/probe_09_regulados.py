"""Auditoria da flag is_regulado e de canal='outros' na camada tratada."""
from __future__ import annotations

import sys

import duckdb

from nicho_bahia import paths
from nicho_bahia.config import load_config


def main() -> None:
    cfg = load_config()
    con = duckdb.connect()
    con.execute("SET threads TO 4")
    p = paths.TREATED_PARQUET.as_posix()
    con.execute(f"CREATE VIEW t AS SELECT * FROM read_parquet('{p}')")

    print("=== 1. famílias com maior SHARE de valor regulado (top 20) ===")
    df = con.execute(
        """
        SELECT familia_catalogo,
               round(100.0*sum(valor_total_real) FILTER (WHERE is_regulado)/sum(valor_total_real),2) AS pct_reg,
               round(sum(valor_total_real) FILTER (WHERE is_regulado),2) AS valor_reg,
               round(sum(valor_total_real),2) AS valor_total,
               count(*) AS linhas
        FROM t GROUP BY 1 HAVING sum(valor_total_real) FILTER (WHERE is_regulado) > 0
        ORDER BY valor_reg DESC LIMIT 20
        """
    ).fetch_df()
    print(df.to_string(index=False))

    print("\n=== 2. famílias da lista 'saude_oportunidade' (devem ficar majoritariamente fora) ===")
    prefixos = tuple(str(f) for f in cfg.get("regulados.saude_oportunidade"))
    cond = " OR ".join(f"familia_key LIKE '{p}%'" for p in prefixos)
    df2 = con.execute(
        f"""
        SELECT familia_catalogo, count(*) AS linhas,
               round(100.0*count(*) FILTER (WHERE is_regulado)/count(*),2) AS pct_linhas_reg,
               round(sum(valor_total_real),2) AS valor,
               round(100.0*sum(valor_total_real) FILTER (WHERE is_regulado)/sum(valor_total_real),2) AS pct_valor_reg
        FROM t WHERE {cond} GROUP BY 1 ORDER BY valor DESC
        """
    ).fetch_df()
    print(df2.to_string(index=False))

    print("\n=== 3. nomes básicos marcados regulados SÓ por keyword (fora das famílias reguladas) ===")
    fam = tuple(str(f) for f in cfg.get("regulados.familias"))
    cond_fam = " OR ".join(f"familia_key LIKE '{f}%'" for f in fam)
    df3 = con.execute(
        f"""
        SELECT familia_catalogo, nome_basico, count(*) AS linhas,
               round(sum(valor_total_real),2) AS valor
        FROM t WHERE is_regulado AND NOT ({cond_fam})
        GROUP BY 1,2 ORDER BY valor DESC LIMIT 20
        """
    ).fetch_df()
    print(df3.to_string(index=False))

    print("\n=== 4. quantas linhas reguladas vêm de família vs. keyword ===")
    df4 = con.execute(
        f"""
        SELECT count(*) FILTER (WHERE is_regulado AND ({cond_fam})) AS por_familia,
               count(*) FILTER (WHERE is_regulado AND NOT ({cond_fam})) AS por_keyword,
               count(*) FILTER (WHERE is_regulado) AS total
        FROM t
        """
    ).fetch_df()
    print(df4.to_string(index=False))

    print("\n=== 5. canal='outros' ===")
    df5 = con.execute(
        """
        SELECT forma_contratacao, count(*) AS linhas FROM t WHERE canal='outros'
        GROUP BY 1 ORDER BY linhas DESC
        """
    ).fetch_df()
    print(df5.to_string(index=False))

    print("\n=== 6. distribuição de valor por canal ===")
    df6 = con.execute(
        """
        SELECT canal, count(*) AS linhas, round(sum(valor_total_real),2) AS valor_real,
               round(100.0*sum(valor_total_real)/sum(sum(valor_total_real)) OVER (),2) AS pct_valor
        FROM t GROUP BY 1 ORDER BY valor_real DESC
        """
    ).fetch_df()
    print(df6.to_string(index=False))

    print("\n=== 7. cobertura: anos, meses, famílias, itens ===")
    df7 = con.execute(
        """
        SELECT count(DISTINCT ano) AS anos, count(DISTINCT ano_mes) AS meses,
               count(DISTINCT familia_key) AS familias, count(DISTINCT item_key) AS itens,
               count(DISTINCT afm_aps) AS afms, count(DISTINCT fornecedor_id) AS fornecedores,
               count(DISTINCT ug_key) AS ugs, count(DISTINCT municipio_key) AS municipios,
               count(DISTINCT regiao_key) AS regioes
        FROM t
        """
    ).fetch_df()
    print(df7.to_string(index=False))

    print("\n=== 8. famílias elegíveis para ranking (>=30 AFM e >= R$ 1 mi real) ===")
    df8 = con.execute(
        """
        WITH f AS (
          SELECT familia_catalogo, count(DISTINCT afm_aps) AS afms, sum(valor_total_real) AS valor
          FROM t GROUP BY 1
        )
        SELECT count(*) AS familias,
               count(*) FILTER (WHERE afms>=30 AND valor>=1000000) AS elegiveis,
               count(*) FILTER (WHERE afms>=30 AND valor>=1000000 AND NOT is_reg) AS elegiveis_nao_reguladas
        FROM (SELECT f.*, EXISTS(SELECT 1 FROM t WHERE t.familia_catalogo=f.familia_catalogo AND t.is_regulado) AS is_reg FROM f)
        """
    ).fetch_df()
    print(df8.to_string(index=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
