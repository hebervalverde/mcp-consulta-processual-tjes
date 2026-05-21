# Arquitetura

## Visão geral

```
                       ┌──────────────────────────┐
   Claude Code  ──MCP──▶│      mcp_server.py       │
   (3 ferramentas)      │  (JSON-RPC 2.0 / stdio)  │
                        └────────────┬─────────────┘
   CLIs ────────────────▶            │
   consultar.py                      ▼
   buscar.py            ┌──────────────────────────┐
                        │         tjes.py          │
                        │       (biblioteca)       │
                        └──────┬────────────┬──────┘
                               │            │
                  ┌────────────▼──┐   ┌─────▼──────────────────┐
                  │  DataJud/CNJ  │   │  Jurisprudência TJES   │
                  │  (Elastic)    │   │  (Apache Solr público) │
                  └───────────────┘   └────────────────────────┘
```

Tudo passa por `tjes.py`. O servidor MCP e os CLIs são apenas camadas finas
em cima da biblioteca.

## Fonte 1 — DataJud / CNJ

API pública do Conselho Nacional de Justiça com metadados e movimentos de
todos os processos do país.

- **Endpoint:** `https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal}/_search`
- **Método:** `POST`
- **Autenticação:** header `Authorization: APIKey ...` — a chave é **pública**
  e divulgada pelo próprio CNJ na documentação do DataJud (não é segredo).
- **Corpo:** consulta Elasticsearch, ex.: `{"query":{"match":{"numeroProcesso":"<20 dígitos>"}}}`
- **Retorna:** classe, assuntos, órgão julgador, datas e a lista completa de
  movimentos. **Não retorna** o texto dos documentos.

## Fonte 2 — Jurisprudência do TJES

Sistema de consulta de jurisprudência do Tribunal de Justiça do ES, com backend
Apache Solr. É **público, sem captcha e sem login**.

- **Endpoint:** `https://sistemas.tjes.jus.br/consulta-jurisprudencia/api/search`
- **Método:** `GET` com parâmetros `core`, `q`, `page`, `per_page`, `sort`
- **`q`:** sintaxe de query do Solr. Ex.: `nr_processo:"5032569-92.2023.8.08.0024"`
  para um processo específico, ou texto livre para busca temática.
- **Retorna:** o **inteiro teor** das sentenças, decisões e acórdãos, além de
  ementa, magistrado, órgão julgador, classe e assunto.

As cinco bases (cores Solr) estão documentadas em [FERRAMENTAS.md](FERRAMENTAS.md).

## Número de processo (padrão CNJ)

O formato é `NNNNNNN-DD.AAAA.J.TR.OOOO` (20 dígitos). O `tjes.py` normaliza
automaticamente: aceita com ou sem pontuação e converte conforme a fonte exige
(o DataJud usa só dígitos; a jurisprudência usa o formato pontuado).

## Observação sobre TLS/SSL

Em ambientes com proxy que inspeciona HTTPS (comum em redes corporativas), a
verificação de certificado pode falhar. O `tjes.py` tenta a verificação normal
e, se ela falhar com erro de certificado, repete a requisição com a verificação
desativada. É aceitável aqui porque são consultas **somente leitura** a
endpoints públicos do governo, sem envio de credenciais.

## O que o projeto NÃO acessa

Petições das partes e peças internas em PDF dependem de habilitação no PJe (ser
parte ou advogado no processo) e **não** são cobertas. O projeto cobre
metadados, movimentos e o inteiro teor de todas as **decisões judiciais**.
