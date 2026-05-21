# Instalação

## Pré-requisitos

- **Python 3.8+** (já vem no macOS e na maioria das distribuições Linux)
- **Claude Code** — para usar o modo MCP (opcional; os CLIs funcionam sem ele)
- Nenhuma biblioteca Python externa — o projeto usa só a biblioteca padrão

## Instalação rápida

```bash
git clone https://github.com/hebervalverde/mcp-consulta-processual-tjes.git
cd mcp-consulta-processual-tjes
sh instalar.sh
```

O `instalar.sh` faz três coisas:

1. Confere se o Python 3 está disponível
2. Registra o servidor MCP no Claude Code (`claude mcp add`, escopo `user`)
3. Ativa os git hooks do repositório (`core.hooksPath`)

Depois, **reinicie o Claude Code** para carregar o MCP.

## Instalação manual

### 1. Registrar o servidor MCP

```bash
claude mcp add consulta-processual --scope user -- python3 /CAMINHO/PARA/mcp_server.py
```

Troque `/CAMINHO/PARA/` pelo diretório onde você clonou o repositório.
Confira com:

```bash
claude mcp list
```

Deve aparecer `consulta-processual: ... - ✓ Connected`.

### 2. Ativar os git hooks (opcional)

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

### 3. Ativar os hooks do Claude Code (opcional)

Veja [HOOKS.md](HOOKS.md).

## Verificação

Teste o servidor MCP sem o Claude Code:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | python3 mcp_server.py
```

Deve responder com os dados de `initialize` e a lista de 3 ferramentas.

Teste os CLIs:

```bash
python3 buscar.py "concurso público CNH" --n 3
```

## Desinstalação

```bash
claude mcp remove consulta-processual --scope user
```
