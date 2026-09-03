"""Generated strategy - iteration 3, attempt 1.
accepted: True
generated: 2026-08-19T08:03:41.884225+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

_UNQUOTED_CHARS = list(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
_QUOTED_SAFE_CHARS = list(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&()*+,-./:;<=>?@[]^_`{|}~"
)
_NON_ASCII_CHARS = list("áéíóúàèìòùäöüßñçÁÉÍÓÚÄÖÜÑØæåαβγδ€£¥千万円🚀")

unquoted_key = st.text(
    alphabet=st.sampled_from(_UNQUOTED_CHARS), min_size=1, max_size=12
)
quoted_key = st.text(
    alphabet=st.sampled_from(_QUOTED_SAFE_CHARS + _NON_ASCII_CHARS),
    min_size=1,
    max_size=12,
).map(lambda s: f'"{s}"')
literal_key = st.text(
    alphabet=st.sampled_from(_QUOTED_SAFE_CHARS + _NON_ASCII_CHARS),
    min_size=1,
    max_size=12,
).map(lambda s: f"'{s}'")

simple_key = st.one_of(unquoted_key, quoted_key, literal_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=3).map(
    lambda parts: ".".join(parts)
)
key = st.one_of(simple_key, dotted_key)

local_date_val = st.tuples(
    st.integers(1970, 2099), st.integers(1, 12), st.integers(1, 28)
).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}")


@composite
def date_time_val(draw):
    date_str = draw(local_date_val)

    kind = draw(
        st.sampled_from(["offset_dt", "local_dt", "local_d", "local_t"])
    )
    if kind == "local_d":
        return date_str

    h = draw(st.integers(0, 23))
    mi = draw(st.integers(0, 59))
    s = draw(st.integers(0, 59))
    time_str = f"{h:02d}:{mi:02d}:{s:02d}"
    if draw(st.booleans()):
        frac = draw(
            st.one_of(
                st.integers(0, 999999).map(lambda x: f".{x:06d}"),
                st.just(".9999999999999999999"),
                st.just(".0000000000000000001"),
                st.just(".1234567890123456789"),
            )
        )
        time_str += frac

    if kind == "local_t":
        return time_str
    elif kind == "local_dt":
        delim = draw(st.sampled_from(["T", "t", " "]))
        return f"{date_str}{delim}{time_str}"
    else:
        offset = draw(
            st.one_of(st.just("Z"), st.just("-07:00"), st.just("+02:00"))
        )
        return f"{date_str}T{time_str}{offset}"


ml_basic_string = st.sampled_from(
    [
        '"""\nline 1\nline 2\n"""',
        '"""hello\nworld"""',
        '"""\n  multiline \\\n  trimmed line\n"""',
        '""" multiline with "quotes" and \'literal\' """',
        '""" non-ascii UTF-8: こんにちは世界 🚀 """',
        '""" unicode \\u0000 \\u0041 \\U0001F600 """',
    ]
)

ml_literal_string = st.sampled_from(
    [
        "'''\nfirst line\nsecond line\n'''",
        "'''hello\nworld'''",
        "'''literal \\n not escaped'''",
        "'''non-ascii UTF-8: こんにちは '''",
    ]
)

non_ascii_string = st.text(
    alphabet=st.sampled_from(_NON_ASCII_CHARS + _QUOTED_SAFE_CHARS),
    min_size=1,
    max_size=10,
).map(lambda s: f'"{s}"')

inf_val = st.sampled_from(["inf", "+inf", "-inf"])

scalar_val = st.one_of(
    local_date_val,
    st.integers().map(str),
    st.sampled_from(
        [
            "9223372036854775808",
            "-9223372036854775809",
            "18446744073709551615",
            "999999999999999999999999",
            "1_000_000",
            "007",
            "01234",
            "-05",
        ]
    ),
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(lambda x: f"0x{x:x}"),
    st.integers(min_value=0, max_value=0o777777).map(lambda x: f"0o{x:o}"),
    st.integers(min_value=0, max_value=0b11111111).map(lambda x: f"0b{x:b}"),
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    inf_val,
    st.sampled_from(
        ["nan", "+nan", "-nan", "1.0e+100", "-0.0", "1e10", "1.5e-5"]
    ),
    st.sampled_from(["true", "false"]),
    non_ascii_string,
    ml_basic_string,
    ml_literal_string,
    st.sampled_from(
        [
            '"hello\\nworld"',
            '"escaped \\" quote"',
            '"unicode \\u0000 \\u0041 \\U0001F600"',
            '"invalid \\z escape"',
            "'literal \\n text'",
        ]
    ),
    date_time_val(),
)


