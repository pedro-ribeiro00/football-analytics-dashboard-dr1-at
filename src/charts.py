"""Mapas mplsoccer/Matplotlib, relação Seaborn e exploração Plotly."""
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns
from mplsoccer import Pitch
from src.metrics import grouped_stats

GREEN = '#087f68'
RED = '#e76f51'

def field():
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#f1f7f4', line_color='#78958b')
    fig, ax = pitch.draw(figsize=(10, 6.8))
    return pitch, fig, ax

def pass_map(df):
    p, fig, ax = field()
    passes = df[df.type.eq('Pass')].dropna(subset=['x','y','end_x','end_y'])
    for complete, label, color in [(True,'Completo',GREEN),(False,'Incompleto',RED)]:
        rows = passes[passes.pass_complete.eq(complete)]
        p.arrows(rows.x, rows.y, rows.end_x, rows.end_y, ax=ax, color=color, alpha=.6, width=1.5, label=label)
    ax.legend(loc='upper left')
    ax.set_title('Mapa de passes | ataque →', fontsize=15)
    return fig

def shot_map(df):
    p, fig, ax = field()
    shots = df[df.type.eq('Shot')].dropna(subset=['x','y'])
    for goal, label, color in [(True,'Gol',GREEN),(False,'Outros chutes',RED)]:
        rows = shots[shots.shot_outcome.eq('Goal').eq(goal)]
        p.scatter(rows.x, rows.y, s=40+rows.shot_statsbomb_xg*650, color=color, edgecolors='white', ax=ax, label=label)
    ax.legend(loc='upper left')
    ax.set_title('Mapa de chutes | área do círculo cresce com xG | ataque →', fontsize=12)
    return fig

def heatmap(df):
    p, fig, ax = field()
    rows = df.dropna(subset=['x','y'])
    bins = p.bin_statistic(rows.x, rows.y, statistic='count', bins=(12, 8))
    im = p.heatmap(bins, ax=ax, cmap='YlGnBu', edgecolors='#ffffff')
    fig.colorbar(im, ax=ax, shrink=.7, label='Eventos com localização')
    ax.set_title('Densidade de ações registradas | ataque →')
    return fig

def interactive_map(df, kind):
    # O campo-base é desenhado pelo mplsoccer; Plotly fornece hover e zoom.
    _, background, ax = field()
    ax.set_position([0,0,1,1]); ax.set_xlim(0,120); ax.set_ylim(80,0)
    buf = BytesIO(); background.savefig(buf, format='png', dpi=120, pad_inches=0)
    plt.close(background)
    fig = go.Figure()
    fig.add_layout_image(source='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode(), x=0,y=0,sizex=120,sizey=80,xref='x',yref='y',xanchor='left',yanchor='top',layer='below',sizing='stretch')
    rows = df[df.type.eq(kind)].dropna(subset=['x','y'])
    if kind == 'Pass':
        for complete, color, label in [(True,GREEN,'Completo'),(False,RED,'Incompleto')]:
            group = rows[rows.pass_complete.eq(complete)].dropna(subset=['end_x','end_y'])
            xs=[]; ys=[]
            for r in group.itertuples(): xs.extend([r.x,r.end_x,None]); ys.extend([r.y,r.end_y,None])
            fig.add_trace(go.Scatter(x=xs,y=ys,mode='lines',line=dict(color=color,width=1),name=label,hoverinfo='skip'))
        result = rows.pass_outcome.fillna('Complete')
        sizes = 8
    else:
        result = rows.shot_outcome
        sizes = 9 + rows.shot_statsbomb_xg * 30
    hover = pd.DataFrame({'player':rows.player.fillna('Sem jogador'),'minute':rows.minute,'outcome':result,'xg':rows.shot_statsbomb_xg})
    fig.add_trace(go.Scatter(x=rows.x,y=rows.y,mode='markers',marker=dict(size=sizes,color=GREEN,opacity=.8),customdata=hover.to_numpy(),hovertemplate='%{customdata[0]}<br>Minuto %{customdata[1]}<br>%{customdata[2]}<br>xG: %{customdata[3]:.3f}<extra></extra>',name='Origem do evento'))
    fig.update_layout(height=510,margin=dict(l=5,r=5,t=30,b=5),title='Explore com o cursor e o zoom | ataque →',xaxis=dict(range=[0,120],visible=False),yaxis=dict(range=[80,0],visible=False,scaleanchor='x'),legend=dict(orientation='h'))
    return fig

def timeline(df):
    shots = df[df.type.eq('Shot') & df.period.ne(5)].sort_values(['period','index']).copy()
    shots['xG acumulado'] = shots.groupby('team').shot_statsbomb_xg.cumsum()
    # Eixo sequencial evita regressão do relógio após acréscimos.
    shots['Ordem do chute'] = range(1,len(shots)+1)
    return px.line(shots,x='Ordem do chute',y='xG acumulado',color='team',markers=True,hover_data=['minute','player','shot_outcome'],labels={'team':'Equipe'},title='Criação de chances: xG acumulado por sequência de chutes',line_shape='hv')

def player_relation(df):
    table = grouped_stats(df,'player')
    fig, ax = plt.subplots(figsize=(10,5))
    if not table.empty:
        sns.scatterplot(data=table,x='Passes',y='xG',size='Chutes',sizes=(40,320),color=GREEN,ax=ax)
        for _, row in table.nlargest(4,'xG').iterrows(): ax.annotate(row['player'].split()[-1],(row['Passes'],row['xG']),xytext=(4,5),textcoords='offset points')
    ax.set_title('Participação na circulação e na finalização')
    sns.despine(ax=ax); fig.tight_layout()
    return fig

def comparison(table, metric):
    return px.bar(table,x='Jogador',y=metric,color='Jogador',text_auto='.2f',title=f'Comparação: {metric}')
