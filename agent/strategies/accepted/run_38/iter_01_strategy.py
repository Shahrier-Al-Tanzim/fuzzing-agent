"""Generated strategy - iteration 1, attempt 2.
accepted: True
generated: 2026-09-01T22:08:35.352033+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

ASCII_ALNUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
UNQUOTED_KEY_CHARS = ASCII_ALNUM + "-_"
SAFE_BASIC_CHARS = ASCII_ALNUM + " -_!#$%&'()*+,./:;<=>?@[]^{|}~"
SAFE_LITERAL_CHARS = ASCII_ALNUM + ' -_!#$%&"()*+,./:;<=>?@[]^{|}~'
NON_ASCII_CHARS = "café_日本語_áéíóú_ñ_µ_π_🚀"

unquoted_key = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
quoted_basic_key = st.text(
    alphabet=SAFE_BASIC_CHARS + NON_ASCII_CHARS, min_size=1, max_size=10
).map(lambda s: f'"{s}"')
quoted_literal_key = st.text(
    alphabet=SAFE_LITERAL_CHARS + NON_ASCII_CHARS, min_size=1, max_size=10
).map(lambda s: f"'{s}'")

simple_key = st.one_of(unquoted_key, quoted_basic_key, quoted_literal_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=3).map(
    lambda ks: ".".join(ks)
)
key = st.one_of(simple_key, dotted_key)

dec_int_values = st.integers(-10000, 10000).map(str)
oct_int_values = st.sampled_from(
    ["0o755", "0o644", "0o0", "0o1234", "0o777", "0o0123", "0o5_2_1"]
)
overflow_ints = st.sampled_from(
    [
        "9223372036854775807",
        "-9223372036854775808",
        "9223372036854775808",
        "-9223372036854775809",
        "18446744073709551615",
    ]
)
leading_zero_ints = st.sampled_from(["007", "0123", "000", "-01"])
other_int_formats = st.sampled_from(
    [
        "0xDEADBEEF",
        "0x1_2_3",
        "0b110101",
        "1_000_000",
        "+123",
        "0",
        "-0",
        "+0",
    ]
)

int_values = st.one_of(
    dec_int_values,
    oct_int_values,
    overflow_ints,
    leading_zero_ints,
    other_int_formats,
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

basic_str = st.text(
    alphabet=SAFE_BASIC_CHARS + NON_ASCII_CHARS, max_size=20
).map(lambda s: f'"{s}"')
literal_str = st.text(
    alphabet=SAFE_LITERAL_CHARS + NON_ASCII_CHARS, max_size=20
).map(lambda s: f"'{s}'")
escaped_str = st.sampled_from(
    [
        '"hello\\nworld"',
        '"tab\\ttest"',
        '"quote\\""',
        '"bs\\\\\\\\"',
        '"\\u0041\\u0042"',
        '"\\U0001F600"',
        '""',
        "''",
        '""""""',
        "''''''",
        '"café \\u00e9"',
    ]
)
ml_basic_str = st.text(
    alphabet=SAFE_BASIC_CHARS + NON_ASCII_CHARS, max_size=30
).map(lambda s: f'"""\n{s}\n"""')
ml_literal_str = st.text(
    alphabet=SAFE_LITERAL_CHARS + NON_ASCII_CHARS, max_size=30
).map(lambda s: f"'''\n{s}\n'''")

string_values = st.one_of(
    basic_str, literal_str, escaped_str, ml_basic_str, ml_literal_str
)

scalar_value = st.one_of(
    int_values, float_values, bool_values, datetime_values, string_values
)


@composite
def recursive_value(draw, depth=0):
    if depth >= 2:
        return draw(scalar_value)

    choice = draw(st.integers(0, 2))
    if choice == 0:
        return draw(scalar_value)
    elif choice == 1:
        n = draw(st.integers(0, 3))
        elems = [draw(recursive_value(depth=depth + 1)) for _ in range(n)]
        body = ", ".join(elems)
        if elems and draw(st.booleans()):
            body += ","
        return f"[{body}]"
    else:
        n = draw(st.integers(0, 3))
        pairs = []
        for i in range(n):
            k = f"k{i}"
            v = draw(recursive_value(depth=depth + 1))
            pairs.append(f"{k} = {v}")
        body = ", ".join(pairs)
        if pairs and draw(st.booleans()):
            body += ","
        return f"{{{body}}}"


@composite
def document(draw):
    if draw(st.integers(1, 10)) == 1:
        return draw(st.sampled_from(["", "\n", "# Empty document\n", " \t \n"]))

    num_sections = draw(st.integers(1, 4))
    lines = []

    for sec_i in range(num_sections):
        if sec_i > 0 or draw(st.booleans()):
            kind = draw(st.sampled_from(["std", "arr"]))
            sec_name = f"section_{sec_i}"
            if kind == "std":
                lines.append(f"[{sec_name}]")
            else:
                lines.append(f"[[array_{sec_i}]]")

        num_kv = draw(st.integers(1, 4))
        for kv_i in range(num_kv):
            k_type = draw(st.integers(0, 3))
            if k_type == 0:
                k = f"key_{sec_i}_{kv_i}"
            elif k_type == 1:
                k = f'"café_key_{sec_i}_{kv_i}"'
            elif k_type == 2:
                k = f"'literal_key_{sec_i}_{kv_i}'"
            else:
                k = f"sub_{sec_i}.k_{kv_i}"

            v = draw(recursive_value())
            op = draw(st.sampled_from([" = ", "=", " = "]))
            lines.append(f"{k}{op}{v}")

            if draw(st.booleans()):
                cmt = draw(
                    st.text(
                        alphabet=SAFE_BASIC_CHARS + NON_ASCII_CHARS, max_size=12
                    )
                )
                lines.append(f"# {cmt}")

    return "\n".join(lines)


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