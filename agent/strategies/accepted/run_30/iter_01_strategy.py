"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-08-21T11:50:44.785013+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
NON_ASCII_CHARS = "äöüßéèàáñÅæø©®™µΔπΩ€£¥ÿœαβγδεçðø§¿¡🚀"
BASIC_STRING_SAFE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
BASIC_STRING_CHARS = BASIC_STRING_SAFE_CHARS + NON_ASCII_CHARS

LITERAL_STRING_SAFE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !\"#$%&()*+,-./:;<=>?@[\\]^_`{|}~"
LITERAL_STRING_CHARS = LITERAL_STRING_SAFE_CHARS + NON_ASCII_CHARS

simple_unquoted_key = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
simple_basic_key = st.text(alphabet=BASIC_STRING_CHARS, min_size=1, max_size=10).map(lambda s: f'"{s}"')
simple_literal_key = st.text(alphabet=LITERAL_STRING_CHARS, min_size=0, max_size=10).map(lambda s: f"'{s}'")

simple_key = st.one_of(simple_unquoted_key, simple_basic_key, simple_literal_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(lambda parts: ".".join(parts))
key_strat = st.one_of(simple_key, dotted_key)

scalar_values = st.one_of(
    st.integers().map(str),
    st.sampled_from([
        "9223372036854775807", "-9223372036854775808", "9223372036854775808",
        "-9223372036854775809", "007", "000123", "0x123abc", "0o755", "0b1010",
        "1_000_000", "0x12_ab", "0o7_55", "0b1_01"
    ]),
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from([
        "inf", "-inf", "+inf", "nan", "-nan", "+nan",
        "0.0", "-0.0", "1e100", "1.5e-10", "1_000.000_1"
    ]),
    st.sampled_from(["true", "false"]),
    st.sampled_from(["{}", "{ }"]),
    st.sampled_from(["[]", "[ ]"]),
    st.text(alphabet=BASIC_STRING_CHARS, min_size=0, max_size=15).map(lambda s: f'"{s}"'),
    st.tuples(
        st.text(alphabet=BASIC_STRING_CHARS, min_size=0, max_size=5),
        st.sampled_from(["\\\\", "\\\"", "\\b", "\\f", "\\n", "\\r", "\\t", "\\u0041", "\\u4e2d", "\\U0001f600", "\\z"]),
        st.text(alphabet=BASIC_STRING_CHARS, min_size=0, max_size=5)
    ).map(lambda t: f'"{t[0]}{t[1]}{t[2]}"'),
    st.text(alphabet=LITERAL_STRING_CHARS, min_size=0, max_size=15).map(lambda s: f"'{s}'"),
    st.text(alphabet=BASIC_STRING_CHARS + "\n", min_size=0, max_size=20).map(lambda s: f'"""{s}"""'),
    st.text(alphabet=LITERAL_STRING_CHARS + "\n", min_size=0, max_size=20).map(lambda s: f"'''{s}'''"),
    st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28)).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
    ),
    st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(
        lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"
    ),
    st.tuples(
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59),
        st.sampled_from(["999999", "9999999999999999999", "123456789"])
    ).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}.{t[3]}"),
    st.tuples(
        st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59),
        st.sampled_from(["Z", "+00:00", "-05:00", "+02:30"])
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}{t[6]}"),
    st.tuples(
        st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28),
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59),
        st.sampled_from(["9999999999999999999", "1234567890123456789"])
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]}Z")
)

@composite
def value_gen(draw, depth=0):
    if depth > 3:
        return draw(scalar_values)
    return draw(st.one_of(
        scalar_values,
        array_gen(depth=depth + 1),
        inline_table_gen(depth=depth + 1)
    ))

@composite
def array_gen(draw, depth=0):
    if depth > 3:
        return "[]"
    elements = draw(st.lists(value_gen(depth=depth + 1), max_size=4))
    trailing = draw(st.sampled_from(["", ","]))
    return "[" + ", ".join(elements) + trailing + "]"

@composite
def inline_table_gen(draw, depth=0):
    if depth > 3:
        return "{}"
    pairs = draw(st.lists(
        st.tuples(simple_key, value_gen(depth=depth + 1)).map(lambda p: f"{p[0]} = {p[1]}"),
        max_size=4
    ))
    trailing = draw(st.sampled_from(["", ","]))
    return "{" + ", ".join(pairs) + trailing + "}"

