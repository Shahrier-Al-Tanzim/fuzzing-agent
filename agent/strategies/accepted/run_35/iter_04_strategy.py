"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-09-01T19:40:36.894766+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Safe alphabets
UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
SAFE_CHAR = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "
SAFE_BASIC_INSIDE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ !#$%&'()*+,-./:;<=>?@[]^`{|}~"

# Keys
unquoted_key = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
basic_quoted_key = st.text(alphabet=SAFE_BASIC_INSIDE, min_size=1, max_size=10).map(
    lambda s: f'"{s}"'
)
literal_quoted_key = st.text(alphabet=SAFE_CHAR, min_size=1, max_size=10).map(
    lambda s: f"'{s}'"
)

simple_key = st.one_of(unquoted_key, basic_quoted_key, literal_quoted_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(
    lambda parts: ".".join(parts)
)
key_strat = st.one_of(simple_key, dotted_key)

# Extreme & standard integers (Divergence #3, #4)
integers_strat = st.one_of(
    st.integers(
        min_value=-9223372036854775808, max_value=9223372036854775807
    ).map(str),
    st.integers(0, 0xFFFFFFFF).map(lambda v: f"0x{v:x}"),
    st.integers(0, 0o777777).map(lambda v: f"0o{v:o}"),
    st.integers(0, 65535).map(lambda v: f"0b{v:b}"),
    st.sampled_from(
        [
            "0",
            "-0",
            "+0",
            "9223372036854775808",  # > INT64_MAX
            "-9223372036854775809",  # < INT64_MIN
            "18446744073709551615",
            "007",  # Leading zero
            "0123",
            "1_000_000",
            "0xDEADBEEF",
            "0xFFFFFFFFFFFFFFFF",
            "0b1101_0010",
            "0o777_666",
        ]
    ),
)

# Extreme & standard floats
floats_strat = st.one_of(
    st.floats(
        min_value=-1e15, max_value=1e15, allow_nan=False, allow_infinity=False
    ).map(str),
    st.sampled_from(
        [
            "inf",
            "-inf",
            "+inf",
            "nan",
            "-nan",
            "+nan",
            "1.0e-10",
            "1.0E+10",
            "1e5",
            "1.5e-3",
            "-2E-2",
            "1_000.000_1",
            "1e99999",
            "-1e99999",
            "0.0",
            "-0.0",
        ]
    ),
)

bools_strat = st.sampled_from(["true", "false"])

# Dates and Times (Divergence #2)
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
            "1979-05-27T00:32:00.9999999999999999999Z",  # 19 digits secfrac
            "2020-01-01T12:00:00.123456789+02:00",
            "1999-12-31 23:59:59.999999-05:00",
            "0000-01-01T00:00:00Z",
        ]
    ),
)

# Strings
strings_strat = st.one_of(
    st.text(alphabet=SAFE_BASIC_INSIDE, min_size=0, max_size=12).map(
        lambda s: f'"{s}"'
    ),
    st.text(alphabet=SAFE_CHAR, min_size=0, max_size=12).map(
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
            '""',
            "''",
        ]
    ),
    st.sampled_from(
        [
            '"""\nfirst line\nsecond line\n"""',
            '"""hello "world" """',
            '"""escaped \\\nnewline"""',
            '"""line1\nline2\nline3"""',
            '""" "" """',
        ]
    ),
    st.sampled_from(
        [
            "'''\nfirst line\nsecond line\n'''",
            "'''C:\\Users\\name'''",
            "'''line1\nline2'''",
            "''''''",
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

# Recursive structure for values emphasizing nested inline tables inside arrays & inline tables
value_strat = st.recursive(
    scalar_val,
    lambda children: st.one_of(
        # Standard array
        st.lists(children, max_size=4).map(lambda lst: f"[{', '.join(lst)}]"),
        # Multiline array
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
        # Trailing comma inline table (Divergence #1)
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
    max_leaves=12,
)


@composite
def simple_kv_document(draw):
    lines = []
    if draw(st.booleans()):
        lines.append("# Flat KV document")
    num_pairs = draw(st.integers(min_value=1, max_value=6))
    for i in range(num_pairs):
        k = draw(
            st.one_of(
                st.text(
                    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=6
                ).map(lambda s: f"var_{i}_{s}"),
                st.text(alphabet=SAFE_BASIC_INSIDE, min_size=1, max_size=6).map(
                    lambda s: f'"str_var_{i}_{s}"'
                ),
            )
        )
        v = draw(value_strat)
        comment = " # comment" if draw(st.booleans()) else ""
        lines.append(f"{k} = {v}{comment}")
    return "\n".join(lines)


@composite
def array_table_document(draw):
    lines = []
    num_tables = draw(st.integers(min_value=1, max_value=4))
    for t_idx in range(num_tables):
        tbl_name = draw(key_strat)
        num_entries = draw(st.integers(min_value=1, max_value=3))
        for _ in range(num_entries):
            lines.append(f"[[{tbl_name}]]")
            num_pairs = draw(st.integers(min_value=1, max_value=4))
            for _ in range(num_pairs):
                k = draw(key_strat)
                v = draw(value_strat)
                comment = " # inline table comment" if draw(st.booleans()) else ""
                lines.append(f"{k} = {v}{comment}")
            lines.append("")
    return "\n".join(lines)


@composite
def standard_document(draw):
    lines = []
    if draw(st.booleans()):
        lines.append("# Top-level comment")

    num_pairs = draw(st.integers(min_value=0, max_value=4))
    for _ in range(num_pairs):
        k = draw(key_strat)
        v = draw(value_strat)
        comment = " # comment" if draw(st.booleans()) else ""
        lines.append(f"{k} = {v}{comment}")

    num_sections = draw(st.integers(min_value=1, max_value=4))
    for sec_idx in range(num_sections):
        lines.append("")
        if draw(st.booleans()):
            lines.append(f"# Section {sec_idx} header comment")

        is_array_table = draw(st.booleans())
        header_key = draw(key_strat)

        if is_array_table:
            lines.append(f"[[{header_key}]]")
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
            comment = " # inline comment" if draw(st.booleans()) else ""
            lines.append(f"{k} = {v}{comment}")

    return "\n".join(lines)


# Stack overflow & slowdown target strategies
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


@composite
def many_siblings_doc(draw):
    n = draw(st.integers(min_value=15_000, max_value=30_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([standard_document()] * 15),
    *([simple_kv_document()] * 5),
    *([array_table_document()] * 8),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_mixed_nesting_doc(),
    deep_quoted_mixed_doc(),
    many_siblings_doc(),
)