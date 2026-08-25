# Decommissioning Monitor

**Offshore decommissioning datasets from Brazil, the United States, the United Kingdom and Norway**

Snapshot of 12 August 2026 · Compiled by Tadeu Santana Cordeiro, Veridis Engenharia · CC BY 4.0

**DOI: [10.5281/zenodo.21919402](https://doi.org/10.5281/zenodo.21919402)**

---

## What this is

Eight datasets on the end of life of offshore oil and gas structures, extracted directly from the public systems of four regulators and one securities authority on a single day, then normalised to a common convention.

Nothing here is a forecast, a model output or a paid subscription extract. Every figure is a count or a date taken from a public register.

The purpose is narrow and deliberate: **to make the distance between "decommissioning approved" and "decommissioning completed" measurable, and reproducible by anyone.**

---

## The eight datasets

| File | Rows | Content | Source |
|---|---|---|---|
| `ndm_us_estruturas_completo_20260812.csv` | 7,091 | Every offshore structure in the Gulf of Mexico register, with installation and removal dates and lease status | BSEE |
| `ndm_us_ferro_ocioso_20260812.csv` | 531 | Structures still standing on a lease that has expired, been relinquished or terminated | derived from the above |
| `ndm_us_destino_remocao_20260812.csv` | 5,722 | What happened to each removed structure: taken to shore, turned into an artificial reef, or reused | BSEE |
| `ndm_sec_aro_CY2025Q4I_20260812.csv` | 445 | Asset retirement obligation declared by filers, December 2025 quarterly frame | SEC XBRL |
| `ndm_br_instalacoes_offshore_20260812.csv` | 253 | Brazilian offshore installations with lifecycle status, operator, water depth and start year | ANP |
| `ndm_br_processos_pdi_rdi_20260812.csv` | 190 | Brazilian decommissioning cases, with the date the plan was approved and the date the completion report was accepted | ANP |
| `ndm_uk_instalacoes_superficie_20260812.csv` | 309 | UK surface infrastructure with operational status | NSTA |
| `ndm_no_instalacoes_20260812.csv` | 914 | Norwegian fixed facilities, with a ten-state lifecycle field | Sokkeldirektoratet |

Total: **15,455 rows of data.**

---

## Why Brazil is the centre of this

The Brazilian regulator publishes **two dated stamps** for the same case. The PDI is the approved decommissioning plan. The RDI is the report that certifies the work as complete and accepted. Two fields, two dates, one table.

That pair makes execution time directly measurable, without inference. Few registers in this field are built that way, and it is the reason this compilation exists at all.

---

## Three things this data will not tell you

**Age is not delay.** A structure standing on an expired lease is a structure on an expired lease. Extensions, agreements and disputes exist and do not appear in raw registers. Never read these files as evidence of non-compliance.

**Absence from the SEC frame is not absence of provision.** Privately held companies do not file there. Companies reporting under other accounting regimes never appear in a US GAAP extract at all. A fiscal year that does not align with the quarter can fall outside the window.

**Declared provision is consolidated and global.** It cannot be divided by structure, and any per-asset figure derived from it would be invented.

---

## Reading order

1. `LASTRO_PUBLICO.md` — every published claim, the file that backs it, and the exact recipe to recompute it
2. `FONTES.md` — the agency, the URL, the query parameters and the extraction date for each dataset
3. `DICIONARIO.md` — every column, the meaning of an empty value, and the join keys
4. `LICENCAS.md` — attribution obligations and the licence of each source
5. `MANIFESTO.md` — SHA-256, byte size and row count of every file

These five are written in Portuguese. The datasets themselves are language-neutral: column names are ASCII, and the categorical values are reproduced exactly as the source regulator publishes them, in the original language.

---

## Conventions you need before recomputing anything

| Convention | Consequence if ignored |
|---|---|
| Text grouping is **case-insensitive** | The SEC file returns 429 companies instead of 428 |
| Median of an even sample is the mean of the two central values | The Brazilian pending median shifts |
| In the SEC file, take the **largest** value per company name | The total moves by US$ 4.68 billion |
| Ages and durations are published as **whole years** | See below |
| Decimal separator is a point, dates are ISO 8601 | Parsing breaks silently |

**On whole years.** The US register recorded only the year of installation for structures predating around 1990, which is 69.2% of the file. In those rows the day and month appear as 1 January. The uncertainty is roughly six months per record. Removal dates are exact in 99.8% of cases. Publishing a decimal on an age derived from a year-only record would claim a precision the source does not have.

Restricting the analysis to exact dates would be worse, not better: only post-1990 installations have full dates, and to appear among the removed they must have had short lives. That filter selects short lifespans by construction and drags the median from 19 years down to 10.5.

---

## Verify everything yourself

The folder ships with its own verifier. It recomputes every published claim from the CSV files alone, following the recipes in `LASTRO_PUBLICO.md`, checks the derived-column formulas row by row, validates the file conventions, and confirms every SHA-256 in `MANIFESTO.md`. No network access, no external libraries, Python 3.10 or later:

```
python verificar.py
```

A non-zero exit code means at least one claim did not reproduce. If that ever happens on an unmodified copy of this deposit, the correction path below applies.

---

## Attribution required by the sources

Contains data under the Norwegian Licence for Open Government Data (NLOD), distributed by Sokkeldirektoratet.

Contains information provided by the North Sea Transition Authority, licensed under the Open Government Licence v3.0.

Brazilian data: Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP), Painel Dinâmico de Descomissionamento de Instalações de Exploração e Produção. Published under Article 14 of ANP Resolution 817/2020.

US data: Bureau of Safety and Environmental Enforcement and Securities and Exchange Commission, works of the United States federal government.

Redistribution of these files must reproduce the two attributions above.

---

## Citation

> Cordeiro, T. S. (2026). *Decommissioning Monitor: offshore decommissioning datasets from Brazil, the US, the UK and Norway (2026-08-12 snapshot)* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.21919402

---

## Corrections

If a figure here is wrong, the correction path is direct: identify the file, the column and the row, and state what the source says. Corrections are incorporated into the next dated extraction and published as a new version.

**Earlier versions are never overwritten.** The snapshot is the point.

---

## What this dataset does not include

An analysis linking each registered operator to the parent company that declares provision was produced and **deliberately left out of this deposit**. It named companies under an adverse label without individual documentary grounding for each one, and that does not belong in a permanent public dataset. No figure published from these files depends on it.

Five further sources were evaluated and excluded because their licences do not permit commercial redistribution, or because no licence is published at all. They are listed in `LICENCAS.md`, section 5. The effective licence of a merged record is the most restrictive intersection of its parts, and a single field from a non-commercial source would make the entire compilation non-redistributable.
