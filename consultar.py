#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consultar.py - Dossie completo de um processo (CLI).

Uso:
    python3 consultar.py <numero-do-processo>

Exemplo:
    python3 consultar.py 5032569-92.2023.8.08.0024

Gera, em  processos/<numero>/ :
    datajud.json     -> metadados crus do DataJud/CNJ
    movimentos.txt   -> linha do tempo legivel (todos os andamentos)
    decisoes/        -> inteiro teor de cada sentenca/decisao/acordao (.txt e .html)
    RESUMO.md        -> visao consolidada do processo
"""

import json
import os
import sys

import tjes


def _slug(texto, limite=70):
    """Transforma um texto em nome de arquivo seguro."""
    limpo = "".join(c if (c.isalnum() or c in " -_") else "_" for c in str(texto))
    return "_".join(limpo.split())[:limite]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    numero = sys.argv[1]
    nro = tjes.formatar_cnj(numero)
    raiz = os.path.dirname(os.path.abspath(__file__))
    base = os.path.join(raiz, "processos", nro)
    dir_dec = os.path.join(base, "decisoes")
    os.makedirs(dir_dec, exist_ok=True)

    print(f"\n=== Processo {nro} ===")
    print(f"Saida: {base}\n")

    # ---- 1. DataJud: metadados + movimentos --------------------------------
    print("[1/2] DataJud/CNJ - metadados e movimentos ...")
    registros = tjes.datajud(numero)
    with open(os.path.join(base, "datajud.json"), "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)

    linhas_mov = [f"PROCESSO {nro}", "=" * 60, ""]
    for s in registros:
        classe = (s.get("classe") or {}).get("nome", "?")
        orgao = (s.get("orgaoJulgador") or {}).get("nome", "?")
        movs = tjes.movimentos_ordenados(s)
        print(f"  - {s.get('grau')}: {classe} | {orgao} | {len(movs)} movimentos")
        linhas_mov += [f"[{s.get('grau')}] {classe}", f"Orgao: {orgao}", "-" * 60]
        for m in movs:
            comp = "; ".join(c.get("nome", "") for c in m.get("complementosTabelados", []))
            linhas_mov.append(
                f"  {m.get('dataHora','')[:19]}  {m.get('nome','')}"
                + (f"  ({comp})" if comp else "")
            )
        linhas_mov.append("")
    with open(os.path.join(base, "movimentos.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_mov))

    # ---- 2. Jurisprudencia: inteiro teor das decisoes ----------------------
    print("[2/2] Jurisprudencia TJES - inteiro teor das decisoes ...")
    juris = tjes.jurisp_processo(numero)
    decisoes = []
    indice = 0
    for core, docs in juris.items():
        if isinstance(docs, dict):  # ocorreu erro nessa base
            print(f"  ! {core}: {docs.get('erro')}")
            continue
        for d in docs:
            indice += 1
            texto = tjes.texto_decisao(d)
            html = tjes.html_decisao(d)
            classe = d.get("classe_judicial", "")
            nome = f"{indice:02d}_{core}_{_slug(classe)}_{d.get('id','')}"
            if texto:
                with open(os.path.join(dir_dec, nome + ".txt"), "w", encoding="utf-8") as f:
                    f.write(texto)
            if html:
                with open(os.path.join(dir_dec, nome + ".html"), "w", encoding="utf-8") as f:
                    f.write(html)
            with open(os.path.join(dir_dec, nome + ".meta.json"), "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            decisoes.append({
                "core": core, "classe": classe,
                "magistrado": d.get("magistrado", ""),
                "orgao": d.get("orgao_julgador", ""),
                "data": d.get("dt_juntada", ""),
                "ementa": (d.get("ementa") or "").strip(),
                "chars": len(texto), "arquivo": nome,
            })
            print(f"  - {core}: {classe} | {d.get('magistrado','')} | {len(texto)} chars")

    # ---- RESUMO.md ---------------------------------------------------------
    res = [f"# Processo {nro}", ""]
    for s in registros:
        res += [
            f"## {s.get('grau')} - {(s.get('classe') or {}).get('nome','?')}",
            f"- Orgao julgador: {(s.get('orgaoJulgador') or {}).get('nome','?')}",
            f"- Ajuizamento: {s.get('dataAjuizamento','?')}",
            f"- Ultima atualizacao: {s.get('dataHoraUltimaAtualizacao','?')}",
            f"- Assuntos: {', '.join(a.get('nome','') for a in s.get('assuntos',[]) or [])}",
            f"- Movimentos: {len(s.get('movimentos',[]) or [])}",
            "",
        ]
    res += ["## Decisoes com inteiro teor disponivel", ""]
    for x in decisoes:
        res += [
            f"### {x['arquivo']}",
            f"- Base: {x['core']} | Classe: {x['classe']}",
            f"- Magistrado(a): {x['magistrado']}",
            f"- Orgao: {x['orgao']} | Data: {x['data']}",
            f"- Tamanho do texto: {x['chars']} caracteres",
        ]
        if x["ementa"]:
            res += ["", "**Ementa:**", "", x["ementa"]]
        res.append("")
    with open(os.path.join(base, "RESUMO.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(res))

    print(f"\nConcluido. {len(decisoes)} decisao(oes) com inteiro teor salvas.")
    print(f"Abra: {os.path.join(base, 'RESUMO.md')}\n")


if __name__ == "__main__":
    main()
