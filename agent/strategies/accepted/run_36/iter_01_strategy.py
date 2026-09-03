"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-09-01T20:31:25.561821+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
BASIC_STR_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'()*+,-./:;<=>?@[]^_`{|}~ "
LITERAL_STR_ALPHABET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!"#$%&()*+,-./:;<=>?@[]^_`{|}~ '
ML_BASIC_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n!#$%&'()*+,-./:;<=>?@[]^_`{|}~"
ML_LITERAL_ALPHABET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t\n!"#$%&()*+,-./:;<=>?@[]^_`{|}~'

unquoted_key_st = st.text(
    alphabet=UNQUOTED_ALPHABET, min_size=1, max_size=10
)
basic_str_st = st.text(
    alphabet=BASIC_STR_ALPHABET, min_size=0, max_size=15
).map(lambda s: f'"{s}"')
literal_str_st = st.text(
    alphabet=LITERAL_STR_ALPHABET, min_size=0, max_size=15
).map(lambda s: f"'{s}'")

ml_basic_str_st = st.text(
    alphabet=ML_BASIC_ALPHABET, min_size=0, max_size=20
).map(lambda s: f'"""\n{s}\n"""')

ml_literal_str_st = st.text(
    alphabet=ML_LITERAL_ALPHABET, min_size=0, max_size=20
).map(lambda s: f"'''\n{s}\n'''")

non_ascii_key_st = st.sampled_from([
    '"\u00e9\u00e0"',
    '"\u65e5\u672c"',
    '"key_\u00e9"',
    "'clé'",
])

non_ascii_str_st = st.sampled_from([
    '"\u00e9\u00e0\u00e8\u00f4"',
    '"\u65e5\u672c\u8b9e"',
    '"\U0001f600\U0001f680"',
    '"\u0041\u0042\u0043 \u00e9\u00e0"',
    '"\\u00e9\\u00e0"',
    '"\\U0001f600"',
    "'éàèô'",
    "'日本語'",
])

escaped_str_st = st.sampled_from([
    '"hello\\nworld"',
    '"hello\\tworld"',
    '"quote\\\"inside"',
    '"slash\\\\backslash"',
    '"unicode\\u0041test"',
    '"unicode\\U0001F600emoji"',
])

string_st = st.one_of(
    basic_str_st,
    literal_str_st,
    ml_basic_str_st,
    ml_literal_str_st,
    non_ascii_str_st,
    escaped_str_st,
)

simple_key_st = st.one_of(
    unquoted_key_st, basic_str_st, literal_str_st, non_ascii_key_st
)


@composite
def dotted_key_st(draw):
    parts = draw(st.lists(simple_key_st, min_size=2, max_size=4))
    return ".".join(parts)


key_st = st.one_of(simple_key_st, dotted_key_st())

int_overflow_st = st.sampled_from([
    "9223372036854775807",
    "9223372036854775808",
    "9223372036854775809",
    "18446744073709551615",
    "99999999999999999999",
    "-9223372036854775808",
    "-9223372036854775809",
    "-99999999999999999999",
])

int_st = st.one_of(
    st.integers().map(str),
    int_overflow_st,
    st.sampled_from([
        "0",
        "-0",
        "1_000_000",
        "+99",
    ]),
    st.integers(0, 999).map(lambda i: f"0{i:02d}"),
    st.integers(0, 0xFFFFFFFF).map(lambda i: f"0x{i:x}"),
    st.integers(0, 0o777777).map(lambda i: f"0o{i:o}"),
    st.integers(0, 0b11111111).map(lambda i: f"0b{i:b}"),
)

float_st = st.one_of(
    st.floats().map(str),
    st.sampled_from([
        "inf",
        "-inf",
        "+inf",
        "nan",
        "-nan",
        "+nan",
        "0.0",
        "-0.0",
        "1e10",
        "1.5e-3",
        "1_000.0",
    ]),
)

bool_st = st.sampled_from(["true", "false"])


@composite
def datetime_st(draw):
    y = draw(st.integers(1970, 2030))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 28))
    hh = draw(st.integers(0, 23))
    mm = draw(st.integers(0, 59))
    ss = draw(st.integers(0, 59))
    kind = draw(st.integers(1, 5))
    if kind == 1:
        return f"{y:04d}-{m:02d}-{d:02d}"
    elif kind == 2:
        return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}:{ss:02d}"
    elif kind == 3:
        return f"{hh:02d}:{mm:02d}:{ss:02d}"
    elif kind == 4:
        return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}:{ss:02d}-07:00"
    else:
        frac = draw(st.sampled_from(["999999", "9999999999999999999", "123456"]))
        return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}:{ss:02d}.{frac}Z"


scalar_st = st.one_of(
    string_st,
    int_st,
    float_st,
    bool_st,
    datetime_st(),
)


@composite
def value_strategy(draw, depth=0):
    if depth >= 3:
        return draw(st.one_of(scalar_st, st.just("[]"), st.just("{}")))
    return draw(
        st.one_of(
            scalar_st,
            array_val_st(depth=depth + 1),
            inline_table_val_st(depth=depth + 1),
        )
    )


@composite
def array_val_st(draw, depth=0):
    elems = draw(st.lists(value_strategy(depth=depth), min_size=0, max_size=5))
    trailing = "," if (elems and draw(st.booleans())) else ""
    return "[" + ", ".join(elems) + trailing + "]"


@composite
def inline_table_val_st(draw, depth=0):
    keys = draw(st.lists(simple_key_st, min_size=0, max_size=4, unique=True))
    kvs = [f"{k} = {draw(value_strategy(depth=depth))}" for k in keys]
    trailing = "," if (kvs and draw(st.booleans())) else ""
    return "{" + ", ".join(kvs) + trailing + "}"


@composite
def key_value_line(draw):
    k = draw(key_st)
    v = draw(value_strategy())
    return f"{k} = {v}"


@composite
def table_header_line(draw):
    k = draw(key_st)
    is_array_table = draw(st.booleans())
    if is_array_table:
        return f"[[{k}]]"
    return f"[{k}]"


@composite
def comment_line(draw):
    cmt = draw(st.text(alphabet=BASIC_STR_ALPHABET, min_size=0, max_size=20))
    return f"# {cmt}"


@composite
def document(draw):
    lines_count = draw(st.integers(0, 10))
    if lines_count == 0:
        return ""

    lines = []
    used_keys = set()
    for i in range(lines_count):
        choice = draw(st.integers(1, 4))
        if choice == 1:
            k = f"k_{i}" if draw(st.booleans()) else draw(key_st)
            v = draw(value_strategy())
            lines.append(f"{k} = {v}")
        elif choice == 2:
            lines.append(draw(table_header_line()))
        elif choice == 3:
            lines.append(draw(comment_line()))
        else:
            lines.append("")
    return "\n".join(lines)


@composite
def deep_array_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    val = "[" * n + "1" + "]" * n
    return f"arr = {val}\n"


@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    val = "{a=" * n + "1" + "}" * n
    return f"tbl = {val}\n"


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    k = "a." * n + "k"
    return f"{k} = 1\n"


@composite
def deep_mixed_nesting_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    val = "[{a=" * n + "1" + "}]" * n
    return f"mix = {val}\n"


@composite
def deep_quoted_mixed_doc(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    val = '[{"k"=' * n + "1" + "}]" * n
    return f"qmix = {val}\n"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([document()] * 20),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_mixed_nesting_doc(),
    deep_quoted_mixed_doc(),
    many_siblings(),
)