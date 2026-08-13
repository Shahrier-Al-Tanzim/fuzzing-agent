"""Generated strategy - iteration 0, attempt 3.
accepted: True
generated: 2026-08-13T08:28:01.027654+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=20).filter(lambda s: s.isidentifier()),
        st.text(min_size=2, max_size=20).filter(lambda s: s.startswith('"') and s.endswith('"')),
        st.text(min_size=2, max_size=20).filter(lambda s: s.startswith("'") and s.endswith("'"))
    ))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.text(min_size=1, max_size=20).filter(lambda s: s.isidentifier()),
        st.text(min_size=2, max_size=20).filter(lambda s: s.startswith('"') and s.endswith('"')),
        st.text(min_size=2, max_size=20).filter(lambda s: s.startswith("'") and s.endswith("'"))
    ))

@composite
def pair(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def array(draw, elements=st.integers(min_value=0, max_value=10)):
    n = draw(elements)
    return f"[{', '.join(draw(st.lists(value(), min_size=n, max_size=n)))}]"

@composite
def table(draw, pairs=st.integers(min_value=0, max_value=10)):
    n = draw(pairs)
    return f"{{{', '.join(draw(st.lists(pair(), min_size=n, max_size=n)))}}}"

@composite
def document(draw, elements=st.integers(min_value=0, max_value=10)):
    n = draw(elements)
    return "\n".join(draw(st.lists(st.one_of(pair(), array(), table()), min_size=n, max_size=n)))

toml_strategy = document()