"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-09-01T19:05:54.177524+00:00
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
    "\\u0000",
    "\\U0001F600",
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
    choice = draw(st.integers(0, 5))
    if choice == 0:
        return "1979-05-27T07:32:00Z"
    elif choice == 1:
        # Divergence #2: over-long fractional seconds
        nines = "9" * draw(st.integers(10, 30))
        return f"1979-05-27T00:32:00.{nines}-07:00"
    elif choice == 2:
        return "1979-05-27 07:32:00-07:00"
    elif choice == 3:
        return "1979-05-27"
    elif choice == 4:
        return "07:32:00"
    else:
        # Generated timestamp with fractional seconds
        t = draw(
            st.tuples(
                st.integers(1970, 2038),
                st.integers(1, 12),
                st.integers(1, 28),
                st.integers(0, 23),
                st.integers(0, 59),
                st.integers(0, 59),
                st.integers(1, 999999999),
            )
        )
        return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]}Z"


@composite
def extreme_scalar_val(draw):
    return draw(
        st.sampled_from([
            "9223372036854775808",  # Divergence #3 (int overflow)
            "-9223372036854775809",
            "18446744073709551615",
            "-18446744073709551616",
            "007",  # Divergence #4 (leading zero)
            "0123",
            "0000",
            "1_000_000",
            "0xDEADBEEF",
            "0o755",
            "0b101010",
            "0x7fffffffffffffff",
            "0xffffffffffffffff",
            "1e309",
            "-1e309",
            "1.0e-300",
            "nan",
            "-nan",
            "inf",
            "-inf",
            "+inf",
            "0.0",
            "-0.0",
            "3.141592653589793",
        ])
    )


@composite
def scalar_val(draw):
    strategy = st.one_of(
        st.integers(-9223372036854775807, 9223372036854775807).map(str),
        extreme_scalar_val(),
        st.floats(allow_nan=True, allow_infinity=True).map(str),
        st.sampled_from(["true", "false"]),
        basic_string_val(),
        literal_string_val(),
        ml_basic_string_val(),
        ml_literal_string_val(),
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
    used_keys = set()
    for i in range(num_pairs):
        k = draw(simple_key())
        if k in used_keys:
            k = f"{k}_{i}"
        used_keys.add(k)
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
    used_top_keys = set()

    # Top level key-value pairs
    num_top = draw(st.integers(1, 4))
    for i in range(num_top):
        k = draw(key_strat())
        while k in used_top_keys:
            k = f"{k}_{i}"
        used_top_keys.add(k)
        v = draw(value_strat(depth=0))
        lines.append(f"{k} = {v}")

    # Sections
    num_sections = draw(st.integers(0, 3))
    used_sections = set()
    for s_idx in range(num_sections):
        sec_name = draw(key_strat())
        is_array_table = draw(st.booleans())

        if is_array_table:
            lines.append(f"[[{sec_name}]]")
        else:
            while sec_name in used_sections or sec_name in used_top_keys:
                sec_name = f"{sec_name}_{s_idx}"
            used_sections.add(sec_name)
            lines.append(f"[{sec_name}]")

        num_pairs = draw(st.integers(1, 4))
        sec_keys = set()
        for p_idx in range(num_pairs):
            k = draw(key_strat())
            while k in sec_keys:
                k = f"{k}_{p_idx}"
            sec_keys.add(k)
            v = draw(value_strat(depth=0))
            lines.append(f"{k} = {v}")

    return "\n".join(lines)


@composite
def diverse_document(draw):
    lines = []
    if draw(st.booleans()):
        lines.append(
            draw(
                st.sampled_from(
                    ["# Configuration file", "# Generated by Hypothesis", ""]
                )
            )
        )

    num_pairs = draw(st.integers(1, 5))
    used_keys = set()
    for i in range(num_pairs):
        k = draw(key_strat())
        if k in used_keys:
            k = f"{k}_{i}"
        used_keys.add(k)

        val_kind = draw(st.integers(0, 7))
        if val_kind == 0:
            v = draw(inline_table_strat(depth=0))
        elif val_kind == 1:
            v = draw(array_strat(depth=0))
        elif val_kind == 2:
            v = draw(date_time_val())
        elif val_kind == 3:
            v = draw(st.one_of(ml_basic_string_val(), ml_literal_string_val()))
        elif val_kind == 4:
            v = draw(extreme_scalar_val())
        elif val_kind == 5:
            v = draw(
                st.sampled_from([
                    "0.0",
                    "-0.0",
                    "1e10",
                    "+inf",
                    "-inf",
                    "nan",
                    "3.14159",
                ])
            )
        else:
            v = draw(scalar_val())

        lines.append(f"{k} = {v}")
        if draw(st.booleans()):
            lines.append(f"# comment for {k}")

    num_tables = draw(st.integers(0, 4))
    table_keys = set()
    for t_i in range(num_tables):
        t_name = draw(simple_key())
        is_array = draw(st.booleans())
        if is_array:
            lines.append(f"[[{t_name}]]")
        else:
            if t_name in table_keys or t_name in used_keys:
                t_name = f"section_{t_i}_{t_name}"
            table_keys.add(t_name)
            lines.append(f"[{t_name}]")

        sub_count = draw(st.integers(1, 3))
        sub_keys = set()
        for sk_i in range(sub_count):
            sk = draw(key_strat())
            if sk in sub_keys:
                sk = f"{sk}_{sk_i}"
            sub_keys.add(sk)
            sv = draw(value_strat(depth=0))
            lines.append(f"{sk} = {sv}")

    return "\n".join(lines)


@composite
def array_table_deep_inline_doc(draw):
    """Deeply nested inline tables inside array-of-tables with extreme numeric/string values."""
    lines = []
    num_tables = draw(st.integers(1, 4))
    for t_i in range(num_tables):
        t_name = draw(simple_key())
        lines.append(f"[[{t_name}]]")
        num_keys = draw(st.integers(1, 4))
        for k_i in range(num_keys):
            k = draw(key_strat())
            depth = draw(st.integers(3, 8))
            val = draw(st.one_of(extreme_scalar_val(), date_time_val(), scalar_val()))
            curr = f"{{ val = {val} }}"
            for d in range(depth - 1):
                trailing = draw(st.sampled_from(["", ","]))
                nest_kind = draw(st.integers(0, 2))
                if nest_kind == 0:
                    curr = f"{{ sub_{d} = {curr}{trailing} }}"
                elif nest_kind == 1:
                    curr = f"[{curr}{trailing}]"
                else:
                    curr = f"{{ k_{d} = [{curr}{trailing}]{trailing} }}"
            lines.append(f"{k} = {curr}")
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
    *([valid_document()] * 18),
    *([diverse_document()] * 18),
    *([array_table_deep_inline_doc()] * 10),
    *([empty_document()] * 3),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    deep_mixed_nesting_doc(),
    deep_quoted_mixed_doc(),
    many_siblings_doc(),
)