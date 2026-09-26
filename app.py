"""Assessment de Sports Analytics — Pedro Henrique Nunes Ribeiro."""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from src.data import load_competitions, load_matches, load_events, load_lineups, filter_events, export_csv
from src.metrics import calculate_stats, grouped_stats
from src import charts

st.set_page_config(page_title='Futebol em Dados', page_icon='⚽', layout='wide')
st.markdown('''<style>[data-testid="stMetric"]{background:#edf7f3;border-top:3px solid #087f68;padding:14px;border-radius:8px} .block-container{padding-top:2rem}</style>''', unsafe_allow_html=True)
st.title('⚽ Futebol em Dados')
st.caption('SPORTS ANALYTICS • Pedro Henrique Nunes Ribeiro • StatsBomb Open Data')
st.markdown('**Como a circulação da bola e a qualidade das finalizações ajudam a explicar uma partida?**')

with st.sidebar:
    st.header('Selecione a partida')
    progress = st.progress(0, text='Carregando catálogo')
    try:
        with st.spinner('Consultando competições abertas…'):
            competitions = load_competitions()
        progress.progress(20, text='Competições disponíveis')
        catalog = competitions.drop_duplicates('competition_id').set_index('competition_id')
        ids = catalog.index.tolist()
        cid = st.selectbox('Competição',ids,index=ids.index(43) if 43 in ids else 0,format_func=lambda x:f"{catalog.loc[x,'competition_name']} · {catalog.loc[x,'competition_gender']}",key='competition')
        seasons = competitions[competitions.competition_id.eq(cid)].drop_duplicates('season_id').set_index('season_id')
        sids = seasons.index.tolist()
        sid = st.selectbox('Temporada',sids,index=sids.index(106) if 106 in sids else 0,format_func=lambda x:str(seasons.loc[x,'season_name']),key=f'season_{cid}')
        with st.spinner('Carregando partidas…'): matches = load_matches(cid,sid).sort_values('match_date',ascending=False)
        if matches.empty: st.warning('Nenhuma partida disponível.'); st.stop()
        progress.progress(45, text='Partidas disponíveis')
        match_index = matches.set_index('match_id'); mids = match_index.index.tolist()
        mid = st.selectbox('Partida',mids,index=mids.index(3869685) if 3869685 in mids else 0,format_func=lambda x:f"{match_index.loc[x,'home_team']} × {match_index.loc[x,'away_team']} | {match_index.loc[x,'match_date']}",key=f'match_{cid}_{sid}')
        with st.spinner('Carregando e preparando eventos…'): events = load_events(mid)
        progress.progress(85, text='Eventos preparados')
        try:
            lineups = load_lineups(mid)
        except Exception:
            lineups = {}; st.caption('Escalações indisponíveis; jogadores com eventos continuam disponíveis.')
        progress.progress(100, text='Dados prontos')
    except Exception as exc:
        st.error('Não foi possível consultar a StatsBomb. Verifique a conexão e tente novamente.')
        with st.expander('Detalhes técnicos'): st.code(str(exc))
        if st.button('Tentar novamente'): st.cache_data.clear(); st.rerun()
        st.stop()
    st.divider()
    teams = sorted(events.team.dropna().unique())
    team = st.selectbox('Equipe para mapas e jogador',['Todas']+teams,key=f'team_{mid}')
    roster = set(events.player.dropna() if team=='Todas' else events.loc[events.team.eq(team),'player'].dropna())
    for name, lineup in lineups.items():
        if team=='Todas' or name==team: roster.update(lineup.player_name.dropna())
    players = sorted(roster)
    player = st.selectbox('Jogador',['Todos']+players,key=f'player_{mid}_{team}')
    st.caption('Fonte: StatsBomb. Dados abertos para pesquisa. Sem credenciais de API.')
    logo = Path(__file__).parent/'assets'/'statsbomb-logo.svg'
    if logo.exists(): st.image(str(logo),width=180)
    st.markdown('[Dados e termos de uso](https://github.com/hudl/open-data)')

