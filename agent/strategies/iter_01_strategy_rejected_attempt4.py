"""Generated strategy - iteration 1, attempt 4.
accepted: False
generated: 2026-09-01T21:12:15.924040+00:00
"""
import string
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = string.ascii_letters + string.digits + "-_"
SAFE_BASIC_CHARS = (
    string.ascii_letters + string.digits + " !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
)
NON_ASCII_CHARS = "caféüber日本語★éñ\u00e9\u00f1\u2603"


@composite
def unquoted_key(draw):
    return draw(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10))


@composite
def quoted_key(draw):
    chars = SAFE_BASIC_CHARS + NON_ASCII_CHARS
    s = draw(st.text(alphabet=chars, min_size=1, max_size=10))
    return f'"{s}"'


@composite
def simple_key(draw):
    return draw(st.one_of(unquoted_key(), quoted_key()))


@composite
def dotted_key(draw):
    parts = draw(st.lists(simple_key(), min_size=2, max_size=3))
    return ".".join(parts)


@composite
def key_strat(draw):
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
                    "0123",
                    "000",
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
    chars = SAFE_BASIC_CHARS + NON_ASCII_CHARS
    return draw(
        st.one_of(
            st.text(alphabet=chars, min_size=0, max_size=15).map(
                lambda s: f'"{s}"'
            ),
            st.tuples(
                st.text(alphabet=chars, min_size=0, max_size=5),
                st.sampled_from(
                    [
                        "\\n",
                        "\\t",
                        '\\"',
                        "\\\\",
                        "\\u0020",
                        "\\U00000020",
                        "\\b",
                        "\\f",
                        "\\u00e9",
                    ]
                ),
                st.text(alphabet=chars, min_size=0, max_size=5),
            ).map(lambda t: f'"{t[0]}{t[1]}{t[2]}"'),
            st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=15).map(
                lambda s: f"'{s}'"
            ),
            st.text(alphabet=chars + "\n ", min_size=0, max_size=20).map(
                lambda s: f'"""{s}"""'
            ),
            st.text(
                alphabet=SAFE_BASIC_CHARS + "\n ", min_size=0, max_size=20
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
def array_val(draw, max_depth=2):
    if max_depth <= 0:
        elems = draw(st.lists(scalar_value(), min_size=0, max_size=3))
    else:
        elems = draw(
            st.lists(
                st.one_of(
                    scalar_value(),
                    array_val(max_depth=max_depth - 1),
                    inline_table_val(max_depth=max_depth - 1),
                ),
                min_size=0,
                max_size=3,
            )
        )
    comma = draw(st.sampled_from([", ", ""])) if elems else ""
    return f"[{', '.join(elems)}{comma}]"


@composite
def inline_table_val(draw, max_depth=2):
    if max_depth <= 0:
        val_strat = scalar_value()
    else:
        val_strat = st.one_of(
            scalar_value(),
            array_val(max_depth=max_depth - 1),
            inline_table_val(max_depth=max_depth - 1),
        )

    keys = draw(st.sets(simple_key(), min_size=0, max_size=3))
    pairs = [f"{k} = {draw(val_strat)}" for k in keys]
    trailing = draw(st.sampled_from([", ", ""])) if pairs else ""
    return f"{{{', '.join(pairs)}{trailing}}}"


@composite
def value_strat(draw, max_depth=2):
    return draw(
        st.one_of(
            scalar_value(),
            array_val(max_depth=max_depth),
            inline_table_val(max_depth=max_depth),
        )
    )


@composite
def pair_expr(draw, key_suffix=""):
    k_base = draw(key_strat())
    k = f"{k_base}_{key_suffix}" if key_suffix else k_base
    v = draw(value_strat(max_depth=2))
    sep = draw(st.sampled_from([" = ", "=", " = ", " ="]))
    return f"{k}{sep}{v}"


@composite
def table_hdr(draw, suffix=""):
    k_base = draw(key_strat())
    k = f"{k_base}_{suffix}" if suffix else k_base
    return draw(st.one_of(st.just(f"[{k}]"), st.just(f"[[{k}]]")))


@composite
def comment_expr(draw):
    comment_text = draw(
        st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=20)
    )
    return f"# {comment_text}"


@composite
def document(draw):
    num_lines = draw(st.integers(min_value=1, max_value=12))
    lines = []
    allow_dup = draw(st.booleans())
    for i in range(num_lines):
        kind = draw(st.sampled_from(["pair", "pair", "table", "comment"]))
        if kind == "pair":
            suf = "" if (allow_dup and i > 0 and draw(st.booleans())) else str(i)
            lines.append(draw(pair_expr(key_suffix=suf)))
        elif kind == "table":
            lines.append(draw(table_hdr(suffix=str(i))))
        else:
            lines.append(draw(comment_expr()))
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