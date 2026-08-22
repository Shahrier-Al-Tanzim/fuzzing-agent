"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-08-22T08:40:52.243132+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Alphabets for safe string construction without unescaped special characters
UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_SAFE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ~!@#$%^&*()_+-=[]{}|;:,.<>/?"
LITERAL_SAFE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ~!@#$%^&*()_+-=[]{}\\|;:,.<>/?"

# Key strategies
unquoted_key_st = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
basic_key_st = st.text(alphabet=BASIC_SAFE_CHARS, min_size=0, max_size=10).map(lambda s: f'"{s}"')
literal_key_st = st.text(alphabet=LITERAL_SAFE_CHARS, min_size=0, max_size=10).map(lambda s: f"'{s}'")
simple_key_st = st.one_of(unquoted_key_st, basic_key_st, literal_key_st)
dotted_key_st = st.lists(simple_key_st, min_size=2, max_size=4).map(lambda parts: ".".join(parts))

# Reuse fixed keys to explicitly generate duplicate keys
frequent_keys = st.sampled_from(["a", "b", "c", "x", "y", "z", "a.b", "x.y"])
key_st = st.one_of(simple_key_st, dotted_key_st, frequent_keys)

# Extreme integers & integer divergences (#3 overflow, #4 leading zero)
extreme_ints = st.sampled_from([
    "0", "-0", "+0",
    "9223372036854775807", "-9223372036854775808",  # INT64 bounds
    "9223372036854775808", "-9223372036854775809",  # Divergence #3: past INT64
    "18446744073709551615",
    "007", "01234", "-005", "00",                   # Divergence #4: leading zero decimal
    "1_000_000", "+123", "-456"
])
arbitrary_int = st.integers().map(str)
hex_int = st.integers(min_value=0, max_value=0xFFFFFFFF).map(lambda x: f"0x{x:x}")
oct_int = st.integers(min_value=0, max_value=0o777777).map(lambda x: f"0o{x:o}")
bin_int = st.integers(min_value=0, max_value=0b11111111).map(lambda x: f"0b{x:b}")

integer_val = st.one_of(extreme_ints, arbitrary_int, hex_int, oct_int, bin_int)

# Floats
float_specials = st.sampled_from([
    "0.0", "-0.0", "+0.0", "inf", "-inf", "+inf", "nan", "-nan", "+nan",
    "1e9999", "-1e9999", "3.14159", "1.0e+6", "-2E-3", "1_000.000_1"
])
arbitrary_float = st.floats(allow_nan=True, allow_infinity=True).map(str)
float_val = st.one_of(float_specials, arbitrary_float)

# Booleans
bool_val = st.sampled_from(["true", "false"])

# Date / Time with over-long fractional seconds (Divergence #2)
@composite
def date_time_val(draw):
    y = draw(st.integers(1970, 2038))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 28))
    hh = draw(st.integers(0, 23))
    mm = draw(st.integers(0, 59))
    ss = draw(st.integers(0, 59))
    
    frac_choice = draw(st.sampled_from(["none", "normal", "overlong"]))
    if frac_choice == "normal":
        frac = f".{draw(st.integers(0, 999999)):06d}"
    elif frac_choice == "overlong":
        # Divergence #2: fractional seconds beyond microsecond precision (e.g. 19 digits)
        digits = "".join(draw(st.lists(st.sampled_from("0123456789"), min_size=15, max_size=25)))
        frac = f".{digits}"
    else:
        frac = ""
        
    date_part = f"{y:04d}-{m:02d}-{d:02d}"
    time_part = f"{hh:02d}:{mm:02d}:{ss:02d}{frac}"
    delim = draw(st.sampled_from(["T", "t", " "]))
    tz = draw(st.sampled_from(["Z", "+00:00", "-07:00", "+05:30", ""]))
    
    dt_type = draw(st.sampled_from(["offset_datetime", "local_datetime", "local_date", "local_time"]))
    if dt_type == "offset_datetime":
        return f"{date_part}{delim}{time_part}{tz if tz else 'Z'}"
    elif dt_type == "local_datetime":
        return f"{date_part}{delim}{time_part}"
    elif dt_type == "local_date":
        return date_part
    else:
        return time_part