match = match_index.loc[mid]
with st.container(border=True):
    st.subheader(f"{match.home_team} {int(match.home_score)} × {int(match.away_score)} {match.away_team}")
    st.caption(f"{catalog.loc[cid,'competition_name']} • {seasons.loc[sid,'season_name']} • {match.match_date} • {match.competition_stage}")
    st.caption('Placar oficial do jogo completo. Disputa de pênaltis excluída das métricas, mapas e comparação.')

period_names = {1:'1º tempo',2:'2º tempo',3:'Prorrogação 1',4:'Prorrogação 2'}
available_periods = [x for x in period_names if x in events.period.unique()]
max_minute = max(1,int(events.loc[events.period.ne(5),'minute'].max()))
with st.expander('Filtros de período, eventos e tabela', expanded=False):
    with st.form(f'filters_{mid}'):
        c1,c2,c3 = st.columns([2,2,1])
        periods = c1.multiselect('Períodos',available_periods,default=available_periods,format_func=period_names.get)
        minutes = c2.slider('Intervalo de minutos (inclusivo)',0,max_minute,(0,max_minute))
        limit = c3.number_input('Linhas na tabela',min_value=10,max_value=5000,value=100,step=10)
        types = st.multiselect('Tipos de evento',sorted(events.type.dropna().unique()),default=sorted(events.type.dropna().unique()))
        search = st.text_input('Buscar jogador na tabela',placeholder='Parte do nome; busca literal')
        st.form_submit_button('Aplicar filtros',type='primary')
# Formulário mantém os valores aplicados entre reruns; sessão guarda o contexto da análise.
st.session_state['analysis_context'] = {'match_id':int(mid),'periods':periods,'minutes':minutes,'player':player}
base = filter_events(events,periods,minutes,types)
selected = filter_events(events,periods,minutes,types,None if team=='Todas' else team,None if player=='Todos' else player)
st.caption(f'Filtros aplicados: {len(base):,} eventos da partida e {len(selected):,} no recorte de equipe/jogador. Tipos de evento também afetam as métricas. Minutos podem se sobrepor entre períodos nos acréscimos.')
if selected.empty: st.info('Nenhum evento no recorte. Amplie os filtros ou selecione outro jogador.')

def metrics_row(df):
    stats = calculate_stats(df)
    labels = ['Passes','Passes completos','Precisão (%)','Chutes','xG','Conversão (%)']
    for col,label in zip(st.columns(6),labels):
        value = stats[label]
        col.metric(label,'—' if value is None else f'{value:.2f}' if isinstance(value,float) else value)

def show_figure(fig):
    st.pyplot(fig); plt.close(fig)

overview, passes_tab, shots_tab, player_tab, comparison_tab, data_tab = st.tabs(['Partida','Passes','Chutes','Jogador','Comparação','Eventos / CSV'])
with overview:
    st.subheader('Panorama da partida no período e nos eventos selecionados')
    st.caption('Esta aba inclui as duas equipes; os seletores de equipe/jogador afetam as abas Passes, Chutes, Jogador e Eventos.')
    metrics_row(base)
    teams_table = grouped_stats(base,'team')
    st.dataframe(teams_table.rename(columns={'team':'Equipe'}),hide_index=True,width='stretch')
    st.plotly_chart(charts.timeline(base),width='stretch')
    show_figure(charts.player_relation(base))
    st.caption('Relação descritiva: passes e xG não demonstram causalidade. Não há estimativa de posse baseada na contagem de eventos.')
with passes_tab:
    metrics_row(selected)
    only_complete = st.checkbox('Exibir somente passes completos')
    pass_data = selected[selected.pass_complete] if only_complete else selected
    mode = st.radio('Visualização de passes',['Mapa mplsoccer','Interativo com hover'],horizontal=True)
    if mode=='Mapa mplsoccer': show_figure(charts.pass_map(pass_data))
    else: st.plotly_chart(charts.interactive_map(pass_data,'Pass'),width='stretch')
    st.caption('Origem e destino nas coordenadas StatsBomb (120 × 80). Os dois times atacam para a direita nesta representação normalizada.')
