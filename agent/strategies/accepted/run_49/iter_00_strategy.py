"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-09-03T13:43:18.682512+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Character sets defined without external imports
ASCII_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
UNQUOTED_KEY_CHARS = ASCII_LETTERS + DIGITS + "-_"
BASIC_STRING_SAFE = ASCII_LETTERS + DIGITS + " !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
LITERAL_STRING_SAFE = ASCII_LETTERS + DIGITS + ' "!#$%&()*+,-./:;<=>?@[\\]^_`{|}~'

# Primitives
unquoted_key_strat = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
quoted_basic_key_strat = st.text(alphabet=BASIC_STRING_SAFE, min_size=1, max_size=10).map(lambda x: f'"{x}"')
quoted_literal_key_strat = st.text(alphabet=LITERAL_STRING_SAFE, min_size=1, max_size=10).map(lambda x: f"'{x}'")

simple_key_strat = st.one_of(unquoted_key_strat, quoted_basic_key_strat, quoted_literal_key_strat)
dotted_key_strat = st.lists(simple_key_strat, min_size=2, max_size=4).map(lambda parts: ".".join(parts))
key_strat = st.one_of(simple_key_strat, dotted_key_strat)

scalar_val_strat = st.one_of(
    # Strings
    st.text(alphabet=BASIC_STRING_SAFE, min_size=0, max_size=15).map(lambda x: f'"{x}"'),
    st.text(alphabet=LITERAL_STRING_SAFE, min_size=0, max_size=15).map(lambda x: f"'{x}'"),
    st.text(alphabet=BASIC_STRING_SAFE + "\n", min_size=0, max_size=20).map(lambda x: f'"""{x}"""'),
    st.text(alphabet=LITERAL_STRING_SAFE + "\n", min_size=0, max_size=20).map(lambda x: f"'''{x}'''"),
    st.text(alphabet=ASCII_LETTERS + DIGITS + " ", min_size=1, max_size=5).map(lambda s: f'"esc\\n\\t\\"{s}\\""'),
    # Integers (including extreme/overflow values and leading zeros)
    st.integers(-9223372036854775808, 9223372036854775807).map(str),
    st.sampled_from(["9223372036854775808", "-9223372036854775809", "18446744073709551615"]),
    st.sampled_from(["007", "0123", "00001"]),
    st.integers(0, 65535).map(lambda x: f"0x{x:x}"),
    st.integers(0, 511).map(lambda x: f"0o{x:o}"),
    st.integers(0, 255).map(lambda x: f"0b{x:b}"),
    # Floats & Inf/NaN
    st.floats(allow_nan=False, allow_infinity=False).map(str),
    st.sampled_from(["inf", "-inf", "nan", "+nan", "+inf", "1e10", "1.5e-3"]),
    # Booleans
    st.sampled_from(["true", "false"]),
    # Dates/Times (including Divergence #2: over-long fractional seconds)
    st.tuples(st.integers(1970, 2099), st.integers(1, 12), st.integers(1, 28)).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
    ),
    st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(
        lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"
    ),
    st.just("1979-05-27T00:32:00.9999999999999999999Z"),
)

@composite
def value_gen(draw, depth=0):
    if depth >= 2:
        return draw(scalar_val_strat)
    return draw(st.one_of(
        scalar_val_strat,
        array_gen(depth=depth + 1),
        inline_table_gen(depth=depth + 1)
    ))

@composite
def array_gen(draw, depth=0):
    elems = draw(st.lists(value_gen(depth=depth + 1), min_size=0, max_size=4))
    trailing = draw(st.sampled_from(["", ","])) if elems else ""
    return f"[{', '.join(elems)}{trailing}]"

@composite
def inline_table_gen(draw, depth=0):
    keys = draw(st.lists(key_strat, min_size=0, max_size=3))
    pairs = [f"{k} = {draw(value_gen(depth=depth + 1))}" for k in keys]
    # Divergence #1: test trailing comma in inline tables
    trailing = draw(st.sampled_from(["", ","])) if pairs else ""
    return f"{{{', '.join(pairs)}{trailing}}}"

@composite
def pair_line_gen(draw):
    k = draw(key_strat)
    v = draw(value_gen())
    comment = draw(st.sampled_from(["", " # comment"]))
    return f"{k} = {v}{comment}"

@composite
def table_header_gen(draw):
    k = draw(key_strat)
    is_array = draw(st.booleans())
    return f"[[{k}]]" if is_array else f"[{k}]"

@composite
def standard_document_gen(draw):
    lines = draw(st.lists(st.one_of(pair_line_gen(), table_header_gen()), min_size=1, max_size=12))
    return "\n".join(lines)

# Direct construction for extreme-depth and high-sibling stress cases
@composite
def deep_array_document_gen(draw):
    depth = draw(st.integers(1000, 3000))
    val = draw(scalar_val_strat)
    open_b = "[" * depth
    close_b = "]" * depth
    return f"deep_arr = {open_b}{val}{close_b}"

@composite
def deep_inline_table_document_gen(draw):
    depth = draw(st.integers(500, 1500))
    val = draw(scalar_val_strat)
    prefix = "".join([f"k{i} = {{" for i in range(depth)])
    suffix = "}" * depth
    return f"deep_tbl = {prefix}{val}{suffix}"

@composite
def many_siblings_document_gen(draw):
    count = draw(st.integers(200, 500))
    lines = [f"key_{i} = {i}" for i in range(count)]
    return "\n".join(lines)

# Combine strategies ensuring deep/sibling stress cases stay a minority
toml_strategy = st.one_of(
    *([standard_document_gen()] * 17),
    deep_array_document_gen(),
    deep_inline_table_document_gen(),
    many_siblings_document_gen()
)