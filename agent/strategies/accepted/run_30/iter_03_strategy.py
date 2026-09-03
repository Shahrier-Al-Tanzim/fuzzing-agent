"""Generated strategy - iteration 3, attempt 2.
accepted: True
generated: 2026-08-21T12:04:06.904478+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_BASIC_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
SAFE_LITERAL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !\"#$%&()*+,-./:;<=>?@[\\]^_`{|}~"

valid_escapes = st.sampled_from([
    "\\\\", "\\\"", "\\b", "\\f", "\\n", "\\r", "\\t",
    "\\u0041", "\\u4e2d", "\\U0001f600"
])

valid_basic_string = st.tuples(
    st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=5),
    st.one_of(st.just(""), valid_escapes),
    st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=5)
).map(lambda t: f'"{t[0]}{t[1]}{t[2]}"')

valid_literal_string = st.text(alphabet=SAFE_LITERAL_CHARS, min_size=0, max_size=10).map(
    lambda s: f"'{s}'"
)

valid_ml_basic = st.text(alphabet=SAFE_BASIC_CHARS + " \t\n", min_size=0, max_size=15).map(
    lambda s: f'"""{s}"""'
)
valid_ml_literal = st.text(alphabet=SAFE_LITERAL_CHARS + " \t\n", min_size=0, max_size=15).map(
    lambda s: f"'''{s}'''"
)

date_str = st.tuples(st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28)).map(
    lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
)
time_str = st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(
    lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"
)
datetime_str = st.tuples(
    date_str, time_str, st.sampled_from(["Z", "+00:00", "-05:00", ".9999999999999999999Z"])
).map(lambda t: f"{t[0]}T{t[1]}{t[2]}")

scalar_values = st.one_of(
    st.integers(-9223372036854775808, 9223372036854775807).map(str),
    st.sampled_from([
        "9223372036854775808", "-9223372036854775809", "18446744073709551615",
        "007", "000123", "0x123abc", "0o755", "0b1010", "0x7fffffffffffffff",
        "1_000_000", "0x12_ab"
    ]),
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from(["inf", "-inf", "+inf", "nan", "-nan", "+nan", "0.0", "-0.0", "1e100", "1.5e-10"]),
    st.sampled_from(["true", "false"]),
    valid_basic_string,
    valid_literal_string,
    valid_ml_basic,
    valid_ml_literal,
    date_str,
    time_str,
    datetime_str,
)

@composite
def array_val(draw, depth=0):
    if depth > 2:
        return "[]"
    elems = draw(st.lists(
        st.one_of(
            scalar_values,
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1)
        ),
        max_size=3
    ))
    trailing = draw(st.sampled_from(["", ","]))
    return "[" + ", ".join(elems) + trailing + "]"

@composite
def inline_table_val(draw, depth=0):
    if depth > 2:
        return "{}"
    keys = ["a", "b", "c", "d"]
    n = draw(st.integers(0, 3))
    pairs = []
    for i in range(n):
        v = draw(st.one_of(
            scalar_values,
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1)
        ))
        pairs.append(f"{keys[i]} = {v}")
    trailing = draw(st.sampled_from(["", ","]))
    return "{" + ", ".join(pairs) + trailing + "}"

@composite
def value_gen(draw, depth=0):
    return draw(st.one_of(
        scalar_values,
        array_val(depth=depth),
        inline_table_val(depth=depth)
    ))

@composite
def standard_document(draw):
    num_lines = draw(st.integers(1, 10))
    lines = []
    for i in range(num_lines):
        line_type = draw(st.sampled_from(["pair", "pair", "pair", "table", "comment"]))
        if line_type == "comment":
            lines.append(f"# comment line {i}")
        elif line_type == "table":
            sec_name = f"sec_{i}"
            is_arr = draw(st.booleans())
            if is_arr:
                lines.append(f"[[{sec_name}]]")
            else:
                lines.append(f"[{sec_name}]")
        else:
            k = f"k_{i}"
            v = draw(value_gen(depth=0))
            comment = draw(st.sampled_from(["", " # comment", " # \u4e2d\u6587"]))
            lines.append(f"{k} = {v}{comment}")
    return "\n".join(lines)

@composite
def mega_deep_array_doc(draw):
    n = draw(st.integers(min_value=1000000, max_value=1500000))
    return f"k = " + ("[" * n) + "1" + ("]" * n)

@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=200000, max_value=800000))
    return f"k = " + ("{a=" * n) + "1" + ("}" * n)

@composite
def deep_array_inline_table_doc(draw):
    n = draw(st.integers(min_value=100000, max_value=400000))
    return f"k = " + ("[{a=" * n) + "1" + ("}]" * n)

@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=10000, max_value=50000))
    dotted = "a." * n + "b"
    return f"[{dotted}]\nx = 1"

@composite
def wide_inline_table_doc(draw):
    n = draw(st.integers(min_value=100, max_value=1000))
    items = ", ".join(f"k{i}={i}" for i in range(n))
    return f"k = {{{items},}}"

@composite
def wide_doc(draw):
    n = draw(st.integers(min_value=100, max_value=1000))
    lines = [f"k{i} = {i}" for i in range(n)]
    return "\n".join(lines)

@composite
def escape_transform_doc(draw):
    n = draw(st.integers(min_value=1000, max_value=10000))
    s = "\\u0041\\n\\t\\\\\\\"\\b\\f\\r" * n
    return f'k = "{s}"'

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

standard_branches = [standard_document() for _ in range(25)]
stress_branches = [
    mega_deep_array_doc(),
    deep_inline_table_doc(),
    deep_array_inline_table_doc(),
    deep_dotted_key_doc(),
    wide_inline_table_doc(),
    wide_doc(),
    escape_transform_doc(),
    divergence_doc()
]

toml_strategy = st.one_of(*(standard_branches + stress_branches))