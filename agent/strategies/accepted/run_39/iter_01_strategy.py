"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-09-01T23:22:26.385948+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
ASCII_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_!@#$%^&*()+=[]{}|;:,.<>?/~`"
NON_ASCII_CHARS = (
    "éèêàâäôöûüçñαβγδε日本語中国語こんにちは世界🚀🔥✨"
    + "".join(chr(c) for c in range(0x00A0, 0x0100))
)
DOUBLE_QUOTE_SAFE = ASCII_SAFE.replace('"', "").replace("\\", "") + NON_ASCII_CHARS
SINGLE_QUOTE_SAFE = ASCII_SAFE.replace("'", "") + NON_ASCII_CHARS

simple_key_strategy = st.one_of(
    st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10),
    st.text(alphabet=DOUBLE_QUOTE_SAFE, min_size=1, max_size=10).map(
        lambda s: f'"{s}"'
    ),
    st.text(alphabet=SINGLE_QUOTE_SAFE, min_size=1, max_size=10).map(
        lambda s: f"'{s}'"
    ),
)

key_strategy = st.one_of(
    simple_key_strategy,
    st.lists(simple_key_strategy, min_size=2, max_size=4).map(
        lambda parts: ".".join(parts)
    ),
)

scalar_int_strategy = st.one_of(
    st.integers().map(str),
    st.sampled_from(
        [
            "0",
            "-0",
            "9223372036854775807",
            "-9223372036854775808",
            "9223372036854775808",
            "-9223372036854775809",
            "999999999999999999999999",
            "1_000_000",
            "1_0_0_0",
        ]
    ),
    st.integers(0, 999).map(lambda x: f"0{x:02d}"),
    st.integers(0, 65535).map(lambda x: f"0x{x:x}"),
    st.integers(0, 511).map(lambda x: f"0o{x:o}"),
    st.integers(0, 255).map(lambda x: f"0b{x:b}"),
)

scalar_float_strategy = st.one_of(
    st.sampled_from(["inf", "+inf", "-inf"]),
    st.sampled_from(["nan", "+nan", "-nan"]),
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from(
        [
            "1e10",
            "1.5e-3",
            "-0.0",
            "+0.0",
            "3.14159_26535",
            "1.0",
            "-1.5",
        ]
    ),
)

date_str = st.tuples(
    st.integers(1900, 2099), st.integers(1, 12), st.integers(1, 28)
).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}")

time_str = st.tuples(
    st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}")

frac_time_str = st.tuples(
    st.integers(0, 23),
    st.integers(0, 59),
    st.integers(0, 59),
    st.sampled_from(["999", "9999999999999999999", "123456789"]),
).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}.{t[3]}")

scalar_datetime_strategy = st.one_of(
    date_str,
    time_str,
    frac_time_str,
    st.tuples(date_str, time_str).map(lambda t: f"{t[0]}T{t[1]}"),
    st.tuples(
        date_str,
        time_str,
        st.sampled_from(["Z", "+05:00", "-08:00", "+00:00"]),
    ).map(lambda t: f"{t[0]}T{t[1]}{t[2]}"),
)

scalar_string_strategy = st.one_of(
    st.text(alphabet=DOUBLE_QUOTE_SAFE, min_size=0, max_size=20).map(
        lambda s: f'"{s}"'
    ),
    st.text(alphabet=SINGLE_QUOTE_SAFE, min_size=0, max_size=20).map(
        lambda s: f"'{s}'"
    ),
    st.text(alphabet=DOUBLE_QUOTE_SAFE, min_size=0, max_size=20).map(
        lambda s: f'"""\n{s}\n"""'
    ),
    st.text(alphabet=SINGLE_QUOTE_SAFE, min_size=0, max_size=20).map(
        lambda s: f"'''\n{s}\n'''"
    ),
    st.sampled_from(
        [
            '"hello\\nworld"',
            '"tab\\tseparated"',
            '"quote\\"inside"',
            '"slash\\\\slash"',
            '"unicode \\u0041 \\u00e9 \\u2665"',
            '"hex \\U00000041 \\U0001F600"',
            '"invalid \\z escape"',
            '"non_ascii_éèñ_日本語"',
            "'literal_utf8_🚀'",
        ]
    ),
)

