"""Generated strategy - iteration 0, attempt 1.
accepted: False
generated: 2026-08-19T11:29:34.146283+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&'()*+,-./:;<=>?@[]^_`{|}~"

unquoted_key_st = st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=15)

escapes = st.one_of(
    st.just('\\"'), st.just('\\\\'), st.just('\\b'), st.just('\\f'),
    st.just('\\n'), st.just('\\r'), st.just('\\t'),
    st.integers(0, 0xFFFF).map(lambda x: f"\\u{x:04x}"),
    st.integers(0, 0x10FFFF).map(lambda x: f"\\U{x:08x}"),
    st.just('\\z')
)

@composite
def basic_string_val(draw):
    parts = draw(st.lists(st.one_of(
        st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=10),
        escapes
    ), min_size=0, max_size=5))
    return f'"{"".join(parts)}"'

@composite
def literal_string_val(draw):
    s = draw(st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15))
    return f"'{s}'"

@composite
def ml_basic_string_val(draw):
    s = draw(st.text(alphabet=BASIC_STR_CHARS + "\n\t ", min_size=0, max_size=20))
    return f'"""{s}"""'

@composite
def ml_literal_string_val(draw):
    s = draw(st.text(alphabet=BASIC_STR_CHARS + "\n\t ", min_size=0, max_size=20))
    return f"'''{s}'''"

string_val = st.one_of(
    basic_string_val(),
    literal_string_val(),
    ml_basic_string_val(),
    ml_literal_string_val()
)

quoted_key_st = st.one_of(basic_string_val(), literal_string_val())
simple_key_st = st.one_of(unquoted_key_st, quoted_key_st)

@composite
def dotted_key_st(draw):
    keys = draw(st.lists(simple_key_st, min_size=2, max_size=4))
    return ".".join(keys)

key_st = st.one_of(simple_key_st, dotted_key_st)

int_val = st.one_of(
    st.integers().map(str),
    st.just("9223372036854775808"),
    st.just("-9223372036854775809"),
    st.just("007"),
    st.just("00000"),
    st.integers(-1000, 1000).map(lambda x: f"{x:_d}"),
    st.integers(0, 0xFFFFFFFF).map(lambda x: f"0x{x:x}"),
    st.integers(0, 0o777777).map(lambda x: f"0o{x:o}"),
    st.integers(0, 0b11111111).map(lambda x: f"0b{x:b}")
)

float_val = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.just("inf"), st.just("-inf"), st.just("nan"), st.just("+nan"),
    st.just("0.0"), st.just("-0.0"), st.just("1e6"), st.just("1.5e-10")
)

bool_val = st.one_of(st.just("true"), st.just("false"))

@composite
def offset_date_time_val(draw):
    y = draw(st.integers(1970, 2038))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 28))
    h = draw(st.integers(0, 23))
    mi = draw(st.integers(0, 59))
    s = draw(st.integers(0, 59))
    
    has_frac = draw(st.booleans())
    frac_str = ""
    if has_frac:
        frac_digits = draw(st.one_of(
            st.integers(1, 6).map(lambda k: f".{k:03d}"),
            st.just(".9999999999999999999")
        ))
        frac_str = frac_digits
        
    delim = draw(st.sampled_from(["T", "t", " "]))
    offset = draw(st.sampled_from(["Z", "+00:00", "-07:00", "+05:30"]))
    return f"{y:04d}-{m:02d}-{d:02d}{delim}{h:02d}:{mi:02d}:{s:02d}{frac_str}{offset}"

@composite
def local_date_val(draw):
    y = draw(st.integers(1970, 2038))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 28))
    return f"{y:04d}-{m:02d}-{d:02d}"

@composite
def local_time_val(draw):
    h = draw(st.integers(0, 23))
    mi = draw(st.integers(0, 59))
    s = draw(st.integers(0, 59))
    return f"{h:02d}:{mi:02d}:{s:02d}"

date_time_val = st.one_of(offset_date_time_val(), local_date_val(), local_time_val())

scalar_val = st.one_of(string_val, int_val, float_val, bool_val, date_time_val)

@composite
def array_val(draw, depth=0):
    if depth >= 5:
        elems = draw(st.lists(scalar_val, min_size=0, max_size=5))
    else:
        child = st.one_of(
            scalar_val,
            array_val(depth=depth+1),
            array_val(depth=depth+1),
            inline_table_val(depth=depth+1)
        )
        elems = draw(st.lists(child, min_size=0, max_size=5))
    
    trailing_comma = draw(st.booleans()) and len(elems) > 0
    comma_str = "," if trailing_comma else ""
    return f"[{', '.join(elems)}{comma_str}]"

@composite
def inline_table_val(draw, depth=0):
    if depth >= 5:
        val_st = scalar_val
    else:
        val_st = st.one_of(
            scalar_val,
            array_val(depth=depth+1),
            inline_table_val(depth=depth+1)
        )
    
    @composite
    def kv_pair(draw):
        k = draw(key_st)
        v = draw(val_st)
        return f"{k} = {v}"
        
    pairs = draw(st.lists(kv_pair(), min_size=0, max_size=4))
    trailing = draw(st.booleans()) and len(pairs) > 0
    trail_str = "," if trailing else ""
    return f"{{{', '.join(pairs)}{trail_str}}}"

value_st = st.one_of(
    scalar_val,
    array_val(),
    inline_table_val()
)

@composite
def key_value_line(draw):
    k = draw(key_st)
    v = draw(value_st)
    comment = f" # {draw(st.text(alphabet=BASIC_STR_CHARS, max_size=10))}" if draw(st.booleans()) else ""
    return f"{k} = {v}{comment}"

@composite
def table_header(draw):
    k = draw(key_st)
    comment = f" # {draw(st.text(alphabet=BASIC_STR_CHARS, max_size=10))}" if draw(st.booleans()) else ""
    return f"[{k}]{comment}"

@composite
def array_table_header(draw):
    k = draw(key_st)
    comment = f" # {draw(st.text(alphabet=BASIC_STR_CHARS, max_size=10))}" if draw(st.booleans()) else ""
    return f"[[{k}]]{comment}"

@composite
def comment_line(draw):
    text = draw(st.text(alphabet=BASIC_STR_CHARS, max_size=20))
    return f"#{text}"

@composite
def malformed_line(draw):
    k = draw(key_st)
    v = draw(scalar_val)
    choice = draw(st.integers(0, 4))
    if choice == 0:
        return f"{k} {v}"
    elif choice == 1:
        return f"[{k}"
    elif choice == 2:
        return f'{k} = "{v}'
    elif choice == 3:
        return f"{k} = {v},"
    else:
        return f"{k} = \\"

@composite
def ordinary_document(draw):
    if draw(st.booleans()) and draw(st.booleans()):
        return ""
        
    line_st = st.one_of(
        key_value_line(),
        table_header(),
        array_table_header(),
        comment_line(),
        malformed_line()
    )
    lines = draw(st.lists(line_st, min_size=0, max_size=15))
    return "\n".join(lines)

@composite
def scale_deep_nesting(draw):
    n = draw(st.integers(min_value=1000, max_value=48000))
    open_brackets = "[" * n
    close_brackets = "]" * n
    val = draw(scalar_val)
    k = draw(unquoted_key_st)
    return f"{k} = {open_brackets}{val}{close_brackets}"

@composite
def scale_large_array(draw):
    n = draw(st.integers(min_value=1000, max_value=25000))
    val = draw(st.one_of(st.just("1"), st.just("true"), st.just('"x"')))
    elems = f"{val}," * (n - 1) + val
    k = draw(unquoted_key_st)
    return f"{k} = [{elems}]"

@composite
def scale_huge_namespace(draw):
    n = draw(st.integers(min_value=500, max_value=5000))
    prefix = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=5))
    lines = [f"{prefix}_{i} = {i}" for i in range(n)]
    header = draw(table_header())
    return header + "\n" + "\n".join(lines)

@composite
def scale_long_tokens(draw):
    length = draw(st.integers(min_value=10000, max_value=100000))
    key_part = "a" * length
    val_part = "x" * length
    choice = draw(st.integers(0, 1))
    if choice == 0:
        return f'{key_part} = "{val_part}"'
    else:
        return f'["{key_part}"]\n{key_part} = 1'

toml_strategy = st.one_of(
    ordinary_document(),
    ordinary_document(),
    ordinary_document(),
    ordinary_document(),
    ordinary_document(),
    scale_deep_nesting(),
    scale_large_array(),
    scale_huge_namespace(),
    scale_long_tokens()
)