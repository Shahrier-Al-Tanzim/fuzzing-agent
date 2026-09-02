"""Generated strategy - iteration 2, attempt 1.
accepted: True
generated: 2026-09-01T19:29:00.366471+00:00
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
basic_quoted_key = st.text(alphabet=SAFE_CHAR, min_size=1, max_size=8).map(
    lambda s: f'"{s}"'
)
literal_quoted_key = st.text(alphabet=SAFE_CHAR, min_size=1, max_size=8).map(
    lambda s: f"'{s}'"
)

simple_key = st.one_of(unquoted_key, basic_quoted_key, literal_quoted_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=3).map(
    lambda parts: ".".join(parts)
)
key_strat = st.one_of(simple_key, dotted_key)

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

# Strings (including ML_BASIC_STRING, ML_LITERAL_STRING, escapes, unicode)
strings_strat = st.one_of(
    st.text(alphabet=SAFE_CHAR, min_size=0, max_size=10).map(
        lambda s: f'"{s}"'
    ),
    st.text(alphabet=SAFE_CHAR, min_size=0, max_size=10).map(
        lambda s: f"'{s}'"
    ),
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
    st.sampled_from(
        [
            '"""\nfirst line\nsecond line\n"""',
            '"""hello "world" """',
            '"""escaped \\\nnewline"""',
            '"""line1\nline2\nline3"""',
        ]
    ),
    st.sampled_from(
        [
            "'''\nfirst line\nsecond line\n'''",
            "'''C:\\Users\\name'''",
            "'''line1\nline2'''",
        ]
    ),
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

# Recursive structure for values with enhanced formatting options
value_strat = st.recursive(
    scalar_val,
    lambda children: st.one_of(
        # Inline single-line array
        st.lists(children, max_size=4).map(lambda lst: f"[{', '.join(lst)}]"),
        # Multiline array with newlines and trailing comma
        st.lists(children, max_size=4).map(
            lambda lst: "[\n  " + ",\n  ".join(lst) + ("\n" if lst else "") + "]"
        ),
        st.just("[]"),
        # Inline table
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
    lines = []

    # Top-level comments
    if draw(st.booleans()):
        lines.append("# Top-level comment")

    # Top-level pairs with structural diversity (simple, quoted, dotted keys)
    num_pairs = draw(st.integers(min_value=1, max_value=5))
    for _ in range(num_pairs):
        k = draw(key_strat)
        v = draw(value_strat)
        comment = (
            f" # comment" if draw(st.booleans()) else ""
        )
        lines.append(f"{k} = {v}{comment}")

    # Section tables (standard tables and array tables)
    num_sections = draw(st.integers(min_value=1, max_value=4))
    for _ in range(num_sections):
        lines.append("")
        if draw(st.booleans()):
            lines.append("# Section header comment")

        is_array_table = draw(st.booleans())
        header_key = draw(key_strat)

        if is_array_table:
            lines.append(f"[[{header_key}]]")
            # Optionally draw multiple array table elements
            if draw(st.booleans()):
                num_sec_pairs = draw(st.integers(min_value=1, max_value=3))
                for _ in range(num_sec_pairs):
                    k = draw(simple_key)
                    v = draw(value_strat)
                    lines.append(f"{k} = {v}")
                lines.append(f"\n[[{header_key}]]")
        else:
            lines.append(f"[{header_key}]")

        num_sec_pairs = draw(st.integers(min_value=0, max_value=4))
        for _ in range(num_sec_pairs):
            k = draw(key_strat)
            v = draw(value_strat)
            comment = (
                f" # inline comment" if draw(st.booleans()) else ""
            )
            lines.append(f"{k} = {v}{comment}")

    return "\n".join(lines)


# Deep recursion strategies for stack overflow fuzzing
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


# Linear search slowdown / timeout fuzzing
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