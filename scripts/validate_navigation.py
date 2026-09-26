import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from streamlit.testing.v1 import AppTest
at=AppTest.from_file(str(root/'app.py'),default_timeout=120).run()
assert not at.exception and not at.error
for label,needle in [('Jogador A','Lionel'),('Jogador B','Kylian')]:
    widget=next(x for x in at.selectbox if x.label==label)
    widget.select(next(x for x in widget.options if needle in x))
next(x for x in at.button if x.label=='Comparar').click().run()
assert not at.exception
assert any('Lionel' in str(d.value) and 'Kylian' in str(d.value) for d in at.dataframe)
next(x for x in at.selectbox if x.label=='Equipe para mapas e jogador').select('Argentina').run()
assert not at.exception
# Another season and competition exercises the dependent options.
s=next(x for x in at.selectbox if x.label=='Temporada'); s.select('2018').run()
assert not at.exception and not at.error
c=next(x for x in at.selectbox if x.label=='Competição'); c.select(next(x for x in c.options if 'Women' in x)).run()
assert not at.exception and not at.error
print('COMPARISON, TEAM, SEASON, COMPETITION OK')
