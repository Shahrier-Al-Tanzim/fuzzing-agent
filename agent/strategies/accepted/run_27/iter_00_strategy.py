"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-08-20T17:18:28.871160+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
QUOTED_BASIC_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _!#$%&'()*+,-./:;<=>?@[]^{|}~"
)
QUOTED_LITERAL_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \"_!#$%&()*+,-./:;<=>?@[]^{|}~"
)

# --- Keys ---

unquoted_key = st.text(alphabet=UNQUOTED, min_size=1, max_size=10)
basic_quoted_key = st.text(alphabet=QUOTED_BASIC_CHARS, min_size=0, max_size=10).map(
    lambda s: f'"{s}"'
)
literal_quoted_key = st.text(alphabet=QUOTED_LITERAL_CHARS, min_size=0, max_size=10).map(
    lambda s: f"'{s}'"
)

simple_key = st.one_of(unquoted_key, basic_quoted_key, literal_quoted_key)

dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(lambda parts: ".".join(parts))

key = st.one_of(simple_key, dotted_key)


# --- Scalars ---

integers = st.one_of(
    st.integers(-1000, 1000).map(str),
    st.just("0"),
    st.just("-0"),
    st.just("9223372036854775807"),  # INT64_MAX
    st.just("9223372036854775808"),  # INT64_MAX + 1 (Divergence #3)
    st.just("-9223372036854775808"),  # INT64_MIN
    st.just("-9223372036854775809"),  # INT64_MIN - 1
    st.just("18446744073709551615"),
    st.integers(1, 999).map(lambda i: f"0{i:02d}"),  # Leading zeros (Divergence #4)
    st.integers(0, 0xFFFF).map(lambda i: f"0x{i:x}"),
    st.integers(0, 0o777).map(lambda i: f"0o{i:o}"),
    st.integers(0, 0b1111).map(lambda i: f"0b{i:b}"),
    st.just("1_000_000"),
)

floats = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.just("inf"),
    st.just("-inf"),
    st.just("nan"),
    st.just("+nan"),
    st.just("1e6"),
    st.just("-2E-3"),
    st.just("3.14159e+10"),
    st.just("1_000.000_1"),
)

strings = st.one_of(
    basic_quoted_key,
    literal_quoted_key,
    st.text(alphabet=QUOTED_BASIC_CHARS, max_size=10).map(lambda s: f'"""{s}"""'),
    st.text(alphabet=QUOTED_LITERAL_CHARS, max_size=10).map(lambda s: f"'''{s}'''"),
    st.just('"hello\\nworld"'),
    st.just('"foo\\tbar"'),
    st.just('"\\u0041\\u0042"'),
    st.just('"\\U0001F600"'),
    st.just('"invalid\\xescape"'),
)

booleans = st.one_of(st.just("true"), st.just("false"))

dates_and_times = st.one_of(
    st.tuples(st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28)).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
    ),
    st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(
        lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"
    ),
    st.tuples(
        st.integers(1970, 2030),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"),
    st.just(
        "1979-05-27T00:32:00.9999999999999999999-07:00"
    ),  # Over-long frac seconds (Divergence #2)
)

scalars = st.one_of(integers, floats, strings, booleans, dates_and_times)


# --- Recursive Values (Arrays and Inline Tables) ---


@composite
def array_val(draw, child_strat):
    elems = draw(st.lists(child_strat, max_size=4))
    trailing = draw(st.booleans())
    if elems and trailing:
        return f"[{', '.join(elems)},]"
    return f"[{', '.join(elems)}]"


@composite
def inline_table_val(draw, child_strat):
    pairs = draw(st.lists(st.tuples(simple_key, child_strat), max_size=3))
    pair_strs = [f"{k} = {v}" for k, v in pairs]
    # Divergence #1: Trailing comma in inline table
    trailing = draw(st.booleans())
    if pair_strs and trailing:
        return "{" + ", ".join(pair_strs) + ",}"
    return "{" + ", ".join(pair_strs) + "}"


value_strategy = st.recursive(
    scalars,
    lambda children: st.one_of(
        array_val(children),
        inline_table_val(children),
    ),
    max_leaves=12,
)


# --- Document Structure ---


@composite
def pair_line(draw, val_strat=None):
    k = draw(key)
    v = draw(val_strat if val_strat is not None else value_strategy)
    comment = draw(st.one_of(st.just(""), st.just(" # comment")))
    return f"{k} = {v}{comment}"


@composite
def standard_table_header(draw):
    k = draw(key)
    comment = draw(st.one_of(st.just(""), st.just(" # comment")))
    return f"[{k}]{comment}"


@composite
def array_table_header(draw):
    k = draw(key)
    comment = draw(st.one_of(st.just(""), st.just(" # comment")))
    return f"[[{k}]]{comment}"


@composite
def document(draw):
    line_strat = st.one_of(
        pair_line(),
        pair_line(),
        pair_line(),
        standard_table_header(),
        array_table_header(),
        st.just("# comment line"),
        st.just(""),
    )
    lines = draw(st.lists(line_strat, min_size=0, max_size=12))
    return "\n".join(lines)


# --- Extreme Nesting Shapes (Rule 16) ---


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
def deep_val_doc(draw, deep_strat):
    v = draw(deep_strat)
    return f"k = {v}"


@composite
def deep_key_doc(draw, deep_key_strat):
    k = draw(deep_key_strat)
    return f"{k} = 1"


# --- Many Siblings Strategy (Rule 17) ---


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


# --- Final Strategy Composition ---

toml_strategy = st.one_of(
    *([document()] * 25),
    deep_val_doc(deep_array()),
    deep_val_doc(deep_inline_table()),
    deep_key_doc(deep_dotted_key()),
    deep_val_doc(deep_mixed_nesting()),
    deep_val_doc(deep_quoted_mixed()),
    many_siblings(),
)