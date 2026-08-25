# Lastro das afirmações publicadas

**Autor:** Tadeu Santana Cordeiro
**Extração de todas as bases:** 12/08/2026
**Objetivo:** permitir que qualquer pessoa refaça cada número publicado a partir dos arquivos desta pasta, sem depender de mim.

---

## Como ler este documento

Cada linha traz a afirmação, o arquivo que a sustenta, e a receita exata de recálculo. Onde a receita depende de uma convenção de software, a convenção está escrita.

---

## 1. Convenções que a receita exige

Sem estas, os números não reproduzem.

| Convenção | Por quê |
|---|---|
| **Agrupamento de texto é insensível a maiúsculas e minúsculas** | O cadastro da SEC traz o mesmo emissor com grafias diferentes. Agrupamento sensível a caixa devolve 429 empresas em vez de 428 |
| Normalizar espaço não separável antes de comparar nome | O cadastro da SEC usa U+00A0 em alguns nomes. **A base publicada já foi normalizada**, então a convenção é inócua sobre este arquivo e fica registrada para quem reextrair da fonte |
| **Mediana de amostra par é a média dos dois centrais** | Com 22 valores, a mediana é a média do 11º e do 12º |
| **Idade e duração em anos, calculadas de data para data, divididas por 365,25** | Ver a nota de granularidade na seção 4 |
| **Data de referência para toda idade: 12/08/2026** | Data da extração |

---

## 2. Estados Unidos

| Afirmação | Base | Receita |
|---|---|---|
| 7.091 estruturas no cadastro | `ndm_us_estruturas_completo_20260812.csv` | contar linhas |
| 5.766 removidas, 1.325 de pé | idem | `removida` preenchida contra vazia |
| Vida mediana até a remoção: 19 anos | idem | mediana de `vida_anos` |
| Ritmo 188/ano na década de 2010 e 73/ano na de 2020 | idem | agrupar `removida` por década; anualizar dividindo por 10 e por 6,5 |
| 531 estruturas de pé em contrato encerrado | `ndm_us_ferro_ocioso_20260812.csv` | contar linhas. Equivale a filtrar a base completa por `removida` vazia e `contrato_status` em TERMIN, RELINQ ou EXPIR |
| Idade mediana 47 anos, máxima 78 | idem | mediana e máximo de `idade_anos`, **arredondados ao inteiro mais próximo**. Brutos: 46,6 e 77,6 |
| Mais antiga instalada em 1949 | idem | coluna `instalada` nas linhas de idade máxima |
| 272 estruturas maiores | idem | `estrutura_maior = Y` |
| 5.722 destinos: 3.201 para terra, 610 recife, 81 reúso, 1.830 em branco | `ndm_us_destino_remocao_20260812.csv` | agrupar `REMOVAL_DISPOSITION` |
| 428 empresas com provisão declarada, somando US$ 208,1 bilhões | `ndm_sec_aro_CY2025Q4I_20260812.csv` | agrupar por `empresa` com as convenções da seção 1; **tomar o MAIOR valor de cada grupo** e somar. Ver a nota abaixo |
| O total sem deduplicar ficaria 19,6% acima | idem | soma bruta por `cik` menos soma deduplicada, dividido pela soma deduplicada |

> ⚠️ **Seis grupos têm valores divergentes entre os dois CIK.** A regra adotada é tomar o maior, que corresponde à entidade consolidada. Os seis, para conferência:
>
> | Empresa | Valores nos dois CIK |
> |---|---|
> | Duke Energy Corporation | 9.625.000.000 e 9.046.000.000 |
> | The Southern Company | 9.601.000.000 e 8.939.000.000 |
> | Sempra | 3.948.000.000 e 3.743.000.000 |
> | **Northern States Power Co** | **3.215.000.000 e 24.000.000** |
> | Evergy, Inc. | 1.342.300.000 e 1.308.100.000 |
> | Western Midstream Partners, LP | 437.800.000 e 427.858.000 |
>
> Tomando o menor em cada um, o total seria **US$ 203,5 bilhões**. A diferença entre as duas escolhas é de **US$ 4,68 bilhões**, e por isso a regra precisa estar escrita.

---

## 3. Brasil

| Afirmação | Base | Receita |
|---|---|---|
| 253 instalações offshore | `ndm_br_instalacoes_offshore_20260812.csv` | contar linhas |
| 35 em "Fora de Operação Permanentemente - Aguarda Descomissionamento" | idem | filtrar `situacao` |
| Idade mediana 43 anos | idem | mediana de `idade_calculada` nas 35 |
| 34 plataformas fixas entre as 35 | idem | agrupar `classe` |
| As 35 são da Petrobras | idem | agrupar `operador_grupo` |
| Guaricema 1: 1970, 56 anos, 28,7 m | idem | linha `PLATAFORMA DE GUARICEMA 1` |
| PDI de Guaricema aprovado em 07/11/2024, sem RDI | `ndm_br_processos_pdi_rdi_20260812.csv` | protocolo `48610.208347/2024-22` |
| 10 processos integrais no mar com plano aprovado e sem relatório de conclusão (5 de instalação, 5 de campo) | idem | `tipo_pdi = Integral` e `classe` contendo MAR e `pendente_anos` preenchido |
| Mediana de 7,1 anos entre esses 10 | idem | mediana de `pendente_anos` no mesmo recorte |
| Mais antigo: Mexilhão, Bacia de Santos, PDI aprovado em 30/05/2016 | idem | máximo de `pendente_anos` no mesmo recorte |