with shots_tab:
    stats = calculate_stats(selected)
    for col,key in zip(st.columns(4),['Chutes','Gols de finalizações','xG','Conversão (%)']):
        value=stats[key]; col.metric(key,'—' if value is None else f'{value:.2f}')
    show_figure(charts.shot_map(selected))
    st.plotly_chart(charts.interactive_map(selected,'Shot'),width='stretch')
    st.caption('xG é a probabilidade estimada de gol de cada finalização. Pênaltis durante o jogo estão incluídos; cobranças da disputa estão excluídas. Gols contra são exibidos separadamente na tabela de métricas.')
with player_tab:
    st.subheader(player if player!='Todos' else 'Ações do recorte selecionado')
    metrics_row(selected)
    show_figure(charts.heatmap(selected))
    st.caption('O mapa conta eventos com posição, não distância percorrida, toques exatos nem tempo de ocupação do campo. Reservas sem eventos podem ter métricas zeradas.')
with comparison_tab:
    all_players = sorted(events.player.dropna().unique())
    if len(all_players)>=2:
        with st.form(f'compare_{mid}'):
            a,b=st.columns(2)
            pa=a.selectbox('Jogador A',all_players)
            pb=b.selectbox('Jogador B',all_players,index=1)
            st.form_submit_button('Comparar',type='primary')
        st.session_state[f'comparison_{mid}'] = [pa,pb]
        table=pd.DataFrame([{'Jogador':p,**calculate_stats(base[base.player.eq(p)])} for p in [pa,pb]])
        st.caption('Comparação usa os mesmos filtros de período, minuto e evento para ambos; ignora o seletor individual da sidebar. Valores absolutos, sem ajuste por minutos jogados.')
        if pa==pb: st.info('Selecione jogadores diferentes para uma comparação útil.')
        st.dataframe(table,hide_index=True,width='stretch')
        metric=st.selectbox('Métrica do gráfico',['Passes','Passes completos','Precisão (%)','Chutes','Gols de finalizações','xG','Conversão (%)'])
        st.plotly_chart(charts.comparison(table,metric),width='stretch')
    else: st.info('Jogadores insuficientes para comparação.')
with data_tab:
    view=selected.copy()
    if search: view=view[view.player.fillna('').str.contains(search,case=False,regex=False)]
    preferred=['id','period','minute','second','team','player','type','pass_outcome','shot_outcome','shot_statsbomb_xg','x','y','end_x','end_y']
    st.dataframe(view[preferred].head(int(limit)),hide_index=True,width='stretch')
    st.caption(f'Exibindo até {int(limit)} de {len(view)} eventos. CSV contém todas as linhas filtradas e todas as colunas; listas e objetos são serializados como JSON.')
    st.download_button('Baixar eventos filtrados (CSV)',export_csv(view),file_name=f'eventos_{mid}.csv',mime='text/csv')
    shootout=events[events.period.eq(5)]
    if not shootout.empty:
        with st.expander('Disputa de pênaltis (consulta separada, sem os filtros acima)'):
            st.dataframe(shootout.loc[shootout.type.eq('Shot'),['team','player','shot_outcome']],hide_index=True)
with st.expander('Metodologia e limites'):
    st.markdown('''Passes completos: eventos Pass sem pass_outcome. Precisão = completos / passes. Conversão = gols de finalizações / chutes. Ausência de denominador aparece como “—”. No alvo: Goal, Saved e Saved to Post. xG: soma de shot_statsbomb_xg. Desarmes ganhos: Duel/Tackle com resultado Won ou Success. Cartões: campos foul_committed_card e bad_behaviour_card. O placar oficial é independente dos filtros. Dados abertos não cobrem todas as ligas e temporadas; este painel não atribui causalidade nem mede rastreamento dos atletas.''')
