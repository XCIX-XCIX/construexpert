# ConstruExpert · Termômetro

Termômetro ConstruExpert, metodologia v1.0 (a mesma da edição mensal do dia 15): nota de 0 a 100, cinco pilares com peso, cada indicador comparado ao mínimo e ao máximo dos últimos 60 meses. Faixas: 0–39 vermelho, 40–59 amarelo, 60–100 verde.

- `termometro/`: a página. Ela lê `termometro/dados.json`.
- `scripts/coleta_ce.py`: busca Banco Central (Selic, INCC-M), Ipeadata (ICST da FGV), IBGE SIDRA (varejo de material de construção e SINAPI) e calcula a nota.
- `manual.json`: séries mensais sem API aberta (CUB RS e SC, SBPE, cimento, Caged). Precisa de 12 meses de histórico para o indicador entrar na conta. Ao salvar, a página recalcula sozinha.
- `.github/workflows/atualizar.yml`: roda todo dia às 7h23 (Brasília). Para atualizar na hora: aba **Actions** → *Atualizar termômetro* → **Run workflow**.

É uma leitura analítica do ciclo e não uma recomendação de investimento.
