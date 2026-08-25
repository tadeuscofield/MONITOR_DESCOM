#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificar_snapshot.py — Carimbo de snapshot regulatório, verificação.

O que ESTE script verifica (biblioteca padrão, sem rede):
  1. Cada arquivo do snapshot bate com o SHA-256 registrado na ata.
  2. O SHA-256 da ata em disco.
  3. Se houver certificado de atestação: o document_hash do certificado é o
     hash da ata, e o report_data[0:32] do quote TDX vincula exatamente esse
     hash (binding RAW, offset 568 do quote v4).

O que este script NÃO verifica, e onde se verifica:
  - cadeia PCK até a raiz Intel pinada, assinaturas ECDSA, medições do build,
    assinatura do emissor, revogação e TCB — isso é o verificador DCAP
    completo (DCAP-Offline-Verifier/cli.py, 5 carimbos, exit 0).

Uso:  python verificar_snapshot.py <pasta_do_snapshot> [certificado.json]
Exit: 0 = tudo que este script checa confere · 1 = alguma divergência.
"""

import hashlib
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

OFFSET_REPORT_DATA_TDX_V4 = 568   # Header(48) + report_data@520 do TD Report


def sha256_hex(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    pasta = Path(sys.argv[1])
    cert_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    ata_path = pasta / "ata_snapshot.json"
    if not ata_path.is_file():
        print(f"FALHA: {ata_path} não existe")
        return 1

    ata_hash = sha256_hex(ata_path)
    ata = json.loads(ata_path.read_text(encoding="utf-8"))
    print(f"snapshot : {pasta.name}")
    print(f"ata      : sha256 {ata_hash}")
    print(f"captura  : {ata['captura']['inicio_utc']}  completa={ata['captura']['completa']}")
    print("-" * 72)

    falhas = 0

    # 0) elo da cadeia, quando declarado
    cadeia = ata.get("cadeia")
    if cadeia:
        ant = pasta.parent / cadeia["snapshot_anterior"] / "ata_snapshot.json"
        if not ant.is_file():
            print(f"FALHA  cadeia: ata anterior ausente ({cadeia['snapshot_anterior']})")
            falhas += 1
        elif sha256_hex(ant) != cadeia["ata_anterior_sha256"]:
            print(f"FALHA  cadeia: hash da ata anterior diverge do declarado")
            falhas += 1
        else:
            print(f"OK     cadeia: elo com {cadeia['snapshot_anterior']} confere")

    # 1) arquivos x ata
    for reg in ata["arquivos"]:
        p = pasta / reg["arquivo"]
        if not p.is_file():
            print(f"FALHA  {reg['arquivo']}: arquivo ausente")
            falhas += 1
            continue
        h = sha256_hex(p)
        esperado = reg["resposta"]["sha256"]
        tam = p.stat().st_size
        if h == esperado and tam == reg["resposta"]["bytes"]:
            print(f"OK     {reg['arquivo']:<38} {tam:>9,} bytes  hash confere")
        else:
            print(f"FALHA  {reg['arquivo']}: hash/tamanho divergem da ata")
            print(f"       ata: {esperado} · disco: {h}")
            falhas += 1

    # 2) certificado, se fornecido
    if cert_path:
        print("-" * 72)
        if not cert_path.is_file():
            print(f"FALHA  certificado ausente: {cert_path}")
            falhas += 1
        else:
            cert = json.loads(cert_path.read_text(encoding="utf-8"))
            doc_hash = (cert.get("document_hash") or "").lower().removeprefix("0x")
            if doc_hash == ata_hash:
                print(f"OK     certificado.document_hash == sha256 da ata")
            else:
                print(f"FALHA  certificado.document_hash != sha256 da ata")
                print(f"       cert: {doc_hash}")
                falhas += 1

            quote_hex = cert.get("quote_hex") or ""
            try:
                quote = bytes.fromhex(quote_hex)
            except ValueError:
                quote = b""
            if len(quote) >= OFFSET_REPORT_DATA_TDX_V4 + 64:
                versao = int.from_bytes(quote[0:2], "little")
                rd = quote[OFFSET_REPORT_DATA_TDX_V4:
                           OFFSET_REPORT_DATA_TDX_V4 + 64]
                if versao != 4:
                    print(f"FALHA  quote não é TDX v4 (versão {versao})")
                    falhas += 1
                elif rd[0:32].hex() == ata_hash:
                    print(f"OK     report_data[0:32] do quote vincula a ata (binding RAW)")
                    print(f"       report_data[32:64] (commitment do emissor): {rd[32:64].hex()}")
                else:
                    print(f"FALHA  report_data[0:32] NÃO vincula a ata")
                    print(f"       quote: {rd[0:32].hex()}")
                    falhas += 1
            else:
                print("FALHA  quote ausente ou curto demais para TDX v4")
                falhas += 1

            assinado = bool(cert.get("issuer_signature"))
            print(f"{'OK   ' if assinado else 'AVISO'}  assinatura do emissor "
                  f"{'presente' if assinado else 'AUSENTE (pré-certificado; falta finalize)'}")
            if not assinado:
                falhas += 1

    print("-" * 72)
    print("Este script NÃO verificou: cadeia PCK→raiz Intel, ECDSA, medições do")
    print("build, revogação e TCB. Verificação completa (5 carimbos):")
    print("  python DCAP-Offline-Verifier/cli.py --cert <certificado.json>")
    print("-" * 72)
    print("VEREDITO PARCIAL:", "OK" if falhas == 0 else f"{falhas} FALHA(S)")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
