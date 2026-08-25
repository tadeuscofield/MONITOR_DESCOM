#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diff_capturas.py — o que mudou, instalação por instalação, entre duas capturas.

O agregado diz que um número mexeu. Este script diz QUAL registro mexeu e de
quê para quê, que é a única forma de separar evento regulatório real de
oscilação de painel.

Uso:
  python diff_capturas.py                      # compara as duas últimas
  python diff_capturas.py <capturaA> <capturaB>
  python diff_capturas.py --todas              # varre a série inteira
"""

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

RAIZ = Path(__file__).resolve().parent
HISTORICO = RAIZ / "carimbo" / "historico"
sys.path.insert(0, str(RAIZ / "site"))
from edicao import parse_dsr  # noqa: E402


def _data(v):
    """O painel devolve data como epoch em ms; string passa direto."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        from datetime import datetime, timezone
        return datetime.fromtimestamp(v / 1000, tz=timezone.utc).date().isoformat()
    return (v or "")[:10] if v else ""


def carregar(pasta: Path):
    """Instalações offshore e processos, indexados por chave estável."""
    inst = parse_dsr(json.loads((pasta / "02_INSTALACAO.json")
                                .read_text(encoding="utf-8")), "INSTALACAO")
    proc = parse_dsr(json.loads((pasta / "01_DESCOMISSIONAMENTO_PROCESSOS.json")
                                .read_text(encoding="utf-8")), "PROC")
    mar = {}
    for r in inst:
        if r.get("NOM_AMBIENTE") != "MAR":
            continue
        k = r.get("NOM_INSTALACAO") or r.get("SIG_INSTALACAO") or str(len(mar))
        mar[k] = r
    # A chave estável do processo é o PROTOCOLO do SEI. Cair em índice de linha
    # aqui produziria diferença falsa toda vez que a ordem das linhas mudasse.
    pr = {}
    for r in proc:
        k = r.get("PROTOCOLO")
        if not k:
            raise RuntimeError("linha de processo sem PROTOCOLO: chave instável")
        pr[k] = r
    return mar, pr


def comparar(a: Path, b: Path, verboso=True):
    ma, pa = carregar(a)
    mb, pb = carregar(b)
    achados = []

    for k in sorted(set(ma) | set(mb)):
        ra, rb = ma.get(k), mb.get(k)
        if ra is None:
            achados.append(("instalação ENTROU no cadastro", k,
                            "", rb.get("DSC_SITUACAO")))
            continue
        if rb is None:
            achados.append(("instalação SAIU do cadastro", k,
                            ra.get("DSC_SITUACAO"), ""))
            continue
        if ra.get("DSC_SITUACAO") != rb.get("DSC_SITUACAO"):
            achados.append(("mudou de situação", k,
                            ra.get("DSC_SITUACAO"), rb.get("DSC_SITUACAO")))

    for k in sorted(set(pa) | set(pb)):
        ra, rb = pa.get(k), pb.get(k)
        if ra is None:
            achados.append(("processo NOVO", str(k), "",
                            f"PDI={rb.get('STATUS_PDI')} RDI={rb.get('STATUS_RDI')}"))
            continue
        if rb is None:
            achados.append(("processo SUMIU", str(k),
                            f"PDI={ra.get('STATUS_PDI')}", ""))
            continue
        for campo in ("STATUS_PDI", "STATUS_RDI", "DAT_APROVACAO_PDI",
                      "DAT_APROVACAO_RDI", "DSC_TIPO_PDI", "DSC_DETALHE_EVENTO"):
            va, vb = ra.get(campo), rb.get(campo)
            if campo.startswith("DAT_"):
                va, vb = _data(va), _data(vb)
            if va != vb:
                achados.append((f"processo mudou {campo}", str(k), str(va), str(vb)))

    if verboso:
        print(f"\n{a.name}  ->  {b.name}")
        print("-" * 78)
        if not achados:
            print("  nenhuma diferença por registro")
        for tipo, chave, de, para in achados:
            print(f"  {tipo}")
            print(f"    registro: {chave}")
            print(f"    de   : {de}")
            print(f"    para : {para}")
    return achados


def main() -> int:
    snaps = sorted(d for d in HISTORICO.iterdir()
                   if d.is_dir() and (d / "02_INSTALACAO.json").is_file())
    if len(snaps) < 2:
        print("preciso de pelo menos duas capturas"); return 1

    if "--todas" in sys.argv:
        total = 0
        for a, b in zip(snaps, snaps[1:]):
            total += len(comparar(a, b))
        print("\n" + "=" * 78)
        print(f"total de diferenças por registro na série: {total}")
        return 0

    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(args) == 2:
        comparar(HISTORICO / args[0], HISTORICO / args[1])
    else:
        comparar(snaps[-2], snaps[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
