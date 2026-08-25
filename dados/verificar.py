#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificar.py — Decommissioning Monitor, snapshot 2026-08-12
Autor: Tadeu Santana Cordeiro (Veridis Engenharia) · CC BY 4.0

PT: Recalcula, a partir apenas dos CSV desta pasta, cada número publicado,
    seguindo as receitas de LASTRO_PUBLICO.md. Sem rede, sem dependência
    externa. Saída diferente de zero = alguma afirmação não reproduziu.

EN: Recomputes every published claim from the CSV files in this folder,
    following the recipes in LASTRO_PUBLICO.md. No network, standard
    library only (Python 3.10+). Non-zero exit = a claim failed.

Uso / usage:  python verificar.py
"""

import csv
import hashlib
import statistics
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DIR = Path(__file__).resolve().parent
REF = date(2026, 8, 12)          # data de referência de toda idade
RESULTS = []

# ---------------------------------------------------------------- utilitários

def check(cid, desc, esperado, obtido):
    ok = (esperado == obtido)
    RESULTS.append((cid, desc, esperado, obtido, ok))

def check_num(cid, desc, esperado, obtido, casas=6):
    ok = abs(float(esperado) - float(obtido)) < 10 ** (-casas)
    RESULTS.append((cid, desc, esperado, round(float(obtido), casas), ok))

def load(nome):
    with open(DIR / nome, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def d(s):
    return date.fromisoformat(s)

def anos(fim, inicio):
    return (fim - inicio).days / 365.25

def mediana(vals):
    return statistics.median(vals)   # amostra par = média dos dois centrais

def conta(rows, col):
    out = {}
    for r in rows:
        out[r[col]] = out.get(r[col], 0) + 1
    return out

# ------------------------------------------------------------------- arquivos

F_US   = "ndm_us_estruturas_completo_20260812.csv"
F_FER  = "ndm_us_ferro_ocioso_20260812.csv"
F_DES  = "ndm_us_destino_remocao_20260812.csv"
F_SEC  = "ndm_sec_aro_CY2025Q4I_20260812.csv"
F_BRI  = "ndm_br_instalacoes_offshore_20260812.csv"
F_BRP  = "ndm_br_processos_pdi_rdi_20260812.csv"
F_UK   = "ndm_uk_instalacoes_superficie_20260812.csv"
F_NO   = "ndm_no_instalacoes_20260812.csv"

us  = load(F_US)
fer = load(F_FER)
des = load(F_DES)
sec = load(F_SEC)
bri = load(F_BRI)
brp = load(F_BRP)
uk  = load(F_UK)
no  = load(F_NO)

# ------------------------------------------------ A. convenções de arquivo

DATAS = {F_US: ["instalada", "removida"], F_FER: ["instalada"],
         F_SEC: ["extraido"], F_BRP: ["aprov_pdi", "aprov_rdi"],
         F_UK: ["inicio", "fim", "instalada", "atualizada"],
         F_NO: ["inicio", "parada", "removida"]}
NUMS = {F_US: ["vida_anos", "lamina_m", "lat", "lon"],
        F_FER: ["idade_anos", "lamina_m", "lat", "lon"],
        F_SEC: ["aro_usd"],
        F_BRI: ["lamina_m", "ano_inicio", "idade_calculada", "idade_anp", "lat", "lon"],
        F_BRP: ["ciclo_anos", "pendente_anos"],
        F_UK: ["lat", "lon"], F_NO: ["lamina_m", "vida_projeto"]}
TAB = {F_US: us, F_FER: fer, F_DES: des, F_SEC: sec,
       F_BRI: bri, F_BRP: brp, F_UK: uk, F_NO: no}

viol_data, viol_num, viol_espaco = 0, 0, 0
for nome, rows in TAB.items():
    for r in rows:
        for c, v in r.items():
            if v != v.strip():
                viol_espaco += 1
        for c in DATAS.get(nome, []):
            if r[c]:
                try:
                    d(r[c])
                except ValueError:
                    viol_data += 1
        for c in NUMS.get(nome, []):
            if r[c]:
                try:
                    float(r[c])
                except ValueError:
                    viol_num += 1

check("A1", "datas fora do ISO 8601", 0, viol_data)
check("A2", "números que não parseiam com ponto decimal", 0, viol_num)
check("A3", "campos com espaço sobrando na borda", 0, viol_espaco)

# ------------------------------------------------ B. LASTRO §2 — Estados Unidos

check("B1", "estruturas no cadastro", 7091, len(us))
rem  = [r for r in us if r["removida"]]
pe   = [r for r in us if not r["removida"]]
check("B2a", "removidas", 5766, len(rem))
check("B2b", "de pé", 1325, len(pe))

vidas = [float(r["vida_anos"]) for r in rem if r["vida_anos"]]
check_num("B3a", "vida mediana bruta", 18.9, round(mediana(vidas), 1))
check("B3b", "vida mediana em anos inteiros", 19, round(mediana(vidas)))

dec2010 = sum(1 for r in rem if 2010 <= d(r["removida"]).year <= 2019)
dec2020 = sum(1 for r in rem if 2020 <= d(r["removida"]).year <= 2029)
check("B4a", "remoções na década de 2010", 1885, dec2010)
check("B4b", "remoções na década de 2020", 476, dec2020)
check_num("B4c", "ritmo anualizado 2010s", 188.5, round(dec2010 / 10, 1))
check_num("B4d", "ritmo anualizado 2020s", 73.2, round(dec2020 / 6.5, 1))

check("B5a", "ferro ocioso: linhas", 531, len(fer))
ENC = {"EXPIR", "RELINQ", "TERMIN", "REJECT", "NO-ISS", "CANCEL", "CONSOL", "NO-EXE"}
FIL = {"TERMIN", "RELINQ", "EXPIR"}
eq_filtro = {(r["complexo"], r["num"]) for r in us
             if not r["removida"] and r["contrato_status"] in FIL}
eq_fer = {(r["complexo"], r["num"]) for r in fer}
check("B5b", "equivalência do filtro na base completa (mesmos pares)", True,
      eq_filtro == eq_fer and len(eq_fer) == 531)
check("B5c", "status presentes no ferro ocioso",
      {"TERMIN": 312, "RELINQ": 213, "EXPIR": 6}, conta(fer, "contrato_status"))

idades = sorted(float(r["idade_anos"]) for r in fer)
check_num("B6a", "idade mediana bruta", 46.6, round(mediana(idades), 1))
check_num("B6b", "idade máxima bruta", 77.6, round(max(idades), 1))
check("B6c", "publicáveis (inteiro mais próximo)", (47, 78),
      (round(mediana(idades)), round(max(idades))))

top = [r for r in fer if float(r["idade_anos"]) == max(idades)]
check("B7", "mais antigas: n e ano de instalação", (4, {"1949-01-01"}),
      (len(top), {r["instalada"] for r in top}))
check("B8", "estruturas maiores (Y)", 272,
      sum(1 for r in fer if r["estrutura_maior"] == "Y"))

check("B9", "destinos de remoção",
      {"To Shore": 3201, "": 1830, "Rigs-to-Reef": 610, "Reuse": 81},
      conta(des, "REMOVAL_DISPOSITION"))

# SEC — dedup por empresa, insensível a caixa, MAIOR valor por grupo
check("B10a", "SEC: linhas", 445, len(sec))
check("B10b", "SEC: CIK distintos", 445, len({r["cik"] for r in sec}))
grupos = {}
for r in sec:
    grupos.setdefault(r["empresa"].casefold(), []).append(int(float(r["aro_usd"])))
check("B10c", "SEC: empresas (insensível a caixa)", 428, len(grupos))
check("B10d", "SEC: grupos sensíveis a caixa (contraprova)", 429,
      len({r["empresa"] for r in sec}))
check("B10e", "SEC: empresas com dois CIK", 17,
      sum(1 for v in grupos.values() if len(v) > 1))

soma_max = sum(max(v) for v in grupos.values())
soma_min = sum(min(v) for v in grupos.values())
soma_cik = sum(int(float(r["aro_usd"])) for r in sec)
check("B11a", "SEC: soma deduplicada (MAIOR por grupo), US$", 208_145_279_217, soma_max)
check("B11b", "SEC: soma bruta por CIK, US$", 248_903_697_217, soma_cik)
check_num("B11c", "SEC: inflação sem dedup, %", 19.6,
          round((soma_cik - soma_max) / soma_max * 100, 1))
check("B12a", "SEC: soma com o MENOR por grupo, US$", 203_464_137_217, soma_min)
check("B12b", "SEC: diferença entre as duas regras, US$", 4_681_142_000,
      soma_max - soma_min)

DIVERG = {"duke energy corporation": [9_625_000_000, 9_046_000_000],
          "the southern company": [9_601_000_000, 8_939_000_000],
          "sempra": [3_948_000_000, 3_743_000_000],
          "northern states power co": [3_215_000_000, 24_000_000],
          "evergy, inc.": [1_342_300_000, 1_308_100_000],
          "western midstream partners, lp": [437_800_000, 427_858_000]}
achados = {k: sorted(v, reverse=True) for k, v in grupos.items()
           if len(set(v)) > 1}
check("B12c", "SEC: os seis grupos com valores divergentes", DIVERG, achados)

# ------------------------------------------------ C. LASTRO §3 — Brasil

check("C1", "instalações offshore", 253, len(bri))
AGU = "Fora de Operação Permanentemente - Aguarda Descomissionamento"
agu = [r for r in bri if r["situacao"] == AGU]
check("C2", "aguardando descomissionamento", 35, len(agu))
check("C3", "idade mediana das 35", 43,
      mediana(sorted(int(r["idade_calculada"]) for r in agu)))
check("C4", "classes entre as 35",
      {"Plataforma Fixa": 34, "Unidade Semissubmersível": 1}, conta(agu, "classe"))
check("C5", "operador único das 35", {"PETROBRAS"},
      {r["operador_grupo"] for r in agu})

g1 = next(r for r in bri if r["instalacao"] == "PLATAFORMA DE GUARICEMA 1")
check("C6", "Guaricema 1: ano, idade, lâmina", ("1970", "56", "28.7"),
      (g1["ano_inicio"], g1["idade_calculada"], g1["lamina_m"]))

pg = next(r for r in brp if r["protocolo"] == "48610.208347/2024-22")
check("C7", "PDI de Guaricema: aprovação e RDI pendente", ("2024-11-07", "", ""),
      (pg["aprov_pdi"], pg["status_rdi"], pg["aprov_rdi"]))

def rec(rows, tipo=None, mar=False):
    sel = rows
    if tipo:
        sel = [r for r in sel if r["tipo_pdi"] == tipo]
    if mar:
        sel = [r for r in sel if "MAR" in r["classe"]]
    cic = sorted(float(r["ciclo_anos"]) for r in sel if r["ciclo_anos"])
    pen = sorted(float(r["pendente_anos"]) for r in sel if r["pendente_anos"])
    return cic, pen

cic_t, pen_t = rec(brp)
cic_i, pen_i = rec(brp, tipo="Integral")
cic_m, pen_m = rec(brp, tipo="Integral", mar=True)
check("C8", "recorte 1 (todos): n e medianas",
      (19, 3.4, 103, 3.8),
      (len(cic_t), round(mediana(cic_t), 1), len(pen_t), round(mediana(pen_t), 1)))
check("C9", "recorte 2 (Integral): n e medianas",
      (12, 3.0, 22, 6.85),
      (len(cic_i), round(mediana(cic_i), 1), len(pen_i), round(mediana(pen_i), 2)))
check("C10", "recorte 3 (Integral+MAR): n e medianas",
      (3, 0.4, 10, 7.1),
      (len(cic_m), round(mediana(cic_m), 1), len(pen_m), round(mediana(pen_m), 1)))

pend_mar = [r for r in brp if r["tipo_pdi"] == "Integral"
            and "MAR" in r["classe"] and r["pendente_anos"]]
mais = max(pend_mar, key=lambda r: float(r["pendente_anos"]))
check("C11", "mais antigo pendente offshore integral",
      ("MEXILHÃO", "SANTOS", "2016-05-30"),
      (mais["campo"], mais["bacia"], mais["aprov_pdi"]))

check("C12", "protocolos únicos", 190, len({r["protocolo"] for r in brp}))
check("C13", "tipo_pdi", {"Integral": 35, "Parcial": 6, "": 149}, conta(brp, "tipo_pdi"))
check("C14", "status_pdi",
      {"Aprovado": 122, "Recebido": 27, "": 24, "Encerrado": 13, "Sobrestado": 4},
      conta(brp, "status_pdi"))
check("C15", "classe dos processos",
      {"CAMPO TERRA": 88, "INSTALACAO MAR": 56, "CAMPO MAR": 38,
       "CAMPO MAR | INSTALACAO MAR": 4, "BLOCO MAR": 3, "BLOCO TERRA": 1},
      conta(brp, "classe"))

# ------------------------------------------------ D. LASTRO §4 — Reino Unido e Noruega

check("D1", "Reino Unido: linhas", 309, len(uk))
check("D2", "Reino Unido: status",
      {"ACTIVE": 265, "NOT IN USE": 29, "ABANDONED": 12, "REMOVED": 3},
      conta(uk, "status"))
back = [r for r in uk if r["status"] in ("NOT IN USE", "ABANDONED")]
check("D3", "backlog na água", 41, len(back))
check("D4", "backlog por operador (11 grupos, soma 41)",
      {"REPSOL RESOURCES UK": 9, "TAQA EUROPA B.V.": 6, "PERENCO OIL & GAS": 5,
       "HARBOUR ENERGY PLC": 4, "SHELL PLC": 4,
       "TOTALENERGIES UPSTREAM UK LIMITED": 4, "ENI UK LIMITED": 3,
       "CENTRICA STORAGE HOLDINGS": 2, "SPIRIT ENERGY": 2,
       "FAIRFIELD ENERGY LIMITED": 1, "WINTERSHALL NOORDZEE": 1},
      conta(back, "grupo_reporte"))

check("D5", "Noruega: linhas", 914, len(no))
check("D6", "Noruega: dez fases",
      {"IN SERVICE": 698, "REMOVED": 92, "INSTALLATION": 60, "SHUT DOWN": 35,
       "FUTURE": 15, "ABANDONED IN PLACE": 4, "PARTLY REMOVED": 4,
       "DECOMMISSIONED": 3, "DISPOSAL COMPLETED": 2, "FABRICATION": 1},
      conta(no, "fase"))
check("D7", "Noruega: parada e removida disjuntas", 0,
      sum(1 for r in no if r["parada"] and r["removida"]))
check("D8", "Noruega: nenhuma data anterior a 1950", 0,
      sum(1 for r in no for c in ("inicio", "parada", "removida")
          if r[c] and d(r[c]).year < 1950))

# ------------------------------------------------ E. LASTRO §5 — granularidade

jan1 = [r for r in us if r["instalada"].endswith("-01-01")]
check("E1a", "instalações com dia/mês imputados (01-01)", 4908, len(jan1))
check_num("E1b", "proporção, %", 69.2, round(len(jan1) / len(us) * 100, 1))
check("E2", "instaladas antes de 1990", 4475,
      sum(1 for r in us if d(r["instalada"]).year < 1990))
check("E3", "com 01-01 e de 1990 em diante", 502,
      sum(1 for r in jan1 if d(r["instalada"]).year >= 1990))
rem_jan1 = sum(1 for r in rem if r["removida"].endswith("-01-01"))
check("E4a", "remoções com 01-01", 11, rem_jan1)
check_num("E4b", "remoções exatas, %", 99.8,
          round((len(rem) - rem_jan1) / len(rem) * 100, 1))
exatas = [float(r["vida_anos"]) for r in rem
          if not r["instalada"].endswith("-01-01")
          and not r["removida"].endswith("-01-01")]
check("E5", "subconjunto de datas exatas: n e mediana", (1711, 10.5),
      (len(exatas), round(mediana(sorted(exatas)), 1)))

# ------------------------------------------------ F. LASTRO §6 — limitações

sem_vinculo_pe = sum(1 for r in pe if not r["contrato_ativo"])
check("F1a", "de pé sem vínculo de contrato", 141, sem_vinculo_pe)
check("F1b", "sem vínculo no cadastro inteiro", 296,
      sum(1 for r in us if not r["contrato_ativo"]))
check_num("F1c", "proporção do estoque, %", 10.6,
          round(sem_vinculo_pe / len(pe) * 100, 1))
check_num("F2", "destinos em branco, %", 32.0,
          round(conta(des, "REMOVAL_DISPOSITION")[""] / len(des) * 100, 1))
check("F3", "uf vazia nas instalações brasileiras", 233,
      sum(1 for r in bri if not r["uf"]))

# ------------------------------------------------ G. fórmulas das colunas derivadas

TOL = 0.06   # tolerância de arredondamento a 1 casa decimal


def quase(a, b):
    return abs(a - b) <= TOL


div = sum(1 for r in rem
          if not quase(float(r["vida_anos"]), anos(d(r["removida"]), d(r["instalada"]))))
check("G1", "vida_anos = (removida - instalada)/365,25 nas 5.766", 0, div)

div = sum(1 for r in fer
          if not quase(float(r["idade_anos"]), anos(REF, d(r["instalada"]))))
check("G2", "idade_anos = (2026-08-12 - instalada)/365,25 nas 531", 0, div)

div = 0
for r in bri:
    ano = int(float(r["ano_inicio"])) if r["ano_inicio"] else 0
    esperada = str(2026 - ano) if ano > 1900 else ""
    if r["idade_calculada"] != esperada:
        div += 1
check("G3", "idade_calculada = 2026 - ano_inicio (ou vazio)", 0, div)

div_c = sum(1 for r in brp if r["ciclo_anos"]
            and not quase(float(r["ciclo_anos"]),
                          anos(d(r["aprov_rdi"]), d(r["aprov_pdi"]))))
div_p = sum(1 for r in brp if r["pendente_anos"]
            and not quase(float(r["pendente_anos"]),
                          anos(REF, d(r["aprov_pdi"]))))
check("G4", "ciclo_anos e pendente_anos conferem com as datas", (0, 0),
      (div_c, div_p))
check("G5", "preenchimento: 19 ciclos e 103 pendências", (19, 103),
      (sum(1 for r in brp if r["ciclo_anos"]),
       sum(1 for r in brp if r["pendente_anos"])))

# ------------------------------------------------ H. MANIFESTO

manif = (DIR / "MANIFESTO.md").read_text(encoding="utf-8-sig")
listados = []
for linha in manif.splitlines():
    if linha.startswith("| `") and "sha" not in linha.lower():
        cel = [c.strip() for c in linha.strip("|").split("|")]
        if len(cel) == 4 and cel[3].startswith("`"):
            nome = cel[0].strip("`")
            tam = int(cel[1].replace(".", ""))
            nlin = int(cel[2]) if cel[2] else None
            sha = cel[3].strip("`")
            listados.append((nome, tam, nlin, sha))

check("H1", "arquivos listados no manifesto", 14, len(listados))
falha_sha, falha_tam, falha_lin = [], [], []
for nome, tam, nlin, sha in listados:
    p = DIR / nome
    if not p.exists():
        falha_sha.append(nome)
        continue
    if hashlib.sha256(p.read_bytes()).hexdigest() != sha:
        falha_sha.append(nome)
    if p.stat().st_size != tam:
        falha_tam.append(nome)
    if nlin is not None:
        with open(p, encoding="utf-8-sig", newline="") as f:
            n = sum(1 for _ in csv.reader(f)) - 1
        if n != nlin:
            falha_lin.append(nome)
check("H2", "hashes SHA-256 divergentes", [], falha_sha)
check("H3", "tamanhos divergentes", [], falha_tam)
check("H4", "contagens de linha divergentes", [], falha_lin)

no_disco = {p.name for p in DIR.iterdir() if p.is_file()}
check("H5", "pasta = listados + MANIFESTO.md",
      sorted({n for n, *_ in listados} | {"MANIFESTO.md"}), sorted(no_disco))

# ------------------------------------------------------------------- relatório

print(f"Decommissioning Monitor — verificação do snapshot 2026-08-12")
print(f"Pasta: {DIR}")
print("-" * 78)
falhas = 0
for cid, desc, esp, obt, ok in RESULTS:
    tag = "OK    " if ok else "FALHA "
    if not ok:
        falhas += 1
        print(f"{tag}{cid:<5} {desc}")
        print(f"      esperado: {esp}")
        print(f"      obtido  : {obt}")
    else:
        print(f"{tag}{cid:<5} {desc}: {obt}")
print("-" * 78)
print(f"{len(RESULTS)} verificações · {len(RESULTS) - falhas} OK · {falhas} falhas")
sys.exit(1 if falhas else 0)
