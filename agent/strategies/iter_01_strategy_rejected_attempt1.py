"""Generated strategy - iteration 1, attempt 1.
accepted: False
generated: 2026-09-01T22:07:33.603646+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

ALPHA_NUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
UNQUOTED_KEY_CHARS = ALPHA_NUM + "-_"
NON_ASCII_CHARS = "éàöçñαβγδλ中文🎉🚀"
SAFE_BASIC_CHARS = ALPHA_NUM + " -_!#$%&'()*+,./:;<=>?@[]^{|}~" + NON_ASCII_CHARS
SAFE_LITERAL_CHARS = ALPHA_NUM + " -_!#$%&()*+,./:;<=>?@[]^{|}~" + NON_ASCII_CHARS

unquoted_key = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
quoted_basic_key = st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=10).map(
    lambda s: f'"{s}"'
)
quoted_literal_key = st.text(
    alphabet=SAFE_LITERAL_CHARS, min_size=0, max_size=10
).map(lambda s: f"'{s}'")

simple_key = st.one_of(unquoted_key, quoted_basic_key, quoted_literal_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(
    lambda ks: ".".join(ks)
)
key = st.one_of(simple_key, dotted_key)

dec_int = st.integers(-10000, 10000).map(str)
hex_int = st.integers(0, 65535).map(lambda n: f"0x{n:X}")
oct_int = st.text(alphabet="01234567", min_size=1, max_size=6).map(
    lambda s: f"0o{s}"
)
bin_int = st.integers(0, 255).map(lambda n: f"0b{n:b}")

int_values = st.one_of(
    dec_int,
    hex_int,
    oct_int,
    bin_int,
    st.sampled_from(
        [
            "9223372036854775807",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "18446744073709551615",
            "0",
            "-0",
            "+0",
            "007",
            "0123",
            "000",
            "-01",
            "0xDEADBEEF",
            "0x1_2_3",
            "0o755",
            "0o0",
            "0o123",
            "0o7_5_5",
            "0b110101",
            "1_000_000",
            "+123",
        ]
    ),
)

float_values = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from(
        [
            "inf",
            "+inf",
            "-inf",
            "nan",
            "+nan",
            "-nan",
            "0.0",
            "-0.0",
            "+0.0",
            "1e10",
            "1.5e-3",
            "3.14_159",
            "1.0e+2",
            "-1.23E-4",
        ]
    ),
)

bool_values = st.sampled_from(["true", "false"])

normal_date = st.tuples(
    st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28)
).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}")

normal_time = st.tuples(
    st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}")

normal_datetime = st.tuples(
    st.integers(1970, 2030),
    st.integers(1, 12),
    st.integers(1, 28),
    st.integers(0, 23),
    st.integers(0, 59),
    st.integers(0, 59),
).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z")

long_frac_datetime = st.tuples(
    st.integers(1970, 2030),
    st.integers(1, 12),
    st.integers(1, 28),
    st.integers(0, 23),
    st.integers(0, 59),
    st.integers(0, 59),
    st.text(alphabet="0123456789", min_size=15, max_size=25),
).map(
    lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]}Z"
)

datetime_values = st.one_of(
    normal_date, normal_time, normal_datetime, long_frac_datetime
)

string_values = st.one_of(
    st.text(alphabet=SAFE_BASIC_CHARS, max_size=20).map(lambda s: f'"{s}"'),
    st.text(alphabet=SAFE_LITERAL_CHARS, max_size=20).map(lambda s: f"'{s}'"),
    st.sampled_from(
        [
            '"hello\\nworld"',
            '"tab\\ttest"',
            '"quote\\""',
            '"bs\\\\\\\\"',
            '"\\u0041\\u0042"',
            '"\\U0001F600"',
            '"\\u00e9\\u00e0"',
            '"café"',
            "'café'",
            '"日本語"',
            "'日本語'",
            '""',
            "''",
            '""""""',
            "''''''",
        ]
    ),
    st.text(alphabet=SAFE_BASIC_CHARS + "\n", max_size=30).map(
        lambda s: f'"""{s}"""'
    ),
    st.text(alphabet=SAFE_LITERAL_CHARS + "\n", max_size=30).map(
        lambda s: f"'''{s}'''"
    ),
)

scalar_value = st.one_of(
    int_values, float_values, bool_values, datetime_values, string_values
)


@composite
def recursive_value(draw, depth=0):
    if depth >= 3:
        return draw(scalar_value)

    choice = draw(st.integers(0, 2))
    if choice == 0:
        return draw(scalar_value)
    elif choice == 1:
        n = draw(st.integers(0, 4))
        elems = [draw(recursive_value(depth=depth + 1)) for _ in range(n)]
        comma_sep = ", " if draw(st.booleans()) else ","
        body = comma_sep.join(elems)
        if elems and draw(st.booleans()):
            body += ","
        return f"[{body}]"
    else:
        n = draw(st.integers(0, 3))
        pairs = []
        for i in range(n):
            k = draw(unquoted_key)
            v = draw(recursive_value(depth=depth + 1))
            pairs.append(f"{k}_{i} = {v}")
        body = ", ".join(pairs)
        if pairs and draw(st.booleans()):
            body += ","
        return f"{{{body}}}"


@composite
def table_header(draw):
    k = draw(key)
    if draw(st.booleans()):
        return f"[{k}]"
    else:
        return f"[[{k}]]"


@composite
def document(draw):
    if draw(st.integers(1, 10)) == 1:
        return draw(st.sampled_from(["", "\n", "# Empty document\n", " \t \n"]))

    num_items = draw(st.integers(1, 8))
    items = []

    for i in range(num_items):
        kind = draw(st.sampled_from(["kv", "kv", "kv", "table", "comment"]))
        if kind == "kv":
            base_k = draw(key)
            if base_k.startswith('"') or base_k.startswith("'"):
                k = f'"{i}_{base_k[1:]}'
            else:
                k = f"k{i}_{base_k}"
            v = draw(recursive_value())
            op = draw(st.sampled_from([" = ", "=", " = ", " = "]))
            items.append(f"{k}{op}{v}")
        elif kind == "table":
            items.append(draw(table_header()))
        else:
            comment_text = draw(st.text(alphabet=SAFE_BASIC_CHARS, max_size=15))
            items.append(f"# {comment_text}")

    return "\n".join(items)


@composite
def deep_array_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    return f"k = {'[' * n}1{']' * n}"


@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    return f"k = {'{a=' * n}1{'}' * n}"


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    return f"{'a.' * n}k = 1"


@composite
def deep_mixed_nesting_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return f"k = {'[{a=' * n}1{'}]' * n}"


@composite
def deep_quoted_mixed_doc(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    val = '[{"k"=' * n + "1" + "}]" * n
    return f"k = {val}"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([document()] * 25),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_mixed_nesting_doc(),
    deep_quoted_mixed_doc(),
    many_siblings(),
)