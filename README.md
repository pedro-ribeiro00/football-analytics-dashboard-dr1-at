# ⚽ Futebol em Dados

Assessment DR1 - Pedro Henrique Nunes Ribeiro.

Projeto simples de Sports Analytics desenvolvido em Python e Streamlit. A pergunta escolhida foi:

**Como passes e finalizações ajudam a entender o desempenho em uma partida de futebol?**

Os dados são obtidos da base aberta da StatsBomb com a biblioteca StatsBombPy.

## Funcionalidades

- seleção de competição, temporada, partida, equipe e jogador;
- métricas de gols, passes, chutes, xG e conversão;
- mapa de passes, mapa de chutes e mapa de calor com mplsoccer;
- gráficos com Matplotlib e Seaborn;
- comparação simples entre dois jogadores;
- filtros por minuto, período e tipo de evento;
- tabela de eventos e download em CSV;
- uso de cache, Session State, spinner e barra de progresso.

## Como executar

1. python -m venv .venv
2. ative o ambiente virtual;
3. pip install -r requirements.txt
4. streamlit run app.py

No Windows, o ambiente pode ser ativado com .venv\Scripts\Activate.ps1.

## Links

- GitHub: https://github.com/pedro-ribeiro00/football-analytics-dashboard-dr1-at
- Streamlit: https://football-analytics-dashboard-dr1-at-4aghbnevsnk9fraw96gafh.streamlit.app/

## Bibliotecas utilizadas

- Streamlit
- StatsBombPy
- mplsoccer
- Pandas
- Matplotlib
- Seaborn

Fonte dos dados: StatsBomb Open Data.
