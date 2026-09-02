"""Generated strategy - iteration 1, attempt 2.
accepted: False
generated: 2026-09-01T21:09:38.744232+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

BASIC_STR_CHARS = (
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    " !#$%&'()*+,-./:;<=>?@[]^_`{|}~\u00e9\u00e0\u00f1\u00fc\u4f60\u597d\u2603"
)
LITERAL_STR_CHARS = (
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    " !\"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\u00e9\u00e0\u00f1\u00fc\u4f60\u597d\u2603"
)
UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)


@composite
def unquoted_key(draw):
    return draw(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8))


@composite
def quoted_key(draw):
    s = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=8))
    s_clean = (
        s.replace("\\", "").replace('"', "").replace("\n", "").replace("\r", "")
    )
    if not s_clean:
        s_clean = "k"
    return f'"{s_clean}"'


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
            st.sampled_from(["007", "0123", "00", "000", "+01", "-09"]),
            st.sampled_from(
                [
                    "0",
                    "-0",
                    "+0",
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
    clean_b = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15))
    clean_b = (
        clean_b.replace("\\", "")
        .replace('"', "")
        .replace("\n", "")
        .replace("\r", "")
    )

    prefix = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=5))
    prefix = (
        prefix.replace("\\", "")
        .replace('"', "")
        .replace("\n", "")
        .replace("\r", "")
    )
    suffix = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=5))
    suffix = (
        suffix.replace("\\", "")
        .replace('"', "")
        .replace("\n", "")
        .replace("\r", "")
    )
    esc = draw(
        st.sampled_from(
            [
                "\\n",
                "\\t",
                '\\"',
                "\\\\",
                "\\u0020",
                "\\u00e9",
                "\\U00000020",
                "\\U00002603",
                "\\b",
                "\\f",
            ]
        )
    )

    clean_l = draw(
        st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=15)
    )
    clean_l = clean_l.replace("'", "").replace("\n", "").replace("\r", "")

    ml_b = draw(
        st.text(alphabet=BASIC_STR_CHARS + "\n ", min_size=0, max_size=20)
    )
    ml_b = ml_b.replace('"""', "")

    ml_l = draw(
        st.text(alphabet=LITERAL_STR_CHARS + "\n ", min_size=0, max_size=20)
    )
    ml_l = ml_l.replace("'''", "")

    return draw(
        st.one_of(
            st.just(f'"{clean_b}"'),
            st.just(f'"{prefix}{esc}{suffix}"'),
            st.just(f"'{clean_l}'"),
            st.just(f'"""{ml_b}"""'),
            st.just(f"'''{ml_l}'''"),
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
    num_pairs = draw(st.integers(0, 4))
    pairs = []
    for i in range(num_pairs):
        k = draw(unquoted_key()) + f"_{i}"
        v = draw(value_strat(max_depth=max_depth))
        pairs.append(f"{k} = {v}")
    trailing = draw(st.sampled_from([", ", ""])) if pairs else ""
    return f"{{{', '.join(pairs)}{trailing}}}"


@composite
def pair_expr(draw, key_suffix=""):
    k = draw(key_strat()) + str(key_suffix)
    v = draw(value_strat(max_depth=2))
    sep = draw(st.sampled_from([" = ", "=", " = ", " ="]))
    return f"{k}{sep}{v}"


@composite
def comment_expr(draw):
    comment_text = (
        draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=20))
        .replace("\n", "")
        .replace("\r", "")
    )
    return f"# {comment_text}"


@composite
def document(draw):
    num_lines = draw(st.integers(1, 10))
    lines = []
    used_table_names = set()
    current_key_idx = 0

    for _ in range(num_lines):
        line_type = draw(st.sampled_from(["pair", "pair", "table", "comment"]))
        if line_type == "pair":
            current_key_idx += 1
            lines.append(draw(pair_expr(key_suffix=f"_{current_key_idx}")))
        elif line_type == "comment":
            lines.append(draw(comment_expr()))
        else:
            tbl_name = draw(unquoted_key())
            is_array = draw(st.booleans())
            if is_array:
                lines.append(f"[[{tbl_name}]]")
                current_key_idx += 1
                lines.append(draw(pair_expr(key_suffix=f"_{current_key_idx}")))
            else:
                if tbl_name not in used_table_names:
                    used_table_names.add(tbl_name)
                    lines.append(f"[{tbl_name}]")
                    current_key_idx += 1
                    lines.append(
                        draw(pair_expr(key_suffix=f"_{current_key_idx}"))
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
    *([document()] * 30),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_mixed_nesting_doc(),
    deep_quoted_mixed_doc(),
    many_siblings_doc(),
)