scalar_value_strategy = st.one_of(
    st.sampled_from(["true", "false"]),
    scalar_int_strategy,
    scalar_float_strategy,
    scalar_datetime_strategy,
    scalar_string_strategy,
)


@composite
def array_strategy(draw, depth=0):
    if draw(st.booleans()):
        return "[]"
    elems = draw(st.lists(value_strategy(depth=depth), min_size=1, max_size=4))
    trailing = "," if draw(st.booleans()) else ""
    return f"[{', '.join(elems)}{trailing}]"


@composite
def inline_table_strategy(draw, depth=0):
    if draw(st.booleans()):
        return "{}"
    keys = draw(
        st.lists(simple_key_strategy, min_size=1, max_size=3, unique=True)
    )
    pairs = [f"{k} = {draw(value_strategy(depth=depth))}" for k in keys]
    trailing = "," if draw(st.booleans()) else ""
    return f"{{{', '.join(pairs)}{trailing}}}"


@composite
def value_strategy(draw, depth=0):
    if depth >= 3:
        return draw(scalar_value_strategy)
    return draw(
        st.one_of(
            scalar_value_strategy,
            array_strategy(depth=depth + 1),
            inline_table_strategy(depth=depth + 1),
        )
    )


@composite
def table_section(draw, key_pool):
    header_name = draw(st.sampled_from(key_pool) | key_strategy)
    if draw(st.booleans()):
        header = f"[[{header_name}]]"
    else:
        header = f"[{header_name}]"

    num_pairs = draw(st.integers(1, 4))
    local_keys = draw(
        st.lists(simple_key_strategy, min_size=num_pairs, max_size=num_pairs, unique=True)
    )

    lines = [header]
    for k in local_keys:
        v = draw(value_strategy())
        lines.append(f"{k} = {v}")
        if draw(st.integers(1, 10)) <= 2:
            comment_text = draw(st.text(alphabet=DOUBLE_QUOTE_SAFE, max_size=15))
            lines.append(f"# {comment_text}")
    return "\n".join(lines)


@composite
def root_section(draw, key_pool):
    num_pairs = draw(st.integers(1, 3))
    local_keys = draw(
        st.lists(simple_key_strategy, min_size=num_pairs, max_size=num_pairs, unique=True)
    )
    lines = []
    for k in local_keys:
        v = draw(value_strategy())
        if draw(st.integers(1, 100)) <= 3:
            bad_choice = draw(st.sampled_from(["no_eq", "unclosed_str"]))
            if bad_choice == "no_eq":
                lines.append(f"{k} {v}")
            else:
                lines.append(f'{k} = "{v}')
        else:
            lines.append(f"{k} = {v}")
    return "\n".join(lines)


@composite
def document(draw):
    key_pool = ["item", "user", "server", "data", "a", "b", "c", "x", "y"]
    sections = []

    if draw(st.booleans()):
        sections.append(draw(root_section(key_pool)))

    num_tables = draw(st.integers(1, 4))
    for _ in range(num_tables):
        sections.append(draw(table_section(key_pool)))

    return "\n\n".join(s for s in sections if s)


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    val = "[" * n + "1" + "]" * n
    return f"deep_arr = {val}"


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    val = "{a=" * n + "1" + "}" * n
    return f"deep_tbl = {val}"


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    k = "a." * n + "k"
    return f"{k} = 1"


@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    val = "[{a=" * n + "1" + "}]" * n
    return f"deep_mix = {val}"


@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    val = '[{"k"=' * n + "1" + "}]" * n
    return f"deep_qmix = {val}"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([document()] * 20),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    deep_mixed_nesting(),
    deep_quoted_mixed(),
    many_siblings(),
)