#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refinalizar_com_frescor.py — acrescenta o frescor aos certificados já emitidos.

NÃO reatesta nada. O quote, que é a prova do hardware, já existe e não é tocado.
O que este script faz é reassinar o mesmo pré-certificado congelando junto o
material que o fabricante publica (revogação e nível de TCB), para que a
assinatura do emissor passe a cobri-lo. A CVM não precisa estar ligada.

Trava de segurança: se o quote ou o hash do documento mudarem em relação ao
certificado atual, aborta sem gravar. O certificado novo tem de ser o mesmo mais
o frescor, nunca outra coisa.

Uso:  python refinalizar_com_frescor.py [--dry-run]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

AQUI = Path(__file__).resolve().parent
HISTORICO = AQUI / "historico"
CLAUDE = AQUI.parent.parent
VERIFICADOR = CLAUDE / "DCAP-Offline-Verifier" / "cli.py"
ENV = dict(os.environ, PYTHONUTF8="1")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not VERIFICADOR.is_file():
        print(f"verificador não encontrado: {VERIFICADOR}"); return 1

    alvos = []
    for d in sorted(x for x in HISTORICO.iterdir() if x.is_dir()):
        pre = d / "ATESTADOS" / "ata_snapshot-precertificado.json"
        cert = d / "ATESTADOS" / "ata_snapshot-autocontido.json"
        if not (pre.is_file() and cert.is_file()):
            continue
        c = json.loads(cert.read_text(encoding="utf-8"))
        if "collateral" in c:
            print(f"  já tem frescor, pulando: {d.name}")
            continue
        alvos.append((d, pre, cert, c))

    print(f"certificados a refinalizar: {len(alvos)}")
    if a.dry_run or not alvos:
        for d, *_ in alvos:
            print(f"    {d.name}")
        return 0

    feitos, falhou = 0, 0
    for d, pre, cert, atual in alvos:
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp) / "novo.json"
            r = subprocess.run(
                [sys.executable, str(VERIFICADOR), "--finalize", str(pre),
                 "--out", str(saida)],
                capture_output=True, text=True, env=ENV, cwd=str(VERIFICADOR.parent))
            if r.returncode != 0 or not saida.is_file():
                print(f"  FALHOU  {d.name}: verificador saiu {r.returncode}")
                falhou += 1
                continue
            novo = json.loads(saida.read_text(encoding="utf-8"))

            # trava: só pode ter mudado o collateral e a assinatura que o cobre
            if novo.get("quote_hex") != atual.get("quote_hex"):
                print(f"  ABORTA  {d.name}: quote mudou, isso nunca deveria acontecer")
                return 1
            if novo.get("document_hash") != atual.get("document_hash"):
                print(f"  ABORTA  {d.name}: hash do documento mudou")
                return 1
            if "collateral" not in novo:
                print(f"  PULADO  {d.name}: collateral não foi congelado (sem internet?)")
                falhou += 1
                continue
            extras = set(novo) - set(atual) - {"collateral"}
            if extras:
                print(f"  ABORTA  {d.name}: campos inesperados {sorted(extras)}")
                return 1

            shutil.copyfile(saida, cert)
            # confere o que acabou de gravar, com os 7 carimbos
            v = subprocess.run(
                [sys.executable, str(VERIFICADOR), "--cert", str(cert)],
                capture_output=True, text=True, env=ENV, cwd=str(VERIFICADOR.parent))
            tcb = ""
            for linha in (v.stdout or "").splitlines():
                if "FRESCOR DE TCB" in linha:
                    tcb = linha.split(":")[-1].strip()
            if v.returncode != 0:
                print(f"  FALHOU  {d.name}: certificado novo não verifica")
                falhou += 1
                continue
            print(f"  OK      {d.name}  ·  frescor: {tcb}")
            feitos += 1

    print(f"\nrefinalizados: {feitos} · falharam: {falhou}")
    if feitos:
        print("O quote e o hash do documento não mudaram em nenhum deles.")
        print("Rode o ciclo semanal ou gerar_planilha.py para reconsolidar a pasta da semana.")
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