# Strings (basic, literal, multiline, escapes)
escapes = st.sampled_from(['\\"', '\\\\', '\\b', '\\f', '\\n', '\\r', '\\t', '\\u0020', '\\U0001F600', '\\z'])

@composite
def basic_string_val(draw):
    parts = draw(st.lists(st.one_of(
        st.text(alphabet=BASIC_SAFE_CHARS, min_size=1, max_size=5),
        escapes
    ), max_size=5))
    return f'"{ "".join(parts) }"'

@composite
def ml_basic_string_val(draw):
    content = draw(st.text(alphabet=BASIC_SAFE_CHARS + "\n\r\t", max_size=20))
    return f'"""{content}"""'

@composite
def literal_string_val(draw):
    content = draw(st.text(alphabet=LITERAL_SAFE_CHARS, max_size=15))
    return f"'{content}'"

@composite
def ml_literal_string_val(draw):
    content = draw(st.text(alphabet=LITERAL_SAFE_CHARS + "\n\r\t", max_size=20))
    return f"'''{content}'''"

string_val = st.one_of(
    basic_string_val(),
    ml_basic_string_val(),
    literal_string_val(),
    ml_literal_string_val()
)

scalar_val = st.one_of(integer_val, float_val, bool_val, date_time_val(), string_val)

# Recursive nested structures
@composite
def inline_table_val(draw, depth=0):
    if depth >= 20:
        val_st = scalar_val
    else:
        val_st = st.one_of(scalar_val, array_val(depth=depth+1), inline_table_val(depth=depth+1))
    
    num_pairs = draw(st.integers(0, 4))
    pairs = []
    for _ in range(num_pairs):
        k = draw(key_st)
        v = draw(val_st)
        pairs.append(f"{k} = {v}")
    
    body = ", ".join(pairs)
    # Divergence #1: trailing comma in inline table
    if pairs and draw(st.booleans()):
        body += ","
    return f"{{{body}}}"

@composite
def array_val(draw, depth=0):
    if depth >= 20:
        elem_st = scalar_val
    else:
        elem_st = st.one_of(
            scalar_val, scalar_val,
            array_val(depth=depth+1), array_val(depth=depth+1),
            inline_table_val(depth=depth+1)
        )
    elems = draw(st.lists(elem_st, max_size=5))
    body = ", ".join(elems)
    if elems and draw(st.booleans()):
        body += ","
    return f"[{body}]"

@composite
def value_val(draw, depth=0):
    return draw(st.one_of(
        scalar_val,
        scalar_val,
        array_val(depth=depth),
        inline_table_val(depth=depth)
    ))

# Deep recursion strategy specifically targeting parser recursion limit / stack overflow (Divergence #5)
@composite
def deep_array_val(draw, depth=0):
    if depth >= 200:
        return f"[{draw(scalar_val)}]"
    inner = draw(st.one_of(
        deep_array_val(depth=depth+1),
        deep_array_val(depth=depth+1),
        scalar_val
    ))
    return f"[{inner}]"

# Document components
@composite
def pair_val(draw, depth=0):
    k = draw(key_st)
    v = draw(value_val(depth=depth))
    return f"{k} = {v}"

@composite
def table_header(draw):
    k = draw(key_st)
    if draw(st.booleans()):
        return f"[[{k}]]"
    return f"[{k}]"

@composite
def comment_line(draw):
    content = draw(st.text(alphabet=BASIC_SAFE_CHARS, max_size=20))
    return f"# {content}"

@composite
def standard_document(draw):
    lines = draw(st.lists(
        st.one_of(
            pair_val(depth=0),
            pair_val(depth=0),
            table_header(),
            comment_line(),
            st.just("")
        ),
        min_size=0, max_size=15
    ))
    return "\n".join(lines)

@composite
def deep_nested_document(draw):
    k = draw(key_st)
    v = draw(deep_array_val(depth=0))
    return f"{k} = {v}"

# Top-level strategy yielding complete TOML documents as Python strings
toml_strategy = st.one_of(
    standard_document(),
    deep_nested_document(),
    st.just("")
)