"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-09-01T18:49:10.940295+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

SAFE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!?@#$%^&*()[]{}<>"
NON_ASCII_CHARS = "éàèùâêîôûäëïöüÿçñÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÑαβγδε日本語中国語✨🚀"
SAFE_BASIC_CHARS = SAFE_CHARS + NON_ASCII_CHARS
VALID_ESCAPES = [
    '\\"',
    "\\\\",
    "\\n",
    "\\t",
    "\\r",
    "\\f",
    "\\b",
    "\\u0041",
    "\\U00000041",
    "\\u00E9",
    "\\u4E2D",
]
KEY_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"


@composite
def basic_string_val(draw):
    pieces = draw(
        st.lists(
            st.one_of(
                st.text(alphabet=SAFE_BASIC_CHARS, min_size=1, max_size=8),
                st.sampled_from(VALID_ESCAPES),
            ),
            min_size=0,
            max_size=4,
        )
    )
    body = "".join(pieces)
    return f'"{body}"'


@composite
def literal_string_val(draw):
    safe_lit = SAFE_BASIC_CHARS.replace("'", "")
    body = draw(st.text(alphabet=safe_lit, min_size=0, max_size=15))
    return f"'{body}'"


@composite
def ml_basic_string_val(draw):
    pieces = draw(
        st.lists(
            st.one_of(
                st.text(
                    alphabet=SAFE_BASIC_CHARS + " \n", min_size=1, max_size=8
                ),
                st.sampled_from(VALID_ESCAPES),
            ),
            min_size=0,
            max_size=4,
        )
    )
    body = "".join(pieces).replace('"""', '""\\"')
    return f'"""{body}"""'


@composite
def ml_literal_string_val(draw):
    safe_lit = (SAFE_BASIC_CHARS + " \n").replace("'''", "")
    body = draw(st.text(alphabet=safe_lit, min_size=0, max_size=15))
    return f"'''{body}'''"


@composite
def unquoted_key(draw):
    return draw(st.text(alphabet=KEY_ALPHABET, min_size=1, max_size=10))


@composite
def quoted_key(draw):
    return draw(st.one_of(basic_string_val(), literal_string_val()))


@composite
def simple_key(draw):
    return draw(st.one_of(unquoted_key(), quoted_key()))


@composite
def dotted_key(draw):
    num_parts = draw(st.integers(2, 4))
    parts = [draw(simple_key()) for _ in range(num_parts)]
    return ".".join(parts)


@composite
def key_strat(draw):
    return draw(st.one_of(simple_key(), dotted_key()))


@composite
def date_time_val(draw):
    choice = draw(st.integers(0, 4))
    if choice == 0:
        return "1979-05-27T07:32:00Z"
    elif choice == 1:
        # Over-long fractional seconds (Divergence #2)
        nines = "9" * draw(st.integers(10, 25))
        return f"1979-05-27T00:32:00.{nines}-07:00"
    elif choice == 2:
        return "1979-05-27 07:32:00-07:00"
    elif choice == 3:
        return "1979-05-27"
    else:
        return "07:32:00"


@composite
def scalar_val(draw):
    strategy = st.one_of(
        # Integers (normal, overflow, leading zero, underscores, hex/oct/bin)
        st.integers(-9223372036854775807, 9223372036854775807).map(str),
        st.sampled_from([
            "9223372036854775808",  # Divergence #3 (int overflow)
            "-9223372036854775809",
            "007",  # Divergence #4 (leading zero)
            "0123",
            "1_000_000",
            "0xDEADBEEF",
            "0o755",
            "0b101010",
        ]),
        # Floats
        st.floats(allow_nan=True, allow_infinity=True).map(str),
        st.sampled_from(["0.0", "-0.0", "1e10", "nan", "-nan", "inf", "-inf"]),
        # Booleans
        st.sampled_from(["true", "false"]),
        # Strings (including non-ASCII)
        basic_string_val(),
        literal_string_val(),
        ml_basic_string_val(),
        ml_literal_string_val(),
        # Date / Time
        date_time_val(),
    )
    return draw(strategy)


@composite
def value_strat(draw, depth=0):
    if depth >= 2:
        return draw(scalar_val())
    choice = draw(st.integers(0, 4))
    if choice == 0:
        return draw(array_strat(depth=depth + 1))
    elif choice == 1:
        return draw(inline_table_strat(depth=depth + 1))
    else:
        return draw(scalar_val())


@composite
def array_strat(draw, depth=0):
    elems = draw(
        st.lists(value_strat(depth=depth + 1), min_size=0, max_size=3)
    )
    trailing = draw(st.sampled_from(["", ","])) if elems else ""
    return "[" + ", ".join(elems) + trailing + "]"


@composite
def inline_table_strat(draw, depth=0):
    num_pairs = draw(st.integers(0, 3))
    pairs = []
    for _ in range(num_pairs):
        k = draw(simple_key())
        v = draw(value_strat(depth=depth + 1))
        pairs.append(f"{k} = {v}")
    # Divergence #1: trailing comma in inline table
    trailing = draw(st.sampled_from(["", ","])) if pairs else ""
    return "{" + ", ".join(pairs) + trailing + "}"


@composite
def empty_document(draw):
    choice = draw(st.integers(0, 3))
    if choice == 0:
        return ""
    elif choice == 1:
        return "# Empty TOML file"
    elif choice == 2:
        return "\n\n  \t\n"
    else:
        return "# Comment 1\n# Comment 2\n"


@composite
def valid_document(draw):
    lines = []
    # Top level key-value pairs
    num_top = draw(st.integers(1, 4))
    for _ in range(num_top):
        k = draw(key_strat())
        v = draw(value_strat(depth=0))
        lines.append(f"{k} = {v}")

    # Sections
    num_sections = draw(st.integers(0, 3))
    for _ in range(num_sections):
        sec_name = draw(key_strat())
        is_array_table = draw(st.booleans())
        if is_array_table:
            lines.append(f"[[{sec_name}]]")
        else:
            lines.append(f"[{sec_name}]")
        num_pairs = draw(st.integers(1, 4))
        for _ in range(num_pairs):
            k = draw(key_strat())
            v = draw(value_strat(depth=0))
            lines.append(f"{k} = {v}")

    return "\n".join(lines)


# --- Deep Shapes (Rule 16) ---


@composite
def deep_array_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    val = "[" * n + "1" + "]" * n
    return f"deep_arr = {val}"


@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    val = "{a=" * n + "1" + "}" * n
    return f"deep_tbl = {val}"


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    k = "a." * n + "k"
    return f"{k} = 1"


@composite
def deep_mixed_nesting_doc(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    val = "[{a=" * n + "1" + "}]" * n
    return f"deep_mix = {val}"


@composite
def deep_quoted_mixed_doc(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    val = '[{"k"=' * n + "1" + "}]" * n
    return f"deep_qmix = {val}"


# --- Sibling Keys (Rule 17) ---


@composite
def many_siblings_doc(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[flat_table]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    *([valid_document()] * 20),
    *([empty_document()] * 3),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_mixed_nesting_doc(),
    deep_quoted_mixed_doc(),
    many_siblings_doc(),
)