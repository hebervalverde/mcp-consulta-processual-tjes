#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
buscar.py - Busca de jurisprudencia (texto livre) no TJES.

Uso:
    python3 buscar.py "termos de busca" [opcoes]

Opcoes:
    --core  <base>   base a pesquisar (padrao: pje2g). Ver lista abaixo.
    --n     <num>    quantidade de resultados (padrao: 20)
    --exato          busca a expressao exata (frase entre aspas)

Bases (cores):
    pje1g                1o grau  - sentencas e decisoes
    pje2g                2o grau  - acordaos          <- padrao
    pje2g_mono           2o grau  - decisoes monocraticas
    legado               jurisprudencia legada
    turma_recursal_legado turmas recursais (legado)

Exemplos:
    python3 buscar.py "PMES concurso CNH"
    python3 buscar.py "Sumula 266" --core pje2g --n 30
    python3 buscar.py "CFSd 2022 eliminacao" --core pje1g
"""

import json
import os
import sys

import tjes


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    core, n, exato, termos = "pje2g", 20, False, []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--core":
            core = args[i + 1]; i += 2
        elif a == "--n":
            n = int(args[i + 1]); i += 2
        elif a == "--exato":
            exato = True; i += 1
        else:
            termos.append(a); i += 1

    q = " ".join(termos)
    if exato and not q.startswith('"'):
        q = f'"{q}"'

    print(f"\n=== Busca de jurisprudencia ===")
    print(f"Termo: {q}  |  Base: {core}\n")
    r = tjes.jurisp_search(core, q=q, per_page=n)
    docs = r.get("docs", [])
    print(f"{r.get('total', 0)} resultado(s) no total. Exibindo {len(docs)}.\n")

    for k, d in enumerate(docs, 1):
        ementa = (d.get("ementa") or tjes.texto_decisao(d) or "")
        ementa = " ".join(ementa.split())[:320]
        print(f"{k:2d}. Processo {d.get('nr_processo', '?')}")
        print(f"    Classe : {d.get('classe_judicial', '')}")
        print(f"    Orgao  : {d.get('orgao_julgador', '')}")
        print(f"    Magistr: {d.get('magistrado', '')}  |  Data: {str(d.get('dt_juntada',''))[:10]}")
        print(f"    Assunto: {d.get('assunto_principal', '')}")
        if ementa:
            print(f"    >> {ementa}...")
        print()

    # salva o resultado bruto para consulta posterior
    raiz = os.path.dirname(os.path.abspath(__file__))
    saida = os.path.join(raiz, "buscas")
    os.makedirs(saida, exist_ok=True)
    slug = "_".join("".join(c if c.isalnum() else " " for c in q).split())[:50]
    caminho = os.path.join(saida, f"{core}_{slug}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    print(f"Resultado completo salvo em: {caminho}\n")


if __name__ == "__main__":
    main()
