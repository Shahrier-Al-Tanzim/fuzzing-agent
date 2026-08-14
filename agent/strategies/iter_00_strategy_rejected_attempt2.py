"""Generated strategy - iteration 0, attempt 2.
accepted: False
generated: 2026-08-14T08:52:47.107561+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def scalar_value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100, allow_nan=True, allow_infinity=True).map(str),
        st.booleans().map(lambda b: "true" if b else "false"),
        st.sampled_from(["inf", "-inf", "nan"]),
        st.datetimes().map(lambda dt: dt.isoformat() + "Z"),
        st.text(min_size=1, max_size=100).map(lambda s: '"' + s.replace('"', '\\"') + '"'),
        st.text(min_size=1, max_size=100).map(lambda s: "'" + s.replace("'", "\\'") + "'")
    ))

@composite
def array_value(draw):
    elements = draw(st.lists(scalar_value(), min_size=0, max_size=10))
    return "[" + ", ".join(elements) + "]"

@composite
def inline_table_value(draw):
    pairs = draw(st.lists(st.tuples(st.text(min_size=1, max_size=100), scalar_value()), min_size=0, max_size=10))
    return "{" + ", ".join(f"{k} = {v}" for k, v in pairs) + "}"

@composite
def table_value(draw):
    name = draw(st.text(min_size=1, max_size=100))
    return f"[{name}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(scalar_value(), array_value(), inline_table_value(), table_value()), min_size=0, max_size=10))
    return "\n".join(elements)

toml_strategy = document()