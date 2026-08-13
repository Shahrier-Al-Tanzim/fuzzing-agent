"""Generated strategy - iteration 0, attempt 3.
accepted: True
generated: 2026-08-13T08:41:33.424793+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).filter(lambda s: s.isidentifier()),
        st.text(min_size=2, max_size=10).filter(lambda s: s.startswith('"') and s.endswith('"')),
        st.text(min_size=2, max_size=10).filter(lambda s: s.startswith("'") and s.endswith("'"))
    ))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-1000, max_value=1000).map(str),
        st.floats(min_value=-1000, max_value=1000).map(str),
        st.text(min_size=1, max_size=10).filter(lambda s: s.isidentifier()),
        st.text(min_size=2, max_size=10).filter(lambda s: s.startswith('"') and s.endswith('"')),
        st.text(min_size=2, max_size=10).filter(lambda s: s.startswith("'") and s.endswith("'"))
    ))

@composite
def pair(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def array(draw):
    elements = [draw(value()) for _ in range(draw(st.integers(min_value=0, max_value=10)))]
    return f"[{', '.join(elements)}]"

@composite
def table(draw):
    pairs = [draw(pair()) for _ in range(draw(st.integers(min_value=0, max_value=10)))]
    return "\n".join(pairs)

@composite
def document(draw):
    elements = [draw(st.one_of(pair(), table(), array())) for _ in range(draw(st.integers(min_value=0, max_value=10)))]
    return "\n".join(elements)

toml_strategy = document()