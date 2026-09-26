"""Dashboard simples de Sports Analytics para o Assessment DR1."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from mplsoccer import Pitch
from statsbombpy import sb


st.set_page_config(page_title="Futebol em Dados", page_icon="⚽", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background-color: #f3f7f5;
        padding: 10px;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Funções de carregamento
# -----------------------------
@st.cache_data
def carregar_competicoes():
    return sb.competitions()


@st.cache_data
def carregar_partidas(competition_id, season_id):
    return sb.matches(competition_id=competition_id, season_id=season_id)


@st.cache_data
def carregar_eventos(match_id):
    eventos = sb.events(match_id=match_id).copy()

    # A disputa de pênaltis aparece como período 5 na base.
    # Para a análise da partida, usamos os períodos 1 a 4.
    eventos = eventos[eventos["period"] <= 4].copy()

    def pegar_coordenada(valor, posicao):
        if isinstance(valor, (list, tuple)) and len(valor) > posicao:
            return valor[posicao]
        return None

    eventos["x"] = eventos["location"].apply(lambda x: pegar_coordenada(x, 0))
    eventos["y"] = eventos["location"].apply(lambda x: pegar_coordenada(x, 1))

    if "pass_end_location" in eventos.columns:
        eventos["end_x"] = eventos["pass_end_location"].apply(lambda x: pegar_coordenada(x, 0))
        eventos["end_y"] = eventos["pass_end_location"].apply(lambda x: pegar_coordenada(x, 1))
    else:
        eventos["end_x"] = None
        eventos["end_y"] = None

    if "pass_outcome" not in eventos.columns:
        eventos["pass_outcome"] = None
    if "shot_outcome" not in eventos.columns:
        eventos["shot_outcome"] = None
    if "shot_statsbomb_xg" not in eventos.columns:
        eventos["shot_statsbomb_xg"] = 0.0

    eventos["shot_statsbomb_xg"] = pd.to_numeric(
        eventos["shot_statsbomb_xg"], errors="coerce"
    ).fillna(0)

    return eventos


# -----------------------------
# Funções de cálculo
# -----------------------------
def calcular_metricas(eventos):
    passes = eventos[eventos["type"] == "Pass"]
    chutes = eventos[eventos["type"] == "Shot"]

    passes_completos = passes["pass_outcome"].isna().sum()
    gols = (chutes["shot_outcome"] == "Goal").sum()

    precisao = (passes_completos / len(passes) * 100) if len(passes) else 0
    conversao = (gols / len(chutes) * 100) if len(chutes) else 0

    return {
        "passes": len(passes),
        "passes_completos": int(passes_completos),
        "precisao": precisao,
        "chutes": len(chutes),
        "gols": int(gols),
        "xg": float(chutes["shot_statsbomb_xg"].sum()),
        "conversao": conversao,
    }


# -----------------------------
# Funções de visualização
# -----------------------------
def mapa_passes(eventos, somente_completos=False):
    passes = eventos[eventos["type"] == "Pass"].dropna(
        subset=["x", "y", "end_x", "end_y"]
    )

    if somente_completos:
        passes = passes[passes["pass_outcome"].isna()]

    pitch = Pitch(pitch_type="statsbomb", line_color="gray")
    fig, ax = pitch.draw(figsize=(10, 6))

    completos = passes[passes["pass_outcome"].isna()]
    incompletos = passes[passes["pass_outcome"].notna()]

    if not completos.empty:
        pitch.arrows(
            completos["x"], completos["y"], completos["end_x"], completos["end_y"],
            ax=ax, color="seagreen", width=1.5, alpha=0.7, label="Completo"
        )

    if not incompletos.empty:
        pitch.arrows(
            incompletos["x"], incompletos["y"], incompletos["end_x"], incompletos["end_y"],
            ax=ax, color="tomato", width=1.5, alpha=0.6, label="Incompleto"
        )

    ax.set_title("Mapa de passes")
    if not passes.empty:
        ax.legend(loc="upper left")
    return fig


def mapa_chutes(eventos):
    chutes = eventos[eventos["type"] == "Shot"].dropna(subset=["x", "y"])

    pitch = Pitch(pitch_type="statsbomb", line_color="gray")
    fig, ax = pitch.draw(figsize=(10, 6))

    gols = chutes[chutes["shot_outcome"] == "Goal"]
    outros = chutes[chutes["shot_outcome"] != "Goal"]

    if not outros.empty:
        pitch.scatter(
            outros["x"], outros["y"],
            s=40 + outros["shot_statsbomb_xg"] * 400,
            color="tomato", alpha=0.7, ax=ax, label="Outros chutes"
        )

    if not gols.empty:
        pitch.scatter(
            gols["x"], gols["y"],
            s=60 + gols["shot_statsbomb_xg"] * 400,
            color="seagreen", edgecolors="black", ax=ax, label="Gol"
        )

    ax.set_title("Mapa de chutes - tamanho do ponto representa o xG")
    if not chutes.empty:
        ax.legend(loc="upper left")
    return fig


def mapa_calor(eventos):
    localizados = eventos.dropna(subset=["x", "y"])
    pitch = Pitch(pitch_type="statsbomb", line_color="gray")
    fig, ax = pitch.draw(figsize=(10, 6))

    if not localizados.empty:
        estatistica = pitch.bin_statistic(
            localizados["x"], localizados["y"], statistic="count", bins=(12, 8)
        )
        pitch.heatmap(estatistica, ax=ax, cmap="Blues", edgecolors="white")

    ax.set_title("Mapa de calor dos eventos")
    return fig


def grafico_eventos_por_tempo(eventos):
    dados = eventos.copy()
    dados["faixa"] = (dados["minute"] // 15) * 15
    contagem = dados.groupby("faixa").size()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(contagem.index, contagem.values, marker="o")
    ax.set_title("Quantidade de eventos por intervalo de 15 minutos")
    ax.set_xlabel("Minuto")
    ax.set_ylabel("Eventos")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def grafico_comparacao_jogadores(eventos, jogador_a, jogador_b, metrica):
    linhas = []
    for jogador in [jogador_a, jogador_b]:
        dados_jogador = eventos[eventos["player"] == jogador]
        metricas = calcular_metricas(dados_jogador)
        linhas.append({"Jogador": jogador, "Valor": metricas[metrica]})

    tabela = pd.DataFrame(linhas)
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.barplot(data=tabela, x="Jogador", y="Valor", ax=ax)
    ax.set_title(f"Comparação de jogadores - {metrica.replace('_', ' ').title()}")
    fig.tight_layout()
    return fig, tabela


# -----------------------------
# Interface
# -----------------------------
st.title("⚽ Futebol em Dados")
st.write("Dashboard simples de análise de uma partida usando dados abertos da StatsBomb.")

if "ultimo_jogador" not in st.session_state:
    st.session_state["ultimo_jogador"] = "Todos"

with st.sidebar:
    st.header("Seleção")
    barra = st.progress(0)

    with st.spinner("Carregando competições..."):
        competicoes = carregar_competicoes()
    barra.progress(30)

    lista_competicoes = competicoes.drop_duplicates("competition_id")
    ids_competicoes = lista_competicoes["competition_id"].tolist()
    indice_padrao = ids_competicoes.index(43) if 43 in ids_competicoes else 0

    competition_id = st.selectbox(
        "Competição",
        ids_competicoes,
        index=indice_padrao,
        format_func=lambda x: lista_competicoes.loc[
            lista_competicoes["competition_id"] == x, "competition_name"
        ].iloc[0],
    )

    temporadas = competicoes[competicoes["competition_id"] == competition_id]
    season_ids = temporadas["season_id"].tolist()
    indice_temporada = season_ids.index(106) if 106 in season_ids else 0

    season_id = st.selectbox(
        "Temporada",
        season_ids,
        index=indice_temporada,
        key=f"temporada_{competition_id}",
        format_func=lambda x: temporadas.loc[
            temporadas["season_id"] == x, "season_name"
        ].iloc[0],
    )

    with st.spinner("Carregando partidas..."):
        partidas = carregar_partidas(competition_id, season_id)
    barra.progress(65)

    match_ids = partidas["match_id"].tolist()
    indice_partida = match_ids.index(3869685) if 3869685 in match_ids else 0

    match_id = st.selectbox(
        "Partida",
        match_ids,
        index=indice_partida,
        key=f"partida_{competition_id}_{season_id}",
        format_func=lambda x: (
            f"{partidas.loc[partidas['match_id'] == x, 'home_team'].iloc[0]} x "
            f"{partidas.loc[partidas['match_id'] == x, 'away_team'].iloc[0]}"
        ),
    )

    with st.spinner("Carregando eventos..."):
        eventos = carregar_eventos(match_id)
    barra.progress(100)

    jogadores = sorted(eventos["player"].dropna().unique().tolist())
    jogador = st.selectbox("Jogador", ["Todos"] + jogadores, key=f"jogador_{match_id}")
    st.session_state["ultimo_jogador"] = jogador

    equipes = sorted(eventos["team"].dropna().unique().tolist())
    equipe = st.selectbox("Equipe", ["Todas"] + equipes, key=f"equipe_{match_id}")

    st.caption("Fonte: StatsBomb Open Data")

partida = partidas[partidas["match_id"] == match_id].iloc[0]
competicao_nome = temporadas.loc[
    temporadas["season_id"] == season_id, "competition_name"
].iloc[0]
temporada_nome = temporadas.loc[
    temporadas["season_id"] == season_id, "season_name"
].iloc[0]

with st.container(border=True):
    st.subheader(
        f"{partida['home_team']} {int(partida['home_score'])} x "
        f"{int(partida['away_score'])} {partida['away_team']}"
    )
    st.caption(f"{competicao_nome} - {temporada_nome} - {partida['match_date']}")

max_minuto = int(eventos["minute"].max()) if not eventos.empty else 90

with st.form("filtros"):
    st.subheader("Filtros")
    c1, c2 = st.columns(2)
    intervalo = c1.slider("Intervalo de minutos", 0, max_minuto, (0, max_minuto))
    quantidade_linhas = c2.number_input("Quantidade de eventos na tabela", 10, 500, 100, 10)

    tipos_disponiveis = sorted(eventos["type"].dropna().unique().tolist())
    tipos = st.multiselect("Tipos de evento", tipos_disponiveis, default=tipos_disponiveis)
    periodo = st.radio("Período", ["Partida toda", "1º tempo", "2º tempo"], horizontal=True)
    somente_passes_completos = st.checkbox("Mostrar apenas passes completos no mapa de passes")
    busca_jogador = st.text_input("Buscar jogador na tabela", placeholder="Ex.: Messi")
    st.form_submit_button("Aplicar filtros")

filtrados = eventos[
    eventos["minute"].between(intervalo[0], intervalo[1])
    & eventos["type"].isin(tipos)
].copy()

if periodo == "1º tempo":
    filtrados = filtrados[filtrados["period"] == 1]
elif periodo == "2º tempo":
    filtrados = filtrados[filtrados["period"] == 2]

if equipe != "Todas":
    filtrados = filtrados[filtrados["team"] == equipe]

if jogador != "Todos":
    filtrados = filtrados[filtrados["player"] == jogador]

aba_resumo, aba_mapas, aba_jogador, aba_dados = st.tabs(
    ["Resumo", "Mapas", "Jogador", "Eventos / CSV"]
)

with aba_resumo:
    st.subheader("Resumo da partida")

    dados_partida = eventos.copy()
    metricas = calcular_metricas(dados_partida)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gols na partida", int(partida["home_score"] + partida["away_score"]))
    c2.metric("Passes", metricas["passes"])
    c3.metric("Chutes", metricas["chutes"])
    c4.metric("xG total", f"{metricas['xg']:.2f}")

    st.pyplot(grafico_eventos_por_tempo(dados_partida))

    chutes_equipes = (
        dados_partida[dados_partida["type"] == "Shot"]
        .groupby("team")
        .size()
        .reset_index(name="Chutes")
    )
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.barplot(data=chutes_equipes, x="team", y="Chutes", ax=ax)
    ax.set_title("Chutes por equipe")
    ax.set_xlabel("Equipe")
    fig.tight_layout()
    st.pyplot(fig)

with aba_mapas:
    st.subheader("Mapas da partida")
    st.caption("Os mapas mudam de acordo com a equipe, jogador e filtros selecionados.")

    tipo_mapa = st.radio(
        "Escolha o mapa",
        ["Passes", "Chutes", "Mapa de calor"],
        horizontal=True,
    )

    if tipo_mapa == "Passes":
        st.pyplot(mapa_passes(filtrados, somente_passes_completos))
    elif tipo_mapa == "Chutes":
        st.pyplot(mapa_chutes(filtrados))
    else:
        st.pyplot(mapa_calor(filtrados))

with aba_jogador:
    st.subheader("Análise de jogador")

    if jogador == "Todos":
        st.info("Selecione um jogador na barra lateral para ver as métricas individuais.")
    else:
        dados_jogador = eventos[eventos["player"] == jogador]
        m = calcular_metricas(dados_jogador)

        c1, c2, c3 = st.columns(3)
        c1.metric("Passes completos", m["passes_completos"])
        c2.metric("Chutes", m["chutes"])
        c3.metric("Conversão de chutes", f"{m['conversao']:.1f}%")

    st.divider()
    st.subheader("Comparar dois jogadores")

    if len(jogadores) >= 2:
        with st.form("comparacao"):
            a, b = st.columns(2)
            jogador_a = a.selectbox("Jogador A", jogadores, index=0)
            jogador_b = b.selectbox("Jogador B", jogadores, index=1)
            metrica_escolhida = st.selectbox(
                "Métrica", ["passes", "chutes", "gols", "xg"]
            )
            st.form_submit_button("Comparar")

        grafico, tabela = grafico_comparacao_jogadores(
            eventos, jogador_a, jogador_b, metrica_escolhida
        )
        st.pyplot(grafico)
        st.dataframe(tabela, hide_index=True)

with aba_dados:
    st.subheader("Eventos da partida")

    tabela_eventos = filtrados.copy()
    if busca_jogador:
        tabela_eventos = tabela_eventos[
            tabela_eventos["player"].fillna("").str.contains(
                busca_jogador, case=False, regex=False
            )
        ]

    colunas = [
        "minute", "team", "player", "type", "pass_outcome",
        "shot_outcome", "shot_statsbomb_xg"
    ]
    colunas = [c for c in colunas if c in tabela_eventos.columns]

    st.dataframe(tabela_eventos[colunas].head(int(quantidade_linhas)), use_container_width=True)

    csv = tabela_eventos.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar dados filtrados em CSV",
        data=csv,
        file_name=f"eventos_{match_id}.csv",
        mime="text/csv",
    )

st.caption(
    f"Último jogador selecionado nesta sessão: {st.session_state['ultimo_jogador']}"
)
