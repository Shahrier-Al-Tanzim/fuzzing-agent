"""Generated strategy - iteration 0, attempt 3.
accepted: False
generated: 2026-08-14T08:53:00.311096+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def scalar_value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e100, max_value=1e100).map(str),
        st.sampled_from(["true", "false"]),
        st.sampled_from(["inf", "-inf", "nan"]),
        st.text(min_size=1, max_size=100).map(lambda s: f'"{s}"'),
        st.text(min_size=1, max_size=100).map(lambda s: f"'{s}'")
    ))

@composite
def array_value(draw):
    return draw(st.lists(scalar_value(), min_size=0, max_size=10))

@composite
def inline_table_value(draw):
    pairs = draw(st.lists(st.tuples(st.text(min_size=1, max_size=100), scalar_value()), min_size=0, max_size=10))
    return draw(st.one_of(
        st.just(""),
        st.just(","),
        st.just(f"{{{', '.join(f'{k} = {v}' for k, v in pairs)}}}"),
        st.just(f"{{{', '.join(f'{k} = {v}' for k, v in pairs)}, }}")
    ))

@composite
def table_value(draw):
    return draw(st.one_of(
        scalar_value(),
        array_value(),
        inline_table_value()
    ))

@composite
def document(draw):
    return draw(st.one_of(
        st.just(""),
        table_value(),
        st.lists(table_value(), min_size=1, max_size=10).map(lambda values: "\n".join(values))
    ))

toml_strategy = document()