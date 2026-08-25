#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conferir_carimbo.py — afere o portão do post 08 antes de publicar.

O post 08 afirma, em presente, que a captura roda por rotina diária, que os
registros se encadeiam por hash e que vão para atestação em lotes. Nenhuma
dessas três coisas pode ser publicada sem contagem. Este script conta:

  1. dias cobertos pela captura, e quais dias faltaram desde o início;
  2. quantas atas carregam o elo da cadeia;
  3. quantos lotes de atestação em hardware saíram, e se algum snapshot tem
     tentativa em modo local sem quote guardada junto do certificado;
  4. se o certificado mais recente ainda confere com a ata.

Uso:  python conferir_carimbo.py [--minimo-lotes 3]

Exit 0 = o post 08 pode sair como está escrito.
Exit 1 = há buraco: o texto precisa ser ajustado ao que existe, ou o post espera.
"""

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

RAIZ = Path(__file__).resolve().parent
HISTORICO = RAIZ / "carimbo" / "historico"
HORA_AGENDADA = 12   # a tarefa roda às 11h30; antes disso o dia ainda não venceu


def sha256_hex(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minimo-lotes", type=int, default=3,
                    help="lotes de atestação exigidos pelo semáforo do post 08")
    ap.add_argument("--ate", help="data final da janela, AAAA-MM-DD (padrão: hoje)")
    a = ap.parse_args()

    if not HISTORICO.is_dir():
        print("FALHA: histórico de capturas não existe"); return 1

    snaps = sorted(d for d in HISTORICO.iterdir()
                   if d.is_dir() and (d / "ata_snapshot.json").is_file())
    if not snaps:
        print("FALHA: nenhuma captura no histórico"); return 1

    # 1. cobertura por dia
    dias = {}
    for d in snaps:
        ata = json.loads((d / "ata_snapshot.json").read_text(encoding="utf-8"))
        dia = ata["captura"]["inicio_utc"][:10]
        dias.setdefault(dia, []).append(d.name)

    inicio = datetime.date.fromisoformat(min(dias))
    fim = datetime.date.fromisoformat(a.ate) if a.ate else datetime.date.today()
    # O dia corrente só conta como buraco DEPOIS da hora agendada. Antes disso a
    # captura ainda vai acontecer, e acusar falta seria alarme falso.
    if not a.ate and fim == datetime.date.today() \
            and datetime.datetime.now().hour < HORA_AGENDADA:
        fim -= datetime.timedelta(days=1)
    esperados = [inicio + datetime.timedelta(days=i)
                 for i in range((fim - inicio).days + 1)]
    faltando = [d.isoformat() for d in esperados if d.isoformat() not in dias]

    # 2. cadeia
    com_elo = 0
    for d in snaps:
        ata = json.loads((d / "ata_snapshot.json").read_text(encoding="utf-8"))
        if ata.get("cadeia"):
            com_elo += 1

    # 3. lotes atestados e higiene do lote
    atestados, sujos = [], []
    for d in snaps:
        cert = d / "ATESTADOS" / "ata_snapshot-autocontido.json"
        if cert.is_file():
            atestados.append(d)
        lote = d / "ATESTADOS" / "lote_manifesto.csv"
        if lote.is_file() and "LOCAL (CVM desligada" in lote.read_text(
                encoding="utf-8-sig", errors="replace"):
            sujos.append(d.name)

    # 4. o certificado mais novo ainda confere
    cert_ok = None
    if atestados:
        d = atestados[-1]
        c = json.loads((d / "ATESTADOS" / "ata_snapshot-autocontido.json")
                       .read_text(encoding="utf-8"))
        doc = (c.get("document_hash") or "").lower().removeprefix("0x")
        cert_ok = (doc == sha256_hex(d / "ata_snapshot.json")
                   and bool(c.get("issuer_signature")))

    print(f"janela      : {inicio.isoformat()} a {fim.isoformat()}  "
          f"({len(esperados)} dias)")
    print(f"capturas    : {len(snaps)} em {len(dias)} dia(s) distinto(s)")
    print(f"cadeia      : {com_elo} de {len(snaps)} atas com elo")
    print(f"atestação   : {len(atestados)} lote(s) em hardware, mínimo exigido {a.minimo_lotes}")
    if cert_ok is not None:
        print(f"certificado : {'confere com a ata e está assinado' if cert_ok else 'NÃO CONFERE'}")
    print("-" * 70)

    falhas = []
    if faltando:
        falhas.append(f"{len(faltando)} dia(s) sem captura: "
                      + ", ".join(faltando[:8]) + ("…" if len(faltando) > 8 else ""))
    if len(atestados) < a.minimo_lotes:
        falhas.append(f"lotes de atestação insuficientes: {len(atestados)} de {a.minimo_lotes}")
    if com_elo < len(snaps) - 2:
        falhas.append(f"cadeia incompleta além das duas atas de gênese: {com_elo}/{len(snaps)}")
    if sujos:
        falhas.append("lote com tentativa em modo local junto do certificado: "
                      + ", ".join(sujos))
    if cert_ok is False:
        falhas.append("o certificado mais recente não confere com a ata")

    if not falhas:
        print("PORTÃO ABERTO: o post 08 pode sair afirmando rotina diária,")
        print("encadeamento e atestação em lotes, como está escrito.")
        return 0

    print("PORTÃO FECHADO. O post 08 NÃO pode sair como está escrito:")
    for f in falhas:
        print("  · " + f)
    print()
    print("Caminhos: rodar o ciclo que falta, ou ajustar o texto ao que existe")
    print("(tirar 'diária', dizer o número real de lotes), nunca publicar assim.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
