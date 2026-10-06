#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ciclo_semanal.py — fecha a semana do diário do descomissionamento.

Um comando só, com a CVM ligada:

  1. lista os snapshots ainda não atestados no histórico;
  2. atesta a ata de cada um em hardware seguro (TEE), com assinatura do
     emissor pedida ao enclave da CVM (finalize --assinar-no-tee, a partir da
     publicação da troca de CVM) e verificação completa; o certificado novo
     tem de ser da chave do enclave;
  3. reverifica cada ata: elo da cadeia, hashes dos arquivos e vínculo do
     quote com a ata (report_data[0:32]);
  4. regenera o site, o que produz a edição da semana e o delta contra a
     edição anterior;
  5. imprime o resumo do que mudou na semana.

Portões (nada de atestação de mentira):
  - com ata pendente, antes de atestar (e também no --dry-run): a ferramenta
    de lote precisa ter --assinar-no-tee, o endereço da CVM precisa estar em
    VERIDIS_CVM_URL ou ~/.veridis/cvm_url, e a chave de operador no caminho
    do verificador; faltando qualquer um, lista o que falta e não emite;
  - se a CVM estiver desligada, o atestador cai em modo local e devolve
    exit 1: este script ABORTA antes de tocar no site;
  - se a verificação de qualquer ata falhar, aborta;
  - se o build do site recusar (número divergente, verificador com falha,
    travessão), aborta e a página antiga continua no lugar.

Uso:
  python ciclo_semanal.py            # ciclo completo
  python ciclo_semanal.py --dry-run  # só mostra o que faria

