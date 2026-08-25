# Dicionário de dados

**Autor:** Tadeu Santana Cordeiro
**Data:** 12/08/2026

---

## Convenções válidas para todos os arquivos

| Item | Convenção |
|---|---|
| Codificação | UTF-8 com BOM |
| Separador de campo | vírgula |
| Delimitador de texto | aspas duplas |
| **Separador decimal** | **ponto**, em todas as colunas numéricas de todos os arquivos |
| **Data** | **ISO 8601**, `AAAA-MM-DD`, em todos os arquivos |
| Campo vazio | string vazia, nunca `NULL`, `NA` ou `-` |
| Data de referência para idade | 12/08/2026 |
| Duração em anos | diferença em dias dividida por 365,25 |

> **Semântica do vazio.** Vazio significa **não informado na fonte**. Não significa zero nem "não se aplica". Onde a distinção importa, ela está descrita na coluna correspondente abaixo.

---

## Estados Unidos

### `ndm_us_estruturas_completo_20260812.csv` — 7.091 linhas

Cadastro completo de estruturas do Golfo do México. **Chave: `complexo` + `num`**, que dá 7.091 pares únicos para 7.091 linhas. ⚠️ `estrutura` + `num` **não é chave**: rende cerca de 1.160 pares distintos (1.156 com comparação insensível a caixa, 1.164 sensível), e o par `A`+`1` aparece 1.608 vezes.

| Coluna | Tipo | Descrição |
|---|---|---|
| `estrutura` | texto | Nome da estrutura. Repete muito: dezenas se chamam apenas A, B ou C. Nunca usar sozinho como chave |
| `num` | inteiro | Número da estrutura dentro do complexo. **Só 17 valores distintos em 7.091 linhas.** Nunca usar como identificador sozinho |
| `complexo` | inteiro | Identificador do complexo a que pertence |
| `operador` | texto | Operador registrado |
| `tipo` | texto | Código de tipo de estrutura |
| `estrutura_maior` | Y ou N | Marcador de estrutura de grande porte. Y em 2.844 linhas, N em 4.247. Nunca vazio |
| `contrato` | texto | Número do contrato de concessão |
| `contrato_status` | texto | Situação: PRIMRY, UNIT, PROD, SOP, DSO, OPERNS, RENACV são ativos; EXPIR, RELINQ, TERMIN, REJECT, NO-ISS, CANCEL, CONSOL, NO-EXE são encerrados |
| `contrato_ativo` | S, N ou vazio | Derivado do anterior. Vazio significa **estrutura sem vínculo de contrato no dado**: 296 linhas no cadastro inteiro, das quais **141 estão entre as 1.325 ainda de pé** |
| `instalada` | data | ⚠️ Ver nota de granularidade |
| `removida` | data | Vazio significa **ainda no mar** |
| `vida_anos` | decimal | Instalação até remoção. Vazio quando não removida |
| `lamina_m` | decimal | Lâmina d'água em metros |
| `lat`, `lon` | decimal | Coordenadas, sem validação de projeção |

> ⚠️ **Granularidade de `instalada`.** 4.908 das 7.091 linhas, ou 69,2%, trazem `01-01` como dia e mês. Não é dado sujo: o BSEE passou a registrar data completa por volta de 1990. Os dois conjuntos não coincidem exatamente: são 4.475 instalações anteriores a 1990, e 502 linhas com `01-01` são de 1990 em diante. A incerteza é de ±6 meses. `removida` é exata em 99,8% dos casos. **Publicar idade e duração sempre em anos inteiros.**

### `ndm_us_ferro_ocioso_20260812.csv` — 531 linhas

Subconjunto do anterior: `removida` vazia, `contrato_status` encerrado e `instalada` preenchida. **Chave: `complexo` + `num`**, única nas 531 linhas.

Colunas: `complexo`, `num`, `estrutura`, `operador`, `tipo`, `estrutura_maior`, `contrato`, `contrato_status`, `instalada`, `idade_anos`, `lamina_m`, `lat`, `lon`.

`idade_anos` é de `instalada` até 12/08/2026. As colunas `removida` e `vida_anos` não existem aqui, por definição do recorte.

### `ndm_us_destino_remocao_20260812.csv` — 5.722 linhas

| Coluna | Descrição |
|---|---|
| `COMPLEX_ID_NUM`, `STRUCTURE_NUMBER` | Chave de junção com as bases acima. **5.721 dos 5.722 casam**; o par (625, 1) não existe no cadastro-mãe e tem destino vazio |
| `REMOVAL_DISPOSITION` | To Shore (3.201), vazio (1.830), Rigs-to-Reef (610), Reuse (81) |

Vazio aqui significa **destino não informado**, 32% dos registros.

### `ndm_sec_aro_CY2025Q4I_20260812.csv` — 445 linhas

Provisão de desmobilização de ativo declarada à SEC, quadro trimestral de dezembro de 2025.

| Coluna | Descrição |
|---|---|
| `cik` | Identificador do emissor na SEC. **445 valores distintos** |
| `empresa` | Razão social. **428 valores distintos.** 17 empresas declaram sob dois CIK |
| `aro_usd` | Valor em dólares |
| `tag`, `quadro`, `extraido` | Etiqueta XBRL, período e data de extração |

> ⚠️ **Deduplicar por `empresa`, nunca por `cik`.** E o agrupamento precisa ser **insensível a maiúsculas** e normalizar espaço não separável (U+00A0). Somar por CIK infla o total em 19,6%.
>
> ⚠️ **Cobre todos os setores**, não apenas óleo e gás. Inclui elétricas, mineração e varejo.

---

## Brasil

### `ndm_br_instalacoes_offshore_20260812.csv` — 253 linhas

