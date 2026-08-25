# Manifesto

**Autor:** Tadeu Santana Cordeiro
**Extração de todas as bases:** 12/08/2026
**DOI:** 10.5281/zenodo.21919402

Este manifesto existe para que qualquer pessoa confirme que baixou exatamente os arquivos que geraram os números publicados. Um único byte diferente muda o hash.

## Conferência

```
Windows PowerShell:   Get-FileHash -Algorithm SHA256 <arquivo>
Linux ou macOS:       sha256sum <arquivo>
Verificação completa: python verificar.py
```

## Arquivos

| Arquivo | Bytes | Linhas de dados | SHA-256 |
|---|---|---|---|
| `DICIONARIO.md` | 9.599 |  | `479eb7171252ddcef20ff96d8f99b7759659803af62ffa0ea18c0e0c9fbf6ac7` |
| `FONTES.md` | 7.345 |  | `d79f2c88224d7144ef238e92c497624c8b887bb4935137fa7b86000d32eabab3` |
| `LASTRO_PUBLICO.md` | 8.815 |  | `7462a22cee0fb082d7977ad6ccdddfa958e8483c609187db60b4158ac5aa2472` |
| `LICENCAS.md` | 5.019 |  | `02db88fdbd4b1f12373cfa7ebc57157b133bf24d999251b99bc1709e2f31a1d2` |
| `ndm_br_instalacoes_offshore_20260812.csv` | 45.099 | 253 | `3fda31e01befa76400b9dd81161108b16749507b81def1f2dfc223d8864fec74` |
| `ndm_br_processos_pdi_rdi_20260812.csv` | 27.735 | 190 | `6e652545c82216d1413fa18d33ea08924e2703e4f33f22acf0408ac7041626ab` |
| `ndm_no_instalacoes_20260812.csv` | 91.596 | 914 | `124fb5ca2f002371e8039b6924114dd48e385d0456204aa7e484cecf1f6f350e` |
| `ndm_sec_aro_CY2025Q4I_20260812.csv` | 46.038 | 445 | `ae7201ca65ee1e6ed975882e8e983419dee04b08ab6485859293f349141883e3` |
| `ndm_uk_instalacoes_superficie_20260812.csv` | 69.253 | 309 | `1c4b617352c6358863031242e4b115fcaf34a5296039f614d950c6239d290475` |
| `ndm_us_destino_remocao_20260812.csv` | 123.267 | 5722 | `05e8dcc0dfaf5ec0033fbd2a8758bdded7317efa68ed62a825c3e491ee9ec0a6` |
| `ndm_us_estruturas_completo_20260812.csv` | 979.360 | 7091 | `d5463ffb2f294ef099d0a21429b1ddbfb601f96a1ff767e0c1626c1f00599c5d` |
| `ndm_us_ferro_ocioso_20260812.csv` | 66.796 | 531 | `6c054bfa497d51a4026b5626366423f675d23922edcac7a2bc6a47daa5bb87a1` |
| `README.md` | 7.880 |  | `b8362c5450a7b0ebbbbb2d73a48318b2a55f550b17c379caad8443ac50d739bd` |
| `verificar.py` | 17.469 |  | `0618db4516b517c36ca719f1f7b7d75ed285852a30459296cc7ae45d39c44f43` |

## Totais

| Item | Valor |
|---|---|
| Arquivos listados | 14 |
| Bases de dados | 8 |
| Documentos e código | 6 |
| Tamanho dos listados | 1.505.271 bytes |
| Linhas de dados | 15.455 |

> Este manifesto **não se auto-inclui**: um arquivo não pode conter o próprio hash. A pasta publicada tem um arquivo a mais que a contagem acima.

## Nota

As bases são snapshot datado e não são sobrescritas. Extração posterior gera arquivo com nova data no nome, e este manifesto continua válido para a extração de 12/08/2026.

`README.md` em inglês descreve o conjunto. `verificar.py` reexecuta todas as afirmações. Fontes e URLs em `FONTES.md`. Licenças em `LICENCAS.md`. Colunas em `DICIONARIO.md`. Receitas em `LASTRO_PUBLICO.md`.
