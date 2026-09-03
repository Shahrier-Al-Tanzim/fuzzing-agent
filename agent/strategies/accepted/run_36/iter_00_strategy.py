"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-09-01T20:25:57.388956+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
BASIC_STR_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'()*+,-./:;<=>?@[]^_`{|}~ "
LITERAL_STR_ALPHABET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!"#$%&()*+,-./:;<=>?@[]^_`{|}~ '

unquoted_key_st = st.text(
    alphabet=UNQUOTED_ALPHABET, min_size=1, max_size=10
)
basic_str_st = st.text(
    alphabet=BASIC_STR_ALPHABET, min_size=0, max_size=15
).map(lambda s: f'"{s}"')
literal_str_st = st.text(
    alphabet=LITERAL_STR_ALPHABET, min_size=0, max_size=15
).map(lambda s: f"'{s}'")

escaped_str_st = st.sampled_from(
    [
        '"hello\\nworld"',
        '"hello\\tworld"',
        '"quote\\\"inside"',
        '"slash\\\\backslash"',
        '"unicode\\u0041test"',
        '"unicode\\U0001F600emoji"',
        '"""\nmulti\nline\nbasic\n"""',
        "'''\nmulti\nline\nliteral\n'''",
    ]
)

simple_key_st = st.one_of(unquoted_key_st, basic_str_st, literal_str_st)


@composite
def dotted_key_st(draw):
    parts = draw(st.lists(simple_key_st, min_size=2, max_size=4))
    return ".".join(parts)


key_st = st.one_of(simple_key_st, dotted_key_st())

int_st = st.one_of(
    st.integers().map(str),
    st.sampled_from(
        [
            "0",
            "-0",
            "9223372036854775807",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "1_000_000",
            "+99",
        ]
    ),
    st.integers(0, 999).map(lambda i: f"0{i:02d}"),
    st.integers(0, 0xFFFFFFFF).map(lambda i: f"0x{i:x}"),
    st.integers(0, 0o777777).map(lambda i: f"0o{i:o}"),
    st.integers(0, 0b11111111).map(lambda i: f"0b{i:b}"),
)

float_st = st.one_of(
    st.floats().map(str),
    st.sampled_from(
        [
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
        ]
    ),
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
        frac = draw(
            st.sampled_from(["999999", "9999999999999999999", "123456"])
        )
        return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}:{ss:02d}.{frac}Z"
    elif kind == 2:
        return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}:{ss:02d}-07:00"
    elif kind == 3:
        return f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}:{ss:02d}"
    elif kind == 4:
        return f"{y:04d}-{m:02d}-{d:02d}"
    else:
        return f"{hh:02d}:{mm:02d}:{ss:02d}"


scalar_st = st.one_of(
    basic_str_st,
    literal_str_st,
    escaped_str_st,
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

    duplicate_key = draw(st.booleans())
    dup_k = draw(simple_key_st) if duplicate_key else None

    lines = []
    for _ in range(lines_count):
        choice = draw(st.integers(1, 4))
        if choice == 1:
            if dup_k and draw(st.booleans()):
                lines.append(f"{dup_k} = {draw(value_strategy())}")
            else:
                lines.append(draw(key_value_line()))
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