@composite
def key_value_pair(draw, depth=0):
    k = draw(key_strat)
    v = draw(value_gen(depth=depth))
    comment = draw(st.sampled_from(["", " # comment", " # trailing comment non-ascii äöü", " # \u4e2d\u6587 comment"]))
    return f"{k} = {v}{comment}"

@composite
def table_header(draw):
    k = draw(key_strat)
    is_array_table = draw(st.booleans())
    comment = draw(st.sampled_from(["", " # table comment", " # table äöü"]))
    if is_array_table:
        return f"[[{k}]]{comment}"
    return f"[{k}]{comment}"

@composite
def standard_document(draw):
    lines = draw(st.lists(
        st.one_of(
            key_value_pair(),
            table_header(),
            st.sampled_from(["# full line comment", "# comment non-ascii äöü", ""])
        ),
        min_size=1,
        max_size=15
    ))
    return "\n".join(lines)

@composite
def deep_array_doc(draw):
    k = draw(key_strat)
    n = draw(st.integers(min_value=50000, max_value=220000))
    return f"{k} = " + ("[" * n) + "1" + ("]" * n)

@composite
def deep_inline_table_doc(draw):
    k = draw(key_strat)
    n = draw(st.integers(min_value=50000, max_value=220000))
    return f"{k} = " + ("{a=" * n) + "1" + ("}" * n)

@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=5000, max_value=50000))
    dotted = "a." * n + "b"
    return f"[{dotted}]\nx = 1"

@composite
def deep_nested_string_escapes_doc(draw):
    k = draw(key_strat)
    n = draw(st.integers(min_value=1000, max_value=20000))
    return f"{k} = " + ("{a=" * n) + '"\\u4e2d\\n\\t\\\\" ' + ("}" * n)

@composite
def deep_array_of_inline_tables_doc(draw):
    k = draw(key_strat)
    n = draw(st.integers(min_value=10000, max_value=100000))
    return f"{k} = " + ("[{a=" * n) + "1" + ("}]" * n)

@composite
def huge_string_doc(draw):
    k = draw(key_strat)
    n = draw(st.integers(min_value=10000, max_value=50000))
    s = "a\\n\\t\\u0041\\u4e2d" * n
    return f'{k} = "{s}"'

@composite
def wide_inline_table_doc(draw):
    k = draw(key_strat)
    n = draw(st.integers(min_value=100, max_value=2000))
    items = ", ".join(f"k{i}={i}" for i in range(n))
    return f"{k} = {{{items},}}"

@composite
def wide_doc(draw):
    n = draw(st.integers(min_value=100, max_value=2000))
    lines = [f"k{i} = {i}" for i in range(n)]
    return "\n".join(lines)

@composite
def duplicate_keys_doc(draw):
    k = draw(key_strat)
    v1 = draw(scalar_values)
    v2 = draw(scalar_values)
    return f"{k} = {v1}\n{k} = {v2}\n"

@composite
def divergence_doc(draw):
    div_type = draw(st.integers(1, 5))
    if div_type == 1:
        return "x = { a = 1, b = 2, }"
    elif div_type == 2:
        return "x = 1979-05-27T00:32:00.9999999999999999999-07:00"
    elif div_type == 3:
        return "x = 9223372036854775808"
    elif div_type == 4:
        return "x = 007"
    else:
        return "x = { a = 007, b = 9223372036854775808, c = 1979-05-27T00:32:00.9999999999999999999Z, }"

@composite
def near_valid_doc(draw):
    k = draw(key_strat)
    v = draw(scalar_values)
    choice = draw(st.integers(1, 6))
    if choice == 1:
        return f"{k} {v}"
    elif choice == 2:
        return f"{k} = [{v}"
    elif choice == 3:
        return f'{k} = "{v}'
    elif choice == 4:
        return f"{k} = {{\n{k} = {v}\n}}"
    elif choice == 5:
        return f"[{k}\nx = 1"
    else:
        return f"{k} = = {v}"

standard_docs = [standard_document() for _ in range(30)]
special_docs = [
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_nested_string_escapes_doc(),
    deep_array_of_inline_tables_doc(),
    huge_string_doc(),
    wide_inline_table_doc(),
    wide_doc(),
    duplicate_keys_doc(),
    divergence_doc(),
    near_valid_doc()
]

toml_strategy = st.one_of(*(standard_docs + special_docs))