> **Atenção ao recorte.** A base mistura `CAMPO TERRA`, `CAMPO MAR`, `INSTALACAO MAR`, `BLOCO MAR` e `BLOCO TERRA`. Números de recortes diferentes não são comparáveis. Para referência, os três recortes principais:
>
> | Recorte | Concluídos | Pendentes |
> |---|---|---|
> | Todos os tipos e classes | n=19, mediana 3,4 anos | n=103, mediana 3,8 |
> | Integral, todas as classes | n=12, mediana 3,0 | n=22, mediana 6,85 |
> | **Integral, só classe MAR** | n=3, mediana 0,4 | **n=10, mediana 7,1** |
>
> **Só o terceiro recorte é usado em publicação.** O primeiro e o segundo incluem campo terrestre. E os três ciclos concluídos offshore são amostra pequena demais para servir de linha de base; por isso nenhuma publicação afirma tempo típico de execução no Brasil.

---

## 4. Reino Unido e Noruega

| Afirmação | Base | Receita |
|---|---|---|
| Reino Unido: 309 instalações de superfície | `ndm_uk_instalacoes_superficie_20260812.csv` | contar linhas |
| 265 ativas, 29 fora de uso, 12 abandonadas, 3 removidas | idem | agrupar `status` |
| 41 fora de operação e ainda na água | idem | `status` em NOT IN USE ou ABANDONED |
| Operadores do backlog, **11 grupos somando 41**: REPSOL RESOURCES UK 9, TAQA EUROPA B.V. 6, PERENCO OIL & GAS 5, HARBOUR ENERGY PLC 4, SHELL PLC 4, TOTALENERGIES UPSTREAM UK LIMITED 4, ENI UK LIMITED 3, CENTRICA STORAGE HOLDINGS 2, SPIRIT ENERGY 2, FAIRFIELD ENERGY LIMITED 1, WINTERSHALL NOORDZEE 1 | idem | agrupar `grupo_reporte` no recorte das 41. **Não incluir as 3 removidas** |
| Noruega: 914 instalações fixas, 10 fases de ciclo de vida | `ndm_no_instalacoes_20260812.csv` | contar linhas; valores distintos de `fase` |

---

## 5. Notas de granularidade que acompanham todo número de idade

1. **Estados Unidos.** O BSEE registrou apenas o ano de instalação para estruturas anteriores a 1990, o que corresponde a 69,2% do cadastro (4.908 de 7.091). Nessas linhas o dia e o mês vêm como 1º de janeiro. A incerteza é de ±6 meses por registro. Datas de remoção são exatas em 99,8% dos casos. **Por isso idade e duração são publicadas em anos inteiros.**
2. **Restringir ao subconjunto de datas exatas seria erro.** Só instalações posteriores a 1990 têm data completa, e para estarem no conjunto de removidas precisam ter vida curta. O filtro seleciona vida curta por construção: a mediana cairia de 19 para 10,5 anos, o que subestima grosseiramente.
3. **Brasil.** A coluna `idade_anp` não é consistente com `ano_inicio`. Toda idade brasileira publicada foi calculada de `ano_inicio`, e a coluna original fica no arquivo para conferência.
4. **A coorte de referência dos Estados Unidos é do Golfo do México**, água rasa, jaqueta, mercado de barcaças maduro. Aplicá-la a outra bacia é premissa, não medida.
5. **Removidas primeiro tendem a ser as mais fáceis**, o que empurra a mediana para baixo. O índice é conservador, não inflado.

---

## 6. Limitações declaradas

1. **Idade não é atraso.** Nos Estados Unidos o corte é contrato encerrado, e ainda assim pode haver prorrogação, acordo ou litígio que o dado bruto não mostra. A formulação correta é "em contrato encerrado", nunca "em descumprimento".
2. **141 estruturas americanas de pé não têm vínculo de contrato no dado**, 10,6% do estoque, e ficam fora da classificação.
3. **32% dos destinos de remoção estão em branco.**
4. **Não localizar provisão no extrato da SEC não é ausência de provisão.** Empresa de capital fechado não é obrigada a publicar; quem reporta sob outro regime contábil não aparece nesse extrato; exercício fiscal deslocado pode não cair no recorte trimestral.
5. **A provisão declarada é consolidada e global.** Não pode ser alocada por estrutura.
6. **O arquivo da SEC cobre todos os setores**, não apenas óleo e gás offshore. Inclui elétricas, mineração e varejo. O total de US$ 208,1 bilhões é de toda a amostra, não do setor offshore.
7. **A coluna de UF da base brasileira está vazia em 233 das 253 linhas.** Localização por estado, quando citada, vem da bacia sedimentar ou da coordenada, e isso é inferência.
