"""Generated strategy - iteration 1, attempt 2.
accepted: False
generated: 2026-08-15T10:23:25.986060+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.text(min_size=1, max_size=10).filter(lambda x: all(c.isalnum() or c in '-_' for c in x))
    ))

@composite
def dotted_key(draw):
    keys = draw(st.lists(key(), min_size=1, max_size=5))
    return '.'.join(keys)

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e10, max_value=1e10).map(str),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: 'true' if x else 'false'),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T00:00:00Z"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28), st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28), st.integers(0, 23), st.integers(0, 59), st.integers(0, 59), st.integers(0, 999999))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]:06d}Z"),
        array(),
        inline_table(),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"' + '\\u' + st.text(min_size=4, max_size=4, alphabet='0123456789ABCDEF').example()),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"' + '\\U' + st.text(min_size=8, max_size=8, alphabet='0123456789ABCDEF').example()),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"' + '\\x' + st.text(min_size=2, max_size=2, alphabet='0123456789ABCDEF').example()),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"' + '\\n'),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"' + '\\t'),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"' + '\\r'),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"' + '\\b'),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"' + '\\f'),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"' + '\\'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'" + '\\u' + st.text(min_size=4, max_size=4, alphabet='0123456789ABCDEF').example()),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'" + '\\U' + st.text(min_size=8, max_size=8, alphabet='0123456789ABCDEF').example()),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'" + '\\x' + st.text(min_size=2, max_size=2, alphabet='0123456789ABCDEF').example()),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'" + '\\n'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'" + '\\t'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'" + '\\r'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'" + '\\b'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'" + '\\f'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'" + '\\'),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"{x:08x}"),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"{x:016x}"),
        st.integers(min_value=0, max_value=2**63-1).map(lambda x: f"0o{x:012o}"),
        st.integers(min_value=0, max_value=2**63-1).map(lambda x: f"0b{x:064b}"),
        st.integers(min_value=-2**63, max_value=2**63-1).map(lambda x: f"{x}"),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f"{x}"),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f"{x}e10"),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f"{x}e-10"),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f"{x}e+10"),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f"{x}e+100"),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f"{x}e-100"),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f"inf"),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f"-inf"),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f"nan"),
        st.floats(min_value=-1e10, max_value=1e10).map(lambda x: f"-nan"),
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
    header = draw(st.one_of(key().map(lambda k: f"[{k}]"), key().map(lambda k: f"[[{k}]]")))
    return header

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=0, max_size=10))
    return "\n".join(elements)

toml_strategy = document()