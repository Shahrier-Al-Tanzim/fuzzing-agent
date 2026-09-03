"""Generated strategy - iteration 0, attempt 7.
accepted: False
generated: 2026-09-02T21:22:08.057609+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
ESCAPABLE_CHARS = ['"', '\\', '\n', '\r', '\t']
ESCAPE_SEQUENCES = [f'\\{ch}' for ch in ESCAPABLE_CHARS] + [f'\\u{hex(i)[2:].zfill(4)}' for i in range(0x10000, 0x110000)]
BASIC_STRING = st.one_of(
    st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: f'"{x}"'),
    st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10).map(lambda x: f"'{x}'"),
    st.lists(st.sampled_from(ESCAPE_SEQUENCES)).map(lambda seqs: '"' + ''.join(seqs) + '"')
)

@composite
def key(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10),
        BASIC_STRING
    ))

@composite
def value(draw):
    return draw(st.one_of(
        BASIC_STRING,
        st.integers().map(str),
        st.floats().map(str),
        st.just('true'),
        st.just('false'),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28)).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
        st.recursive(lambda: st.lists(value()), max_leaves=5).map(lambda arr: f"[{', '.join(arr)}]"),
        st.recursive(lambda: st.dictionaries(key(), value()), max_leaves=5).map(lambda d: "{" + ", ".join(f"{k}={v}" for k, v in d.items()) + "}")
    ))

@composite
def pair(draw):
    k = draw(key())
    v = draw(value())
    return f"{k} = {v}"

@composite
def table(draw):
    return f"[{draw(key())}]"

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table()), min_size=1, max_size=10))
    return "\n".join(elements)

toml_strategy = st.one_of(
    document(),
    st.recursive(lambda: st.lists(value()), max_leaves=5).map(lambda arr: f"[{', '.join(arr)}]"),
    st.recursive(lambda: st.dictionaries(key(), value()), max_leaves=5).map(lambda d: "{" + ", ".join(f"{k}={v}" for k, v in d.items()) + "}")
)