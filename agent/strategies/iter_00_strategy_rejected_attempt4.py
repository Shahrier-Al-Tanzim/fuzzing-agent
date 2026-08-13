"""Generated strategy - iteration 0, attempt 4.
accepted: False
generated: 2026-08-13T07:59:37.194710+00:00
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
        st.datetimes(min_year=1970, max_year=2100).map(lambda dt: dt.isoformat()),
        st.text(min_size=1, max_size=100).map(lambda s: f'"{s}"')
    ))

@composite
def array_value(draw):
    elements = draw(st.lists(scalar_value(), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table_value(draw):
    pairs = draw(st.lists(st.tuples(st.text(min_size=1, max_size=100), scalar_value()), min_size=0, max_size=10))
    return f"{{{', '.join(f'{key} = {value}' for key, value in pairs)}}}"

@composite
def table_value(draw):
    name = draw(st.text(min_size=1, max_size=100))
    return f"[{name}]\n"

@composite
def document(draw):
    tables = draw(st.lists(table_value(), min_size=0, max_size=10))
    return "\n".join(tables)

toml_strategy = document()