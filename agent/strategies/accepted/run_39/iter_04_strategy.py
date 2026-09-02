"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-09-01T23:41:16.505997+00:00
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
DOUBLE_QUOTE_SAFE = (
    ASCII_SAFE.replace('"', "").replace("\\", "") + NON_ASCII_CHARS
)
SINGLE_QUOTE_SAFE = ASCII_SAFE.replace("'", "") + NON_ASCII_CHARS

simple_key_strategy = st.one_of(
    st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12),
    st.text(alphabet=DOUBLE_QUOTE_SAFE, min_size=1, max_size=12).map(
        lambda s: f'"{s}"'
    ),
    st.text(alphabet=SINGLE_QUOTE_SAFE, min_size=1, max_size=12).map(
        lambda s: f"'{s}'"
    ),
)

dotted_key_strategy = st.lists(
    st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=6),
    min_size=2,
    max_size=3,
    unique=True,
).map(lambda parts: ".".join(parts))

key_strategy = st.one_of(simple_key_strategy, dotted_key_strategy)

# Divergence #3 (int overflow) and Divergence #4 (leading zero ints) included
scalar_int_strategy = st.one_of(
    st.integers().map(str),
    st.sampled_from(
        [
            "0",
            "-0",
            "+0",
            "007",
            "00001",
            "01234",
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
    st.sampled_from(["inf", "+inf", "-inf", "nan", "+nan", "-nan"]),
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from(
        [
            "1e10",
            "1.5e-3",
            "1e309",
            "-1e309",
            "1e-324",
            "1.5e308",
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

# Divergence #2 (19-digit fractional seconds) included
frac_time_str = st.tuples(
    st.integers(0, 23),
    st.integers(0, 59),
    st.integers(0, 59),
    st.sampled_from(
        [
            "999",
            "9999999999999999999",
            "12345678901234567890",
            "123456789",
        ]
    ),
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
    st.tuples(
        date_str,
        frac_time_str,
        st.sampled_from(["Z", "-07:00", "+02:00"]),
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
            '"unicode \\u0000 \\u0041 \\u00e9 \\u2665"',
            '"hex \\U00000041 \\U0001F600 \\U0010FFFF"',
            '"invalid \\z escape"',
            '"non_ascii_éèñ_日本語"',
            "'literal_utf8_🚀'",
            '"""\nline1 \\\nline2\n"""',
            "'''\nliteral \\\nno escape\n'''",
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
        st.lists(
            st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    pairs = [f"{k} = {draw(value_strategy(depth=depth))}" for k in keys]
    # Divergence #1: trailing comma in inline table
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
def flat_document(draw):
    num_pairs = draw(st.integers(2, 6))
    keys = draw(
        st.lists(
            st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8),
            min_size=num_pairs,
            max_size=num_pairs,
            unique=True,
        )
    )
    lines = []
    for k in keys:
        v = draw(value_strategy())
        lines.append(f"{k} = {v}")
        if draw(st.booleans()):
            comment_text = draw(
                st.text(alphabet=DOUBLE_QUOTE_SAFE, max_size=20)
            )
            lines.append(f"# {comment_text}")
    return "\n".join(lines)


@composite
def root_section(draw):
    num_pairs = draw(st.integers(1, 3))
    keys = draw(
        st.lists(
            st.text(
                alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8
            ).map(lambda k: f"r_{k}"),
            min_size=num_pairs,
            max_size=num_pairs,
            unique=True,
        )
    )
    lines = []
    for k in keys:
        v = draw(value_strategy())
        lines.append(f"{k} = {v}")
    return "\n".join(lines)


@composite
def table_section(draw, header_name=None):
    if header_name is None:
        tbl_key = draw(
            st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8)
        )
        is_array = draw(st.booleans())
        header = f"[[tbl_{tbl_key}]]" if is_array else f"[tbl_{tbl_key}]"
    else:
        is_array = draw(st.booleans())
        header = f"[[{header_name}]]" if is_array else f"[{header_name}]"

    num_pairs = draw(st.integers(1, 4))
    local_keys = draw(
        st.lists(
            st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8),
            min_size=num_pairs,
            max_size=num_pairs,
            unique=True,
        )
    )

    lines = [header]
    for k in local_keys:
        v = draw(value_strategy())
        lines.append(f"{k} = {v}")
        if draw(st.integers(1, 10)) <= 2:
            comment_text = draw(
                st.text(alphabet=DOUBLE_QUOTE_SAFE, max_size=15)
            )
            lines.append(f"# {comment_text}")
    return "\n".join(lines)


@composite
def table_heavy_document(draw):
    lines = []
    if draw(st.booleans()):
        lines.append(draw(root_section()))
    num_tables = draw(st.integers(2, 5))
    table_names = draw(
        st.lists(
            st.text(
                alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8
            ).map(lambda name: f"sec_{name}"),
            min_size=num_tables,
            max_size=num_tables,
            unique=True,
        )
    )
    for name in table_names:
        lines.append(draw(table_section(header_name=name)))
    return "\n\n".join(lines)


@composite
def array_of_tables_document(draw):
    lines = []
    if draw(st.booleans()):
        lines.append(draw(root_section()))
    aot_name = draw(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8).map(
            lambda name: f"aot_{name}"
        )
    )
    num_entries = draw(st.integers(2, 4))
    for _ in range(num_entries):
        num_keys = draw(st.integers(1, 3))
        keys = draw(
            st.lists(
                st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8),
                min_size=num_keys,
                max_size=num_keys,
                unique=True,
            )
        )
        lines.append(f"[[{aot_name}]]")
        for k in keys:
            v = draw(value_strategy())
            lines.append(f"{k} = {v}")
    return "\n\n".join(lines)


@composite
def dotted_key_document(draw):
    lines = []
    if draw(st.booleans()):
        lines.append(draw(root_section()))

    prefix = draw(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=6)
    )
    num_pairs = draw(st.integers(2, 5))
    suffixes = draw(
        st.lists(
            st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=6),
            min_size=num_pairs,
            max_size=num_pairs,
            unique=True,
        )
    )
    for s in suffixes:
        v = draw(value_strategy())
        lines.append(f"dot_{prefix}.{s} = {v}")
    return "\n".join(lines)


@composite
def mixed_structure_document(draw):
    sections = []
    if draw(st.booleans()):
        sections.append(draw(root_section()))

    num_elements = draw(st.integers(2, 5))
    tbl_idx = 0
    for _ in range(num_elements):
        choice = draw(st.integers(1, 4))
        if choice == 1:
            k = draw(
                st.text(
                    alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8
                ).map(lambda name: f"mix_{name}_{tbl_idx}")
            )
            v = draw(value_strategy())
            sections.append(f"{k} = {v}")
        elif choice == 2:
            tbl_idx += 1
            name = f"mix_tbl_{tbl_idx}"
            sections.append(draw(table_section(header_name=name)))
        elif choice == 3:
            tbl_idx += 1
            hdr = f"[dotted_sec_{tbl_idx}]"
            sub1 = draw(
                st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=6)
            )
            sub2 = draw(
                st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=6)
            )
            v = draw(value_strategy())
            sections.append(f"{hdr}\n{sub1}.{sub2} = {v}")
        else:
            comment_text = draw(
                st.text(alphabet=DOUBLE_QUOTE_SAFE, max_size=30)
            )
            sections.append(f"# {comment_text}")
    return "\n\n".join(s for s in sections if s)


