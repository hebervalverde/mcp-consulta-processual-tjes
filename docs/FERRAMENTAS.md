# Ferramentas

## Ferramentas MCP (no Claude Code)

Depois de registrar o MCP e reiniciar o Claude Code, peça em linguagem
natural — o Claude escolhe a ferramenta certa.

### `consultar_processo`

Metadados, andamentos e lista de decisões de um processo.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `numero` | string | sim | Número do processo, com ou sem pontuação |

### `buscar_jurisprudencia`

Busca jurisprudência por texto livre.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `termo` | string | sim | Palavras-chave |
| `base` | string | não | `pje1g`, `pje2g` (padrão), `pje2g_mono`, `legado`, `turma_recursal_legado` |
| `quantidade` | inteiro | não | Número de resultados (padrão 15) |

### `inteiro_teor`

Texto integral de todas as decisões de um processo.

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `numero` | string | sim | Número do processo |

## Ferramentas de linha de comando

### `consultar.py`

```bash
python3 consultar.py 5032569-92.2023.8.08.0024
```

Gera, em `processos/<numero>/`:

- `datajud.json` — metadados crus do DataJud
- `movimentos.txt` — linha do tempo legível
- `decisoes/` — inteiro teor de cada decisão (`.txt`, `.html`, `.meta.json`)
- `RESUMO.md` — visão consolidada

### `buscar.py`

```bash
python3 buscar.py "termos de busca" [--core BASE] [--n NUM] [--exato]
```

| Opção | Descrição |
|---|---|
| `--core` | Base a pesquisar (padrão `pje2g`) |
| `--n` | Quantidade de resultados (padrão 20) |
| `--exato` | Busca a expressão exata (frase entre aspas) |

Os resultados são salvos em `buscas/`.

## Bases de jurisprudência (cores)

| Core | Conteúdo | Volume aproximado |
|---|---|---|
| `pje1g` | 1º grau (PJe) — sentenças e decisões | ~1,4 milhão |
| `pje2g` | 2º grau (PJe) — acórdãos | ~200 mil |
| `pje2g_mono` | 2º grau (PJe) — decisões monocráticas | ~88 mil |
| `legado` | Jurisprudência de sistemas antigos | ~327 mil |
| `turma_recursal_legado` | Turmas Recursais (legado) | ~59 mil |
