# Fontes: de onde veio cada base

**Autor:** Tadeu Santana Cordeiro
**Extração:** 12/08/2026
**Método:** toda URL abaixo foi acessada e respondeu no dia da extração. Nenhuma foi copiada de relatório de terceiro.

---

## Estados Unidos, estruturas offshore

**Órgão:** Bureau of Safety and Environmental Enforcement (BSEE), Departamento do Interior dos Estados Unidos
**Portal:** `https://www.data.bsee.gov/Main/RawData.aspx`

| Arquivo baixado | URL | Bytes |
|---|---|---|
| `PlatStrucRawData.zip` | `https://www.data.bsee.gov/Platform/Files/PlatStrucRawData.zip` | 1.758.553 |
| `DecomCostEstRawData.zip` | `https://www.data.bsee.gov/Leasing/Files/DecomCostEstRawData.zip` | 850.856 |
| `PermStrucRawData.zip` | `https://www.data.bsee.gov/Other/Files/PermStrucRawData.zip` | 8.555 |
| `BoreholeRawData.zip` | `https://www.data.bsee.gov/Well/Files/BoreholeRawData.zip` | 3.483.964 |

Dentro do primeiro ZIP, sob `PlatStrucRawData/`, os arquivos usados foram `mv_platstruc_structures.txt` (7.091 registros), `mv_platstruc_leases.txt` (31.666) e `mv_platstruc_removaldisp.txt` (5.722). Apesar da extensão `.txt`, são CSV com aspas e quebra CRLF.

**Bases derivadas:**

| Base publicada | Origem |
|---|---|
| `ndm_us_estruturas_completo_20260812.csv` | `mv_platstruc_structures.txt` cruzado com `mv_platstruc_leases.txt` para trazer a situação do contrato |
| `ndm_us_ferro_ocioso_20260812.csv` | subconjunto da base acima: `removida` vazia, contrato encerrado, `instalada` preenchida |
| `ndm_us_destino_remocao_20260812.csv` | `mv_platstruc_removaldisp.txt`, sem transformação |

Os arquivos `DecomCostEstRawData.zip`, `PermStrucRawData.zip` e `BoreholeRawData.zip` foram baixados na mesma sessão para inspeção de escopo e **não geraram base publicada**. Ficam listados por transparência de método.


> ⚠️ O caminho é sensível a maiúsculas no meio do nome: `PlatStrucRawData.zip`. Escrito `Platstruc`, o servidor devolve **HTML com status 200**, não erro. Validar `Content-Type`, nunca só o código.

---

## Estados Unidos, provisão de desmobilização de ativo

**Órgão:** Securities and Exchange Commission (SEC)
**API:** XBRL frames, quadro `CY2025Q4I`

```
https://data.sec.gov/api/xbrl/frames/us-gaap/AssetRetirementObligationsNoncurrent/USD/CY2025Q4I.json
https://data.sec.gov/api/xbrl/frames/us-gaap/AssetRetirementObligation/USD/CY2025Q4I.json
```

A SEC exige cabeçalho `User-Agent` identificando quem consulta. Não é autenticação.

**Base derivada:** `ndm_sec_aro_CY2025Q4I_20260812.csv`, união das duas tags, 445 linhas por CIK.

> ⚠️ O cadastro traz espaço não separável (U+00A0) dentro de nomes de empresa.

---

## Noruega

**Órgão:** Sokkeldirektoratet (Sodir), antigo Norwegian Petroleum Directorate
**Tabela:** `facility_fixed`, instalações fixas

```
https://factpages.sodir.no/public?/Factpages/external/tableview/facility_fixed
  &rs:Command=Render&rc:Toolbar=false&rc:Parameters=f
  &IpAddress=not_used&CultureCode=en&rs:Format=CSV&Top100=false
```

Resposta: `text/csv`, 277.815 bytes, 914 instalações.

**Base derivada:** `ndm_no_instalacoes_20260812.csv`.

> ⚠️ O CSV começa com BOM UTF-8, que gruda no nome da primeira coluna e a faz retornar vazia sem erro. Registros sem data trazem a **época zero do Excel, literalmente `1900-01-01`**, que foi esvaziada nesta base. **A regra vale só para esse valor específico e só para a Noruega.** Nas bases americanas, anos como 1942 ou 1949 são dado real com dia e mês imputados, e não devem ser filtrados.

---

## Países Baixos

