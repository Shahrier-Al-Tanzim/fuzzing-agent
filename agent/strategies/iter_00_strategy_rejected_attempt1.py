"""Generated strategy - iteration 0, attempt 1.
accepted: False
generated: 2026-08-21T06:26:03.580364+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_QUOTED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ =.,/?:;!@#$%^&*()[]{}<>+|~`"

@composite
def scalar_value(draw):
    return draw(st.one_of(
        # Integers (extreme bounds, normal, leading zero divergence, hex/oct/bin, underscores)
        st.integers(-1000, 1000).map(str),
        st.sampled_from([
            "9223372036854775807", "-9223372036854775808",
            "9223372036854775808", "-9223372036854775809",
            "18446744073709551615"
        ]),
        st.sampled_from(["007", "0123", "0000", "+01", "-02"]),
        st.integers(0, 65535).map(lambda x: f"0x{x:x}"),
        st.integers(0, 511).map(lambda x: f"0o{x:o}"),
        st.integers(0, 255).map(lambda x: f"0b{x:b}"),
        st.sampled_from(["1_000", "1_000_000", "0x12_34", "0o7_7", "0b1_0_1"]),
        # Floats (infs, nans, exponents, special representations)
        st.floats(allow_nan=True, allow_infinity=True).map(str),
        st.sampled_from(["0.0", "-0.0", "inf", "-inf", "+inf", "nan", "-nan", "1e10", "1e-10", "1.5e+5", "0.0e0", "1_000.000_1"]),
        # Booleans
        st.sampled_from(["true", "false"]),
        # Strings (basic, literal, multiline, escapes)
        st.text(alphabet=SAFE_QUOTED_CHARS, min_size=0, max_size=15).map(lambda s: f'"{s}"'),
        st.sampled_from([
            '"hello\\nworld"', '"escaped \\" quote"', '"unicode \\u0041"',
            '"unicode \\U0001F600"', '"invalid \\z escape"', '"bad \\u123 unicode"'
        ]),
        st.text(alphabet=SAFE_QUOTED_CHARS, min_size=0, max_size=15).map(lambda s: f"'{s}'"),
        st.text(alphabet=SAFE_QUOTED_CHARS + "\n", min_size=0, max_size=20).map(lambda s: f'"""{s}"""'),
        st.text(alphabet=SAFE_QUOTED_CHARS + "\n", min_size=0, max_size=20).map(lambda s: f"'''{s}'''"),
        # Date & Time (normal + overlong sub-second precision divergence)
        st.tuples(st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28), st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(
            lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
        ),
        st.sampled_from([
            "1979-05-27T00:32:00.9999999999999999999Z",
            "2020-01-01T12:00:00.123456789123456789+00:00",
            "12:00:00.1234567899999999"
        ]),
        st.tuples(st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28)).map(
            lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
        ),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(
            lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"
        ),
    ))

@composite
def toml_value(draw, depth=0):
    if depth >= 3:
        return draw(scalar_value())
    
    choice = draw(st.integers(0, 3))
    if choice == 0:
        return draw(scalar_value())
    elif choice == 1:
        elems = draw(st.lists(toml_value(depth=depth + 1), min_size=0, max_size=4))
        trailing = draw(st.sampled_from(["", ",", ", "])) if elems else ""
        return f"[{', '.join(elems)}{trailing}]"
    elif choice == 2:
        pairs = draw(st.lists(
            st.tuples(
                st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=5),
                toml_value(depth=depth + 1)
            ),
            min_size=0, max_size=4
        ))
        formatted_pairs = [f"{k} = {v}" for k, v in pairs]
        # Includes trailing comma in inline table (Divergence #1)
        trailing = draw(st.sampled_from(["", ",", ", "])) if formatted_pairs else ""
        return f"{{{', '.join(formatted_pairs)}{trailing}}}"
    else:
        val = draw(scalar_value())
        op = draw(st.sampled_from(["[", "{", "[1, 2", "{a = 1", f"[{val}"]))
        return op

@composite
def key_name(draw):
    return draw(st.one_of(
        st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10),
        st.text(alphabet=SAFE_QUOTED_CHARS, min_size=0, max_size=10).map(lambda s: f'"{s}"'),
        st.text(alphabet=SAFE_QUOTED_CHARS, min_size=0, max_size=10).map(lambda s: f"'{s}'"),
        st.lists(
            st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=5),
            min_size=2, max_size=3
        ).map(lambda parts: ".".join(parts))
    ))

@composite
def key_value_pair(draw):
    k = draw(key_name())
    v = draw(toml_value())
    eq = draw(st.sampled_from([" = ", "=", " =  ", "="]))
    if draw(st.booleans()):
        return f"{k}{eq}{v}"
    else:
        variant = draw(st.sampled_from([
            f"{k}{eq}{v}",
            f"{k}{eq}{v}\n{k}{eq}{v}",  # duplicate key
            f"{k} {v}",                 # missing equals
            f"#{k} = {v}"               # commented out
        ]))
        return variant

@composite
def table_header(draw):
    k = draw(key_name())
    is_array_table = draw(st.booleans())
    if is_array_table:
        return f"[[{k}]]"
    else:
        return f"[{k}]"

@composite
def document(draw):
    n = draw(st.integers(0, 10))
    if n == 0:
        return draw(st.sampled_from(["", "\n", "# Empty document\n"]))
    
    items = []
    for _ in range(n):
        item_type = draw(st.integers(0, 3))
        if item_type == 0:
            items.append(draw(key_value_pair()))
        elif item_type == 1:
            items.append(draw(table_header()))
        elif item_type == 2:
            comment_str = draw(st.text(alphabet=SAFE_QUOTED_CHARS, min_size=0, max_size=20))
            items.append(f"# {comment_str}")
        else:
            tbl = draw(table_header())
            pair1 = draw(key_value_pair())
            pair2 = draw(key_value_pair())
            items.append(f"{tbl}\n{pair1}\n{pair2}")
            
    return "\n".join(items)

# High-depth integer repetition triggers for C stack overflow
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
    key = "a." * n + "k"
    return f"{key} = 1"

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

# Sibling key count trigger for linear key lookup timeout
@composite
def many_siblings_doc(draw):
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
    many_siblings_doc(),
)