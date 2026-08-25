#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ciclo_semanal.py — fecha a semana do diário do descomissionamento.

Um comando só, com a CVM ligada:

  1. lista os snapshots ainda não atestados no histórico;
  2. atesta a ata de cada um em hardware seguro (TEE), com assinatura do
     emissor (finalize) e verificação completa;
  3. reverifica cada ata: elo da cadeia, hashes dos arquivos e vínculo do
     quote com a ata (report_data[0:32]);
  4. regenera o site, o que produz a edição da semana e o delta contra a
     edição anterior;
  5. imprime o resumo do que mudou na semana.

Portões (nada de atestação de mentira):
  - se a CVM estiver desligada, o atestador cai em modo local e devolve
    exit 1: este script ABORTA antes de tocar no site;
  - se a verificação de qualquer ata falhar, aborta;
  - se o build do site recusar (número divergente, verificador com falha,
    travessão), aborta e a página antiga continua no lugar.

Uso:
  python ciclo_semanal.py            # ciclo completo
  python ciclo_semanal.py --dry-run  # só mostra o que faria
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
HISTORICO = AQUI / "historico"
SITE = RAIZ / "site"
CLAUDE = RAIZ.parent
ATESTAR = CLAUDE / "Blockchain-TEE" / "tools" / "atestar_lote.py"
VERIFICADOR = CLAUDE / "DCAP-Offline-Verifier" / "cli.py"

ENV = dict(os.environ, PYTHONUTF8="1")


def roda(cmd, cwd=None):
    print(f"    $ {' '.join(str(c) for c in cmd[1:])}")
    r = subprocess.run([str(c) for c in cmd], text=True, env=ENV,
                       cwd=str(cwd) if cwd else None,
                       capture_output=True)
    saida = (r.stdout or "") + (r.stderr or "")
    for linha in saida.strip().splitlines():
        print("      " + linha)
    return r.returncode, saida


def hoje_iso():
    """Data do lote. Vem do relógio local, e só rotula a pasta: nenhuma
    afirmação de data entra no certificado, que não carimba tempo."""
    import datetime
    return datetime.date.today().isoformat()


