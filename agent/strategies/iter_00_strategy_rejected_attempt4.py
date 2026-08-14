"""Generated strategy - iteration 0, attempt 4.
accepted: False
generated: 2026-08-13T11:51:26.871919+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier()),
        st.text(min_size=2, max_size=20).filter(lambda x: x.startswith('"') and x.endswith('"')),
        st.text(min_size=2, max_size=20).filter(lambda x: x.startswith("'") and x.endswith("'"))
    ))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
        st.text(min_size=1, max_size=20).filter(lambda x: x.startswith('"') and x.endswith('"')),
        st.text(min_size=1, max_size=20).filter(lambda x: x.startswith("'") and x.endswith("'")),
        st.sampled_from(["true", "false"]),
        st.sampled_from(["inf", "-inf", "nan"]),
        st.dates(min_value="1970-01-01", max_value="2100-12-31").map(lambda x: x.strftime("%Y-%m-%dT%H:%M:%S%z")),
        st.dates(min_value="1970-01-01", max_value="2100-12-31").map(lambda x: x.strftime("%Y-%m-%d"))
    ))

@composite
def pair(draw):
    return (draw(key()), draw(value()))

@composite
def table(draw, max_size=5):
    pairs = [draw(pair()) for _ in range(draw(st.integers(min_value=0, max_value=max_size)))]
    return pairs

@composite
def array(draw, max_size=5):
    values = [draw(value()) for _ in range(draw(st.integers(min_value=0, max_value=max_size)))]
    return values

@composite
def document(draw):
    elements = []
    for _ in range(draw(st.integers(min_value=0, max_value=5))):
        elements.append(draw(st.one_of(
            pair().map(lambda x: f"{x[0]} = {x[1]}"),
            table().map(lambda x: "\n".join(f"{k} = {v}" for k, v in x)),
            array().map(lambda x: "[" + ", ".join(x) + "]")
        )))
    return "\n".join(elements)

toml_strategy = document()