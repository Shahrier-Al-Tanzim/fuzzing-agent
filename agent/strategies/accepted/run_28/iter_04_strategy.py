"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-21T06:54:27.592481+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!@#$%^&*()~`?"
LITERAL_STR_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!@#$%^&*()~`?\\"
)


@composite
def simple_key(draw):
    kind = draw(st.integers(0, 2))
    if kind == 0:
        return draw(
            st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
        )
    elif kind == 1:
        s = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=10))
        return f'"{s}"'
    else:
        s = draw(st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=10)).replace("'", "")
        return f"'{s}'"


@composite
def dotted_key(draw):
    n = draw(st.integers(2, 4))
    parts = [draw(simple_key()) for _ in range(n)]
    return ".".join(parts)


@composite
def key_strat(draw):
    return draw(st.one_of(simple_key(), dotted_key()))


@composite
def ml_basic_string(draw):
    s = draw(
        st.text(alphabet=BASIC_STR_CHARS + "\n\t", min_size=0, max_size=20)
    )
    s = s.replace('"""', '""\\"')
    return f'"""{s}"""'


@composite
def ml_literal_string(draw):
    s = draw(
        st.text(alphabet=LITERAL_STR_CHARS + "\n\t", min_size=0, max_size=20)
    ).replace("'''", "''")
    return f"'''{s}'''"


@composite
def scalar_val(draw):
    choice = draw(st.integers(0, 13))
    if choice == 0:
        return str(
            draw(
                st.integers(
                    min_value=-9223372036854775808, max_value=9223372036854775807
                )
            )
        )
    elif choice == 1:
        # Divergences #3 (int overflow) & #4 (leading zero ints)
        return draw(
            st.sampled_from(
                [
                    "9223372036854775808",
                    "-9223372036854775809",
                    "18446744073709551615",
                    "-18446744073709551616",
                    "999999999999999999999",
                    "007",
                    "0001",
                    "0123",
                    "1_000_000",
                    "+1_000_000",
                    "-1_000_000",
                ]
            )
        )
    elif choice == 2:
        return f"0x{draw(st.integers(0, 0xFFFFFFFF)):x}"
    elif choice == 3:
        return f"0o{draw(st.integers(0, 0o777777)):o}"
    elif choice == 4:
        return f"0b{draw(st.integers(0, 0b111111111111)):b}"
    elif choice == 5:
        return str(
            draw(
                st.floats(
                    allow_nan=False,
                    allow_infinity=False,
                    min_value=-1e6,
                    max_value=1e6,
                )
            )
        )
    elif choice == 6:
        return draw(
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
                    "+0.0",
                    "1e10",
                    "1.0e-5",
                    "1e9999",
                    "-1e9999",
                ]
            )
        )
    elif choice == 7:
        return draw(st.sampled_from(["true", "false"]))
    elif choice == 8:
        # Date times, including divergence #2 (overlong fractional seconds)
        return draw(
            st.sampled_from(
                [
                    "1979-05-27T00:32:00Z",
                    "1979-05-27T00:32:00.9999999999999999999-07:00",
                    "1979-05-27T00:32:00.12345678901234567890Z",
                    "1979-05-27T00:32:00",
                    "1979-05-27",
                    "07:32:00",
                    "00:00:00.000000001",
                    "2023-12-31 23:59:59.999Z",
                ]
            )
        )
    elif choice == 9:
        s = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15))
        return f'"{s}"'
    elif choice == 10:
        s = draw(st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=15)).replace("'", "")
        return f"'{s}'"
    elif choice == 11:
        return draw(ml_basic_string())
    elif choice == 12:
        return draw(ml_literal_string())
    else:
        # Strictly uppercase hex digits for valid TOML unicode escapes
        return draw(
            st.sampled_from(
                [
                    '"hello\\nworld"',
                    '"foo\\tbar"',
                    '"\\u0041\\u0042"',
                    '"\\u00E9\\u00F1"',
                    '"\\u0000"',
                    '"\\u0007"',
                    '"\\u001F"',
                    '"\\U0001F600"',
                ]
            )
        )


@composite
def array_val(draw, depth=0):
    if depth >= 3:
        elem_s = scalar_val()
    else:
        elem_s = st.one_of(
            scalar_val(),
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
        )
    elems = draw(st.lists(elem_s, max_size=4))
    trailing = draw(st.booleans()) if elems else False
    body = ", ".join(elems)
    if trailing:
        body += ","
    return "[" + body + "]"


@composite
def inline_table_val(draw, depth=0):
    if depth >= 3:
        v_s = scalar_val()
    else:
        v_s = st.one_of(
            scalar_val(),
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
        )
    keys = draw(st.lists(simple_key(), min_size=0, max_size=4, unique=True))
    pairs = []
    for k in keys:
        v = draw(v_s)
        pairs.append(f"{k} = {v}")
    # Divergence #1: trailing comma in inline table
    trailing = draw(st.booleans()) if pairs else False
    body = ", ".join(pairs)
    if trailing:
        body += ","
    return "{" + body + "}"


