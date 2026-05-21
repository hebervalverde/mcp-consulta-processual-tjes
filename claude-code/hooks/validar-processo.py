#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hook PreToolUse do Claude Code.

Roda ANTES de cada chamada das ferramentas do MCP consulta-processual.
Se a ferramenta recebe um numero de processo, valida que ele tem 20 digitos
(padrao CNJ). Numero invalido -> a chamada e bloqueada, evitando consulta inutil.

Ferramentas sem numero (ex.: buscar_jurisprudencia) passam direto.
"""

import json
import re
import sys


def main():
    try:
        dados = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 - entrada inesperada: nao atrapalha o fluxo
        sys.exit(0)

    entrada = dados.get("tool_input", {}) or {}
    numero = entrada.get("numero")
    if numero is None:
        sys.exit(0)  # ferramenta nao usa numero de processo -> libera

    digitos = re.sub(r"\D", "", str(numero))
    if len(digitos) != 20:
        saida = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Numero de processo invalido: '{numero}' resultou em "
                    f"{len(digitos)} digitos (o padrao CNJ exige 20). "
                    "Confira o numero antes de consultar."
                ),
            }
        }
        print(json.dumps(saida, ensure_ascii=False))

    sys.exit(0)


if __name__ == "__main__":
    main()
