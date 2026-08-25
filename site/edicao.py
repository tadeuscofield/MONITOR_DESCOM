#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edicao.py — Edição semanal do Decommissioning Monitor.

Lê o snapshot ATESTADO mais recente do carimbo, faz o parse do formato DSR
do Power BI (respostas brutas), extrai os indicadores brasileiros e calcula
o delta contra a edição anterior. Só aceita snapshot com certificado de
atestação cujo document_hash bate com o SHA-256 da ata.

Portões: sem certificado → sem edição; hash divergente → aborta;
totais que não reconciliam → aborta.
"""

import hashlib
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HISTORICO = RAIZ / "carimbo" / "historico"
EDICOES = Path(__file__).resolve().parent / "edicoes"

AGU = "Fora de Operação Permanentemente - Aguarda Descomissionamento"


def sha256_hex(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def parse_dsr(bruto: dict, prefixo: str) -> list:
    """Porta fiel do Parse-DSR (anp_extract.ps1): bitmasks R (repete) e
    Ø/0x00D8 (nulo) + ValueDicts. Devolve lista de dicts por linha."""
    data = bruto["results"][0]["result"]["data"]
    sel = data["descriptor"]["Select"]
    n = len(sel)
    nomes = [s["Name"].split(".", 1)[-1] for s in sel]
    ds0 = data["dsr"]["DS"][0]
    dicts = ds0.get("ValueDicts", {})
    dm = ds0["PH"][0]["DM0"]
    col_dn = [None] * n
    prev = [None] * n
    linhas = []
    for item in dm:
        if "S" in item:
            col_dn = [c.get("DN") for c in item["S"]]
        c_vals = item.get("C", [])
        r_mask = int(item.get("R", 0))
        o_mask = int(item.get("Ø", 0))
        ci = 0
        linha = [None] * n
        for i in range(n):
            if (o_mask >> i) & 1:
                v = None
            elif (r_mask >> i) & 1:
                v = prev[i]
            else:
                v = c_vals[ci]
                ci += 1
            dn = col_dn[i]
            if dn is not None and isinstance(v, (int, float)) \
                    and not isinstance(v, bool):
                idx = int(v)
                tabela = dicts.get(dn, [])
                if 0 <= idx < len(tabela):
                    v = tabela[idx]
            linha[i] = v
            prev[i] = v
        linhas.append(dict(zip(nomes, linha)))
    return linhas


def snapshot_atestado_mais_recente():
    """Pasta do snapshot atestado mais novo, com o certificado conferido."""
    candidatos = sorted(
        (d for d in HISTORICO.iterdir() if d.is_dir()
         and (d / "ATESTADOS" / "ata_snapshot-autocontido.json").is_file()),
        reverse=True)
    if not candidatos:
        raise RuntimeError("nenhum snapshot atestado no histórico")
    pasta = candidatos[0]
    ata_hash = sha256_hex(pasta / "ata_snapshot.json")
    cert = json.loads((pasta / "ATESTADOS" / "ata_snapshot-autocontido.json")
                      .read_text(encoding="utf-8"))
    doc = (cert.get("document_hash") or "").lower().removeprefix("0x")
    if doc != ata_hash:
        raise RuntimeError(f"certificado não bate com a ata em {pasta.name}")
    if not cert.get("issuer_signature"):
        raise RuntimeError(f"certificado sem assinatura do emissor em {pasta.name}")
    return pasta, ata_hash


def indicadores(pasta: Path) -> dict:
    ata = json.loads((pasta / "ata_snapshot.json").read_text(encoding="utf-8"))
    inst = parse_dsr(json.loads((pasta / "02_INSTALACAO.json")
                                .read_text(encoding="utf-8")), "INSTALACAO")
    proc = parse_dsr(json.loads((pasta / "01_DESCOMISSIONAMENTO_PROCESSOS.json")
                                .read_text(encoding="utf-8")),
                     "DESCOMISSIONAMENTO_PROCESSOS")

    if not (1000 < len(inst) < 4000 and 100 < len(proc) < 500):
        raise RuntimeError(f"parse fora da faixa: {len(inst)} inst, {len(proc)} proc")

    mar = [r for r in inst if r.get("NOM_AMBIENTE") == "MAR"]
    sit = {}
    for r in mar:
        s = r.get("DSC_SITUACAO") or ""
        sit[s] = sit.get(s, 0) + 1

    ciclo = {"operando": sit.get("Operando", 0),
             "extensao_vida": sit.get("Operando em Extensão de Vida Útil", 0),
             "aguarda_descom": sit.get(AGU, 0),
             "em_descom": sit.get("Em Descomissionamento", 0),
             "descomissionada": sit.get("Descomissionada", 0),
             "hibernacao": sit.get("Fora de Operação Temporariamente - Hibernação", 0),
             "em_construcao": sit.get("Em Construção", 0)}
    ciclo["outras"] = len(mar) - sum(ciclo.values())
    if ciclo["outras"] < 0:
        raise RuntimeError("reconciliação de situações falhou")

    def data_iso(v):
        """Power BI devolve datas como epoch em ms; strings passam direto."""
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            from datetime import datetime, timezone
            return datetime.fromtimestamp(v / 1000, tz=timezone.utc).date().isoformat()
        return (v or "")[:10]

    pdi_aprov = sum(1 for r in proc if r.get("STATUS_PDI") == "Aprovado")
    pdi_receb = sum(1 for r in proc if r.get("STATUS_PDI") == "Recebido")
    rdi_aprov = sum(1 for r in proc if r.get("STATUS_RDI") == "Aprovado")
    ult_pdi = max((data_iso(r.get("DAT_APROVACAO_PDI")) for r in proc), default="")
    ult_rdi = max((data_iso(r.get("DAT_APROVACAO_RDI")) for r in proc), default="")

    carimbos = ata["evidencia_de_tempo"]["carimbos_do_painel_utc"]
    fim = ata["captura"]["fim_utc"]
    refresh = max((c for c in carimbos if c <= fim), default="")

    return {"snapshot": pasta.name,
            "captura_utc": ata["captura"]["inicio_utc"],
            "painel_refresh_utc": refresh,
            "total_offshore": len(mar),
            "total_processos": len(proc),
            "ciclo": ciclo,
            "pdi_aprovados": pdi_aprov,
            "pdi_recebidos": pdi_receb,
            "rdi_aprovados": rdi_aprov,
            "ultima_aprovacao_pdi": ult_pdi,
            "ultima_aprovacao_rdi": ult_rdi}


def gerar_edicao() -> dict:
    """Indicadores da edição atual + delta contra a anterior + persistência."""
    pasta, ata_hash = snapshot_atestado_mais_recente()
    atual = indicadores(pasta)
    atual["ata_sha256"] = ata_hash

    EDICOES.mkdir(exist_ok=True)
    anteriores = sorted(EDICOES.glob("ed_*.json"))
    anterior = None
    for p in reversed(anteriores):
        j = json.loads(p.read_text(encoding="utf-8"))
        if j["snapshot"] != atual["snapshot"]:
            anterior = j
            break

    delta = {}
    if anterior:
        chaves = [("total_offshore", None), ("pdi_aprovados", None),
                  ("pdi_recebidos", None), ("rdi_aprovados", None)]
        for k, _ in chaves:
            delta[k] = atual[k] - anterior[k]
        for k in atual["ciclo"]:
            delta["ciclo." + k] = atual["ciclo"][k] - anterior["ciclo"].get(k, 0)
        atual["delta_contra"] = anterior["snapshot"]
    atual["delta"] = delta

    destino = EDICOES / f"ed_{atual['snapshot']}.json"
    destino.write_text(json.dumps(atual, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    return atual


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass
    ed = gerar_edicao()
    print(json.dumps(ed, ensure_ascii=False, indent=2))
