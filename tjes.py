#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tjes.py - Biblioteca de consulta processual (TJES + DataJud/CNJ).

Zero dependencias: usa apenas a biblioteca padrao do Python 3.

Fontes publicas usadas (sem login de advogado, sem captcha):
  1. DataJud / CNJ
     - Metadados + TODOS os movimentos de qualquer processo de qualquer
       tribunal do Brasil. Nao traz o texto dos documentos.
  2. Jurisprudencia do TJES (backend Apache Solr)
     - Inteiro teor de sentencas e decisoes de 1o grau, acordaos, ementas
       e decisoes monocraticas de 2o grau. 5 bases, +2 milhoes de docs.

O que NAO da para pegar por aqui: peticoes das partes e pecas internas
em PDF -> isso exige habilitacao no PJe (ser parte/advogado no processo).
"""

import json
import re
import ssl
import urllib.request
import urllib.parse

# Contexto SSL: tenta a verificacao normal; se o ambiente tiver um proxy que
# inspeciona HTTPS (certificado proprio na cadeia), cai para um contexto sem
# verificacao. Aceitavel aqui porque sao consultas SO-LEITURA a endpoints
# publicos do governo, sem envio de credenciais ou dados sensiveis.
try:
    _SSL_CTX = ssl.create_default_context()
    # Heuristica: se houver um cert.pem do sistema, usa-o.
    import os as _os
    for _ca in ("/etc/ssl/cert.pem", "/usr/local/etc/openssl/cert.pem"):
        if _os.path.exists(_ca):
            _SSL_CTX.load_verify_locations(_ca)
            break
except Exception:  # noqa: BLE001
    _SSL_CTX = ssl._create_unverified_context()

_SSL_CTX_INSEGURO = ssl._create_unverified_context()

# --- DataJud / CNJ -----------------------------------------------------------
# Chave publica oficial do CNJ (publicada na wiki do DataJud, nao e segredo).
DATAJUD_KEY = "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
DATAJUD_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_{trib}/_search"

# --- Jurisprudencia TJES (Solr) ---------------------------------------------
JURIS_API = "https://sistemas.tjes.jus.br/consulta-jurisprudencia/api"
# Bases (cores Solr) disponiveis e o que cada uma contem:
JURIS_CORES = {
    "pje1g":                "1o grau (PJe) - sentencas e decisoes",
    "pje2g":                "2o grau (PJe) - acordaos",
    "pje2g_mono":           "2o grau (PJe) - decisoes monocraticas",
    "legado":               "Jurisprudencia legada (sistemas antigos)",
    "turma_recursal_legado":"Turmas Recursais (legado)",
}


# ---------------------------------------------------------------------------
# Utilitarios de numero CNJ
# ---------------------------------------------------------------------------
def so_digitos(numero):
    """Remove tudo que nao for digito. '5032569-92.2023.8.08.0024' -> 20 digitos."""
    return re.sub(r"\D", "", str(numero))


def formatar_cnj(numero):
    """Formata 20 digitos no padrao CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO."""
    d = so_digitos(numero)
    if len(d) != 20:
        return str(numero)
    return f"{d[0:7]}-{d[7:9]}.{d[9:13]}.{d[13:14]}.{d[14:16]}.{d[16:20]}"


# ---------------------------------------------------------------------------
# Camada HTTP (urllib puro)
# ---------------------------------------------------------------------------
def _http(url, corpo=None, headers=None, timeout=60):
    """Faz uma requisicao HTTP. Se 'corpo' vier preenchido, e POST; senao, GET."""
    req = urllib.request.Request(url, data=corpo, method="POST" if corpo else "GET")
    req.add_header("User-Agent", "Mozilla/5.0 (consulta-processual; +tjes.py)")
    req.add_header("Accept", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return resp.read()
    except urllib.error.URLError as e:
        # Falha de verificacao de certificado -> repete sem verificar.
        if isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
            with urllib.request.urlopen(req, timeout=timeout,
                                        context=_SSL_CTX_INSEGURO) as resp:
                return resp.read()
        raise


# ---------------------------------------------------------------------------
# 1. DataJud / CNJ - metadados + movimentos
# ---------------------------------------------------------------------------
def datajud(numero, tribunal="tjes"):
    """
    Consulta um processo no DataJud do CNJ.
    Retorna uma lista de registros (um por grau: G1, G2, ...).
    """
    corpo = json.dumps({"query": {"match": {"numeroProcesso": so_digitos(numero)}}}).encode()
    raw = _http(
        DATAJUD_URL.format(trib=tribunal),
        corpo=corpo,
        headers={"Authorization": DATAJUD_KEY, "Content-Type": "application/json"},
    )
    dados = json.loads(raw)
    return [h["_source"] for h in dados.get("hits", {}).get("hits", [])]


def movimentos_ordenados(registro):
    """Devolve os movimentos de um registro do DataJud em ordem cronologica."""
    movs = registro.get("movimentos", []) or []
    return sorted(movs, key=lambda m: m.get("dataHora", ""))


# ---------------------------------------------------------------------------
# 2. Jurisprudencia TJES - inteiro teor das decisoes
# ---------------------------------------------------------------------------
def jurisp_search(core, q="*:*", page=1, per_page=10, sort=None, **filtros):
    """
    Busca generica na jurisprudencia do TJES (sintaxe de query do Solr).
      core     : uma das chaves de JURIS_CORES
      q        : query Solr. Ex.: 'PMES concurso soldado', 'campo:"valor"'
      filtros  : filtros adicionais aceitos pela API (ex.: classe_judicial=...)
    """
    params = {"core": core, "q": q, "page": page, "per_page": per_page}
    if sort:
        params["sort"] = sort
    params.update({k: v for k, v in filtros.items() if v not in (None, "")})
    url = JURIS_API + "/search?" + urllib.parse.urlencode(params)
    return json.loads(_http(url))


def jurisp_processo(numero):
    """
    Recupera TODAS as decisoes de um processo (inteiro teor) em todas as bases.
    Retorna dict {core: [docs]} apenas com os cores que tiveram resultado.
    """
    nro = formatar_cnj(numero)
    digitos = so_digitos(numero)
    resultado = {}
    for core in JURIS_CORES:
        try:
            r = jurisp_search(core, q=f'nr_processo:"{nro}"', per_page=100)
            docs = [d for d in r.get("docs", [])
                    if so_digitos(d.get("nr_processo", "")) == digitos]
            if docs:
                resultado[core] = docs
        except Exception as e:  # noqa: BLE001 - queremos seguir nas outras bases
            resultado[core] = {"erro": str(e)}
    return resultado


def texto_decisao(doc):
    """Extrai o texto plano de um documento de jurisprudencia (qualquer core)."""
    return (doc.get("inteiro_teor") or doc.get("acordao")
            or doc.get("decisao") or doc.get("ementa") or "").strip()


def html_decisao(doc):
    """Extrai a versao HTML de um documento de jurisprudencia, se houver."""
    return (doc.get("inteiro_teor_html") or doc.get("acordao_html")
            or doc.get("decisao_html") or doc.get("ementa_html") or "").strip()


# ---------------------------------------------------------------------------
# Execucao direta para teste rapido: python3 tjes.py <numero>
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("uso: python3 tjes.py <numero-do-processo>")
        sys.exit(1)
    n = sys.argv[1]
    print("Numero formatado:", formatar_cnj(n))
    print("DataJud:", len(datajud(n)), "registro(s)")
    jp = jurisp_processo(n)
    for c, docs in jp.items():
        print(f"Jurisprudencia[{c}]:",
              (f"{len(docs)} doc(s)" if isinstance(docs, list) else docs))
