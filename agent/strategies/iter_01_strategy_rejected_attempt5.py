"""Generated strategy - iteration 1, attempt 5.
accepted: False
generated: 2026-09-01T21:13:07.596087+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

BASIC_STR_CHARS = (
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
    "!#$%&'()*+,-./:;<=>?@[]^_`{|}~"
)
LITERAL_STR_CHARS = (
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
    "!\"#$%&()*+,-./:;<=>?@[\\]^_`{|}~"
)
UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)

NON_ASCII_CHARS = "éàèùœâêîôûäëïöüÿçñµαβγδ€£¥\u00e9\u4f60\u597d\U0001f600"
BASIC_STR_WITH_NON_ASCII = BASIC_STR_CHARS + NON_ASCII_CHARS
LITERAL_STR_WITH_NON_ASCII = LITERAL_STR_CHARS + NON_ASCII_CHARS

COMMON_KEYS = ["a", "b", "x", "same_key", "dup_key"]


@composite
def unquoted_key(draw):
    return draw(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10))


@composite
def quoted_key(draw):
    chars = draw(st.sampled_from([BASIC_STR_CHARS, BASIC_STR_WITH_NON_ASCII]))
    s = draw(st.text(alphabet=chars, min_size=1, max_size=10))
    return f'"{s}"'


@composite
def simple_key(draw):
    return draw(st.one_of(unquoted_key(), quoted_key()))


@composite
def dotted_key(draw):
    parts = draw(st.lists(simple_key(), min_size=2, max_size=4))
    return ".".join(parts)


@composite
def key_strat(draw):
    if draw(st.booleans()):
        k = draw(st.sampled_from(COMMON_KEYS))
        return draw(st.one_of(st.just(k), st.just(f'"{k}"')))
    return draw(st.one_of(simple_key(), dotted_key()))


@composite
def integer_val(draw):
    return draw(
        st.one_of(
            st.integers(-100000, 100000).map(str),
            st.sampled_from(
                [
                    "0",
                    "-0",
                    "+0",
                    "007",
                    "000",
                    "01",
                    "0123",
                    "-0123",
                    "+0123",
                    "9223372036854775807",
                    "-9223372036854775808",
                    "9223372036854775808",
                    "-9223372036854775809",
                    "1_000_000",
                    "+123",
                    "-456",
                ]
            ),
            st.integers(0, 0xFFFF).map(lambda x: f"0x{x:x}"),
            st.integers(0, 0o777).map(lambda x: f"0o{x:o}"),
            st.integers(0, 0b11111111).map(lambda x: f"0b{x:b}"),
        )
    )


@composite
def float_val(draw):
    return draw(
        st.one_of(
            st.floats(allow_nan=True, allow_infinity=True).map(str),
            st.sampled_from(
                [
                    "inf",
                    "-inf",
                    "+inf",
                    "nan",
                    "-nan",
                    "+nan",
                    "1.0",
                    "-0.0",
                    "+0.0",
                    "1e10",
                    "1.5e-3",
                    "1_000.0",
                    "1e+100",
                ]
            ),
        )
    )


@composite
def bool_val(draw):
    return draw(st.sampled_from(["true", "false"]))


@composite
def string_val(draw):
    return draw(
        st.one_of(
            st.text(alphabet=BASIC_STR_WITH_NON_ASCII, min_size=0, max_size=15).map(
                lambda s: f'"{s}"'
            ),
            st.tuples(
                st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=5),
                st.sampled_from(
                    [
                        "\\n",
                        "\\t",
                        '\\"',
                        "\\\\",
                        "\\u0020",
                        "\\U00000020",
                        "\\u00e9",
                        "\\u4f60",
                        "\\z",
                        "\\b",
                        "\\f",
                    ]
                ),
                st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=5),
            ).map(lambda t: f'"{t[0]}{t[1]}{t[2]}"'),
            st.text(alphabet=LITERAL_STR_WITH_NON_ASCII, min_size=0, max_size=15).map(
                lambda s: f"'{s}'"
            ),
            st.text(
                alphabet=BASIC_STR_WITH_NON_ASCII + "\n ", min_size=0, max_size=20
            ).map(lambda s: f'"""{s}"""'),
            st.text(
                alphabet=LITERAL_STR_WITH_NON_ASCII + "\n ", min_size=0, max_size=20
            ).map(lambda s: f"'''{s}'''"),
        )
    )


@composite
def datetime_val(draw):
    year = draw(st.integers(1970, 2030))
    month = draw(st.integers(1, 12))
    day = draw(st.integers(1, 28))
    hour = draw(st.integers(0, 23))
    minute = draw(st.integers(0, 59))
    second = draw(st.integers(0, 59))
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    time_str = f"{hour:02d}:{minute:02d}:{second:02d}"

    frac = draw(
        st.sampled_from(
            ["", ".123", ".9999999999999999999", ".0000000000001"]
        )
    )
    offset = draw(st.sampled_from(["Z", "+00:00", "-08:00", ""]))

    return draw(
        st.one_of(
            st.just(f"{date_str}T{time_str}{frac}{offset}"),
            st.just(f"{date_str}T{time_str}{frac}"),
            st.just(date_str),
            st.just(f"{time_str}{frac}"),
        )
    )


@composite
def scalar_value(draw):
    return draw(
        st.one_of(
            integer_val(), float_val(), bool_val(), string_val(), datetime_val()
        )
    )


@composite
def value_strat(draw, max_depth=2):
    if max_depth <= 0:
        return draw(scalar_value())
    return draw(
        st.one_of(
            scalar_value(),
            array_val(max_depth=max_depth - 1),
            inline_table_val(max_depth=max_depth - 1),
        )
    )


@composite
def array_val(draw, max_depth=2):
    elems = draw(
        st.lists(value_strat(max_depth=max_depth), min_size=0, max_size=4)
    )
    comma = draw(st.sampled_from([", ", ""])) if elems else ""
    return f"[{', '.join(elems)}{comma}]"


@composite
def inline_table_val(draw, max_depth=2):
    pairs = draw(
        st.lists(
            st.tuples(simple_key(), value_strat(max_depth=max_depth)).map(
                lambda p: f"{p[0]} = {p[1]}"
            ),
            min_size=0,
            max_size=4,
        )
    )
    trailing = draw(st.sampled_from([", ", ""])) if pairs else ""
    return f"{{{', '.join(pairs)}{trailing}}}"


@composite
def pair_expr(draw):
    k = draw(key_strat())
    v = draw(value_strat(max_depth=2))
    sep = draw(st.sampled_from([" = ", "=", " = ", " ="]))
    malformed = draw(
        st.sampled_from(["", "", "", "", "", "missing_val", "bad_eq"])
    )
    if malformed == "missing_val":
        return f"{k} ="
    elif malformed == "bad_eq":
        return f"{k} {v}"
    return f"{k}{sep}{v}"


@composite
def duplicate_key_expr(draw):
    k = draw(st.sampled_from(COMMON_KEYS))
    v1 = draw(value_strat(max_depth=1))
    v2 = draw(value_strat(max_depth=1))
    return f"{k} = {v1}\n{k} = {v2}"


@composite
def table_hdr(draw):
    k = draw(key_strat())
    return draw(st.one_of(st.just(f"[{k}]"), st.just(f"[[{k}]]")))


@composite
def comment_expr(draw):
    comment_text = draw(
        st.text(alphabet=BASIC_STR_WITH_NON_ASCII, min_size=0, max_size=20)
    )
    return f"# {comment_text}"


@composite
def document(draw):
    lines = draw(
        st.lists(
            st.one_of(
                pair_expr(),
                duplicate_key_expr(),
                table_hdr(),
                comment_expr(),
            ),
            min_size=0,
            max_size=15,
        )
    )
    return "\n".join(lines)


@composite
def deep_array_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    val = "[" * n + "1" + "]" * n
    return f"k = {val}"


@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    val = "{a=" * n + "1" + "}" * n
    return f"k = {val}"


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    key_str = "a." * n + "k"
    return f"{key_str} = 1"


@composite
def deep_mixed_nesting_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    val = "[{a=" * n + "1" + "}]" * n
    return f"k = {val}"


@composite
def deep_quoted_mixed_doc(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    val = '[{"k"=' * n + "1" + "}]" * n
    return f"k = {val}"


@composite
def many_siblings_doc(draw):
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
    many_siblings_doc(),
)