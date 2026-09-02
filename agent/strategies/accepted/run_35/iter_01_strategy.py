"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-09-01T19:21:42.512638+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Safe alphabets
UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
SAFE_CHAR = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "

# Key strategies
unquoted_key = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8)
basic_quoted_key = st.text(
    alphabet=SAFE_CHAR, min_size=1, max_size=8
).map(lambda s: f'"{s}"')
literal_quoted_key = st.text(
    alphabet=SAFE_CHAR, min_size=1, max_size=8
).map(lambda s: f"'{s}'")

simple_key = st.one_of(unquoted_key, basic_quoted_key, literal_quoted_key)

# Integers (including Divergence #3 and #4)
integers_strat = st.one_of(
    st.integers(
        min_value=-9223372036854775808, max_value=9223372036854775807
    ).map(str),
    st.integers(0, 0xFFFFFFFF).map(lambda v: f"0x{v:x}"),  # HEX_INT
    st.integers(0, 0o7777).map(lambda v: f"0o{v:o}"),  # OCT_INT
    st.integers(0, 255).map(lambda v: f"0b{v:b}"),  # BIN_INT
    st.sampled_from(
        [
            "0",
            "-0",
            "9223372036854775808",  # Integer overflow past INT64_MAX
            "-9223372036854775809",
            "007",  # Leading zero integer
            "0123",
            "1_000_000",
            "0xDEADBEEF",
            "0b1101_0010",
        ]
    ),
)

# Floats (including FLOAT_EXP and INF)
floats_strat = st.one_of(
    st.floats(
        min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False
    ).map(str),
    st.sampled_from(
        [
            "inf",
            "-inf",
            "+inf",  # INF
            "nan",
            "-nan",
            "+nan",
            "1.0e-10",  # FLOAT_EXP
            "1.0E+10",
            "1e5",
            "1.5e-3",
            "1_000.000_1",
        ]
    ),
)

bools_strat = st.sampled_from(["true", "false"])

# Dates and Times (including Divergence #2)
dates_times_strat = st.one_of(
    st.tuples(
        st.integers(1970, 2038), st.integers(1, 12), st.integers(1, 28)
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
    st.tuples(
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
    ).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
    st.tuples(
        st.integers(1970, 2038),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
    ),
    st.sampled_from(
        [
            "1979-05-27T00:32:00.9999999999999999999Z",  # Over-long frac seconds
            "2020-01-01T12:00:00.123456789+02:00",
        ]
    ),
)

# Strings (including ML_BASIC_STRING, ML_LITERAL_STRING, escape_sequence, unicode_escape, non_ascii)
strings_strat = st.one_of(
    st.text(alphabet=SAFE_CHAR, min_size=0, max_size=10).map(
        lambda s: f'"{s}"'
    ),
    st.text(alphabet=SAFE_CHAR, min_size=0, max_size=10).map(
        lambda s: f"'{s}'"
    ),
    # escape_sequence & unicode_escape
    st.sampled_from(
        [
            '"hello\\nworld"',
            '"tab\\ttest"',
            '"quote\\""',
            '"slash\\\\"',
            '"backspace\\b space"',
            '"formfeed\\f feed"',
            '"\\u0000"',
            '"\\u0041"',
            '"\\u00e9"',
            '"\\U0001F600"',
            '"line1\\r\\nline2"',
        ]
    ),
    # ML_BASIC_STRING
    st.sampled_from(
        [
            '"""\nfirst line\nsecond line\n"""',
            '"""hello "world" """',
            '"""escaped \\\nnewline"""',
            '"""line1\nline2\nline3"""',
        ]
    ),
    # ML_LITERAL_STRING
    st.sampled_from(
        [
            "'''\nfirst line\nsecond line\n'''",
            "'''C:\\Users\\name'''",
            "'''line1\nline2'''",
        ]
    ),
    # non_ascii
    st.sampled_from(
        [
            '"café"',
            '"ñ"',
            '"日本語"',
            '"🚀"',
            "'élégant'",
            '"""utf8: 🐍"""',
            "'''utf8: 漢字'''",
        ]
    ),
)

scalar_val = st.one_of(
    integers_strat, floats_strat, bools_strat, dates_times_strat, strings_strat
)

# Recursive structure for values (Arrays and Inline Tables with unique keys)
value_strat = st.recursive(
    scalar_val,
    lambda children: st.one_of(
        st.lists(children, max_size=4).map(lambda lst: f"[{', '.join(lst)}]"),
        st.just("[]"),
        st.lists(
            st.tuples(unquoted_key, children),
            max_size=4,
            unique_by=lambda x: x[0],
        ).map(
            lambda pairs: "{"
            + ", ".join(f"{k} = {v}" for k, v in pairs)
            + "}"
        ),
        st.just("{}"),
        # Trailing comma in inline table (Divergence #1)
        st.lists(
            st.tuples(unquoted_key, children),
            min_size=1,
            max_size=4,
            unique_by=lambda x: x[0],
        ).map(
            lambda pairs: "{"
            + ", ".join(f"{k} = {v}" for k, v in pairs)
            + ",}"
        ),
    ),
    max_leaves=10,
)


@composite
def standard_document(draw):
    num_sections = draw(st.integers(min_value=1, max_value=3))
    lines = []

    # Top-level pairs
    num_pairs = draw(st.integers(min_value=1, max_value=5))
    for i in range(num_pairs):
        k_type = draw(
            st.sampled_from(["simple", "quoted", "dotted", "non_ascii"])
        )
        if k_type == "simple":
            k = f"key_{i}"
        elif k_type == "quoted":
            k = f'"key {i}"'
        elif k_type == "dotted":
            k = f"top_{i}.sub"
        else:
            k = f'"key_café_{i}"'
        v = draw(value_strat)
        lines.append(f"{k} = {v}")

    # Section tables
    for s in range(1, num_sections):
        is_array_table = draw(st.booleans())
        table_name = f"section_{s}"
        if is_array_table:
            lines.append(f"\n[[{table_name}]]")
        else:
            lines.append(f"\n[{table_name}]")

        if draw(st.booleans()):
            lines.append(f"# Comment in section {s}")

        num_sec_pairs = draw(st.integers(min_value=1, max_value=4))
        for j in range(num_sec_pairs):
            k = f"sec_key_{j}"
            v = draw(value_strat)
            lines.append(f"{k} = {v}")

    return "\n".join(lines)


# Deep recursion strategies for stack overflow fuzzing (Rule 16)
@composite
def deep_array_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    p, s = "[" * n, "]" * n
    return f"k = {p}1{s}"


@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=85_000, max_value=105_000))
    p, s = "{a=" * n, "}" * n
    return f"k = {p}1{s}"


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=100_000, max_value=120_000))
    p = "a." * n
    return f"{p}k = 1"


@composite
def deep_mixed_nesting_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=75_000))
    p, s = "[{a=" * n, "}]" * n
    return f"k = {p}1{s}"


@composite
def deep_quoted_mixed_doc(draw):
    n = draw(st.integers(min_value=20_000, max_value=35_000))
    p = '[{"k"=' * n
    s = "}]" * n
    return f"k = {p}1{s}"


# Linear search slowdown / timeout fuzzing (Rule 17)
@composite
def many_siblings_doc(draw):
    n = draw(st.integers(min_value=15_000, max_value=30_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([standard_document()] * 25),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_mixed_nesting_doc(),
    deep_quoted_mixed_doc(),
    many_siblings_doc(),
)