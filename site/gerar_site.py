#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_site.py — Decommissioning Monitor, página do índice.

Lê os CSVs do depósito (dados/), recalcula cada número publicado com as
mesmas receitas do LASTRO_PUBLICO.md e SÓ gera o index.html se todos os
valores baterem com os verificados nas avaliações. Divergência = build falha
e nenhuma página errada vai ao ar.

Uso:  python gerar_site.py     →  site/index.html
"""

import csv
import decimal
import os
import re
import statistics
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
HISTORICO = RAIZ / "carimbo" / "historico"
AQUI = Path(__file__).resolve().parent
REF = date(2026, 8, 12)


def load(nome):
    with open(DADOS / nome, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def med(vals):
    return statistics.median(sorted(vals))


def arred(x, casas=0):
    """Arredondamento meio-para-CIMA, que é o que faz quem confere com uma
    calculadora na mão. O round() embutido do Python é meio-para-PAR:
    round(24.5) devolve 24 e round(25.5) devolve 26. A divergência só aparece
    quando a mediana cai exatamente no meio, o que acontece em contagem par ou
    quando o próprio valor central termina em 0,5, e numa página que pede para
    o leitor refazer a conta essa diferença de uma unidade seria inexplicável."""
    q = decimal.Decimal(1).scaleb(-casas)
    d = decimal.Decimal(repr(x)).quantize(q, rounding=decimal.ROUND_HALF_UP)
    return float(d) if casas else int(d)


falhas = []


def exigir(rotulo, esperado, obtido):
    if esperado != obtido:
        falhas.append(f"{rotulo}: esperado {esperado}, obtido {obtido}")
    return obtido


# ------------------------------------------------------------- recomputação

us = load("ndm_us_estruturas_completo_20260812.csv")
fer = load("ndm_us_ferro_ocioso_20260812.csv")
des = load("ndm_us_destino_remocao_20260812.csv")
sec = load("ndm_sec_aro_CY2025Q4I_20260812.csv")
bri = load("ndm_br_instalacoes_offshore_20260812.csv")
brp = load("ndm_br_processos_pdi_rdi_20260812.csv")
uk = load("ndm_uk_instalacoes_superficie_20260812.csv")
no = load("ndm_no_instalacoes_20260812.csv")

# Brasil
br_total = exigir("br_total", 253, len(bri))
AGU = "Fora de Operação Permanentemente - Aguarda Descomissionamento"
agu = [r for r in bri if r["situacao"] == AGU]
br_agu = exigir("br_agu", 35, len(agu))
br_med = exigir("br_med", 43, int(med([int(r["idade_calculada"]) for r in agu])))
br_fixas = exigir("br_fixas", 34,
                  sum(1 for r in agu if r["classe"] == "Plataforma Fixa"))
g1 = next(r for r in bri if r["instalacao"] == "PLATAFORMA DE GUARICEMA 1")
exigir("guaricema_ano", "1970", g1["ano_inicio"])
exigir("guaricema_idade", "56", g1["idade_calculada"])
pg = next(r for r in brp if r["protocolo"] == "48610.208347/2024-22")
exigir("guaricema_pdi", "2024-11-07", pg["aprov_pdi"])
exigir("guaricema_rdi_vazio", "", pg["aprov_rdi"])

pend_mar = [r for r in brp if r["tipo_pdi"] == "Integral"
            and "MAR" in r["classe"] and r["pendente_anos"]]
br_pend = exigir("br_pend", 10, len(pend_mar))
br_pend_med = exigir("br_pend_med", 7.1,
                     arred(med([float(r["pendente_anos"]) for r in pend_mar]), 1))
mais = max(pend_mar, key=lambda r: float(r["pendente_anos"]))
exigir("mexilhao", ("MEXILHÃO", "SANTOS", "2016-05-30"),
       (mais["campo"], mais["bacia"], mais["aprov_pdi"]))
br_concl_mar = exigir("br_concl_mar", 3,
                      sum(1 for r in brp if r["tipo_pdi"] == "Integral"
                          and "MAR" in r["classe"] and r["ciclo_anos"]))

# Estados Unidos
us_total = exigir("us_total", 7091, len(us))
rem = [r for r in us if r["removida"]]
us_rem = exigir("us_rem", 5766, len(rem))
us_pe = exigir("us_pe", 1325, len(us) - len(rem))
us_vida = exigir("us_vida", 19,
                 arred(med([float(r["vida_anos"]) for r in rem])))
us_ocioso = exigir("us_ocioso", 531, len(fer))
idades = [float(r["idade_anos"]) for r in fer]
us_ocioso_med = exigir("us_ocioso_med", 47, arred(med(idades)))
exigir("us_max_1949", {"1949-01-01"},
       {r["instalada"] for r in fer if float(r["idade_anos"]) == max(idades)})
exc = exigir("excedencia", 2.5, arred(med(idades) / med([float(r["vida_anos"]) for r in rem]), 1))
r2010 = exigir("ritmo2010", 188, round(sum(
    1 for r in rem if 2010 <= int(r["removida"][:4]) <= 2019) / 10))
r2020 = exigir("ritmo2020", 73, round(sum(
    1 for r in rem if int(r["removida"][:4]) >= 2020) / 6.5))
disp = {}
for r in des:
    disp[r["REMOVAL_DISPOSITION"]] = disp.get(r["REMOVAL_DISPOSITION"], 0) + 1
exigir("destinos", {"To Shore": 3201, "": 1830, "Rigs-to-Reef": 610, "Reuse": 81}, disp)

grupos = {}
for r in sec:
    grupos.setdefault(r["empresa"].casefold(), []).append(int(float(r["aro_usd"])))
aro_emp = exigir("aro_emp", 428, len(grupos))
aro_soma = exigir("aro_soma", 208_145_279_217, sum(max(v) for v in grupos.values()))

# Reino Unido e Noruega
uk_total = exigir("uk_total", 309, len(uk))
uk_back = exigir("uk_back", 41,
                 sum(1 for r in uk if r["status"] in ("NOT IN USE", "ABANDONED")))
no_total = exigir("no_total", 914, len(no))
no_fases = exigir("no_fases", 10, len({r["fase"] for r in no}))

linhas_dados = exigir("linhas", 15455,
                      len(us) + len(fer) + len(des) + len(sec) + len(bri)
                      + len(brp) + len(uk) + len(no))
exigir("dest_linhas", 5722, len(des))

# Join real removidas × destinos, pela chave (complexo, num). Nada de subtração.
ch_rem = {(r["complexo"], r["num"]) for r in rem}
ch_des = {(r["COMPLEX_ID_NUM"], r["STRUCTURE_NUMBER"]) for r in des}
dest_match = exigir("dest_match", 5721, len(ch_rem & ch_des))
sem_dest = exigir("sem_dest", 45, len(ch_rem - ch_des))
exigir("dest_orfao", 1, len(ch_des - {(r["complexo"], r["num"]) for r in us}))

# ------------------------------------------------- mapa desenhado pelos dados
# Nenhum basemap, nenhum tile, nenhuma biblioteca: só os pontos dos registros.
# A plataforma continental se desenha sozinha. Projeção equiretangular com
# correção cos(lat média); cada painel cabe numa caixa 560×620.

import math


def _coord(r):
    try:
        la, lo = float(r["lat"]), float(r["lon"])
    except (ValueError, KeyError, TypeError):
        return None
    if (la == 0 and lo == 0) or not (-90 <= la <= 90 and -180 <= lo <= 180):
        return None
    return lo, la


def _painel(pontos, raio, ordem_fills):
    lons = [p[0] for p in pontos]
    lats = [p[1] for p in pontos]
    lo0, lo1, la0, la1 = min(lons), max(lons), min(lats), max(lats)
    plo = (lo1 - lo0) * 0.05 + 0.1
    pla = (la1 - la0) * 0.05 + 0.1
    lo0, lo1, la0, la1 = lo0 - plo, lo1 + plo, la0 - pla, la1 + pla
    k = math.cos(math.radians((la0 + la1) / 2))
    razao = (la1 - la0) / ((lo1 - lo0) * k)          # altura/largura
    w = 560.0 if razao <= 620 / 560 else 620.0 / razao
    esc = w / ((lo1 - lo0) * k)
    h = (la1 - la0) * esc
    partes = []
    for cls, fill in ordem_fills:
        cs = "".join(
            f'<circle cx="{(p[0] - lo0) * k * esc:.1f}" '
            f'cy="{(la1 - p[1]) * esc:.1f}" r="{raio}"/>'
            for p in pontos if p[2] == cls)
        partes.append(f'<g fill="{fill}">{cs}</g>')
    return "".join(partes), f"0 0 {w:.0f} {h:.0f}"


DIM, TEAL, AMBAR, LARANJA, AZUL = "#3f4c59", "#2fa389", "#f0b53d", "#ee7f45", "#4d6478"

fer_chaves = {(r["complexo"], r["num"]) for r in fer}
pts_us, us_sem_coord = [], 0
for r in us:
    c = _coord(r)
    if not c:
        us_sem_coord += 1
        continue
    cls = "rem" if r["removida"] else (
        "oci" if (r["complexo"], r["num"]) in fer_chaves else "ati")
    pts_us.append((c[0], c[1], cls))
mapa_us, vb_us = _painel(pts_us, 1.3,
                         [("rem", DIM), ("ati", TEAL), ("oci", AMBAR)])

SIT_CLS = {"Operando": "op", "Operando em Extensão de Vida Útil": "op",
           AGU: "agu", "Em Descomissionamento": "emd", "Descomissionada": "dec"}
pts_br, br_sem_coord = [], 0
for r in bri:
    c = _coord(r)
    if not c:
        br_sem_coord += 1
        continue
    pts_br.append((c[0], c[1], SIT_CLS.get(r["situacao"], "out")))
mapa_br, vb_br = _painel(pts_br, 3.2,
                         [("dec", DIM), ("out", AZUL), ("op", TEAL),
                          ("emd", LARANJA), ("agu", AMBAR)])

UK_CLS = {"ACTIVE": "op", "NOT IN USE": "agu", "ABANDONED": "agu",
          "REMOVED": "dec"}
pts_uk = [( *c, UK_CLS.get(r["status"], "out"))
          for r in uk if (c := _coord(r))]
mapa_uk, vb_uk = _painel(pts_uk, 2.6,
                         [("dec", DIM), ("out", AZUL), ("op", TEAL),
                          ("agu", AMBAR)])

exigir("mapa_us_pts", 7083, len(pts_us))
exigir("mapa_us_sem", 8, us_sem_coord)
exigir("mapa_br_pts", 227, len(pts_br))
exigir("mapa_br_sem", 26, br_sem_coord)
exigir("mapa_uk_pts", 309, len(pts_uk))
# ferro ocioso plotado + ferro ocioso sem coordenada = 531 (nada some calado)
exigir("mapa_oci_531", 531, sum(1 for p in pts_us if p[2] == "oci")
       + sum(1 for r in fer if not _coord(r)))

SIMBOLOS_ADIADOS = []   # o painel de profundidade se junta a estes mais abaixo

# ------------------------------------------------- painel de lâmina d'água
# O mapa mostra ONDE a estrutura está e descarta a QUE PROFUNDIDADE, que é a
# dimensão em que o setor pensa e que a base traz com cobertura total nos dois
# recortes que importam. Escala logarítmica: a faixa vai de metros a quilômetros.

def _lamina(r):
    try:
        v = float(r["lamina_m"])
        return v if v > 0 else None
    except (ValueError, TypeError, KeyError):
        return None


TOPO_M, FUNDO_M, ALT_SVG = 1.0, 10000.0, 470.0
LOG0, LOGR = math.log10(TOPO_M), math.log10(FUNDO_M) - math.log10(TOPO_M)


def _y(m):
    return 30 + (math.log10(m) - LOG0) / LOGR * ALT_SVG


# Comparação DISJUNTA: as 35 que aguardam contra as 171 que não aguardam, e não
# contra o conjunto inteiro, que as contém. Comparar com o todo esconde o efeito
# e ainda faz o leitor somar a mesma instalação duas vezes no gráfico.
com_lam = [r for r in bri if _lamina(r)]
br_nao_agu_lam = [v for r in com_lam if r["situacao"] != AGU and (v := _lamina(r))]
br_agu_lam = [v for r in agu if (v := _lamina(r))]
fer_lam = [v for r in fer if (v := _lamina(r))]
br_sem_lam = exigir("br_sem_lamina", 47, sum(1 for r in bri if _lamina(r) is None))
# os 47 sem lâmina são unidades móveis de perfuração, e o campo vem ZERADO,
# não ausente: dizer "não traz o campo" seria errado contra o CSV
# Destas, 46 são unidade móvel de perfuração e UMA não é: o FPSO FRADE, unidade
# flutuante de produção, que tem lâmina própria e mesmo assim vem com o campo em
# zero. Não dá para dizer "as 47 são móveis": o gate conta as duas classes
# separadas justamente para não se aprovar sozinho.
MOVEIS = ("Navio Sonda", "Unidade Semissubmersível", "Sonda")
sem_lam_moveis = exigir("sem_lam_moveis", 46,
                        sum(1 for r in bri if _lamina(r) is None
                            and r["classe"] in MOVEIS))
sem_lam_outras = exigir("sem_lam_outras", 1,
                        sum(1 for r in bri if _lamina(r) is None
                            and r["classe"] not in MOVEIS))

br_nao_agu_n = exigir("br_nao_agu_n", 171, len(br_nao_agu_lam))
exigir("br_agu_lam_n", 35, len(br_agu_lam))
exigir("fer_lam_n", 531, len(fer_lam))
br_nao_agu_med = exigir("br_nao_agu_med", 275, arred(med(br_nao_agu_lam)))
br_agu_med = exigir("br_agu_lam_med", 26, arred(med(br_agu_lam)))
br_agu_rasas = exigir("br_agu_rasas", 33, sum(1 for v in br_agu_lam if v < 50))
fer_lam_med = exigir("fer_lam_med", 62, arred(med(fer_lam)))
# A razão é calculada sobre as medianas PUBLICADAS (275 e 26), e não sobre a
# mediana crua (25,5), para que quem dividir os dois números da página chegue
# ao mesmo resultado. Com a crua daria 10,8 e não fecharia com o que está à vista.
razao_lam = exigir("razao_lam", 10.6,
                   arred(br_nao_agu_med / br_agu_med, 1))

# idade por faixa de lâmina: é isto que sustenta "o passivo profundo vem depois"
def _idade(r):
    try:
        return int(r["idade_calculada"])
    except (ValueError, TypeError, KeyError):
        return None


# Os três grupos de idade têm de ser DISJUNTOS, pela mesma razão das colunas do
# gráfico. Medir "abaixo de 300 m" sobre o conjunto todo colocaria a fila dentro
# do grupo raso e inflaria o contraste: dava 38 em vez dos 35 reais.
_fora_fila = [r for r in com_lam if r["situacao"] != AGU]
_fundo = [i for r in _fora_fila if _lamina(r) >= 300 and (i := _idade(r)) is not None]
_raso = [i for r in _fora_fila if _lamina(r) < 300 and (i := _idade(r)) is not None]
_fila = [i for r in agu if (i := _idade(r)) is not None]
exigir("grupos_idade_disjuntos", len(com_lam), len(_fundo) + len(_raso) + len(_fila))
exigir("fila_toda_rasa", 0, sum(1 for r in agu if (v := _lamina(r)) and v >= 300))
idade_fundo = exigir("idade_fundo", 12, arred(med(_fundo)))
idade_raso = exigir("idade_raso", 35, arred(med(_raso)))
idade_fila = exigir("idade_fila", 43, arred(med(_fila)))

GRUPOS_LAM = [
    (br_nao_agu_lam, AZUL, br_nao_agu_med),
    (br_agu_lam, AMBAR, br_agu_med),
    (fer_lam, LARANJA, fer_lam_med),
]
COL_X = [150, 400, 650]
REGUA = [(10, "10 m"), (30, "30 m"), (100, "100 m"), (300, "300 m"),
         (1000, "1 km"), (3000, "3 km")]

_nuvem, _medianas = [], []
for i, (vals, cor, mediana) in enumerate(GRUPOS_LAM):
    cx = COL_X[i]
    s = 7 + i * 131                      # deslocamento determinístico: build estável
    cs = []
    for v in sorted(vals):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        cs.append(f'<circle cx="{cx + (s / 0x7FFFFFFF - .5) * 92:.1f}" '
                  f'cy="{_y(v):.1f}" r="2"/>')
    _nuvem.append(f'<g fill="{cor}" opacity=".8">{"".join(cs)}</g>')
    _medianas.append(f'<line x1="{cx - 60}" y1="{_y(mediana):.1f}" x2="{cx + 60}" '
                     f'y2="{_y(mediana):.1f}" stroke="{cor}" stroke-width="2.5"/>')

_reguas = "".join(f'<line x1="46" y1="{_y(m):.1f}" x2="800" y2="{_y(m):.1f}" '
                  f'stroke="#1d3040" stroke-width="1"/>' for m, _ in REGUA)

DEPTH_SYMBOL = (
    f'<symbol id="depth" viewBox="0 0 810 {30 + ALT_SVG + 52:.0f}">'
    f'<rect x="46" y="18" width="754" height="{ALT_SVG + 18:.0f}" fill="#07131d"/>'
    f'<line x1="46" y1="20" x2="800" y2="20" stroke="#3fa9d6" stroke-width="2"/>'
    + _reguas + "".join(_nuvem) + "".join(_medianas) + "</symbol>")

_rot_regua = "".join(
    f'<text x="40" y="{_y(m) + 4:.1f}" font-size="11" fill="#6d8698" '
    f'text-anchor="end">{rot}</text>' for m, rot in REGUA)
_rot_mediana = "".join(
    f'<text x="{COL_X[i] + 66}" y="{_y(m) + 4:.1f}" font-size="12" font-weight="700" '
    f'fill="{c}">{m} m</text>' for i, (_, c, m) in enumerate(GRUPOS_LAM))


def depth_svg(rotulos, superficie):
    cols = "".join(
        f'<text x="{COL_X[i]}" y="{30 + ALT_SVG + 24:.0f}" font-size="12" '
        f'fill="#cfe0d9" text-anchor="middle" font-weight="600">{r}</text>'
        f'<text x="{COL_X[i]}" y="{30 + ALT_SVG + 40:.0f}" font-size="11" '
        f'fill="#8ba3b4" text-anchor="middle">{len(GRUPOS_LAM[i][0])}</text>'
        for i, r in enumerate(rotulos))
    return (f'<svg viewBox="0 0 810 {30 + ALT_SVG + 52:.0f}" role="img" '
            f'aria-label="{superficie}"><use href="#depth"/>'
            f'<text x="54" y="14" font-size="11" fill="#3fa9d6">{superficie}</text>'
            + _rot_regua + _rot_mediana + cols + "</svg>")


# A marca entra como SVG vetorial embutido, lido do arquivo oficial da Veridis.
# Nada de PNG: o selo tem menos de 1 KB em vetor, escala sem borrar e não exige
# requisição externa, o que a página não pode fazer de qualquer forma.
LOGO = (RAIZ.parent / "VERIDIS_ENGENHARIA_TECNOLOGIA_SITE" / "logo" / "c2_selo.svg")
if not LOGO.is_file():
    falhas.append(f"logo oficial não encontrada em {LOGO}")
    _selo_interno = ""
else:
    _svg = LOGO.read_text(encoding="utf-8")
    _selo_interno = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", _svg, flags=re.S).strip()
    exigir("selo_tem_conteudo", True, len(_selo_interno) > 200)

# O mesmo selo vira favicon, em SVG, sem arquivo externo e sem rasterizar.
import urllib.parse as _up

_fav_svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
            + _selo_interno.replace("\n", "") + "</svg>")
FAVICON = "data:image/svg+xml," + _up.quote(_fav_svg, safe="")

MAP_SYMBOLS = (
    f'<svg width="0" height="0" style="position:absolute" aria-hidden="true">'
    f'<symbol id="map-us" viewBox="{vb_us}">{mapa_us}</symbol>'
    f'<symbol id="map-br" viewBox="{vb_br}">{mapa_br}</symbol>'
    f'<symbol id="map-uk" viewBox="{vb_uk}">{mapa_uk}</symbol>'
    f'<symbol id="selo" viewBox="0 0 64 64">{_selo_interno}</symbol>'
    f'{DEPTH_SYMBOL}</svg>')

# ------------------------------------------------------------ edição semanal

sys.path.insert(0, str(AQUI))
from edicao import gerar_edicao

try:
    ed = gerar_edicao()
except Exception as e:
    falhas.append(f"edição semanal: {e}")
    ed = None

ED_LABELS = [
    ("operando", "Operating", "Operando"),
    ("extensao_vida", "Operating in life extension", "Operando em extensão de vida útil"),
    ("aguarda_descom", "Permanently out of use, awaiting decommissioning",
     "Fora de operação permanente, aguarda descomissionamento"),
    ("em_descom", "Under decommissioning", "Em descomissionamento"),
    ("descomissionada", "Decommissioned", "Descomissionada"),
    ("hibernacao", "Temporarily out of use", "Fora de operação temporária (hibernação)"),
    ("em_construcao", "Under construction", "Em construção"),
    ("outras", "Other situations", "Outras situações"),
]


def ed_tbody(lang):
    linhas = []
    for chave, en, pt in ED_LABELS:
        rot = en if lang == "en" else pt
        val = ed["ciclo"][chave]
        d = ed["delta"].get("ciclo." + chave)
        if d is None:
            dtxt = ""
        elif d == 0:
            dtxt = "="
        else:
            dtxt = f"+{d}" if d > 0 else f"−{abs(d)}"
        destaque = ' class="hl"' if chave == "aguarda_descom" else ""
        linhas.append(f"<tr{destaque}><td>{rot}</td><td>{val}</td>"
                      f"<td>{dtxt}</td></tr>")
    tot = ed["total_offshore"]
    rot_tot = "Total offshore installations" if lang == "en" \
        else "Total de instalações offshore"
    d = ed["delta"].get("total_offshore")
    dtxt = "" if d is None else ("=" if d == 0 else (f"+{d}" if d > 0 else f"−{abs(d)}"))
    linhas.append(f'<tr class="tot"><td>{rot_tot}</td><td>{tot}</td><td>{dtxt}</td></tr>')
    return "".join(linhas)


if ed:
    soma_ciclo = sum(ed["ciclo"].values())
    exigir("ed_soma_ciclo", ed["total_offshore"], soma_ciclo)
    ed_data = ed["captura_utc"][:10]
    ED_V = {
        "ED_DATE_EN": ed_data, "ED_DATE_PT": "/".join(reversed(ed_data.split("-"))),
        "ED_SNAP": ed["snapshot"], "ED_SHA12": ed["ata_sha256"][:12],
        "ED_TBODY_EN": ed_tbody("en"), "ED_TBODY_PT": ed_tbody("pt"),
        "ED_PDI_AP": str(ed["pdi_aprovados"]), "ED_PDI_RE": str(ed["pdi_recebidos"]),
        "ED_RDI_AP": str(ed["rdi_aprovados"]),
        "ED_ULT_PDI_EN": ed["ultima_aprovacao_pdi"],
        "ED_ULT_PDI_PT": "/".join(reversed(ed["ultima_aprovacao_pdi"].split("-"))),
        "ED_ULT_RDI_EN": ed["ultima_aprovacao_rdi"],
        "ED_ULT_RDI_PT": "/".join(reversed(ed["ultima_aprovacao_rdi"].split("-"))),
        "ED_DELTA_EN": ("First edition: this is the baseline. Changes appear "
                        "from the second edition on."
                        if not ed["delta"] else
                        f"Changes measured against the previous attested "
                        f"edition ({ed.get('delta_contra', '')})."),
        "ED_DELTA_PT": ("Primeira edição: esta é a linha de base. As mudanças "
                        "aparecem a partir da segunda."
                        if not ed["delta"] else
                        f"Mudanças medidas contra a edição atestada anterior "
                        f"({ed.get('delta_contra', '')})."),
    }
else:
    ED_V = {}

# O número de verificações vem da EXECUÇÃO do verificador do depósito, não de
# literal. O build também exige zero falhas: verificador quebrado = sem página.
r = subprocess.run([sys.executable, str(DADOS / "verificar.py")],
                   capture_output=True, text=True,
                   env=dict(os.environ, PYTHONUTF8="1"))
m = re.search(r"(\d+) verificações · (\d+) OK · (\d+) falhas",
              r.stdout or "")
if r.returncode != 0 or not m or m.group(3) != "0" or m.group(1) != m.group(2):
    falhas.append(f"verificar.py: exit {r.returncode}, saída não conferida")
    checks = "?"
else:
    checks = m.group(1)

snaps_dirs = [p for p in HISTORICO.iterdir() if p.is_dir()] if HISTORICO.is_dir() else []
snaps = len(snaps_dirs)
snaps_at = sum(1 for p in snaps_dirs
               if (p / "ATESTADOS" / "ata_snapshot-autocontido.json").is_file())
import json as _json
snaps_chain = 0
for p in snaps_dirs:
    f = p / "ata_snapshot.json"
    if f.is_file() and _json.loads(f.read_text(encoding="utf-8")).get("cadeia"):
        snaps_chain += 1

if falhas:
    print("BUILD RECUSADO — números divergem do verificado:")
    for f in falhas:
        print("  ", f)
    sys.exit(1)

# ------------------------------------------------------------------ render


def fmt_en(n):
    return f"{n:,}"


def fmt_pt(n):
    return f"{n:,}".replace(",", ".")


V = {
    "BR_TOTAL": str(br_total), "BR_AGU": str(br_agu), "BR_MED": str(br_med),
    "BR_FIXAS": str(br_fixas), "BR_PEND": str(br_pend),
    "BR_PEND_MED_EN": "7.1", "BR_PEND_MED_PT": "7,1",
    "BR_CONCL": str(br_concl_mar),
    "US_TOTAL_EN": fmt_en(us_total), "US_TOTAL_PT": fmt_pt(us_total),
    "US_REM_EN": fmt_en(us_rem), "US_REM_PT": fmt_pt(us_rem),
    "US_PE_EN": fmt_en(us_pe), "US_PE_PT": fmt_pt(us_pe),
    "US_VIDA": str(us_vida), "US_OCIOSO": str(us_ocioso),
    "US_OCIOSO_MED": str(us_ocioso_med),
    "EXC_EN": "2.5", "EXC_PT": "2,5",
    "RITMO_2010": str(r2010), "RITMO_2020": str(r2020),
    "SHORE_EN": fmt_en(3201), "SHORE_PT": fmt_pt(3201),
    "REEF": "610", "REUSE": "81",
    "ARO_EMP": str(aro_emp), "ARO_BI_EN": "208.1", "ARO_BI_PT": "208,1",
    "UK_TOTAL": str(uk_total), "UK_BACK": str(uk_back),
    "NO_TOTAL": str(no_total), "NO_FASES": str(no_fases),
    "ROWS_EN": fmt_en(linhas_dados), "ROWS_PT": fmt_pt(linhas_dados),
    "DEST_MATCH_EN": fmt_en(dest_match), "DEST_MATCH_PT": fmt_pt(dest_match),
    "SEM_DEST": str(sem_dest),
    "CHECKS": checks, "SNAPS": str(snaps), "SNAPS_AT": str(snaps_at),
    "SNAPS_CHAIN": str(snaps_chain),
    "GERADO_UTC": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    "MAP_SYMBOLS": MAP_SYMBOLS, "FAVICON": FAVICON,
    "MAP_US_VB": vb_us, "MAP_BR_VB": vb_br, "MAP_UK_VB": vb_uk,
    "MP_US_N_EN": fmt_en(len(pts_us)), "MP_US_N_PT": fmt_pt(len(pts_us)),
    "MP_US_SEM": str(us_sem_coord),
    "MP_BR_N": str(len(pts_br)), "MP_BR_SEM": str(br_sem_coord),
    "MP_UK_N": str(len(pts_uk)),
    "DEPTH_EN": depth_svg(["Brazil, not in the queue",
                           "Brazil, awaiting decommissioning",
                           "US Gulf, idle iron"], "sea surface"),
    "DEPTH_PT": depth_svg(["Brasil, fora da fila",
                           "Brasil, aguardando descomissionamento",
                           "Golfo do México, ferro ocioso"], "superfície do mar"),
    "BR_NAO_AGU_N": str(br_nao_agu_n), "BR_NAO_AGU_MED": str(br_nao_agu_med),
    "BR_AGU_MED": str(br_agu_med), "BR_AGU_RASAS": str(br_agu_rasas),
    "FER_LAM_MED": str(fer_lam_med), "BR_SEM_LAM": str(br_sem_lam),
    "SEM_LAM_MOVEIS": str(sem_lam_moveis), "SEM_LAM_OUTRAS": str(sem_lam_outras),
    "RAZAO_LAM_EN": "10.6", "RAZAO_LAM_PT": "10,6",
    "IDADE_FUNDO": str(idade_fundo), "IDADE_RASO": str(idade_raso),
    "IDADE_FILA": str(idade_fila),
    **ED_V,
}

template = (AQUI / "template.html").read_text(encoding="utf-8")
html = template
for k, v in V.items():
    html = html.replace("{{" + k + "}}", v)

sobras = [t for t in html.split("{{")[1:]]
if sobras:
    print("BUILD RECUSADO — placeholders sem valor:",
          sorted({s.split("}}")[0] for s in sobras if "}}" in s}))
    sys.exit(1)

# Portão tipográfico: travessão e meia-risca são proibidos na página inteira.
PROIBIDOS = {"—": "travessão U+2014", "–": "meia-risca U+2013",
             "―": "barra horizontal U+2015"}
tipo_falhas = [nome for ch, nome in PROIBIDOS.items() if ch in html]
if tipo_falhas:
    print("BUILD RECUSADO — caractere proibido:", ", ".join(tipo_falhas))
    sys.exit(1)

saida = AQUI / "index.html"
saida.write_text(html, encoding="utf-8")
print(f"todos os números recomputados e conferidos — {len(V)} valores injetados")
print(f"gerado: {saida}  ({saida.stat().st_size:,} bytes)")