Sem teste de unidade (declarado). A assinatura no enclave só passa por este
script a partir do primeiro ciclo depois da publicação da troca de CVM.
"""

import argparse
import csv
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
# CVM de produção (desde 05/10/2026): a chave do emissor é derivada dentro dela e não existe em
# arquivo, então a assinatura do certificado é pedida ao enclave (--assinar-no-tee), autorizada
# pela chave de operador local. A chave offline não serve para estes quotes: o verificador a
# recusaria. A URL da CVM não fica no CÓDIGO deste repositório, que é público: é configuração
# de operação, não parte do método, e ninguém precisa dela para verificar um certificado. Não é
# segredo: o identificador da app, que forma o endereço, vai no event log dos certificados
# publicados em carimbo/atestacoes que o trazem (os da CVM antiga trazem o dela). Vem da variável
# VERIDIS_CVM_URL ou do arquivo local abaixo.
CVM_URL_ARQUIVO = Path.home() / ".veridis" / "cvm_url"

# Guarda de produção, um lugar só (Blockchain-TEE/tools/verificador_producao.py):
# emitir e conferir só com o verificador no commit do main, sem alteração.
sys.path.insert(0, str(ATESTAR.parent))
from verificador_producao import (VerificadorForaDeProducao, exigir_producao,  # noqa: E402
                                  mensagem_de_recusa)

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


def endereco_da_cvm():
    """URL da CVM de produção (VERIDIS_CVM_URL, ou o arquivo local), ou "" se não configurada."""
    url = os.environ.get("VERIDIS_CVM_URL", "").strip()
    if not url and CVM_URL_ARQUIVO.is_file():
        url = CVM_URL_ARQUIVO.read_text(encoding="utf-8").strip()
    return url.rstrip("/")


def pre_requisitos_da_assinatura_no_enclave():
    """Lista do que falta para pedir a assinatura ao enclave; vazia = pronto.

    Conferido ANTES de atestar, e também no --dry-run: sem isto, uma ferramenta de lote antiga
    (sem --assinar-no-tee) recusava a opção e a mensagem de aborto culpava a CVM desligada."""
    faltas = []
    if not ATESTAR.is_file():
        faltas.append(f"ferramenta de lote não encontrada em {ATESTAR}")
    else:
        r = subprocess.run([sys.executable, str(ATESTAR), "--help"], text=True, env=ENV,
                           capture_output=True)
        if r.returncode != 0:
            faltas.append(f"a ferramenta de lote não respondeu ao --help (saída {r.returncode})")
        elif "--assinar-no-tee" not in (r.stdout or ""):
            faltas.append(f"a ferramenta de lote em {ATESTAR.parent} não tem --assinar-no-tee "
                          "(publicar o Blockchain-TEE com a troca de CVM antes)")
    if not endereco_da_cvm():
        faltas.append(f"endereço da CVM não configurado (VERIDIS_CVM_URL ou {CVM_URL_ARQUIVO})")
    sys.path.insert(0, str(VERIFICADOR.parent))
    from issuer import DEFAULT_OPERATOR_KEY_PATH      # o mesmo caminho que o cli.py usa
    if not Path(DEFAULT_OPERATOR_KEY_PATH).is_file():
        faltas.append(f"chave de operador ausente em {DEFAULT_OPERATOR_KEY_PATH}")
    return faltas


# Arquivos que uma tentativa que não saiu completa e aceita deixa com o nome NORMAL, e que a
# lista de pendentes, a consolidação da semana e o git tomariam por atestação. Vão para o nome
# -TENTATIVA-FALHA, fora do git (.gitignore). O nome não diz "recusado": a saída 3 do cli.py
# (aceito, mas incompleto) também cai aqui. O PDF vai junto: o site o carimba quando ELE aceita a
# atestação, mas o verificador pode recusar o certificado pelo compose da aplicação, que o site
# não confere.
TENTATIVA_FALHA = (
    ("ata_snapshot-autocontido.json", "ata_snapshot-autocontido-TENTATIVA-FALHA.json"),
    ("ata_snapshot-certificate.pdf", "ata_snapshot-certificate-TENTATIVA-FALHA.pdf"),
)


def separar_tentativa_falha(atestados, motivo):
    """Renomeia os artefatos da tentativa falha em `atestados`; devolve os nomes novos.

    O lote_manifesto.csv (versionado) só ACUMULA linhas, e a da tentativa pode ter saído como
    "autocontido assinado": em vez de apagá-la, acrescenta uma linha dizendo que o ciclo a
    descartou e por quê, para o repositório público não mostrar atestação que não ficou."""
    movidos = []
    for nome, novo in TENTATIVA_FALHA:
        p = atestados / nome
        if p.is_file():
            p.replace(atestados / novo)
            movidos.append(novo)
    manifesto = atestados / "lote_manifesto.csv"
    if manifesto.is_file():
        with open(manifesto, "a", newline="", encoding="utf-8-sig") as f:
            csv.writer(f, delimiter=";").writerow(
                ["ata_snapshot.json", "", "", "", f"DESCARTADO pelo ciclo semanal: {motivo}"])
    return movidos


def origem_da_chave_do_certificado(cert_path):
    """'tee', 'offline' ou None: a chave com que o quote do certificado se compromete, pelo
    registro do verificador (None = quote ilegível ou compromisso fora do registro).

    Depois da troca de CVM, toda ata nova tem de vir da CVM de produção ('tee'). 'offline' aqui
    quer dizer que o site ainda estava na CVM antiga e o servidor assinou com a chave offline
    (ISSUER_SIGNING_KEY, opcional): o lote sai 0 nesse caso, e só esta conferência pega."""
    sys.path.insert(0, str(VERIFICADOR.parent))
    from issuer import compromisso_do_cert, emissor_do_compromisso
    e = emissor_do_compromisso(compromisso_do_cert(json.loads(cert_path.read_text(encoding="utf-8"))))
    return e.origem if e is not None else None


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

    # O verificador assina (passo 2) e confere (passo 4b): sem ele no main, nada roda.
    try:
        commit = exigir_producao(VERIFICADOR)
        print(f"    verificador: no main ({commit}), pronto para emitir")
    except VerificadorForaDeProducao as e:
        print("\n" + mensagem_de_recusa(e))
        return 1

    if pendentes:
        faltas = pre_requisitos_da_assinatura_no_enclave()
        for f in faltas:
            print(f"    FALTA: {f}")
        if faltas:
            print("\nNada foi emitido: a assinatura no enclave não tem como acontecer.")
            return 1
        print("    assinatura no enclave: ferramenta, endereço da CVM e chave de operador presentes")

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
                                  "--finalize", "--assinar-no-tee", endereco_da_cvm(),
                                  "--verificador", VERIFICADOR])
            if código != 0 or "MODO LOCAL" in saida.upper():
                # O --finalize grava o certificado ANTES de o portão do verificador recusá-lo.
                # Deixado com o nome normal, a rodada seguinte trataria esta ata como atestada
                # (a lista de pendentes olha só a existência do arquivo) e o publicaria.
                for nome in separar_tentativa_falha(d / "ATESTADOS", "atestação ou assinatura não saiu completa e aceita"):
                    print(f"    da tentativa, renomeado para {nome}")
                print("\nABORTADO: a atestação ou a assinatura não saiu completa e aceita.")
                print("A causa está na saída acima. Causas possíveis: CVM veridis-tee-producao")
                print("desligada, site ainda apontando para a CVM antiga, chave de operador")
                print("recusada pelo enclave, o verificador recusando o certificado, ou o")
                print("certificado aceito mas incompleto (sem collateral ou sem carimbo de tempo).")
                print("Nada foi publicado, e esta ata continua pendente.")
                return 1
            cert = d / "ATESTADOS" / "ata_snapshot-autocontido.json"
            if not cert.is_file():
                for nome in separar_tentativa_falha(d / "ATESTADOS", "certificado assinado não apareceu"):
                    print(f"    da tentativa, renomeado para {nome}")
                print(f"\nABORTADO: certificado assinado não apareceu em {cert}")
                return 1
            origem = origem_da_chave_do_certificado(cert)
            if origem != "tee":
                motivo = ("certificado da chave offline: o site ainda está na CVM antiga"
                          if origem == "offline" else
                          "quote ilegível ou compromisso fora do registro do verificador")
                for nome in separar_tentativa_falha(d / "ATESTADOS", motivo):
                    print(f"    da tentativa, renomeado para {nome}")
                print("\nABORTADO: o certificado não é da chave do enclave da CVM de produção")
                print(f"({motivo}). Esta ata continua pendente.")
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
