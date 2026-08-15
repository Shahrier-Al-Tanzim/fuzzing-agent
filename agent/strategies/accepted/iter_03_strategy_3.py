"""Generated strategy - iteration 3, attempt 2.
accepted: True
generated: 2026-08-15T09:52:07.107592+00:00
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
def escape_sequence(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=1).map(lambda x: f'\\{x}'),
        st.sampled_from(['\\b', '\\f', '\\n', '\\r', '\\t'])
    ))

@composite
def unicode_escape(draw):
    return draw(st.sampled_from(['\\u', '\\U']).map(lambda x: f'{x}{draw(st.text(min_size=4, max_size=4))}'))

@composite
def hex_int(draw):
    return draw(st.text(min_size=1, max_size=10).map(lambda x: f'0x{x}'))

@composite
def inf(draw):
    return draw(st.sampled_from(['inf', '-inf']))

@composite
def nan(draw):
    return draw(st.sampled_from(['nan', '-nan']))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e100, max_value=1e100).map(str),
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
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
                  st.integers(0, 23), st.integers(0, 59), st.integers(0, 59),
                  st.integers(0, 999999))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]:06d}"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
                  st.integers(0, 23), st.integers(0, 59), st.integers(0, 59),
                  st.integers(0, 999999), st.sampled_from(['Z', '+00:00', '-00:00']))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]:06d}{t[7]}"),
        hex_int(),
        inf(),
        nan(),
        escape_sequence(),
        unicode_escape(),
        array(),
        inline_table(),
        st.text(min_size=2, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=2, max_size=10).map(lambda x: f"'{x}'"),
        st.text(min_size=3, max_size=10).map(lambda x: f'"""{x}"""'),
        st.text(min_size=3, max_size=10).map(lambda x: f"'''{x}'''"),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"0x{x:x}"),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"0o{x:o}"),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"0b{x:b}"),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"0x{x:x}_0x{x:x}"),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"0o{x:o}_0o{x:o}"),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"0b{x:b}_0b{x:b}"),
        st.integers(min_value=0, max_value=999999).map(lambda x: f".{x:06d}"),
        st.integers(min_value=0, max_value=999999).map(lambda x: f".{x:06d}Z"),
        st.integers(min_value=0, max_value=999999).map(lambda x: f".{x:06d}+00:00"),
        st.integers(min_value=0, max_value=999999).map(lambda x: f".{x:06d}-00:00"),
        st.integers(min_value=0, max_value=999999).map(lambda x: f".{x:06d}Z+00:00"),
        st.integers(min_value=0, max_value=999999).map(lambda x: f".{x:06d}Z-00:00"),
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
    pairs = draw(st.lists(st.tuples(st.one_of(key(), dotted_key()), value()), min_size=0, max_size=10))
    return f"{{{', '.join(f'{k} = {v}' for k, v in pairs)}}}"

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

toml_strategy = document()