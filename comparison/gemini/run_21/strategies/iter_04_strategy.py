"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-19T18:35:27.636376+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
PRINTABLE_BASIC = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'()*+,-./:;<=>?@[]^_`{|}~ "
PRINTABLE_LITERAL = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!\"#$%&()*+,-./:;<=>?@[]^_`{|}~ "
NON_ASCII_SAMPLES = ["こんにちは", "你好", "München", "éàèüñ", "🚀", "Томск"]

unquoted_key_strat = st.text(
    alphabet=UNQUOTED_KEY_ALPHABET, min_size=1, max_size=10
)
basic_quoted_key_strat = st.text(
    alphabet=PRINTABLE_BASIC, min_size=1, max_size=10
).map(lambda s: f'"{s}"')
literal_quoted_key_strat = st.text(
    alphabet=PRINTABLE_LITERAL, min_size=1, max_size=10
).map(lambda s: f"'{s}'")

simple_key_strat = st.one_of(
    unquoted_key_strat, basic_quoted_key_strat, literal_quoted_key_strat
)
dotted_key_strat = st.lists(simple_key_strat, min_size=2, max_size=4).map(
    lambda parts: ".".join(parts)
)
key_strat = st.one_of(simple_key_strat, dotted_key_strat)

unicode_escape_strat = st.sampled_from(
    [
        '"hello \\u0021 world"',
        '"\\u0041\\u0042\\u0043"',
        '"\\U0001F600 emoji"',
        '"unicode \\u00E9 test"',
        '"\\u0009 tab \\u0020 space"',
    ]
)

non_ascii_strat = st.one_of(
    st.sampled_from(NON_ASCII_SAMPLES).map(lambda s: f'"{s}"'),
    st.sampled_from(NON_ASCII_SAMPLES).map(lambda s: f"'{s}'"),
    st.sampled_from(NON_ASCII_SAMPLES).map(lambda s: f'"""{s}"""'),
    st.sampled_from(NON_ASCII_SAMPLES).map(lambda s: f"'''{s}'''"),
)

int_underscore_strat = st.sampled_from(
    [
        "1_000",
        "1_000_000",
        "+1_2_3",
        "-9_9_9",
        "1_0_0_0",
        "0xDEAD_BEEF",
        "0x1_A_F",
        "0o7_5_5",
        "0b1_0_1_0",
        "1_000.000_1",
    ]
)

overlong_frac_sec_strat = st.tuples(
    st.integers(1970, 2030),
    st.integers(1, 12),
    st.integers(1, 28),
    st.integers(0, 23),
    st.integers(0, 59),
    st.integers(0, 59),
    st.text(alphabet="0123456789", min_size=10, max_size=30),
).map(
    lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]}Z"
)

int_overflow_strat = st.one_of(
    st.integers(min_value=2**63, max_value=2**65).map(str),
    st.integers(min_value=-(2**65), max_value=-(2**63) - 1).map(str),
)

leading_zero_int_strat = st.integers(1, 9999).map(lambda x: f"0{x:03d}")

extreme_scalar_val = st.one_of(
    st.text(alphabet=PRINTABLE_BASIC, min_size=0, max_size=10).map(
        lambda s: f'"{s}"'
    ),
    st.text(alphabet=PRINTABLE_LITERAL, min_size=0, max_size=10).map(
        lambda s: f"'{s}'"
    ),
    unicode_escape_strat,
    non_ascii_strat,
    int_underscore_strat,
    int_overflow_strat,
    leading_zero_int_strat,
    overlong_frac_sec_strat,
    st.sampled_from(
        [
            '"""hello\\nworld"""',
            "'''multi\\nline'''",
            '"valid \\n \\t \\" \\\\ escape"',
            '"invalid \\z escape"',
        ]
    ),
    st.integers(-1000, 1000).map(str),
    st.sampled_from(
        [
            "0",
            "-0",
            "9223372036854775807",
            "9223372036854775808",
            "-9223372036854775808",
            "-9223372036854775809",
            "18446744073709551615",
            "007",
            "01234",
            "+01",
            "-005",
        ]
    ),
    st.integers(0, 65535).map(lambda x: f"0x{x:x}"),
    st.integers(0, 511).map(lambda x: f"0o{x:o}"),
    st.integers(0, 255).map(lambda x: f"0b{x:b}"),
    st.floats(allow_nan=True, allow_infinity=True).map(str),
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
            "1.5e-10",
        ]
    ),
    st.sampled_from(["true", "false"]),
    st.tuples(
        st.integers(1970, 2030),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
    ),
    st.tuples(
        st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28)
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
    st.tuples(
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
    ).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
)