**Órgão:** NLOG, portal de petróleo e gás dos Países Baixos, serviço geográfico operado pelo GDN
**Serviço WFS:** `https://www.gdngeoservices.nl/geoserver/nlog/ows`
**Camada:** `nlog:GDW_NG_FACILITY_UTM`

```
https://www.gdngeoservices.nl/geoserver/nlog/ows?service=WFS&version=2.0.0
  &request=GetFeature&typeName=nlog:GDW_NG_FACILITY_UTM
  &outputFormat=application/json&count=1000
```

Resposta: GeoJSON, 655 instalações.

**Base derivada:** nenhuma. Ver a nota de licença abaixo.

> ⚠️ Das sete camadas do serviço, **só esta é em caixa alta**. Escrita em minúscula, devolve HTTP 400.
>
> ⚠️ **Esta base não foi depositada.** O serviço não publica texto de licença, e licença indeterminada é incompatível com depósito imutável. A consulta acima é pública e devolve, em 12/08/2026, 655 instalações, sendo 118 descomissionadas e 103 removidas. Quem quiser conferir roda a consulta.

---

## Reino Unido

**Órgão:** North Sea Transition Authority (NSTA)
**Organização ArcGIS Online:** `OZMfUznmLTnWccBc` em `services-eu1.arcgis.com`
**Serviço:** `UKCS offshore infrastructure surface points WGS84`, layer **1**
**Camada no dia da extração:** `PETROLEUM_INFRASTRUCTURE_SURFACE_POINTS_WGS84_20260701`

```
https://services-eu1.arcgis.com/OZMfUznmLTnWccBc/arcgis/rest/services/
  UKCS%20offshore%20infrastructure%20surface%20points%20WGS84/FeatureServer/1/query
  ?where=1%3D1&outFields=*&outSR=4326&resultRecordCount=1000&f=json
```

Resposta: 309 registros.

**Base derivada:** `ndm_uk_instalacoes_superficie_20260812.csv`.

> ⚠️ O nome da camada carrega a data de republicação no sufixo. Um coletor que fixe o nome quebra na edição seguinte; resolver pelo catálogo. E o layer é o **1**, não o 0.

---

## Brasil

**Órgão:** Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP)
**Fonte:** Painel Dinâmico de Descomissionamento de Instalações de Exploração e Produção
**Página oficial do painel:**
`https://www.gov.br/anp/pt-br/centrais-de-conteudo/paineis-dinamicos-da-anp/paineis-dinamicos-sobre-exploracao-e-producao-de-petroleo-e-gas/painel-dinamico-de-descomissionamento-de-instalacoes-de-exploracao-e-producao`

**Página de contexto:**
`https://www.gov.br/anp/pt-br/assuntos/exploracao-e-producao-de-oleo-e-gas/seguranca-operacional/descomissionamento-de-instalacoes`

**Base legal do dado:** Resolução ANP nº 817/2020, artigo 14, que determina a publicidade dos Programas de Descomissionamento de Instalações.

**Acesso programático:** API pública do próprio relatório Power BI, host `wabi-brazil-south-d-primary-api.analysis.windows.net`, endpoint `POST /public/reports/querydata?synchronous=true`, autenticação por cabeçalho `X-PowerBI-ResourceKey` sem cookie nem token.

**Tabelas consultadas:** `INSTALACAO` (1.681 registros, 253 offshore), `DESCOMISSIONAMENTO_PROCESSOS` (190), `PAT_ATIVIDADES_PREVISTO` (3.159), `PAT_DADOS_GERAIS_PREVISTO` (449).

**Atualização do painel no dia da extração:** 12/08/2026, 11h05, horário de Brasília, conforme carimbo `lastRefreshTime` retornado pelo próprio serviço.

**Bases derivadas:** `ndm_br_instalacoes_offshore_20260812.csv`, `ndm_br_processos_pdi_rdi_20260812.csv`.

> ⚠️ A chave de recurso e os identificadores do relatório mudam quando a ANP republica o painel. Não há histórico público de versões anteriores. A coluna de idade da tabela não é consistente com o ano de início de operação; toda idade foi recalculada do ano de início.

---

## Conferência

Cada base traz a data de extração no nome do arquivo. O `MANIFESTO.md` desta pasta traz o hash SHA-256, a contagem de linhas e o tamanho de cada arquivo, para que qualquer pessoa confirme que baixou exatamente o que gerou os números publicados.
