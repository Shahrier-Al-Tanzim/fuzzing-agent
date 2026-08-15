"""Generated strategy - iteration 4, attempt 2.
accepted: True
generated: 2026-08-15T11:07:04.425120+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'")
    ))

@composite
def dotted_key(draw):
    parts = draw(st.lists(key(), min_size=2, max_size=5))
    return ".".join(parts)

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e10, max_value=1e10).map(str),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: "true" if x else "false"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
                  st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"),
        array(),
        inline_table(),
        ml_basic_string(),
        ml_literal_string(),
        escape_sequence(),
        unicode_escape(),
        hex_int(),
        oct_int(),
        bin_int(),
        inf_nan(),
        leading_zero_int(),
        int_underscore(),
        int_overflow(),
        offset_date_time()
    ))

@composite
def pair(draw):
    k = draw(st.one_of(key(), dotted_key()))
    v = draw(value())
    return f"{k} = {v}"

@composite
def array(draw):
    elements = draw(st.lists(st.one_of(value(), array(), inline_table()), min_size=0, max_size=10))
    return f"[{', '.join(elements)}]"

@composite
def inline_table(draw):
    pairs = draw(st.lists(pair(), min_size=0, max_size=10))
    return f"{{{', '.join(pairs)}}}"

@composite
def table(draw):
    return draw(st.one_of(
        key().map(lambda k: f"[{k}]"),
        key().map(lambda k: f"[[{k}]]")
    ))

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10))
    return "\n".join(elements)

@composite
def ml_basic_string(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f'"""{x}"""'))

@composite
def ml_literal_string(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f"'''{x}'''"))

@composite
def escape_sequence(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=1).map(lambda x: f"\\{x}"),
        st.text(min_size=1, max_size=4).map(lambda x: f"\\u{x}"),
        st.text(min_size=1, max_size=8).map(lambda x: f"\\U{x}")
    ))

@composite
def unicode_escape(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=4).map(lambda x: f"\\u{x}"),
        st.text(min_size=1, max_size=8).map(lambda x: f"\\U{x}")
    ))

@composite
def hex_int(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f"0x{x}"))

@composite
def oct_int(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f"0o{x}"))

@composite
def bin_int(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f"0b{x}"))

@composite
def inf_nan(draw):
    return draw(st.sampled_from(["inf", "-inf", "nan"]))

@composite
def leading_zero_int(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f"0{x}"))

@composite
def int_underscore(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f"{x}_"))

@composite
def int_overflow(draw):
    return draw(st.integers(min_value=2**63, max_value=2**64-1).map(str))

@composite
def offset_date_time(draw):
    return draw(st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
                          st.integers(0, 23), st.integers(0, 59), st.integers(0, 59),
                          st.sampled_from(['Z', '+00:00', '-00:00'])).map(
                              lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}{t[6]}"))

toml_strategy = st.recursive(
    st.one_of(pair(), table()),
    lambda x: st.one_of(array(), inline_table(), x),
    max_leaves=15
)