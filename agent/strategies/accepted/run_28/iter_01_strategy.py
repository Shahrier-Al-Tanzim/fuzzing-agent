"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-08-21T06:34:58.688907+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!@#$%^&*()éàöäüßµαβγδこんにちは世界🚀ñçÅø"
LITERAL_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!@#$%^&*()\\éàöäüßµαβγδこんにちは世界🚀ñçÅø"


@composite
def simple_key(draw):
    kind = draw(st.integers(0, 2))
    if kind == 0:
        return draw(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10))
    elif kind == 1:
        s = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=10))
        return f'"{s}"'
    else:
        s = draw(st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=10))
        return f"'{s}'"


@composite
def dotted_key(draw):
    parts = draw(st.lists(simple_key(), min_size=2, max_size=3))
    return ".".join(parts)


@composite
def key_strat(draw):
    return draw(st.one_of(simple_key(), dotted_key()))


@composite
def ml_basic_string(draw):
    s = draw(st.text(alphabet=BASIC_STR_CHARS + "\n\t", min_size=0, max_size=20))
    s = s.replace('"""', '""\\"')
    return f'"""{s}"""'


@composite
def ml_literal_string(draw):
    s = draw(
        st.text(alphabet=LITERAL_STR_CHARS + "\n\t", min_size=0, max_size=20)
    )
    s = s.replace("'''", "''")
    return f"'''{s}'''"


@composite
def scalar_val(draw):
    choice = draw(st.integers(0, 13))
    if choice == 0:
        return str(draw(st.integers(-10000, 10000)))
    elif choice == 1:
        # Extreme numbers / divergence #3 & #4
        return draw(
            st.sampled_from(
                ["9223372036854775808", "-9223372036854775809", "007", "1_000_000"]
            )
        )
    elif choice == 2:
        return f"0x{draw(st.integers(0, 0xFFFF)):x}"
    elif choice == 3:
        return f"0o{draw(st.integers(0, 0o777)):o}"
    elif choice == 4:
        return f"0b{draw(st.integers(0, 0b11111111)):b}"
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
                ["inf", "-inf", "nan", "-nan", "0.0", "-0.0", "1e10", "1.0e-5"]
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
                    "1979-05-27T00:32:00",
                    "1979-05-27",
                    "07:32:00",
                ]
            )
        )
    elif choice == 9:
        s = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15))
        return f'"{s}"'
    elif choice == 10:
        s = draw(st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=15))
        return f"'{s}'"
    elif choice == 11:
        return draw(ml_basic_string())
    elif choice == 12:
        return draw(ml_literal_string())
    else:
        return draw(
            st.sampled_from(
                [
                    '"hello\\nworld"',
                    '"foo\\tbar"',
                    '"\\u0041\\u0042"',
                    '"\\u00e9\\u00f1"',
                    '"""multi\nline"""',
                    "'''multiline\nliteral'''",
                ]
            )
        )


@composite
def array_val(draw, depth=0):
    if depth >= 2:
        elem_s = scalar_val()
    else:
        elem_s = st.one_of(
            scalar_val(),
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
        )
    elems = draw(st.lists(elem_s, max_size=4))
    return "[" + ", ".join(elems) + "]"


@composite
def inline_table_val(draw, depth=0):
    if depth >= 2:
        v_s = scalar_val()
    else:
        v_s = st.one_of(
            scalar_val(),
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
        )
    keys = draw(st.lists(simple_key(), min_size=0, max_size=3, unique=True))
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
def table_header(draw):
    k = draw(key_strat())
    is_array = draw(st.booleans())
    if is_array:
        return f"[[{k}]]"
    else:
        return f"[{k}]"


@composite
def document(draw):
    num_sections = draw(st.integers(1, 4))
    lines = []

    if draw(st.booleans()):
        lines.append("# TOML Document")

    used_tables = set()

    for section_idx in range(num_sections):
        if section_idx > 0:
            hdr = draw(table_header())
            if hdr not in used_tables or draw(st.integers(1, 10)) == 1:
                used_tables.add(hdr)
                lines.append(hdr)
        num_pairs = draw(st.integers(0, 5))
        used_keys = set()
        for _ in range(num_pairs):
            k = draw(simple_key())
            # Occasionally emit duplicate key to test parser
            if k not in used_keys or draw(st.integers(1, 10)) == 1:
                used_keys.add(k)
                v = draw(value_strat())
                lines.append(f"{k} = {v}")
    return "\n".join(lines)


# Rule 16: Five extreme-depth shapes constructed via integer repetition
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


# Rule 17: Many sibling keys in one table
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