@composite
def value_strategy(draw, max_depth=3):
    if max_depth <= 0:
        return draw(scalar_val)
    choice = draw(
        st.sampled_from(["scalar", "scalar", "array", "inline_table"])
    )
    if choice == "scalar":
        return draw(scalar_val)
    elif choice == "array":
        elems = draw(
            st.lists(value_strategy(max_depth=max_depth - 1), max_size=4)
        )
        trailing_comma = draw(st.sampled_from(["", ","])) if elems else ""
        return f"[{', '.join(elems)}{trailing_comma}]"
    else:
        keys = draw(st.lists(simple_key, min_size=0, max_size=4))
        pairs = []
        for k in keys:
            v = draw(value_strategy(max_depth=max_depth - 1))
            pairs.append(f"{k} = {v}")
        trailing_comma = draw(st.sampled_from(["", ","])) if pairs else ""
        return f"{{{', '.join(pairs)}{trailing_comma}}}"


@composite
def pair(draw):
    k = draw(key)
    v = draw(value_strategy(max_depth=3))
    if draw(st.booleans()):
        return f"{k} = {v}"
    else:
        bad_type = draw(
            st.sampled_from(["normal", "missing_equals", "unclosed_quote"])
        )
        if bad_type == "missing_equals":
            return f"{k} {v}"
        elif bad_type == "unclosed_quote":
            return f'"{k} = {v}'
        else:
            return f"{k} = {v}"


@composite
def table_header(draw):
    k = draw(key)
    if draw(st.booleans()):
        return f"[[{k}]]"
    else:
        return f"[{k}]"


@composite
def standard_document(draw):
    num_items = draw(st.integers(min_value=1, max_value=12))
    lines = []
    for _ in range(num_items):
        item_type = draw(
            st.sampled_from(["pair", "table", "comment", "blank"])
        )
        if item_type == "pair":
            lines.append(draw(pair()))
        elif item_type == "table":
            lines.append(draw(table_header()))
        elif item_type == "comment":
            c = draw(
                st.text(
                    alphabet=st.sampled_from(_UNQUOTED_CHARS + _NON_ASCII_CHARS),
                    max_size=15,
                )
            )
            lines.append(f"# {c}")
        else:
            lines.append("")
    return "\n".join(lines)


@composite
def duplicate_key_doc(draw):
    k = draw(simple_key)
    v1 = draw(scalar_val)
    v2 = draw(scalar_val)
    header = draw(st.one_of(st.just(""), table_header().map(lambda h: f"{h}\n")))
    return f"{header}duplicate_key = {v1}\nduplicate_key = {v2}\n{k} = {v1}"


@composite
def valid_duplicate_key_doc(draw):
    k = draw(simple_key)
    v1 = draw(scalar_val)
    v2 = draw(scalar_val)
    kind = draw(st.sampled_from(["array_table", "diff_tables"]))
    if kind == "array_table":
        return f"[[{k}]]\nfield = {v1}\n[[{k}]]\nfield = {v2}"
    else:
        return f"[table1]\n{k} = {v1}\n[table2]\n{k} = {v2}"


@composite
def deep_array_doc(draw):
    n = draw(st.integers(min_value=1_000, max_value=60_000))
    val = "[" * n + "1" + "]" * n
    return f"deep_arr = {val}"


@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=1_000, max_value=60_000))
    val = "{a=" * n + "1" + "}" * n
    return f"deep_tbl = {val}"


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=1_000, max_value=60_000))
    key_str = "a." * n + "k"
    return f"{key_str} = 1"


@composite
def many_siblings_doc(draw):
    n = draw(st.integers(min_value=5_000, max_value=25_000))
    lines = ["[table_many_keys]"] + [f"k{i} = {i}" for i in range(n)]
    return "\n".join(lines)


@composite
def array_of_tables_nested_doc(draw):
    k = draw(simple_key)
    num_entries = draw(st.integers(min_value=2, max_value=5))
    lines = []
    for i in range(num_entries):
        lines.append(f"[[{k}]]")
        lines.append(f"id = {i}")
        val = draw(value_strategy(max_depth=3))
        lines.append(f"data = {val}")
    return "\n".join(lines)


toml_strategy = st.one_of(
    standard_document(),
    standard_document(),
    standard_document(),
    valid_duplicate_key_doc(),
    duplicate_key_doc(),
    array_of_tables_nested_doc(),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    many_siblings_doc(),
)