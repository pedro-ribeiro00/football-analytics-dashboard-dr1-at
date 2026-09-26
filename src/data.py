"""Aquisição pública via StatsBombPy e normalização defensiva."""
import json
import pandas as pd
import streamlit as st
from statsbombpy import sb

CREDS = {"user": "", "passwd": ""}

@st.cache_data(ttl=86400, show_spinner=False)
def load_competitions():
    return sb.competitions(creds=CREDS)

@st.cache_data(ttl=86400, show_spinner=False)
def load_matches(competition_id, season_id):
    return sb.matches(competition_id=int(competition_id), season_id=int(season_id), creds=CREDS)

@st.cache_data(ttl=86400, max_entries=8, show_spinner=False)
def load_events(match_id):
    return normalize_events(sb.events(match_id=int(match_id), creds=CREDS))

@st.cache_data(ttl=86400, max_entries=8, show_spinner=False)
def load_lineups(match_id):
    return sb.lineups(match_id=int(match_id), creds=CREDS)

def normalize_events(frame):
    df = frame.copy()
    text_cols = ['id','type','team','player','pass_outcome','shot_outcome','duel_type','duel_outcome','foul_committed_card','bad_behaviour_card']
    for col in text_cols:
        if col not in df: df[col] = None
    for col in ['minute','second','period','index','shot_statsbomb_xg']:
        if col not in df: df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    for col in ['location','pass_end_location']:
        if col not in df: df[col] = None
    def coordinate(value, axis):
        if isinstance(value, (list, tuple)) and len(value) > axis:
            return pd.to_numeric(value[axis], errors='coerce')
        return float('nan')
    for col, source, axis in [('x','location',0),('y','location',1),('end_x','pass_end_location',0),('end_y','pass_end_location',1)]:
        df[col] = df[source].map(lambda v: coordinate(v, axis))
    df['pass_complete'] = df['type'].eq('Pass') & df['pass_outcome'].isna()
    df['time'] = df['minute'] + df['second'] / 60
    return df.sort_values(['period','index']).reset_index(drop=True)

def filter_events(df, periods, minutes, types=None, team=None, player=None):
    mask = df.period.isin(periods) & df.minute.between(*minutes)
    if types is not None: mask &= df.type.isin(types)
    if team: mask &= df.team.eq(team)
    if player: mask &= df.player.eq(player)
    return df.loc[mask].copy()

def export_csv(df):
    result = df.copy()
    for col in result.select_dtypes(include=['object', 'str']):
        result[col] = result[col].map(lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
    return result.to_csv(index=False).encode('utf-8-sig')
