"""Generated strategy - iteration 0, attempt 3.
accepted: False
generated: 2026-08-13T11:54:02.162843+00:00
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
        st.text(min_size=1, max_size=20),
        st.integers(min_value=-1000000, max_value=1000000).map(str),
        st.floats(min_value=-1000000, max_value=1000000).map(str),
        st.sampled_from(["true", "false"]),
        st.sampled_from(["inf", "-inf", "nan"])
    ))

@composite
def pair(draw):
    return (draw(key()), draw(value()))

@composite
def array(draw):
    return draw(st.lists(value(), min_size=0, max_size=10))

@composite
def inline_table(draw):
    return draw(st.lists(pair(), min_size=0, max_size=10))

@composite
def table(draw):
    return draw(st.lists(pair(), min_size=0, max_size=10))

@composite
def document(draw):
    elements = []
    for _ in range(draw(st.integers(min_value=0, max_value=10))):
        elements.append(draw(st.one_of(
            pair().map(lambda p: f"{p[0]} = {p[1]}"),
            table().map(lambda t: "[table]\n" + "\n".join(f"{k} = {v}" for k, v in t)),
            inline_table().map(lambda t: "{ " + ", ".join(f"{k} = {v}" for k, v in t) + " }"),
            array().map(lambda a: "[" + ", ".join(a) + "]")
        )))
    return "\n".join(elements)

toml_strategy = document()