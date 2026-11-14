# ConstruExpert · Termômetro

Termômetro ConstruExpert, metodologia v1.1 (a mesma da edição mensal do dia 15): nota de 0 a 100, cinco pilares com peso, cada indicador comparado ao mínimo e ao máximo dos últimos 60 meses. Faixas: 0–39 vermelho, 40–59 amarelo, 60–100 verde.

- `termometro/`: a página. Ela lê `termometro/dados.json`.
- `scripts/coleta_ce.py`: busca tudo automaticamente: Banco Central (Selic, INCC-M, financiamento imobiliário), Ipeadata (ICST da FGV) e IBGE SIDRA (SINAPI RS e SC, varejo de material de construção, produção de insumos da construção, ocupados na construção pela PNAD) e calcula a nota.
- v1.1 (14/11/2026): CUB, SBPE, SNIC e Caged, sem consulta automática aberta, foram trocados por SINAPI, BC 20704, PIM-PF e PNAD.
- `manual.json`: reservado para séries lançadas à mão (hoje vazio).
- `.github/workflows/atualizar.yml`: roda todo dia às 7h23 (Brasília). Para atualizar na hora: aba **Actions** → *Atualizar termômetro* → **Run workflow**.

É uma leitura analítica do ciclo e não uma recomendação de investimento.