| Coluna | Descrição |
|---|---|
| `instalacao`, `sigla` | Identificação |
| `classe` | Valores **literais**: `Plataforma Fixa` (89), `Unidade Flutuante` (80), `Unidade Semissubmersível` (30), `Navio Sonda` (30), `Sonda` (13), `Monoboia/Q Boias/Cais-Petróleo` (10), `Módulo de Operação de PIG - MOP` (1) |
| `campo`, `operador_grupo`, `operador_concessao` | Campo e operadores |
| `situacao` | Valores **literais**: `Operando` (93), vazio (41), **`Fora de Operação Permanentemente - Aguarda Descomissionamento`** (35), `Em Descomissionamento` (15), `Descomissionada` (14), `Operando em Extensão de Vida Útil` (11), `Em Construção` (8), `Fora de Operação Temporariamente - Hibernação` (7) |
| `lamina_m` | Lâmina d'água |
| `ano_inicio` | Ano de início de operação |
| `idade_calculada` | 2026 menos `ano_inicio`. **Use esta** |
| `idade_anp` | Campo original da fonte. ⚠️ **Não é consistente com `ano_inicio`.** Mantido só para conferência |
| `lat`, `lon`, `uf` | Coordenadas e unidade federativa. ⚠️ `uf` está **vazia em 233 das 253 linhas** |

> ⚠️ Alguns valores de `situacao` trazem descrição de atividade de poço em vez de estado da instalação, como "Perfuração 7-BUZ-109D-RJS". São 29 linhas assim, e não pertencem às categorias de ciclo de vida.

### `ndm_br_processos_pdi_rdi_20260812.csv` — 190 linhas

| Coluna | Descrição |
|---|---|
| `protocolo` | Número do processo na ANP. Chave |
| `ano` | Ano do protocolo |
| `objeto` | Instalações e campos cobertos pelo processo, separados por barra vertical |
| `tipo_pdi` | Integral (35), Parcial (6), **vazio (149)** |
| `status_pdi` | Aprovado (122), Recebido (27), vazio (24), Encerrado (13), Sobrestado (4) |
| `aprov_pdi` | Data de aprovação do plano |
| `status_rdi`, `aprov_rdi` | Situação e data do relatório que atesta obra concluída |
| `ciclo_anos` | `aprov_pdi` até `aprov_rdi`. Preenchido só nos concluídos |
| `pendente_anos` | `aprov_pdi` até 12/08/2026. Preenchido só nos que não têm RDI |
| `campo`, `bacia`, `operador` | Identificação |
| `classe` | **CAMPO TERRA (88), INSTALACAO MAR (56), CAMPO MAR (38), `CAMPO MAR \| INSTALACAO MAR` (4), BLOCO MAR (3), BLOCO TERRA (1)** |

> ⚠️ **`classe` é o filtro mais importante deste arquivo.** A base mistura terra e mar. Número calculado sem esse recorte não é comparável com número calculado com ele. Ver o quadro de recortes no `LASTRO_PUBLICO.md`.

---

## Europa

### `ndm_uk_instalacoes_superficie_20260812.csv` — 309 linhas

| Coluna | Descrição |
|---|---|
| `nome`, `tipo`, `descricao` | Identificação. `tipo`: PLATFORM (247), BUOY (19), TERMINAL (18), FPSO (15), outros |
| `sistema_duto` | Sistema de dutos associado |
| `flag_plataforma` | Marcador de plataforma na origem |
| `feature_id`, `legacy_id` | Identificadores internos do cadastro britânico |
| `grupo_reporte` | Operador que reporta |
| `status` | ACTIVE (265), NOT IN USE (29), ABANDONED (12), REMOVED (3) |
| `inicio`, `fim`, `razao_fim` | ⚠️ `fim` preenchida em apenas 5 das 309 |
| `instalada`, `atualizada`, `tipo_atualizacao` | Datas de cadastro |
| `lat`, `lon` | Coordenadas |

> ⚠️ **O cadastro britânico é inventário corrente, não registro histórico.** Estrutura removida sai da base em vez de ficar marcada, o que explica só 3 REMOVED contra 5.766 no cadastro americano.

### `ndm_no_instalacoes_20260812.csv` — 914 linhas

| Coluna | Descrição |
|---|---|
| `instalacao`, `tipo`, `operador` | Identificação |
| `fase` | Dez estados: IN SERVICE (698), REMOVED (92), INSTALLATION (60), SHUT DOWN (35), FUTURE (15), ABANDONED IN PLACE (4), PARTLY REMOVED (4), DECOMMISSIONED (3), DISPOSAL COMPLETED (2), FABRICATION (1) |
| `superficie` | Y para instalação de superfície |
| `inicio`, `parada`, `removida` | Datas. ⚠️ **`parada` e `removida` são disjuntas**: nenhuma linha tem as duas |
| `lamina_m`, `vida_projeto` | Lâmina d'água e vida de projeto |

> ⚠️ **ABANDONED IN PLACE não é REMOVED.** São juridicamente opostos: abandono no local é passivo permanente autorizado caso a caso, não obra concluída. Colapsar os dois inverte o sinal de qualquer indicador.

---

## Chaves de junção

| De | Para | Chave |
|---|---|---|
| `ndm_us_estruturas_completo` | `ndm_us_ferro_ocioso` | `complexo` + `num`, única nos dois lados |
| `ndm_us_estruturas_completo` | `ndm_us_destino_remocao` | `complexo` + `num` contra `COMPLEX_ID_NUM` + `STRUCTURE_NUMBER` |
| `ndm_br_instalacoes_offshore` | `ndm_br_processos_pdi_rdi` | `campo` contra `campo`. ⚠️ Junção fraca: nomes de campo e de objeto divergem |
