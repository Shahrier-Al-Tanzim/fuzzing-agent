"""Generated strategy - iteration 0, attempt 1.
accepted: False
generated: 2026-09-01T18:40:40.853104+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_STR_CHARS = " !#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~"
LITERAL_STR_CHARS = " !\"#$%&()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

unquoted_key = st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=10)
basic_key = st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=10).map(lambda x: f'"{x}"')
literal_key = st.text(alphabet=LITERAL_STR_CHARS, min_size=1, max_size=10).map(lambda x: f"'{x}'")
simple_key = st.one_of(unquoted_key, basic_key, literal_key)

dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(lambda parts: ".".join(parts))
any_key = st.one_of(simple_key, dotted_key)

int_str = st.one_of(
    st.integers(-1000, 1000).map(str),
    st.sampled_from([
        "0", "-0", "007", "000123", "1_000_000",
        "9223372036854775807", "-9223372036854775808",
        "9223372036854775808", "-9223372036854775809"
    ]),
    st.integers(0, 65535).map(lambda x: f"0x{x:x}"),
    st.integers(0, 511).map(lambda x: f"0o{x:o}"),
    st.integers(0, 255).map(lambda x: f"0b{x:b}")
)

float_str = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from(["inf", "+inf", "-inf", "nan", "+nan", "-nan", "0.0", "-0.0", "1e10", "1.5e-5", "1_000.000_1"])
)

bool_str = st.sampled_from(["true", "false"])

str_str = st.one_of(
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(lambda x: f'"{x}"'),
    st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=15).map(lambda x: f"'{x}'"),
    st.text(alphabet=BASIC_STR_CHARS + "\n\r", min_size=0, max_size=15).map(lambda x: f'"""{x}"""'),
    st.text(alphabet=BASIC_STR_CHARS + "\n\r\\", min_size=0, max_size=15).map(lambda x: f"'''{x}'''"),
    st.sampled_from([
        '"hello\\nworld"', '"escaped \\" quote"', '"tab \\t here"',
        '"unicode \\u0041"', '"ex \\U00000041"', '"invalid \\z escape"'
    ])
)

date_time_str = st.one_of(
    st.tuples(st.integers(1970, 2038), st.integers(1, 12), st.integers(1, 28))
    .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
    st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
    .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
    st.tuples(st.integers(1970, 2038), st.integers(1, 12), st.integers(1, 28), st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
    .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"),
    st.just("1979-05-27T00:32:00.9999999999999999999-07:00")
)

scalar_value = st.one_of(int_str, float_str, bool_str, str_str, date_time_str)

@composite
def toml_array(draw, element_st):
    elems = draw(st.lists(element_st, min_size=0, max_size=5))
    trailing = draw(st.sampled_from(["", ","])) if elems else ""
    return f"[{', '.join(elems)}{trailing}]"

@composite
def toml_inline_table(draw, key_st, val_st):
    pairs = draw(st.lists(st.tuples(key_st, val_st), min_size=0, max_size=4))
    pair_strs = [f"{k} = {v}" for k, v in pairs]
    trailing = draw(st.sampled_from(["", ","])) if pairs else ""
    return f"{{{', '.join(pair_strs)}{trailing}}}"

def recursive_value_builder(base):
    return st.one_of(
        toml_array(base),
        toml_inline_table(simple_key, base)
    )

value_strategy = st.recursive(scalar_value, recursive_value_builder, max_leaves=15)

@composite
def key_value_pair(draw, val_st=value_strategy):
    k = draw(any_key)
    v = draw(val_st)
    comment = draw(st.sampled_from(["", " # comment"]))
    return f"{k} = {v}{comment}"

@composite
def table_header(draw):
    k = draw(any_key)
    comment = draw(st.sampled_from(["", " # comment"]))
    return f"[{k}]{comment}"

@composite
def array_table_header(draw):
    k = draw(any_key)
    comment = draw(st.sampled_from(["", " # comment"]))
    return f"[[{k}]]{comment}"

@composite
def document(draw):
    items = draw(st.lists(
        st.one_of(
            key_value_pair(),
            table_header(),
            array_table_header(),
            st.sampled_from(["", "# comment line"])
        ),
        min_size=0,
        max_size=12
    ))
    return "\n".join(items)

@composite
def deep_array(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    return "[" * n + "1" + "]" * n

@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    return "{a=" * n + "1" + "}" * n

@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    return "a." * n + "k"

@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return "[{a=" * n + "1" + "}]" * n

@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    return '[{"k"=' * n + "1" + "}]" * n

@composite
def deep_doc_val(draw, deep_strat):
    v = draw(deep_strat)
    return f"deep = {v}"

@composite
def deep_doc_key(draw):
    k = draw(deep_dotted_key())
    return f"{k} = 1"

@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)

toml_strategy = st.one_of(
    *([document()] * 20),
    deep_doc_val(deep_array()),
    deep_doc_val(deep_inline_table()),
    deep_doc_key(),
    deep_doc_val(deep_mixed_nesting()),
    deep_doc_val(deep_quoted_mixed()),
    many_siblings()
)