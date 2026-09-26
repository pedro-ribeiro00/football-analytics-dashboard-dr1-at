# Registro de validação

Data: 26/09/2026. Ambiente: Python 3.12.14, macOS ARM64, ambiente virtual isolado. Dependências diretas fixadas em requirements.txt.

## Verificações concluídas

- Instalação de todas as bibliotecas e `pip check`: sem dependências quebradas.
- `python -m pytest -q`: quatro testes aprovados, cobrindo métricas, pênaltis da disputa, denominadores vazios, filtros, coordenadas opcionais e CSV UTF-8 com BOM.
- Consulta real StatsBombPy: competições, temporadas, 64 partidas da Copa 2022, eventos da final e escalações.
- Final 3869685: 4.407 eventos brutos, 4.386 nos períodos 1 a 4; Argentina 20 chutes e 2,758306 xG, França 10 chutes e 2,272618 xG.
- Streamlit AppTest: inicialização sem exceções/erros, escolha de jogador e equipe, modo interativo de passes, checkbox de passes completos, aplicação de filtro vazio e troca de partida.
- Streamlit AppTest adicional: comparação Lionel Messi × Kylian Mbappé, temporada 2018 e outra competição (futebol feminino), sem exceções/erros.
- Servidor Streamlit local iniciado; endpoint `/_stcore/health` respondeu `ok`.
- Inspeção da interface no navegador e captura real em assets/dashboard.png.
- Figuras de passes, chutes, densidade e relação passes × xG renderizadas.
- PDF final renderizado e revisado visualmente; texto português preservado.

## Escopo da validação

Não foi realizada varredura de todas as partidas do catálogo nem teste de carga. A disponibilidade de dados depende do provedor. As versões e o comportamento foram testados no ambiente acima; a publicação no Streamlit Community Cloud requer validação após o deploy.

O Community Cloud apresentou tela de autenticação e aceite de termos. A aplicação **não foi publicada na nuvem** nesta entrega. README e relatório incluem um marcador explícito para a URL final e o roteiro de publicação. GitHub é tratado separadamente do deploy do aplicativo.
