#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
capturar_anp.py — Carimbo de snapshot regulatório, etapa 1: captura.

Captura as respostas BRUTAS da API pública do Painel Dinâmico de
Descomissionamento da ANP (relatório Power BI público) e grava um snapshot
datado, imutável, acompanhado de uma ATA canônica com o SHA-256 de cada
resposta e a evidência de tempo disponível (Date do servidor, relógio local
UTC e lastRefreshTime do próprio painel).

Princípio de desenho: a fronteira de confiança termina nos BYTES servidos.
Nenhum parsing interpretativo acontece aqui; interpretação é trabalho de fora,
rastreável de volta ao bruto carimbado.

A ata é o documento que vai à atestação por TEE (etapa 2, via
Blockchain-TEE/tools/atestar_lote.py). A atestação não faz afirmação sobre
data; a evidência de tempo vive DENTRO da ata, que é o que o quote vincula.

Saída: historico/anp_<UTC>/  com as respostas brutas + ata_snapshot.json
Exit:  0 = snapshot completo · 2 = captura falhou (ex.: chave rotacionada;
       a falha em si é registrada em erro.json, porque também é evidência).
"""

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
HISTORICO = BASE_DIR / "historico"

# ---------------------------------------------------------------- alvo (ANP)
# Receita documentada em FONTES.md do depósito 10.5281/zenodo.21919402 e em
# DecomDashboard/anp_reverse_*/anp_extract.ps1. A chave é do RELATÓRIO PÚBLICO
# (?r= da página gov.br) e muda quando a ANP republica o painel.

HOST = "wabi-brazil-south-d-primary-api.analysis.windows.net"
RESOURCE_KEY = "f1e1b408-5cb4-496e-b74d-8c724088c130"
MODEL_ID = 433277
DATASET_ID = "bddf5cdf-84f2-44dc-9dde-91e9afa6bf60"
REPORT_ID = "518fe871-a3bd-4ef1-9d34-6494ba1e4143"

HEADERS = {
    "X-PowerBI-ResourceKey": RESOURCE_KEY,
    "Origin": "https://app.powerbi.com",
    "Referer": "https://app.powerbi.com/",
    "User-Agent": "Mozilla/5.0 Chrome/126 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json;charset=UTF-8",
}

TABELAS = {
    "DESCOMISSIONAMENTO_PROCESSOS": [
        "PROTOCOLO", "ANO_PROTOCOLO", "DSC_TIPO_PDI", "DSC_MODALIDADE_PDI",
        "STATUS_PDI", "DAT_APROVACAO_PDI", "DAT_INICIO_DECOM",
        "DAT_ENCERRAMENTO_SEM_APROV_PDI", "DAT_SOBRESTAMENTO", "STATUS_RDI",
        "DAT_INICIO_RDI", "DAT_APROVACAO_RDI", "DSC_FONTE", "DSC_DETALHE_EVENTO",
    ],
    "INSTALACAO": [
        "NOM_IDENTIFICACAO", "SIG_INSTALACAO", "DSC_CLASSIFICACAO_INSTO",
        "DSC_CLASSIFICACAO_UPSTREAM", "NOM_AMBIENTE", "NOM_CAMPO",
        "NOM_OPERADOR_INSTALACAO_GRUPO", "NOM_OPERADOR_CONCESSAO",
        "DSC_SITUACAO", "DSC_STATUS_OPERACAO", "MED_LAMINA_DAGUA",
        "NUM_ANO_INICIO_OPERACAO", "NUM_IDADE", "DSC_IDADE_CATEGORIA",
        "MED_LAT_ULTIMA_POSICAO", "MED_LONG_ULTIMA_POSICAO",
        "DSC_DESCOMISSIONADO_PAT", "FONTE_DESCOMISSIONAMENTO", "NOM_UF",
    ],
    "PAT_ATIVIDADES_PREVISTO": [
        "COD_CAMPO", "NUM_ANO_REFERENCIA", "COD_REVISAO_PAT", "ULTIMA_REVISAO",
        "NUM_ANO", "NOM_TIPO_ATIVIDADE", "QTD_ATIVIDADE_FISICA", "NOM_UNIDADE",
        "INVESTIMENTO [R$]",
    ],
    "PAT_DADOS_GERAIS_PREVISTO": [
        "COD_CAMPO", "NUM_ANO_REFERENCIA", "COD_REVISAO_PAT", "ULTIMA_REVISAO",
        "NOM_CAMPO", "TERRA_MAR", "NOM_BACIA", "NOM_ESTADO", "STATUS_DESCOM",
        "VAL_DESCOMISSIONAMENTO_ANALISE", "MOEDA_ANALISE",
    ],
}

# ------------------------------------------------------------------ helpers


def sha256_hex(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def agora_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def montar_query(entidade: str, colunas: list) -> dict:
    select = [{"Column": {"Expression": {"SourceRef": {"Source": "t"}},
                          "Property": c},
               "Name": f"{entidade}.{c}"} for c in colunas]
    query = {"Version": 2,
             "From": [{"Name": "t", "Entity": entidade, "Type": 0}],
             "Select": select}
    comando = {"SemanticQueryDataShapeCommand": {
        "Query": query,
        "Binding": {
            "Primary": {"Groupings": [{"Projections": list(range(len(select)))}]},
            "DataReduction": {"DataVolume": 4,
                              "Primary": {"Window": {"Count": 30000}}},
            "Version": 1}}}
    return {"version": "1.0.0",
            "queries": [{"Query": {"Commands": [comando]},
                         "QueryId": "",
                         "ApplicationContext": {
                             "DatasetId": DATASET_ID,
                             "Sources": [{"ReportId": REPORT_ID, "VisualId": ""}]}}],
            "cancelQueries": [],
            "modelId": MODEL_ID}


def requisitar(url: str, corpo: bytes | None, timeout: int = 120):
    """Devolve (status, headers_dict, bytes). Erro HTTP volta como status."""
    req = urllib.request.Request(url, data=corpo, headers=HEADERS,
                                 method="POST" if corpo else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def dotnet_datas(texto: str) -> list:
    """Extrai todos os /Date(ms)/ e devolve ISO UTC ordenado, sem duplicata."""
    achados = set()
    for m in re.finditer(r"/Date\((\d{12,14})\)/", texto):
        ms = int(m.group(1))
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        achados.add(dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    return sorted(achados)


def sanidade_querydata(dados: bytes) -> str:
    """'ok' | descrição do problema. Sem parsing interpretativo: só sinais."""
    try:
        texto = dados.decode("utf-8", "strict")
    except UnicodeDecodeError:
        return "resposta não é UTF-8"
    if "odata.error" in texto:
        return "servidor devolveu odata.error"
    if '"dsr"' not in texto:
        return "resposta sem bloco dsr (não é dado)"
    if '"descriptor"' not in texto:
        return "resposta sem descriptor"
    return "ok"


# --------------------------------------------------------------------- main


def main() -> int:
    inicio = agora_utc()
    pasta = HISTORICO / ("anp_" + inicio.replace("-", "").replace(":", "").replace("T", "_").rstrip("Z") + "Z")
    pasta.mkdir(parents=True, exist_ok=False)
    print(f"snapshot: {pasta.name}")

    registros = []
    falhas = []

    # 1) modelsAndExploration — estrutura do relatório + lastRefreshTime.
    url_meta = (f"https://{HOST}/public/reports/{RESOURCE_KEY}"
                f"/modelsAndExploration?preferReadOnlySession=true")
    st, hdr, corpo_resp = requisitar(url_meta, None)
    nome = "00_modelsAndExploration.json"
    (pasta / nome).write_bytes(corpo_resp)
    reg = {
        "arquivo": nome,
        "descricao": "estrutura do relatório e carimbos de atualização do painel",
        "requisicao": {"metodo": "GET", "url": url_meta},
        "resposta": {"status": st,
                     "date_servidor": hdr.get("Date", ""),
                     "content_type": hdr.get("Content-Type", ""),
                     "bytes": len(corpo_resp),
                     "sha256": sha256_hex(corpo_resp)},
    }
    if st != 200:
        reg["sanidade"] = f"HTTP {st} — chave de recurso provavelmente rotacionada"
        falhas.append(nome)
    else:
        texto = corpo_resp.decode("utf-8", "replace")
        reg["sanidade"] = "ok" if "lastRefreshTime" in texto else "sem lastRefreshTime"
        reg["carimbos_do_painel_utc"] = dotnet_datas(
            texto[: 2_000_000])  # lastRefresh/nextRefresh vivem no começo
    registros.append(reg)

    # 2) as quatro tabelas, em bruto.
    url_dados = f"https://{HOST}/public/reports/querydata?synchronous=true"
    if st == 200:
        for i, (entidade, colunas) in enumerate(TABELAS.items(), start=1):
            corpo_req = json.dumps(montar_query(entidade, colunas),
                                   separators=(",", ":")).encode("utf-8")
            st_t, hdr_t, corpo_t = requisitar(url_dados, corpo_req)
            nome_t = f"{i:02d}_{entidade}.json"
            (pasta / nome_t).write_bytes(corpo_t)
            san = sanidade_querydata(corpo_t) if st_t == 200 else f"HTTP {st_t}"
            if san != "ok":
                falhas.append(nome_t)
            registros.append({
                "arquivo": nome_t,
                "descricao": f"resposta bruta querydata da tabela {entidade}",
                "requisicao": {"metodo": "POST", "url": url_dados,
                               "corpo": corpo_req.decode("ascii"),
                               "corpo_sha256": sha256_hex(corpo_req)},
                "resposta": {"status": st_t,
                             "date_servidor": hdr_t.get("Date", ""),
                             "content_type": hdr_t.get("Content-Type", ""),
                             "bytes": len(corpo_t),
                             "sha256": sha256_hex(corpo_t)},
                "sanidade": san,
            })
            print(f"  {nome_t:<38} {len(corpo_t):>9,} bytes  {san}")

    fim = agora_utc()

    # Cadeia entre snapshots: cada ata registra o SHA-256 da ata anterior.
    # Remover, inserir ou reordenar um snapshot passa a ser detectável.
    anteriores = sorted(
        d for d in HISTORICO.iterdir()
        if d.is_dir() and d.name != pasta.name and (d / "ata_snapshot.json").is_file()
    )
    if anteriores:
        ult = anteriores[-1]
        cadeia = {"snapshot_anterior": ult.name,
                  "ata_anterior_sha256": sha256_hex((ult / "ata_snapshot.json").read_bytes())}
    else:
        cadeia = None   # gênese da série

    ata = {
        "cadeia": cadeia,
        "formato": "carimbo-anp/1",
        "servico": "Decommissioning Monitor — carimbo de snapshot regulatório",
        "autor": "Tadeu Santana Cordeiro (Veridis Engenharia)",
        "alvo": {
            "orgao": "Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP)",
            "painel": "Painel Dinâmico de Descomissionamento de Instalações de Exploração e Produção",
            "base_legal_publicidade": "Resolução ANP nº 817/2020, art. 14",
            "host": HOST,
            "resource_key": RESOURCE_KEY,
            "model_id": MODEL_ID,
            "dataset_id": DATASET_ID,
            "report_id": REPORT_ID,
        },
        "captura": {"inicio_utc": inicio, "fim_utc": fim,
                    "completa": not falhas, "falhas": falhas},
        "evidencia_de_tempo": {
            "relogio_local_utc": inicio,
            "date_dos_servidores": sorted({r["resposta"]["date_servidor"]
                                           for r in registros
                                           if r["resposta"]["date_servidor"]}),
            "carimbos_do_painel_utc": registros[0].get("carimbos_do_painel_utc", []),
            "nota": ("O Date é do servidor que serviu a resposta (terceiro); "
                     "os carimbos do painel são os lastRefresh/nextRefresh "
                     "publicados pelo próprio relatório."),
        },
        "arquivos": registros,
        "o_que_este_carimbo_prova": (
            "Que os arquivos listados, com estes SHA-256, foram servidos pela "
            "API pública do painel em resposta às requisições registradas. "
            "Não afirma correção do dado da ANP nem substitui o painel."),
        "contexto": {
            "deposito_relacionado": "https://doi.org/10.5281/zenodo.21919402",
            "motivo": ("O painel atualiza sem histórico público de versões e a "
                       "chave do relatório muda quando republicado; sem snapshot "
                       "carimbado, o conteúdo de uma data passada é irrecuperável."),
        },
    }

    ata_bytes = json.dumps(ata, ensure_ascii=False, sort_keys=True,
                           indent=2).encode("utf-8")
    (pasta / "ata_snapshot.json").write_bytes(ata_bytes)
    print(f"\nata_snapshot.json  {len(ata_bytes):,} bytes")
    print(f"sha256 da ata: {sha256_hex(ata_bytes)}")

    if falhas:
        (pasta / "erro.json").write_text(json.dumps(
            {"quando_utc": fim, "falhas": falhas,
             "nota": "captura incompleta registrada como evidência de volatilidade"},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nCAPTURA INCOMPLETA: {falhas} — snapshot NÃO deve ser carimbado")
        return 2

    print("captura completa — pronta para atestação (atestar_lote.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