def make_array(elem_strat):
    return st.lists(elem_strat, min_size=0, max_size=4).map(
        lambda elems: f"[{', '.join(elems)}]"
    )


def make_inline_table(elem_strat, k_strat):
    return st.tuples(
        st.lists(st.tuples(k_strat, elem_strat), min_size=0, max_size=3),
        st.booleans(),
    ).map(
        lambda pair: f"{{{', '.join(f'{k} = {v}' for k, v in pair[0])}{',' if pair[1] and pair[0] else ''}}}"
    )


toml_value = st.recursive(
    extreme_scalar_val,
    lambda child: st.one_of(
        make_array(child), make_inline_table(child, simple_key_strat)
    ),
    max_leaves=8,
)


@composite
def standard_document(draw):
    num_lines = draw(st.integers(min_value=1, max_value=12))
    lines = []
    used_keys = set()
    allow_dup = draw(st.booleans())
    key_counter = 0

    for _ in range(num_lines):
        line_type = draw(
            st.sampled_from(["kv", "table", "arr_table", "comment", "empty"])
        )
        if line_type == "kv":
            if allow_dup and used_keys and draw(st.booleans()):
                k = draw(st.sampled_from(sorted(list(used_keys))))
            else:
                key_counter += 1
                k = f"k_{key_counter}_" + draw(key_strat)
                used_keys.add(k)
            v = draw(toml_value)
            lines.append(f"{k} = {v}")
        elif line_type == "table":
            key_counter += 1
            k = f"tbl_{key_counter}_" + draw(key_strat)
            lines.append(f"[{k}]")
        elif line_type == "arr_table":
            key_counter += 1
            k = f"arr_tbl_{key_counter}_" + draw(key_strat)
            if draw(st.booleans()):
                inline_tbl = draw(
                    make_inline_table(toml_value, simple_key_strat)
                )
                lines.append(f"[[{k}]]\nelem = {inline_tbl}")
            else:
                lines.append(f"[[{k}]]")
        elif line_type == "comment":
            c = draw(
                st.one_of(
                    st.text(alphabet=PRINTABLE_BASIC, min_size=0, max_size=10),
                    st.sampled_from(NON_ASCII_SAMPLES),
                )
            )
            lines.append(f"# {c}")
        else:
            lines.append("")
    return "\n".join(lines)


@composite
def malformed_document(draw):
    choice = draw(
        st.sampled_from(
            [
                "unclosed_array",
                "unclosed_inline",
                "missing_equals",
                "unclosed_quote",
                "invalid_escape",
                "dup_keys",
                "trailing_comma_inline",
            ]
        )
    )
    if choice == "unclosed_array":
        return "a = [1, 2, 3"
    elif choice == "unclosed_inline":
        return "a = {x = 1, y = 2"
    elif choice == "missing_equals":
        return "a 123"
    elif choice == "unclosed_quote":
        return 'a = "unclosed string'
    elif choice == "invalid_escape":
        return 'a = "bad \\x escape"'
    elif choice == "trailing_comma_inline":
        return "a = {x = 1, y = 2, }"
    else:
        k = draw(simple_key_strat)
        return f"{k} = 1\n{k} = 2"


@composite
def deep_array_doc(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    val = draw(extreme_scalar_val)
    return f"k = {'[' * n}{val}{']' * n}"


@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    val = draw(extreme_scalar_val)
    return f"k = {'{a=' * n}{val}{'}' * n}"


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    val = draw(extreme_scalar_val)
    return f"{'a.' * n}k = {val}"


@composite
def deep_array_of_tables_inline_doc(draw):
    n = draw(st.integers(min_value=10, max_value=100))
    lines = ["[[a]]"]
    for i in range(n):
        lines.append(f"k{i} = {{ nested_{i} = [{i}, {i+1}, {i+2}] }}")
    return "\n".join(lines)


@composite
def array_of_tables_nested_inline(draw):
    tbl = draw(unquoted_key_strat)
    n = draw(st.integers(min_value=2, max_value=10))
    lines = []
    for i in range(n):
        lines.append(f"[[{tbl}]]")
        sub_tbl = draw(make_inline_table(toml_value, simple_key_strat))
        lines.append(f"data = {sub_tbl}")
    return "\n".join(lines)


@composite
def many_siblings_doc(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[table]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    standard_document(),
    standard_document(),
    standard_document(),
    standard_document(),
    standard_document(),
    malformed_document(),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_array_of_tables_inline_doc(),
    array_of_tables_nested_inline(),
    many_siblings_doc(),
)