"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-09-01T19:13:50.182598+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Alphabets for safe string generation without external imports
ALPHA_NUM_DASH = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_CHAR = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "

# Key strategies
unquoted_key = st.text(alphabet=ALPHA_NUM_DASH, min_size=1, max_size=10)
basic_quoted_key = st.text(alphabet=SAFE_CHAR, min_size=1, max_size=10).map(
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

# Scalar values covering edge cases and divergences
integers_strat = st.one_of(
    st.integers(
        min_value=-9223372036854775808, max_value=9223372036854775807
    ).map(str),
    st.just("0"),
    st.just("-0"),
    st.just("9223372036854775808"),  # Past INT64_MAX (Divergence #3)
    st.just("-9223372036854775809"),
    st.just("007"),  # Leading-zero (Divergence #4)
    st.just("0123"),
    st.integers(0, 0xFFFFFFFF).map(lambda v: f"0x{v:x}"),
    st.integers(0, 0o7777).map(lambda v: f"0o{v:o}"),
    st.integers(0, 255).map(lambda v: f"0b{v:b}"),
    st.just("1_000_000"),
)

floats_strat = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
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
            "1_000.000_1",
        ]
    ),
)

bools_strat = st.sampled_from(["true", "false"])

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
    st.just(
        "1979-05-27T00:32:00.9999999999999999999Z"
    ),  # Over-long frac seconds (Divergence #2)
)

strings_strat = st.one_of(
    st.text(alphabet=SAFE_CHAR, min_size=0, max_size=15).map(
        lambda s: f'"{s}"'
    ),
    st.text(alphabet=SAFE_CHAR, min_size=0, max_size=15).map(
        lambda s: f"'{s}'"
    ),
    st.text(alphabet=SAFE_CHAR, min_size=0, max_size=15).map(
        lambda s: f'"""{s}"""'
    ),
    st.text(alphabet=SAFE_CHAR, min_size=0, max_size=15).map(
        lambda s: f"'''{s}'''"
    ),
    st.sampled_from(
        [
            '"hello\\nworld"',
            '"tab\\ttest"',
            '"quote\\""',
            '"slash\\\\"',
            '"\\u0000"',
            '"\\u0041"',
            '"\\U0001F600"',
            '"invalid\\zescape"',
        ]
    ),
)

scalar_val = st.one_of(
    integers_strat, floats_strat, bools_strat, dates_times_strat, strings_strat
)

# Recursive structure for values (Arrays and Inline Tables)
value_strat = st.recursive(
    scalar_val,
    lambda children: st.one_of(
        st.lists(children, max_size=5).map(lambda lst: f"[{', '.join(lst)}]"),
        st.just("[]"),
        st.lists(st.tuples(simple_key, children), max_size=5).map(
            lambda pairs: "{"
            + ", ".join(f"{k} = {v}" for k, v in pairs)
            + "}"
        ),
        st.just("{}"),
        # Trailing comma in inline table (Divergence #1)
        st.lists(st.tuples(simple_key, children), min_size=1, max_size=5).map(
            lambda pairs: "{"
            + ", ".join(f"{k} = {v}" for k, v in pairs)
            + ",}"
        ),
    ),
    max_leaves=15,
)

# Standard document expression lines
pair_line = st.tuples(key_strat, value_strat).map(
    lambda pair: f"{pair[0]} = {pair[1]}"
)
table_header = key_strat.map(lambda k: f"[{k}]")
array_table_header = key_strat.map(lambda k: f"[[{k}]]")
comment_line = st.text(alphabet=SAFE_CHAR, min_size=0, max_size=10).map(
    lambda c: f"# {c}"
)
malformed_line = st.sampled_from(
    [
        "key_without_value =",
        "key_missing_equals value",
        "[unclosed_table",
        "[[unclosed_array_table",
    ]
)

doc_line = st.one_of(
    pair_line, table_header, array_table_header, comment_line, malformed_line
)


@composite
def standard_document(draw):
    lines = draw(st.lists(doc_line, min_size=0, max_size=10))
    return "\n".join(lines)


# Deep recursion strategies for stack overflow fuzzing (Rule 16)
@composite
def deep_array_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return f"k = {'[' * n}1{']' * n}"


@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=85_000, max_value=105_000))
    return f"k = {'{a=' * n}1{'}' * n}"


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=100_000, max_value=120_000))
    return f"{'a.' * n}k = 1"


@composite
def deep_mixed_nesting_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=75_000))
    return f"k = {'[{a=' * n}1{'}]' * n}"


@composite
def deep_quoted_mixed_doc(draw):
    n = draw(st.integers(min_value=20_000, max_value=35_000))
    return f'k = {"[{\"k\"=" * n}1{"}]" * n}'


# High sibling count for linear search slowdown / timeout fuzzing (Rule 17)
@composite
def many_siblings_doc(draw):
    n = draw(st.integers(min_value=15_000, max_value=30_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([standard_document()] * 20),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_mixed_nesting_doc(),
    deep_quoted_mixed_doc(),
    many_siblings_doc(),
)