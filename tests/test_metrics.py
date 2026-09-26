import pandas as pd
import pytest
from src.data import normalize_events,filter_events,export_csv
from src.metrics import calculate_stats

def fixture():
    return normalize_events(pd.DataFrame([
        {'type':'Pass','player':'João','period':1,'minute':10,'index':1},
        {'type':'Pass','pass_outcome':'Incomplete','period':1,'minute':11,'index':2},
        {'type':'Shot','shot_outcome':'Goal','shot_statsbomb_xg':.25,'period':2,'minute':70,'index':3},
        {'type':'Shot','shot_outcome':'Saved','shot_statsbomb_xg':.1,'period':2,'minute':80,'index':4},
        {'type':'Shot','shot_outcome':'Goal','shot_statsbomb_xg':.8,'period':5,'minute':120,'index':5},
        {'type':'Own Goal Against','period':2,'minute':85,'index':6},
    ]))

def test_metrics_and_shootout_exclusion():
    s=calculate_stats(fixture())
    assert s['Passes']==2 and s['Passes completos']==1
    assert s['Precisão (%)']==50 and s['Conversão (%)']==50
    assert s['Chutes']==2 and s['Gols de finalizações']==1
    assert s['xG']==pytest.approx(.35)
    assert s['Gols contra cometidos']==1

def test_empty_denominators():
    s=calculate_stats(fixture().iloc[:0])
    assert s['Precisão (%)'] is None and s['Conversão (%)'] is None
    assert s['xG']==0

def test_filters_empty_selection_and_literal_names():
    df=fixture()
    assert len(filter_events(df,[1],(10,10),['Pass'],player='João'))==1
    assert filter_events(df,[],(0,130)).empty
    assert filter_events(df,[1],(0,130),[]).empty

def test_missing_coordinates_and_utf8_csv():
    df=fixture()
    assert df.x.isna().all()
    assert 'João' in export_csv(df).decode('utf-8-sig')
    assert export_csv(df).startswith(b'\xef\xbb\xbf')
