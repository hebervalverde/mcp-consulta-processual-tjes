#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_server.py - Servidor MCP de consulta processual (TJES + DataJud/CNJ).

Expoe ferramentas nativas para o Claude Code:
  - consultar_processo(numero)        -> metadados + andamentos + decisoes
  - buscar_jurisprudencia(termo, ...)  -> busca de jurisprudencia por texto
  - inteiro_teor(numero)               -> texto completo das decisoes

Transporte: stdio / JSON-RPC 2.0 (uma mensagem JSON por linha).
Zero dependencias: apenas a biblioteca padrao do Python 3.
"""

import json
import os
import sys

# garante que o 'import tjes' funcione independente do diretorio de trabalho
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tjes  # noqa: E402

PROTOCOLO_PADRAO = "2025-06-18"


def log(msg):
    """Escreve no stderr (permitido pelo MCP para diagnostico)."""
    print(f"[consulta-processual] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Implementacao das ferramentas
# ---------------------------------------------------------------------------
def _consultar_processo(numero):
    nro = tjes.formatar_cnj(numero)
    regs = tjes.datajud(numero)
    out = [f"PROCESSO {nro}", ""]
    if not regs:
        out.append("Nenhum registro encontrado no DataJud/CNJ.")
    for s in regs:
        classe = (s.get("classe") or {}).get("nome", "?")
        orgao = (s.get("orgaoJulgador") or {}).get("nome", "?")
        movs = tjes.movimentos_ordenados(s)
        out += [
            f"== {s.get('grau')} | {classe} ==",
            f"Orgao julgador: {orgao}",
            f"Ajuizamento: {s.get('dataAjuizamento', '?')}  |  Movimentos: {len(movs)}",
            "Ultimos andamentos:",
        ]
        for m in movs[-10:]:
            out.append(f"  {str(m.get('dataHora',''))[:10]}  {m.get('nome','')}")
        out.append("")
    juris = tjes.jurisp_processo(numero)
    out.append("DECISOES COM INTEIRO TEOR DISPONIVEL:")
    achou = False
    for core, docs in juris.items():
        if isinstance(docs, dict):
            continue
        for d in docs:
            achou = True
            out.append(
                f"  [{core}] {d.get('classe_judicial','')} - "
                f"{d.get('magistrado','')} - {str(d.get('dt_juntada',''))[:10]}"
            )
    if not achou:
        out.append("  (nenhuma)")
    out += ["", "Use 'inteiro_teor' para ler o texto completo das decisoes."]
    return "\n".join(out)


def _buscar_jurisprudencia(termo, base="pje2g", quantidade=15):
    r = tjes.jurisp_search(base, q=termo, per_page=int(quantidade))
    docs = r.get("docs", [])
    out = [
        f"Busca: {termo!r}  |  base: {base}  |  "
        f"{r.get('total', 0)} resultado(s), exibindo {len(docs)}",
        "",
    ]
    for k, d in enumerate(docs, 1):
        ementa = " ".join((d.get("ementa") or tjes.texto_decisao(d) or "").split())[:450]
        out += [
            f"{k}. Processo {d.get('nr_processo','?')}  |  {d.get('classe_judicial','')}",
            f"   {d.get('orgao_julgador','')}  |  {d.get('magistrado','')}  |  "
            f"{str(d.get('dt_juntada',''))[:10]}",
            f"   {ementa}",
            "",
        ]
    return "\n".join(out)


def _inteiro_teor(numero):
    juris = tjes.jurisp_processo(numero)
    out = [f"INTEIRO TEOR - PROCESSO {tjes.formatar_cnj(numero)}", ""]
    achou = False
    for core, docs in juris.items():
        if isinstance(docs, dict):
            continue
        for d in docs:
            achou = True
            out += [
                "=" * 72,
                f"[{core}] {d.get('classe_judicial','')} - {d.get('magistrado','')}",
                "=" * 72,
                tjes.texto_decisao(d),
                "",
            ]
    if not achou:
        out.append("Nenhuma decisao com inteiro teor encontrada.")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Catalogo de ferramentas (esquema exposto ao Claude)
# ---------------------------------------------------------------------------
FERRAMENTAS = [
    {
        "name": "consultar_processo",
        "description": "Consulta um processo do TJES no DataJud/CNJ: classe, orgao "
                       "julgador, andamentos e lista de decisoes disponiveis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "numero": {"type": "string",
                           "description": "Numero do processo, com ou sem pontuacao"},
            },
            "required": ["numero"],
        },
    },
    {
        "name": "buscar_jurisprudencia",
        "description": "Busca jurisprudencia do TJES por texto livre. Retorna "
                       "processos com a respectiva ementa.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "termo": {"type": "string",
                          "description": "Palavras-chave da busca"},
                "base": {"type": "string",
                         "enum": ["pje1g", "pje2g", "pje2g_mono", "legado",
                                  "turma_recursal_legado"],
                         "description": "pje1g=1o grau; pje2g=acordaos (padrao); "
                                        "pje2g_mono=monocraticas; legado/turma=legado"},
                "quantidade": {"type": "integer",
                               "description": "Quantidade de resultados (padrao 15)"},
            },
            "required": ["termo"],
        },
    },
    {
        "name": "inteiro_teor",
        "description": "Retorna o texto integral de todas as sentencas, decisoes e "
                       "acordaos de um processo do TJES.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "numero": {"type": "string",
                           "description": "Numero do processo"},
            },
            "required": ["numero"],
        },
    },
]


def executar(nome, args):
    if nome == "consultar_processo":
        return _consultar_processo(args["numero"])
    if nome == "buscar_jurisprudencia":
        return _buscar_jurisprudencia(
            args["termo"], args.get("base", "pje2g"), args.get("quantidade", 15))
    if nome == "inteiro_teor":
        return _inteiro_teor(args["numero"])
    raise ValueError(f"Ferramenta desconhecida: {nome}")


# ---------------------------------------------------------------------------
# Laco JSON-RPC
# ---------------------------------------------------------------------------
def responder(id_, resultado=None, erro=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    if erro is not None:
        msg["error"] = erro
    else:
        msg["result"] = resultado
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main():
    log("servidor iniciado")
    for linha in sys.stdin:
        linha = linha.strip()
        if not linha:
            continue
        try:
            req = json.loads(linha)
        except Exception as e:  # noqa: BLE001
            log(f"JSON invalido recebido: {e}")
            continue

        metodo = req.get("method")
        id_ = req.get("id")
        params = req.get("params") or {}

        try:
            if metodo == "initialize":
                responder(id_, {
                    "protocolVersion": params.get("protocolVersion", PROTOCOLO_PADRAO),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "consulta-processual", "version": "1.0.0"},
                })
            elif metodo == "notifications/initialized":
                pass  # notificacao: nao ha resposta
            elif metodo == "ping":
                responder(id_, {})
            elif metodo == "tools/list":
                responder(id_, {"tools": FERRAMENTAS})
            elif metodo == "tools/call":
                nome = params.get("name")
                args = params.get("arguments") or {}
                try:
                    texto = executar(nome, args)
                    responder(id_, {"content": [{"type": "text", "text": texto}]})
                except Exception as e:  # noqa: BLE001
                    responder(id_, {"content": [{"type": "text",
                              "text": f"Erro ao executar '{nome}': {e}"}],
                              "isError": True})
            elif id_ is not None:
                responder(id_, erro={"code": -32601,
                          "message": f"Metodo nao suportado: {metodo}"})
        except Exception as e:  # noqa: BLE001
            log(f"erro processando {metodo}: {e}")
            if id_ is not None:
                responder(id_, erro={"code": -32603, "message": str(e)})


if __name__ == "__main__":
    main()
