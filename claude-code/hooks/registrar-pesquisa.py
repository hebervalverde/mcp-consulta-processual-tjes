#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hook PostToolUse do Claude Code.

Roda DEPOIS de cada chamada das ferramentas do MCP consulta-processual e
registra a consulta em  ~/Pesquisa-Processual/log-pesquisas.jsonl  (um JSON
por linha). Serve como trilha de auditoria das pesquisas processuais feitas.
"""

import datetime
import json
import os
import sys


def main():
    try:
        dados = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        sys.exit(0)

    ferramenta = dados.get("tool_name", "")
    if not ferramenta.startswith("mcp__consulta-processual__"):
        sys.exit(0)  # nao e uma ferramenta deste MCP

    registro = {
        "data": datetime.datetime.now().isoformat(timespec="seconds"),
        "ferramenta": ferramenta.split("__")[-1],
        "parametros": dados.get("tool_input", {}),
    }

    log = os.path.expanduser("~/Pesquisa-Processual/log-pesquisas.jsonl")
    try:
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 - falha de log nunca deve quebrar a sessao
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
