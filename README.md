# Decommissioning Monitor

Quanto tempo uma estrutura offshore espera entre o fim da vida útil e o fim da
estrutura. O monitor mede a distância entre "descomissionamento aprovado" e
"descomissionamento concluído" usando só registro público, no Brasil, no Golfo
do México americano, no Reino Unido e na Noruega.

Página: **[decommissioningmonitor.com](https://decommissioningmonitor.com)**
Base e método: **[doi.org/10.5281/zenodo.21919402](https://doi.org/10.5281/zenodo.21919402)**

Por *Veridis Engenharia e Tecnologia*.

---

## A regra que rege este repositório

**Se um número deixa de reproduzir, a página não compila.**

`site/gerar_site.py` não formata dado pronto: ele abre os CSVs do depósito,
**recalcula cada número publicado**, compara com o valor verificado e só então
escreve o HTML. Divergiu, o build sai com erro e a página anterior fica no ar.
Não há caminho para publicar número que não bate.

O mesmo gerador ainda executa o verificador do depósito como subprocesso e
exige zero falhas, conta os snapshots em disco em vez de confiar em literal, e
recusa o build se sobrar placeholder ou se aparecer travessão.

## Rodar

```bash
python site/gerar_site.py      # recalcula tudo e gera site/index.html
python dados/verificar.py      # 77 checagens sobre as bases depositadas
python conferir_carimbo.py     # dias de captura, elos da cadeia, lotes atestados
python gerar_planilha.py       # diário em Excel, regerado do registro
python diff_capturas.py --todas  # o que mudou, instalação por instalação
```

Só biblioteca padrão do Python, fora `openpyxl` para a planilha. Sem build
step, sem framework, sem CDN: a página é um arquivo autocontido que abre com
dois cliques e não faz uma requisição externa.

## O que tem aqui

| Pasta | O que é |
|---|---|
| `site/` | gerador, template e a página. `edicao.py` lê o snapshot atestado e produz a edição semanal |
| `dados/` | o depósito publicado com DOI: 8 CSVs, 15.455 linhas, mais o dicionário, as fontes, as licenças e o verificador |
| `carimbo/` | o serviço de snapshot: captura diária, encadeamento por hash, atestação em hardware e verificação |
| `carimbo/atestacoes/` | os certificados de cada lote, com o relatório da verificação |

## O serviço de carimbo

Os painéis de origem mudam sem histórico público de versões. Por isso o monitor
captura o painel da ANP todo dia às 11h30, fixa cada resposta do servidor por
SHA-256 numa ata datada, e cada ata nova registra também o hash da anterior,
encadeando a série. Uma vez por semana as atas vão para hardware seguro (TEE),
que devolve um certificado.

O certificado prova três coisas: que a ata é exatamente aquela, que passou por
hardware genuíno rodando um programa cujo código é medido, e que conferir isso
não depende da minha palavra. A verificação roda **sem internet**, contra a raiz
de confiança do fabricante do processador.

Ele **não** prova de onde o conteúdo veio: a origem fica declarada na própria
ata, com a consulta escrita ali para qualquer pessoa refazer. E **não** carimba
data, o que é deliberado.

## O que este repositório não traz

- **As respostas brutas do painel**, que a ata referencia por hash. Elas crescem
  cerca de 0,8 MB por dia, e histórico de git é o lugar errado para arquivo que
  só cresce. Vão para uma versão do depósito, que é versionado e citável.
- **A análise que liga cada operador à matriz que declara provisão.** Ela nomeia
  empresa sob rótulo adverso sem lastro documental individual para cada uma, e
  por isso ficou fora do conjunto público. Quem quiser conferir esse recorte
  pede, e recebe com o critério de cada vínculo.
- Estudo interno, planejamento e material editorial.

## Licença

Código sob **MIT**. Bases derivadas e textos sob **CC BY 4.0**, com a atribuição
pedida no depósito. As fontes originais mantêm os próprios termos, declarados em
`dados/LICENCAS.md`, e duas delas exigem atribuição nominal que é reproduzida na
página e no depósito.

## Como citar

> Cordeiro, T. S. (2026). *Decommissioning Monitor: offshore decommissioning
> datasets from Brazil, the US, the UK and Norway (2026-08-12 snapshot)*.
> Zenodo. https://doi.org/10.5281/zenodo.21919402
