"""Generated strategy - iteration 0, attempt 2.
accepted: True
generated: 2026-08-19T11:31:25.608826+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_QUOTED_CHARS = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'()*+,-./:;<=>?@[]^_`{|}~"
SAFE_LITERAL_CHARS = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!\"#$%&()*+,-./:;<=>?@[]^_`{|}~"

# --- Keys ---

@composite
def unquoted_key(draw):
    return draw(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=15))

@composite
def quoted_key(draw):
    s = draw(st.text(alphabet=SAFE_QUOTED_CHARS, min_size=0, max_size=15))
    return f'"{s}"'

@composite
def key_st(draw):
    return draw(st.one_of(unquoted_key(), quoted_key()))

@composite
def dotted_key_st(draw):
    parts = draw(st.lists(key_st(), min_size=2, max_size=4))
    return ".".join(parts)

@composite
def any_key(draw):
    return draw(st.one_of(key_st(), dotted_key_st()))

# --- Scalar Values ---

@composite
def scalar_int(draw):
    choice = draw(st.integers(0, 5))
    if choice == 0:
        return draw(st.sampled_from([
            "0", "-0",
            "9223372036854775807",   # INT64_MAX
            "-9223372036854775808",  # INT64_MIN
            "9223372036854775808",   # INT64_MAX + 1 (Divergence #3)
            "007",                   # Leading zero int (Divergence #4)
            "0123",                  # Leading zero int
        ]))
    elif choice == 1:
        val = draw(st.integers(min_value=0, max_value=0xFFFFFFFF))
        return f"0x{val:x}"
    elif choice == 2:
        val = draw(st.integers(min_value=0, max_value=0o777777))
        return f"0o{val:o}"
    elif choice == 3:
        val = draw(st.integers(min_value=0, max_value=0b11111111))
        return f"0b{val:b}"
    elif choice == 4:
        return draw(st.sampled_from(["1_000_000", "0x12_34", "0o7_77", "0b1_0"]))
    else:
        return str(draw(st.integers(min_value=-1000000, max_value=1000000)))

@composite
def scalar_float(draw):
    choice = draw(st.integers(0, 1))
    if choice == 0:
        return draw(st.sampled_from(["inf", "-inf", "+inf", "nan", "-nan", "+nan", "1e10", "1.5e-3", "-0.0"]))
    else:
        return str(draw(st.floats(allow_nan=True, allow_infinity=True)))

@composite
def scalar_bool(draw):
    return "true" if draw(st.booleans()) else "false"

@composite
def scalar_string(draw):
    kind = draw(st.integers(0, 3))
    if kind == 0:
        content = draw(st.text(alphabet=SAFE_QUOTED_CHARS, min_size=0, max_size=20))
        extra = draw(st.sampled_from(["", "\\n", "\\t", "\\\"", "\\\\", "\\u0020", "\\U00000020", "\\z"]))
        return f'"{content}{extra}"'
    elif kind == 1:
        content = draw(st.text(alphabet=SAFE_LITERAL_CHARS, min_size=0, max_size=20))
        return f"'{content}'"
    elif kind == 2:
        content = draw(st.text(alphabet=SAFE_QUOTED_CHARS, min_size=0, max_size=20))
        return f'"""\n{content}\n"""'
    else:
        content = draw(st.text(alphabet=SAFE_LITERAL_CHARS, min_size=0, max_size=20))
        return f"'''\n{content}\n'''"

@composite
def scalar_datetime(draw):
    y = draw(st.integers(1970, 2030))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 28))
    h = draw(st.integers(0, 23))
    mi = draw(st.integers(0, 59))
    s = draw(st.integers(0, 59))

    frac_choice = draw(st.integers(0, 2))
    if frac_choice == 0:
        frac = ""
    elif frac_choice == 1:
        frac = f".{draw(st.integers(0, 999)):03d}"
    else:
        # Divergence #2: over-long fractional seconds (19 digits)
        frac = "." + "9" * draw(st.integers(10, 20))

    date_str = f"{y:04d}-{m:02d}-{d:02d}"
    time_str = f"{h:02d}:{mi:02d}:{s:02d}{frac}"

    dt_type = draw(st.integers(0, 3))
    if dt_type == 0:
        return f"{date_str}T{time_str}Z"
    elif dt_type == 1:
        return f"{date_str}T{time_str}"
    elif dt_type == 2:
        return date_str
    else:
        return time_str

@composite
def simple_value(draw):
    return draw(st.one_of(
        scalar_int(),
        scalar_float(),
        scalar_bool(),
        scalar_string(),
        scalar_datetime(),
    ))

# --- Recursive Containers ---

@composite
def array_val(draw, depth=0):
    if depth >= 4:
        elems = draw(st.lists(simple_value(), min_size=0, max_size=4))
    else:
        elem_st = st.one_of(
            simple_value(),
            simple_value(),
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
        )
        elems = draw(st.lists(elem_st, min_size=0, max_size=4))

    comma = "," if draw(st.booleans()) and elems else ""
    return f"[{', '.join(elems)}{comma}]"

@composite
def inline_table_val(draw, depth=0):
    if depth >= 4:
        pairs = draw(st.lists(st.tuples(key_st(), simple_value()), min_size=0, max_size=3))
    else:
        val_st = st.one_of(
            simple_value(),
            simple_value(),
            array_val(depth=depth + 1),
            inline_table_val(depth=depth + 1),
        )
        pairs = draw(st.lists(st.tuples(key_st(), val_st), min_size=0, max_size=3))

    formatted_pairs = [f"{k} = {v}" for k, v in pairs]
    # Divergence #1: Trailing comma in inline table
    trailing = "," if draw(st.booleans()) and formatted_pairs else ""
    return "{" + f"{', '.join(formatted_pairs)}{trailing}" + "}"

@composite
def value_st(draw, depth=0):
    return draw(st.one_of(
        simple_value(),
        array_val(depth=depth),
        inline_table_val(depth=depth),
    ))

# --- Top-Level Statements ---

@composite
def pair_st(draw):
    k = draw(any_key())
    v = draw(value_st())
    return f"{k} = {v}"

@composite
def table_st(draw):
    k = draw(any_key())
    is_array_table = draw(st.booleans())
    header = f"[[{k}]]" if is_array_table else f"[{k}]"
    pairs = draw(st.lists(pair_st(), min_size=0, max_size=4))
    return "\n".join([header] + pairs)

@composite
def comment_st(draw):
    text = draw(st.text(alphabet=SAFE_QUOTED_CHARS, min_size=0, max_size=15))
    return f"# {text}"

@composite
def standard_document(draw):
    items = draw(st.lists(
        st.one_of(pair_st(), table_st(), comment_st()),
        min_size=0, max_size=12
    ))
    if draw(st.booleans()) and items:
        items.append(items[0])  # duplicate key / table test
    return "\n".join(items)

# --- Extreme Scale Branches ---

@composite
def scale_deep_array(draw):
    n = draw(st.integers(min_value=50, max_value=300))
    k = draw(key_st())
    open_b = "[" * n
    close_b = "]" * n
    val = draw(simple_value())
    return f"{k} = {open_b}{val}{close_b}"

@composite
def scale_deep_inline_table(draw):
    n = draw(st.integers(min_value=30, max_value=150))
    k_root = draw(key_st())
    parts = [f"k{i} = {{" for i in range(n)]
    tail = "x = 1" + "}" * n
    return f"{k_root} = " + " ".join(parts) + " " + tail

@composite
def scale_large_array(draw):
    n = draw(st.integers(min_value=300, max_value=1500))
    k = draw(key_st())
    vals = [str(draw(st.integers(0, 9))) for _ in range(n)]
    return f"{k} = [{', '.join(vals)}]"

@composite
def scale_long_key_or_string(draw):
    n = draw(st.integers(min_value=1000, max_value=10000))
    choice = draw(st.integers(0, 1))
    if choice == 0:
        key_parts = ["a" * 10] * (n // 10)
        k = ".".join(key_parts)
        return f"{k} = 1"
    else:
        k = draw(key_st())
        s = "A" * n
        return f'{k} = "{s}"'

@composite
def scale_many_keys(draw):
    n = draw(st.integers(min_value=200, max_value=800))
    lines = [f"key_{i} = {i}" for i in range(n)]
    return "\n".join(lines)

toml_strategy = st.one_of(
    standard_document(),
    standard_document(),
    standard_document(),
    standard_document(),
    scale_deep_array(),
    scale_deep_inline_table(),
    scale_large_array(),
    scale_long_key_or_string(),
    scale_many_keys(),
)