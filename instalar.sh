#!/bin/sh
# Instalador do MCP consulta-processual-tjes.
#
# O que faz:
#   1. Confere se o Python 3 esta disponivel
#   2. Registra o servidor MCP no Claude Code (escopo user)
#   3. Ativa os git hooks do repositorio
#
# Uso:  sh instalar.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
echo "==> Projeto: $DIR"
echo ""

# 1. Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERRO: Python 3 nao encontrado. Instale o Python 3 e rode de novo."
    exit 1
fi
echo "==> Python 3 encontrado: $(python3 --version)"

# 2. Servidor MCP
if command -v claude >/dev/null 2>&1; then
    if claude mcp add consulta-processual --scope user -- python3 "$DIR/mcp_server.py" 2>/dev/null; then
        echo "==> MCP 'consulta-processual' registrado no Claude Code."
    else
        echo "==> MCP ja registrado (ou falha). Verifique com: claude mcp list"
    fi
else
    echo "==> Claude Code (comando 'claude') nao encontrado no PATH."
    echo "    Registre o MCP manualmente depois (veja docs/INSTALACAO.md)."
fi

# 3. Git hooks
if [ -d "$DIR/.git" ]; then
    git -C "$DIR" config core.hooksPath .githooks
    chmod +x "$DIR/.githooks/pre-commit" 2>/dev/null
    echo "==> Git hooks ativados (core.hooksPath = .githooks)."
else
    echo "==> Diretorio nao e um repositorio git; git hooks nao ativados."
fi

echo ""
echo "Instalacao concluida. Proximos passos:"
echo "  1. Reinicie o Claude Code para carregar o MCP."
echo "  2. (Opcional) Ative os hooks do Claude Code: veja docs/HOOKS.md"
