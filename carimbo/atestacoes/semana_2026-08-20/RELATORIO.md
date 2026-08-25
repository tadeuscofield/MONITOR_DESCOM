# Atestação da semana, lote de 2026-08-20

Snapshots atestados: 9

| snapshot | sha256 da ata | verificação | frescor congelado | TCB | não revogado |
|---|---|---|---|---|---|
| `anp_20260813_135002Z` | `9a0b5e12cb6187da…` | 7 carimbos OK | sim | UpToDate | SIM |
| `anp_20260813_145535Z` | `0557230363ca153b…` | 7 carimbos OK | sim | UpToDate | SIM |
| `anp_20260813_160049Z` | `8df03871c97c4521…` | 7 carimbos OK | sim | UpToDate | SIM |
| `anp_20260814_143002Z` | `dcb8788a134dc7e0…` | 7 carimbos OK | sim | UpToDate | SIM |
| `anp_20260815_165356Z` | `ce6dae2cec42fe11…` | 7 carimbos OK | sim | UpToDate | SIM |
| `anp_20260816_143002Z` | `f237bae3d988e289…` | 7 carimbos OK | sim | UpToDate | SIM |
| `anp_20260817_143002Z` | `42fcb5311b2824c8…` | 7 carimbos OK | sim | UpToDate | SIM |
| `anp_20260818_143003Z` | `901b8ee0dff3b714…` | 7 carimbos OK | sim | UpToDate | SIM |
| `anp_20260819_143003Z` | `dfece0fb5b247325…` | 7 carimbos OK | sim | UpToDate | SIM |

Verificação com o verificador DCAP completo, sem rede: cadeia de
certificados até a raiz do fabricante pinada, assinaturas, medições do
build, commitment e assinatura do emissor, mais revogação e nível de TCB
congelados no instante da emissão.

O frescor foi acrescentado em 20/08/2026 reassinando o mesmo
pré-certificado. **Nenhuma atestação nova foi feita:** o quote e o hash do
documento são byte a byte os mesmos; o que mudou foi a assinatura do
emissor, que agora cobre também o material congelado do fabricante.

Reexecutar:

```
python <verificador>\cli.py --cert semana_2026-08-20\<arquivo>-autocontido.json
```
