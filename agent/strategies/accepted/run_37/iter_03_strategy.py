"""Generated strategy - iteration 3, attempt 1.
accepted: True
generated: 2026-09-01T21:28:37.061053+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

BASIC_STR_SAFE = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
LITERAL_STR_SAFE = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ !\"#$%&()*+,-./:;<=>?@[\\]^_`{|}~"
UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
NON_ASCII_SAMPLES = ["café", "日本語", "ñ", "µ", "é", "äöü", "αβγ"]
COMMON_KEYS = ["a", "b", "c", "x", "y", "z", "key", "val", "data", "item", "name"]


@composite
def unquoted_key(draw):
    return draw(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8))


@composite
def quoted_key(draw):
    s = draw(
        st.one_of(
            st.text(alphabet=BASIC_STR_SAFE, min_size=1, max_size=8),
            st.sampled_from(NON_ASCII_SAMPLES),
        )
    )
    return f'"{s}"'


@composite
def literal_quoted_key(draw):
    s = draw(st.text(alphabet=LITERAL_STR_SAFE, min_size=1, max_size=8))
    return f"'{s}'"


@composite
def simple_key(draw):
    return draw(
        st.one_of(
            st.sampled_from(COMMON_KEYS),
            unquoted_key(),
            quoted_key(),
            literal_quoted_key(),
        )
    )


def make_key_with_suffix(key_str, suffix):
    if key_str.startswith('"') and key_str.endswith('"'):
        return f'"{key_str[1:-1]}_{suffix}"'
    elif key_str.startswith("'") and key_str.endswith("'"):
        return f"'{key_str[1:-1]}_{suffix}'"
    else:
        return f"{key_str}_{suffix}"


@composite
def dotted_key(draw, suffix=""):
    parts = draw(st.lists(simple_key(), min_size=2, max_size=3))
    if suffix:
        parts = [
            make_key_with_suffix(p, f"{suffix}_{i}") for i, p in enumerate(parts)
        ]
    return ".".join(parts)


@composite
def integer_val(draw):
    return draw(
        st.one_of(
            st.integers(-100000, 100000).map(str),
            st.integers(1, 999).map(lambda x: f"0{x:03d}"),  # Divergence #4
            st.sampled_from(
                [
                    "0",
                    "-0",
                    "+0",
                    "007",
                    "000",
                    "01234",
                    "9223372036854775807",
                    "-9223372036854775808",
                    "9223372036854775808",  # Divergence #3
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
            st.text(alphabet=BASIC_STR_SAFE, min_size=0, max_size=15).map(
                lambda s: f'"{s}"'
            ),
            st.sampled_from(NON_ASCII_SAMPLES).map(lambda s: f'"{s}"'),
            st.sampled_from(NON_ASCII_SAMPLES).map(lambda s: f"'{s}'"),
            st.tuples(
                st.text(alphabet=BASIC_STR_SAFE, min_size=0, max_size=5),
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
                st.text(alphabet=BASIC_STR_SAFE, min_size=0, max_size=5),
            ).map(lambda t: f'"{t[0]}{t[1]}{t[2]}"'),
            st.text(alphabet=LITERAL_STR_SAFE, min_size=0, max_size=15).map(
                lambda s: f"'{s}'"
            ),
            st.text(
                alphabet=BASIC_STR_SAFE + "\n ", min_size=0, max_size=20
            ).map(lambda s: f'"""{s}"""'),
            st.text(
                alphabet=LITERAL_STR_SAFE + "\n ", min_size=0, max_size=20
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

    # Divergence #2: over-long fractional seconds
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
    num_pairs = draw(st.integers(min_value=0, max_value=4))
    pairs = []
    used_keys = set()
    for i in range(num_pairs):
        k = draw(simple_key())
        if k in used_keys:
            k = make_key_with_suffix(k, f"ik_{i}")
        used_keys.add(k)
        v = draw(value_strat(max_depth=max_depth))
        pairs.append(f"{k} = {v}")

    # Divergence #1: trailing comma in inline table
    trailing = draw(st.sampled_from([", ", ""])) if pairs else ""
    return f"{{{', '.join(pairs)}{trailing}}}"


@composite
def document(draw):
    num_lines = draw(st.integers(min_value=1, max_value=15))
    lines = []
    current_table_keys = set()
    global_table_names = []

    for i in range(num_lines):
        line_type = draw(
            st.sampled_from(["pair", "pair", "pair", "table", "comment"])
        )

        if line_type == "comment":
            text = draw(
                st.text(alphabet=BASIC_STR_SAFE, min_size=0, max_size=15)
            )
            lines.append(f"# {text}")

        elif line_type == "table":
            tbl_kind = draw(st.sampled_from(["standard", "array"]))
            use_dotted = draw(st.booleans())
            if use_dotted:
                base_key = draw(dotted_key())
            else:
                base_key = draw(simple_key())

            tbl_name = base_key
            if tbl_name in global_table_names and tbl_kind == "standard":
                tbl_name = make_key_with_suffix(tbl_name, f"tbl_{i}")
            global_table_names.append(tbl_name)

            if tbl_kind == "standard":
                lines.append(f"[{tbl_name}]")
            else:
                lines.append(f"[[{tbl_name}]]")
            current_table_keys = set()

        else:  # pair
            # Re-use key names across tables (duplicate key names in doc, unique in table)
            # 5% chance of intentional duplicate key within same table to fuzz rejection
            allow_dup_in_table = draw(st.integers(1, 20)) == 1
            k = draw(simple_key())

            if not allow_dup_in_table and k in current_table_keys:
                k = make_key_with_suffix(k, f"l{i}")

            current_table_keys.add(k)

            use_dotted = draw(st.booleans())
            if use_dotted and not allow_dup_in_table:
                key_name = draw(dotted_key(suffix=f"l{i}"))
            else:
                key_name = k

            v = draw(value_strat(max_depth=2))
            sep = draw(st.sampled_from([" = ", "=", " = ", " ="]))
            comment_suffix = (
                f" # {draw(st.text(alphabet=BASIC_STR_SAFE, max_size=10))}"
                if draw(st.booleans())
                else ""
            )
            lines.append(f"{key_name}{sep}{v}{comment_suffix}")

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