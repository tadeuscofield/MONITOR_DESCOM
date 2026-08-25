# Licenças e atribuição

**Autor da compilação:** Tadeu Santana Cordeiro
**Data:** 12/08/2026

Duas das fontes usadas aqui **exigem atribuição nominal como condição de uso**. Este arquivo cumpre essa obrigação e declara os termos de cada base.

---

## 1. Atribuições obrigatórias

### Noruega, Sokkeldirektoratet

> Contains data under the Norwegian Licence for Open Government Data (NLOD), distributed by Sokkeldirektoratet.
>
> Contém dados sob a Licença Norueguesa para Dados Abertos de Governo (NLOD), distribuídos pelo Sokkeldirektoratet.

Licença: `https://data.norge.no/nlod/en/2.0`
Base afetada: `ndm_no_instalacoes_20260812.csv`

A NLOD permite uso comercial, cópia, redistribuição e obra derivada, **desde que a fonte seja creditada nominalmente** e que não se sugira endosso do licenciante.

### Reino Unido, North Sea Transition Authority

> Contains information provided by the North Sea Transition Authority, licensed under the Open Government Licence v3.0.
>
> Contém informação fornecida pela North Sea Transition Authority, licenciada sob a Open Government Licence v3.0.

Licença: `https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/`
Base afetada: `ndm_uk_instalacoes_superficie_20260812.csv`

A OGL v3.0 permite uso comercial e obra derivada, **desde que se declare a atribuição e se dê o link para a licença**, e que não se sugira endosso oficial.

---

## 2. Fontes em domínio público

### Estados Unidos, BSEE e SEC

Obra de agência do governo federal dos Estados Unidos. Sob o título 17 do código americano, seção 105, obra do governo federal não é objeto de direito autoral nos Estados Unidos.

Bases afetadas: `ndm_us_estruturas_completo_20260812.csv`, `ndm_us_ferro_ocioso_20260812.csv`, `ndm_us_destino_remocao_20260812.csv`, `ndm_sec_aro_CY2025Q4I_20260812.csv`

Crédito, ainda que não exigido: Bureau of Safety and Environmental Enforcement e Securities and Exchange Commission.

---

## 3. Dado público brasileiro

### Brasil, ANP

Dado público de agência reguladora federal brasileira, com publicidade determinada pelo artigo 14 da Resolução ANP nº 817/2020 e amparada pela Lei nº 12.527/2011, de Acesso à Informação.

Bases afetadas: `ndm_br_instalacoes_offshore_20260812.csv`, `ndm_br_processos_pdi_rdi_20260812.csv`

Crédito: Agência Nacional do Petróleo, Gás Natural e Biocombustíveis, Painel Dinâmico de Descomissionamento de Instalações de Exploração e Produção.

---

## 4. Licença das bases derivadas

Os arquivos `ndm_*.csv` desta pasta são obra derivada, produzida por processamento próprio a partir das fontes acima.

**Termos de uso concedidos:** Creative Commons Atribuição 4.0 Internacional (CC BY 4.0), `https://creativecommons.org/licenses/by/4.0/deed.pt-br`

Atribuição pedida:

> Tadeu Santana Cordeiro, NEPTUNO Decommissioning Monitor, extração de 12/08/2026.

**Esta licença cobre apenas o trabalho de compilação e transformação.** Ela não pode ampliar nem restringir os direitos das fontes originais, que seguem seus próprios termos, declarados nas seções 1 a 3. Quem redistribuir estas bases precisa reproduzir também as atribuições obrigatórias da seção 1.

---

## 5. Fontes deliberadamente NÃO usadas, por licença

Foram avaliadas e descartadas por não permitirem uso comercial ou por não terem licença declarada:

| Fonte | Motivo |
|---|---|
| Global Fishing Watch, infraestrutura offshore | Licença **não comercial**, e a organização declara não ter termos comerciais disponíveis |
| NGO Shipbreaking Platform, lista anual de navios desmantelados | **Sem licença declarada.** Por padrão, todos os direitos reservados |
| OSPAR, inventário de instalações offshore | **Sem licença declarada** |
| Global Tailings Portal | **Sem licença declarada**, e o dado sai por solicitação |
| EMODnet Human Activities | Licença **a verificar**. Excluído até haver confirmação, apesar de trazer peso de estrutura, que é atributo desejável |
| NLOG, instalações dos Países Baixos | **Sem texto de licença publicado no serviço.** Retirado do depósito pela mesma regra das demais. A consulta WFS é pública e está documentada em `FONTES.md`, então a afirmação sobre os Países Baixos continua conferível na fonte |

**Regra aplicada:** a licença efetiva de um registro consolidado é a interseção mais restritiva das licenças dos campos que o compõem. Um único campo de fonte não comercial tornaria todo o conjunto não comercializável. Por isso nenhuma das fontes acima entrou.

---

## 6. Análise retirada deste conjunto

A classificação que ligava operador registrado no regulador americano à matriz que declara provisão à SEC **não faz parte deste conjunto público**. Ela nomeava empresas sob rótulo adverso sem fundamento individual para cada uma, e por isso foi mantida fora, como análise assinada e não como base de dados permanente.

Nenhum número publicado a partir desta pasta depende dela.