def titulo(n, txt):
    print(f"\n[{n}] {txt}")
    print("-" * 72)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not HISTORICO.is_dir():
        print("histórico não existe: nada a fazer"); return 2

    todos = sorted(d for d in HISTORICO.iterdir() if d.is_dir()
                   and (d / "ata_snapshot.json").is_file())
    pendentes = [d for d in todos
                 if not (d / "ATESTADOS" / "ata_snapshot-autocontido.json").is_file()]

    titulo(1, f"Snapshots no histórico: {len(todos)} · sem atestação: {len(pendentes)}")
    for d in pendentes:
        print(f"    pendente: {d.name}")
    if not pendentes:
        print("    tudo já atestado. Sigo direto para o site.")

    if a.dry_run:
        print("\n--dry-run: parando aqui.")
        return 0

    # ---------------------------------------------------------- 2. atestar
    if pendentes:
        if not ATESTAR.is_file():
            print(f"FALHA: atestador não encontrado em {ATESTAR}"); return 1
        titulo(2, "Atestação em hardware (a CVM precisa estar LIGADA)")
        for d in pendentes:
            print(f"  {d.name}")
            código, saida = roda([sys.executable, ATESTAR,
                                  d / "ata_snapshot.json",
                                  "--out", d / "ATESTADOS",
                                  "--finalize",
                                  "--verificador", VERIFICADOR])
            if código != 0 or "MODO LOCAL" in saida.upper():
                print("\nABORTADO: a atestação não saiu em hardware.")
                print("Ligue a CVM em veridisattestation.com e rode de novo.")
                print("Nada foi publicado, e nenhuma ata falsa foi gravada.")
                return 1
            cert = d / "ATESTADOS" / "ata_snapshot-autocontido.json"
            if not cert.is_file():
                print(f"\nABORTADO: certificado assinado não apareceu em {cert}")
                return 1

    # ------------------------------------------------------- 3. verificar
    titulo(3, "Verificação das atas (cadeia, hashes e vínculo do quote)")
    for d in sorted(x for x in HISTORICO.iterdir() if x.is_dir()):
        cert = d / "ATESTADOS" / "ata_snapshot-autocontido.json"
        cmd = [sys.executable, AQUI / "verificar_snapshot.py", d]
        if cert.is_file():
            cmd.append(cert)
        código, saida = roda(cmd)
        if código != 0:
            print(f"\nABORTADO: verificação falhou em {d.name}")
            return 1

    # ------------------------------------------------- 4. regenerar o site
    titulo(4, "Regeneração do site (recomputa tudo e produz a edição)")
    código, saida = roda([sys.executable, SITE / "gerar_site.py"], cwd=SITE)
    if código != 0:
        print("\nABORTADO: o build recusou. A página anterior continua no lugar.")
        return 1

    # ------------------------------------- 4b. pasta da semana + DCAP completo
    titulo("4b", "Consolidação da semana e verificação completa (5 carimbos)")
    semana = RAIZ / "carimbo" / "atestacoes" / f"semana_{hoje_iso()}"
    semana.mkdir(parents=True, exist_ok=True)
    linhas_rel, tudo_ok = [], True
    for d in sorted(x for x in HISTORICO.iterdir() if x.is_dir()):
        cert = d / "ATESTADOS" / "ata_snapshot-autocontido.json"
        if not cert.is_file():
            continue
        destino = semana / f"{d.name}-autocontido.json"
        destino.write_bytes(cert.read_bytes())
        pdf = d / "ATESTADOS" / "ata_snapshot-certificate.pdf"
        if pdf.is_file():
            (semana / f"{d.name}-certificado.pdf").write_bytes(pdf.read_bytes())

        # 5 carimbos: cadeia PCK até a raiz Intel pinada, ECDSA, medições do
        # build, commitment e assinatura do emissor. Só isto autoriza "verificado".
        if VERIFICADOR.is_file():
            código, saida = roda([sys.executable, VERIFICADOR, "--cert", destino])
            ok = código == 0
        else:
            ok, saida = False, "verificador DCAP não encontrado"
        tudo_ok &= ok
        c = json.loads(destino.read_text(encoding="utf-8"))
        tcb = ""
        for linha in saida.splitlines():
            if "FRESCOR DE TCB" in linha:
                tcb = linha.split(":")[-1].strip()
        linhas_rel.append((d.name, (c.get("document_hash") or "").removeprefix("0x"),
                           ("7 carimbos OK" if "collateral" in c else "5 carimbos OK")
                           if ok else "FALHOU",
                           tcb or ("congelado" if "collateral" in c else "não congelado"),
                           pdf.is_file()))

    if linhas_rel:
        rel = [f"# Atestação da semana, lote de {hoje_iso()}", "",
               f"Snapshots atestados: {len(linhas_rel)}", "",
               "| snapshot | sha256 da ata | verificação | frescor | certificado PDF |",
               "|---|---|---|---|---|"]
        for nome, h, v, tcb, tem_pdf in linhas_rel:
            rel.append(f"| `{nome}` | `{h[:16]}…` | {v} | {tcb} | "
                       f"{'sim' if tem_pdf else 'não'} |")
        rel += ["", "Verificação executada com o verificador DCAP completo, sem rede:",
                "cadeia de certificados até a raiz do fabricante pinada, assinaturas,",
                "medições do build, commitment e assinatura do emissor.", "",
                "Reexecutar a qualquer momento:", "",
                "```", f"python <verificador>\\cli.py --cert semana_{hoje_iso()}\\<arquivo>-autocontido.json", "```"]
        (semana / "RELATORIO.md").write_text("\n".join(rel) + "\n", encoding="utf-8")
        print(f"    pasta da semana: {semana}")
        print(f"    {len(linhas_rel)} certificado(s) consolidado(s) · "
              f"{'todos verificados' if tudo_ok else 'ALGUM FALHOU'}")
        if not tudo_ok:
            print("\nABORTADO: verificação DCAP falhou em algum certificado.")
            return 1

    # ------------------------------------------- 4c. planilha do diário
    titulo("4c", "Planilha do diário, regerada do registro")
    código, saida = roda([sys.executable, RAIZ / "gerar_planilha.py"], cwd=RAIZ)
    if código != 0:
        print("\nABORTADO: a planilha não pôde ser gerada.")
        return 1

    # ------------------------------------------------------ 5. o que mudou
    titulo(5, "Edição da semana")
    edicoes = sorted((SITE / "edicoes").glob("ed_*.json"))
    if not edicoes:
        print("    nenhuma edição gerada"); return 1
    ed = json.loads(edicoes[-1].read_text(encoding="utf-8"))
    print(f"    snapshot   : {ed['snapshot']}")
    print(f"    ata sha256 : {ed['ata_sha256'][:16]}…")
    print(f"    offshore   : {ed['total_offshore']}"
          f"  ·  aguardando descomissionamento: {ed['ciclo']['aguarda_descom']}"
          f"  ·  em descomissionamento: {ed['ciclo']['em_descom']}")
    print(f"    processos  : {ed['pdi_aprovados']} PDI aprovados"
          f"  ·  {ed['rdi_aprovados']} RDI aprovados")
    delta = ed.get("delta") or {}
    mudou = {k: v for k, v in delta.items() if v}
    if not delta:
        print("\n    Primeira edição: esta é a linha de base da série.")
    elif not mudou:
        print(f"\n    Nenhuma mudança contra {ed.get('delta_contra', 'a edição anterior')}.")
        print("    Semana sem movimento no painel também é dado, e entra na série.")
    else:
        print(f"\n    Mudanças contra {ed.get('delta_contra', 'a edição anterior')}:")
        for k, v in sorted(mudou.items()):
            print(f"      {k:<28} {v:+d}")

    print("\nCiclo fechado. Pode desligar a CVM.")
    print("Se for publicar, o site regenerado está em site\\index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
