"""Métricas de eventos; disputa de pênaltis nunca integra o jogo."""
import pandas as pd

def calculate_stats(events):
    df = events[events.period.ne(5)]
    passes = df[df.type.eq('Pass')]
    shots = df[df.type.eq('Shot')]
    goals = int(shots.shot_outcome.eq('Goal').sum())
    complete = int(passes.pass_complete.sum())
    cards = df.foul_committed_card.combine_first(df.bad_behaviour_card)
    return {'Eventos': len(df), 'Passes': len(passes), 'Passes completos': complete,
            'Precisão (%)': complete / len(passes) * 100 if len(passes) else None,
            'Chutes': len(shots), 'No alvo': int(shots.shot_outcome.isin(['Goal','Saved','Saved to Post']).sum()),
            'Gols de finalizações': goals, 'Gols contra cometidos': int(df.type.eq('Own Goal Against').sum()),
            'xG': float(shots.shot_statsbomb_xg.sum()),
            'Conversão (%)': goals / len(shots) * 100 if len(shots) else None,
            'Desarmes ganhos': int((df.type.eq('Duel') & df.duel_type.eq('Tackle') & df.duel_outcome.isin(['Won','Success','Success In Play','Success Out'])).sum()),
            'Cartões': int(cards.notna().sum())}

def grouped_stats(df, column):
    rows = [{column: name, **calculate_stats(group)} for name, group in df.groupby(column)]
    return pd.DataFrame(rows)