@composite
def value_strat(draw, depth=0):
    return draw(
        st.one_of(
            scalar_val(),
            array_val(depth=depth),
            inline_table_val(depth=depth),
        )
    )


@composite
def comment_str(draw):
    s = draw(
        st.text(alphabet=UNQUOTED_KEY_CHARS + " ", min_size=0, max_size=15)
    )
    return f"# {s}"


@composite
def document(draw):
    pattern = draw(st.integers(0, 8))
    lines = []

    if draw(st.booleans()):
        lines.append(draw(comment_str()))

    used_tables = set()

    if pattern == 0:
        # Standard table document with mixed scalar/array/inline values
        num_sections = draw(st.integers(1, 4))
        for section_idx in range(num_sections):
            hdr = f"sec_{section_idx}"
            tbl = f"[{hdr}]"
            lines.append(tbl)
            num_pairs = draw(st.integers(1, 5))
            used_keys = set()
            for k_idx in range(num_pairs):
                k = f"k_{k_idx}"
                v = draw(value_strat())
                comment = (
                    f" {draw(comment_str())}" if draw(st.booleans()) else ""
                )
                lines.append(f"{k} = {v}{comment}")

    elif pattern == 1:
        # Array of tables document
        num_sections = draw(st.integers(1, 3))
        for s_idx in range(num_sections):
            hdr = f"arr_tbl_{s_idx % 2}"
            lines.append(f"[[{hdr}]]")
            num_pairs = draw(st.integers(1, 4))
            for k_idx in range(num_pairs):
                k = f"item_{k_idx}"
                v = draw(value_strat())
                lines.append(f"{k} = {v}")

    elif pattern == 2:
        # Dotted key and inline table heavy document
        num_pairs = draw(st.integers(2, 6))
        for i in range(num_pairs):
            k = f"root_{i}.child"
            v = draw(st.one_of(inline_table_val(), scalar_val()))
            lines.append(f"{k} = {v}")

    elif pattern == 3:
        # Complex nested strings, multiline strings, and nested arrays
        num_sections = draw(st.integers(1, 3))
        for s_idx in range(num_sections):
            lines.append(f"[nested_{s_idx}]")
            num_pairs = draw(st.integers(1, 4))
            for k_idx in range(num_pairs):
                k = f"val_{k_idx}"
                v = draw(
                    st.one_of(
                        ml_basic_string(),
                        ml_literal_string(),
                        array_val(),
                        inline_table_val(),
                    )
                )
                lines.append(f"{k} = {v}")

    elif pattern == 4:
        # Co-occurrence of standard tables, array of tables, and root keys
        num_root_keys = draw(st.integers(1, 3))
        for r_idx in range(num_root_keys):
            lines.append(f"root_k{r_idx} = {draw(scalar_val())}")

        lines.append("[sub_section]")
        lines.append(f"sub_k = {draw(inline_table_val())}")

        lines.append("[[arr_sec]]")
        lines.append(f"arr_k = {draw(array_val())}")

    elif pattern == 5:
        # Boundary scalars and divergence heavy (int overflow, overlong subseconds, leading zero ints)
        lines.append("[divergences]")
        lines.append(f"overlong_frac = \"1979-05-27T00:32:00.9999999999999999999-07:00\"")
        lines.append(f"int_overflow = 9223372036854775808")
        lines.append(f"leading_zero = 007")
        lines.append(f"inline_trailing_comma = {draw(inline_table_val())}")

    elif pattern == 6:
        # Dotted section header hierarchy
        lines.append("[a]")
        lines.append(f"k1 = {draw(scalar_val())}")
        lines.append("[a.b]")
        lines.append(f"k2 = {draw(scalar_val())}")
        lines.append("[a.b.c]")
        lines.append(f"k3 = {draw(array_val())}")

    elif pattern == 7:
        # Varied key styles (quoted, unquoted, dotted) in root table
        keys = ["unquoted_key", '"quoted key"', "'literal key'", "a.b.c"]
        for i, k in enumerate(keys):
            lines.append(f"{k} = {draw(value_strat())}")

    else:
        # Comment and whitespace heavy document
        num_pairs = draw(st.integers(1, 4))
        for i in range(num_pairs):
            if draw(st.booleans()):
                lines.append(draw(comment_str()))
            k = f"key_{i}"
            v = draw(scalar_val())
            lines.append(f"{k} = {v} {draw(comment_str())}")

    return "\n".join(lines)


# Extreme-depth shapes constructed via integer repetition (Rule 16)
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


# Many sibling keys in one table (Rule 17)
@composite
def many_siblings_doc(draw):
    n = draw(st.integers(min_value=10_000, max_value=30_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([document()] * 40),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_mixed_nesting_doc(),
    deep_quoted_mixed_doc(),
    many_siblings_doc(),
)