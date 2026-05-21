# 🏛️ MCP Consulta Processual — TJES

Servidor **MCP** (Model Context Protocol) + ferramentas de linha de comando
para consultar **processos judiciais e jurisprudência do Tribunal de Justiça
do Espírito Santo (TJES)** — direto do Claude Code, em linguagem natural.

Sem precisar ser advogado, sem login no PJe, sem captcha.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Dependências](https://img.shields.io/badge/depend%C3%AAncias-zero-brightgreen)
![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

---

## ✨ O que faz

| Você pede | A ferramenta entrega |
|---|---|
| Consultar um processo | Classe, órgão julgador e **todos os andamentos** (via DataJud/CNJ) |
| Ler as decisões de um processo | **Inteiro teor** de sentenças, decisões e acórdãos |
| Pesquisar jurisprudência | Acórdãos e sentenças do TJES por palavra-chave, com ementa |

## 🔌 Fontes de dados (públicas e oficiais)

| Fonte | O que fornece |
|---|---|
| **DataJud / CNJ** | Metadados + movimentos de qualquer processo do Brasil |
| **Jurisprudência TJES** (Apache Solr público) | Inteiro teor de decisões — 5 bases, +2 milhões de documentos |

Detalhes técnicos em [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md).

## 🚀 Instalação

```bash
git clone https://github.com/hebervalverde/mcp-consulta-processual-tjes.git
cd mcp-consulta-processual-tjes
sh instalar.sh
```

Depois, **reinicie o Claude Code**. Guia completo em
[`docs/INSTALACAO.md`](docs/INSTALACAO.md).

## 💬 Uso — modo MCP (Claude Code)

Depois de instalado, é só pedir em português:

> *"consulta o processo 5032569-92.2023.8.08.0024"*
> *"busca jurisprudência do TJES sobre eliminação por CNH em concurso"*
> *"me traz o inteiro teor das decisões do processo 5032569-92.2023.8.08.0024"*

Ferramentas expostas: `consultar_processo`, `buscar_jurisprudencia`,
`inteiro_teor` — referência em [`docs/FERRAMENTAS.md`](docs/FERRAMENTAS.md).

## 🖥️ Uso — modo linha de comando

```bash
# Dossiê completo de um processo (andamentos + inteiro teor das decisões)
python3 consultar.py 5032569-92.2023.8.08.0024

# Buscar jurisprudência
python3 buscar.py "PMES concurso CNH eliminação"
python3 buscar.py "investigação social soldado" --core pje2g --n 30
```

## 🪝 Hooks

O projeto inclui dois tipos de hook — documentados em [`docs/HOOKS.md`](docs/HOOKS.md):

- **Hooks do Claude Code** (`claude-code/hooks/`)
  - `validar-processo.py` (`PreToolUse`) — bloqueia consultas com número de
    processo inválido antes de chamar a API.
  - `registrar-pesquisa.py` (`PostToolUse`) — registra cada consulta em
    `log-pesquisas.jsonl` como trilha de auditoria.
- **Git hook** (`.githooks/pre-commit`) — valida a sintaxe Python (e roda
  `flake8`, se disponível) antes de cada commit.

## 📁 Estrutura

```
mcp-consulta-processual-tjes/
├── tjes.py                 Biblioteca (DataJud + Jurisprudência)
├── mcp_server.py           Servidor MCP (JSON-RPC 2.0 / stdio)
├── consultar.py            CLI: dossiê de um processo
├── buscar.py               CLI: busca de jurisprudência
├── instalar.sh             Instalador (MCP + git hooks)
├── claude-code/
│   ├── settings.example.json   Exemplo de hooks do Claude Code
│   └── hooks/                  Scripts dos hooks
├── .githooks/
│   └── pre-commit          Git hook de qualidade
└── docs/
    ├── INSTALACAO.md
    ├── FERRAMENTAS.md
    ├── HOOKS.md
    └── ARQUITETURA.md
```

## ⚠️ Limitações

Não baixa **petições das partes nem peças internas em PDF** — isso exige
habilitação no PJe (ser parte ou advogado no processo). O projeto cobre
metadados, andamentos e o inteiro teor de **todas as decisões judiciais**.

## ⚖️ Aviso legal

Ferramenta independente, sem vínculo com o TJES ou o CNJ. Usa exclusivamente
APIs **públicas** e dados de **acesso público**. Processos em segredo de justiça
não são acessíveis por estas fontes. Use de forma responsável e respeite a
LGPD ao tratar dados pessoais que apareçam em decisões.

## 📄 Licença

[MIT](LICENSE) © 2026 Heber Valverde
