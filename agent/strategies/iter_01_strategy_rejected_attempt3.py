"""Generated strategy - iteration 1, attempt 3.
accepted: False
generated: 2026-09-01T21:11:14.301420+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

BASIC_STR_CHARS = (
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
    "!#$%&'()*+,-./:;<=>?@[]^_`{|}~\u00e9\u00e0\u00e7\u00f6\u00fc\u03b1\u03b2\u65e5\u672c\u8a9e"
)
LITERAL_STR_CHARS = (
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
    "!\"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\u00e9\u00e0\u00e7\u00f6\u00fc\u03b1\u03b2"
)
UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
NON_ASCII_SAMPLES = ["café", "こんにちは", "Résumé", "über", "αβγ", "€100"]


@composite
def unquoted_key(draw):
    return draw(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10))


@composite
def quoted_key(draw):
    s = draw(
        st.one_of(
            st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=10),
            st.sampled_from(NON_ASCII_SAMPLES),
        )
    )
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
                    "0123",
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
    non_ascii = draw(st.sampled_from(NON_ASCII_SAMPLES))
    return draw(
        st.one_of(
            st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(
                lambda s: f'"{s}"'
            ),
            st.just(f'"{non_ascii}"'),
            st.tuples(
                st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=5),
                st.sampled_from(
                    [
                        "\\n",
                        "\\t",
                        '\\"',
                        "\\\\",
                        "\\u0020",
                        "\\u00e9",
                        "\\U00000020",
                        "\\b",
                        "\\f",
                    ]
                ),
                st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=5),
            ).map(lambda t: f'"{t[0]}{t[1]}{t[2]}"'),
            st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=15).map(
                lambda s: f"'{s}'"
            ),
            st.just(f"'{non_ascii}'"),
            st.text(
                alphabet=BASIC_STR_CHARS + "\n ", min_size=0, max_size=20
            ).map(lambda s: f'"""{s}"""'),
            st.text(
                alphabet=LITERAL_STR_CHARS + "\n ", min_size=0, max_size=20
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
    num_pairs = draw(st.integers(0, 4))
    pairs = []
    for i in range(num_pairs):
        k = f"k{i}" if draw(st.booleans()) else draw(simple_key())
        v = draw(value_strat(max_depth=max_depth))
        pairs.append(f"{k} = {v}")
    trailing = draw(st.sampled_from([", ", ""])) if pairs else ""
    return f"{{{', '.join(pairs)}{trailing}}}"


@composite
def document(draw):
    lines = []

    # 10% chance to explicitly generate duplicate keys
    gen_duplicate = draw(st.integers(1, 10)) == 1

    num_root_pairs = draw(st.integers(1, 5))
    for i in range(num_root_pairs):
        base_k = draw(key_strat())
        k = f"{base_k}_{i}"
        if gen_duplicate and i == 1 and lines:
            # Re-use first key to create duplicate key condition
            k = lines[0].split("=")[0].strip()

        v = draw(value_strat(max_depth=2))
        sep = draw(st.sampled_from([" = ", "=", " = "]))
        line = f"{k}{sep}{v}"

        if draw(st.booleans()):
            cmt = draw(
                st.text(alphabet=UNQUOTED_KEY_CHARS + " ", min_size=0, max_size=10)
            )
            line += f" # {cmt}"
        lines.append(line)

    num_tables = draw(st.integers(0, 3))
    for t_idx in range(num_tables):
        tbl_key = f"tbl_{t_idx}"
        is_array_table = draw(st.booleans())
        if is_array_table:
            lines.append(f"[[{tbl_key}]]")
            if draw(st.booleans()):
                lines.append(f"[[{tbl_key}]]")
        else:
            lines.append(f"[{tbl_key}]")

        num_pairs = draw(st.integers(1, 3))
        for p_idx in range(num_pairs):
            pk = f"subk_{p_idx}"
            pv = draw(value_strat(max_depth=2))
            lines.append(f"{pk} = {pv}")

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