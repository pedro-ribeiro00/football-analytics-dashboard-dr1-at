import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from streamlit.testing.v1 import AppTest
at=AppTest.from_file(str(root/'app.py'),default_timeout=120).run()
assert not at.exception,at.exception
assert not at.error,at.error
print('DEFAULT OK',[(m.label,m.value) for m in at.metric][:6])
print('SELECTS',[(i,x.label,x.value) for i,x in enumerate(at.selectbox)])
# Player filter, all visual branches, empty filters, and match switching.
player=next(x for x in at.selectbox if x.label=='Jogador')
player.select(player.options[2]).run()
assert not at.exception,at.exception
at.radio[0].set_value('Interativo com hover').run()
assert not at.exception,at.exception
at.checkbox[0].check().run()
assert not at.exception,at.exception
next(x for x in at.multiselect if x.label=='Tipos de evento').set_value([])
next(x for x in at.button if x.label=='Aplicar filtros').click().run()
assert not at.exception,at.exception
print('EMPTY AND INTERACTIVE OK')
# Clear filtering by moving to a different match.
match=next(x for x in at.selectbox if x.label=='Partida')
match.select(match.options[1]).run()
assert not at.exception and not at.error,(at.exception,at.error)
print('MATCH SWITCH OK')