@composite
def divergence_heavy_document(draw):
    # Specifically mixes Divergences 1-4 in valid document layouts
    lines = []
    # Divergence 4: leading zero int
    lines.append(f"leading_zero = 007")
    # Divergence 3: overflow int
    lines.append(f"int_overflow = 9223372036854775808")
    # Divergence 2: 19-digit frac seconds
    lines.append(f"overlong_time = 1979-05-27T00:32:00.9999999999999999999-07:00")
    # Divergence 1: trailing comma in inline table
    lines.append(f"inline_tbl = {{ a = 1, b = 2, }}")

    extra_k = draw(
        st.text(
            alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=8
        ).map(lambda name: f"extra_{name}")
    )
    extra_v = draw(value_strategy())
    lines.append(f"{extra_k} = {extra_v}")
    return "\n".join(lines)


@composite
def document(draw):
    doc_type = draw(st.integers(1, 6))
    if doc_type == 1:
        return draw(flat_document())
    elif doc_type == 2:
        return draw(table_heavy_document())
    elif doc_type == 3:
        return draw(mixed_structure_document())
    elif doc_type == 4:
        return draw(array_of_tables_document())
    elif doc_type == 5:
        return draw(dotted_key_document())
    else:
        return draw(divergence_heavy_document())


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
def deep_aot_inline(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    val = "{a=" * n + "1" + "}" * n
    return f"[[tbl]]\nkey = {val}"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([document()] * 25),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    deep_mixed_nesting(),
    deep_quoted_mixed(),
    deep_aot_inline(),
    many_siblings(),
)