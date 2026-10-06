#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refinalizar_com_frescor.py — acrescenta o frescor aos certificados já emitidos.

NÃO reatesta nada. O quote, que é a prova do hardware, já existe e não é tocado.
O que este script faz é reassinar o mesmo pré-certificado congelando junto o
material que o fabricante publica (revogação e nível de TCB), para que a
assinatura do emissor passe a cobri-lo. Para certificados da chave offline a CVM
não precisa estar ligada. Para os da chave do enclave (quote da CVM de produção,
desde 05/10/2026) precisa: a reassinatura é pedida a ela (--assinar-no-tee, com o
endereço de ciclo_semanal.endereco_da_cvm e a chave de operador). O ramo do enclave não
tem teste de unidade e ainda não rodou de verdade (declarado): todo certificado da chave do
enclave já nasce com o frescor, então hoje nenhum cai aqui.

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

    # Reassinar é emitir: só com o verificador no commit do main, sem alteração.
    sys.path.insert(0, str(CLAUDE / "Blockchain-TEE" / "tools"))
    from verificador_producao import (VerificadorForaDeProducao, exigir_producao,
                                      mensagem_de_recusa)
    try:
        print(f"verificador: no main ({exigir_producao(VERIFICADOR)})")
    except VerificadorForaDeProducao as e:
        print(mensagem_de_recusa(e)); return 1

    # Qual chave assina sai do COMPROMISSO do quote, pelo registro do próprio verificador (uma
    # fonte só), e não de um campo de texto do pré-certificado.
    sys.path.insert(0, str(VERIFICADOR.parent))
    from issuer import DEFAULT_OPERATOR_KEY_PATH, compromisso_do_cert, emissor_do_compromisso
    from ciclo_semanal import endereco_da_cvm   # uma fonte só para o endereço da CVM

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
        emissor = emissor_do_compromisso(compromisso_do_cert(json.loads(pre.read_text(encoding="utf-8"))))
        alvos.append((d, pre, cert, c, emissor is not None and emissor.origem == "tee"))

    print(f"certificados a refinalizar: {len(alvos)}")
    if any(no_enclave for *_, no_enclave in alvos):
        # conferido também no --dry-run, como no ciclo semanal
        faltas = []
        if not endereco_da_cvm():
            faltas.append("endereço da CVM não configurado (VERIDIS_CVM_URL ou ~/.veridis/cvm_url)")
        if not Path(DEFAULT_OPERATOR_KEY_PATH).is_file():
            faltas.append(f"chave de operador ausente em {DEFAULT_OPERATOR_KEY_PATH}")
        for f in faltas:
            print(f"    FALTA (certificados da chave do enclave): {f}")
        if faltas:
            return 1
    if a.dry_run or not alvos:
        for d, *_, no_enclave in alvos:
            print(f"    {d.name}{' (chave do enclave)' if no_enclave else ''}")
        return 0

    feitos, falhou = 0, 0
    for d, pre, cert, atual, no_enclave in alvos:
        # Quote da CVM de produção: a chave do emissor vive no enclave, e a reassinatura é pedida
        # a ele. Com a chave offline o verificador recusaria (a chave é escolhida pelo compromisso).
        extra = []
        if no_enclave:
            url = endereco_da_cvm()
            if not url:
                print(f"  FALHOU  {d.name}: chave do enclave e endereço da CVM não configurado")
                falhou += 1
                continue
            extra = ["--assinar-no-tee", url]
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp) / "novo.json"
            r = subprocess.run(
                [sys.executable, str(VERIFICADOR), "--finalize", str(pre),
                 "--out", str(saida)] + extra,
                capture_output=True, text=True, env=ENV, cwd=str(VERIFICADOR.parent))
            if r.returncode != 0 or not saida.is_file():
                print(f"  FALHOU  {d.name}: verificador saiu {r.returncode}"
                      f"{' (assinatura pedida ao enclave)' if no_enclave else ''}; fim da saída dele:")
                for linha in ((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-8:]:
                    print("      | " + linha)
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
