# Hooks

O projeto traz dois tipos de hook: **hooks do Claude Code** (automatizam o uso
do MCP) e **git hooks** (qualidade do código do repositório).

## Hooks do Claude Code

Ficam em `claude-code/hooks/`. São scripts que o Claude Code executa
automaticamente em torno das chamadas das ferramentas do MCP.

### `validar-processo.py` — evento `PreToolUse`

Roda **antes** de cada chamada de ferramenta do MCP. Se a ferramenta recebe um
número de processo, valida que ele tem 20 dígitos (padrão CNJ). Número inválido
→ a chamada é **bloqueada**, com uma mensagem explicativa, evitando uma consulta
inútil à API. Ferramentas sem número (como `buscar_jurisprudencia`) passam direto.

### `registrar-pesquisa.py` — evento `PostToolUse`

Roda **depois** de cada chamada. Registra a consulta em
`~/Pesquisa-Processual/log-pesquisas.jsonl` (um JSON por linha) — uma trilha de
auditoria de todas as pesquisas processuais feitas.

### Como ativar

Copie o bloco `hooks` do arquivo [`../claude-code/settings.example.json`](../claude-code/settings.example.json)
para o seu `~/.claude/settings.json`. Se você já tem um bloco `hooks`, mescle
os arrays `PreToolUse` e `PostToolUse` em vez de sobrescrever.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__consulta-processual__.*",
        "hooks": [
          { "type": "command", "command": "python3 \"$HOME/Pesquisa-Processual/claude-code/hooks/validar-processo.py\"" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__consulta-processual__.*",
        "hooks": [
          { "type": "command", "command": "python3 \"$HOME/Pesquisa-Processual/claude-code/hooks/registrar-pesquisa.py\"" }
        ]
      }
    ]
  }
}
```

> **Ajuste o caminho** `$HOME/Pesquisa-Processual` se você clonou o repositório
> em outro lugar. Reinicie o Claude Code depois de editar o `settings.json`.

O `matcher` `mcp__consulta-processual__.*` é uma expressão regular que casa com
as três ferramentas do MCP (`consultar_processo`, `buscar_jurisprudencia`,
`inteiro_teor`).

## Git hooks

Fica em `.githooks/pre-commit`. Antes de cada commit, valida a sintaxe de todos
os arquivos Python alterados (`python3 -m py_compile`) e, se o `flake8` estiver
instalado, roda também o lint. Commit com erro de sintaxe é abortado.

### Como ativar

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

(O `instalar.sh` já faz isso.)
