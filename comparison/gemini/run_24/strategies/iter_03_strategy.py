"""Generated strategy - iteration 3, attempt 1.
accepted: True
generated: 2026-08-19T20:11:34.142373+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ !#$%&'()*+,-./:;<=>?@[]^_`{|}~\t"
LITERAL_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ !\"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t"
NON_ASCII_CHARS = "ÁÉÍÓÚáéíóúÑñüßäöÖÄ日本語中国語こんにちは世界🚀🔥"

# Key strategies
small_key_pool = st.sampled_from(["a", "b", "c", "x", "y", "item", "data", "owner"])
unquoted_key = st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=10)
basic_key = st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=10).map(lambda s: f'"{s}"')
literal_key = st.text(alphabet=LITERAL_STR_CHARS, min_size=1, max_size=10).map(lambda s: f"'{s}'")

simple_key = st.one_of(small_key_pool, unquoted_key, basic_key, literal_key)

@composite
def dotted_key(draw):
    parts = draw(st.lists(st.one_of(small_key_pool, simple_key), min_size=2, max_size=4))
    return ".".join(parts)

key_strat = st.one_of(simple_key, dotted_key())

# Extreme & Divergence Integers
scalar_int = st.one_of(
    st.integers(min_value=-9223372036854775808, max_value=9223372036854775807).map(str),
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(lambda x: f"0x{x:X}"),
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(lambda x: f"0x{x:x}"),
    st.integers(min_value=0, max_value=0o777777).map(lambda x: f"0o{x:o}"),
    st.integers(min_value=0, max_value=255).map(lambda x: f"0b{x:b}"),
    st.sampled_from([
        "9223372036854775808",
        "-9223372036854775809",
        "99999999999999999999999999999",
        "-99999999999999999999999999999",
        "007", "0123", "000", "-08",
        "1_000_000", "9_223_372_036_854_775_807", "0xDEADBEEF", "0o755", "0b1101", "+0", "-0"
    ])
)

# Extreme Floats
scalar_float = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.tuples(
        st.integers(-1000, 1000),
        st.integers(0, 999),
        st.sampled_from(["e", "E"]),
        st.integers(-30, 30)
    ).map(lambda t: f"{t[0]}.{t[1]:03d}{t[2]}{t[3]}"),
    st.sampled_from([
        "inf", "-inf", "+inf", "nan", "-nan", "+nan",
        "1.0e10", "-1.5e-5", "1.0e+20", "+1.0", "-0.0", "0.0", "1_000.0",
        "1e6", "1e-3", "-1E+10", "1.5E2"
    ])
)

scalar_bool = st.sampled_from(["true", "false"])

# Date times with extreme/divergent fractional seconds precision
@composite
def scalar_datetime(draw):
    y = draw(st.integers(1900, 2100))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 28))
    h = draw(st.integers(0, 23))
    mi = draw(st.integers(0, 59))
    s = draw(st.integers(0, 59))
    frac_digits = draw(st.integers(0, 25))
    frac_str = ""
    if frac_digits > 0:
        frac_str = "." + draw(st.text(alphabet="0123456789", min_size=frac_digits, max_size=frac_digits))
    kind = draw(st.sampled_from(["offset", "offset", "local_d", "local_d", "local_dt", "local_t"]))
    if kind == "local_d":
        return f"{y:04d}-{m:02d}-{d:02d}"
    elif kind == "local_t":
        return f"{h:02d}:{mi:02d}:{s:02d}{frac_str}"
    elif kind == "local_dt":
        delim = draw(st.sampled_from(["T", "t", " "]))
        return f"{y:04d}-{m:02d}-{d:02d}{delim}{h:02d}:{mi:02d}:{s:02d}{frac_str}"
    else:
        delim = draw(st.sampled_from(["T", "t", " "]))
        offset = draw(st.sampled_from(["Z", "+00:00", "-07:00", "+02:00", "+05:30", "z"]))
        return f"{y:04d}-{m:02d}-{d:02d}{delim}{h:02d}:{mi:02d}:{s:02d}{frac_str}{offset}"

# Strings
scalar_string = st.one_of(
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(lambda s: f'"{s}"'),
    st.text(alphabet=BASIC_STR_CHARS + NON_ASCII_CHARS, min_size=1, max_size=15).map(lambda s: f'"{s}"'),
    st.text(alphabet=BASIC_STR_CHARS + NON_ASCII_CHARS + "\n", min_size=0, max_size=30).map(lambda s: f'"""{s}"""'),
    st.sampled_from([
        '"""\nline 1\nline 2\n"""',
        '"""multiline basic string with \\"\\"\\" quotes inside"""',
        '"""\nThe quick brown fox \\\n jumps over the lazy dog.\n"""',
        '"hello\\nworld"', '"tab\\tseparated"', '"quote\\"inside"', '"backslash\\\\"', '"\\u0041"', '"\\U0001F600"'
    ]),
    st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=15).map(lambda s: f"'{s}'"),
    st.text(alphabet=LITERAL_STR_CHARS + NON_ASCII_CHARS, min_size=1, max_size=15).map(lambda s: f"'{s}'"),
    st.text(alphabet=LITERAL_STR_CHARS + NON_ASCII_CHARS + "\n", min_size=0, max_size=30).map(lambda s: f"'''{s}'''"),
    st.sampled_from(['"invalid\\xescape"', '"unclosed string', "'''unclosed multiline"])
)

scalar_value = st.one_of(scalar_int, scalar_float, scalar_bool, scalar_datetime(), scalar_string)

@composite
def make_array(draw, element_strat):
    elems = draw(st.lists(element_strat, min_size=0, max_size=5))
    return f"[{', '.join(elems)}]"

@composite
def make_inline_table(draw, element_strat):
    keys = draw(st.lists(key_strat, min_size=0, max_size=4, unique=True))
    pairs = [f"{k} = {draw(element_strat)}" for k in keys]
    # Includes spec divergence #1: trailing comma in inline tables
    if pairs and draw(st.booleans()):
        return "{" + ", ".join(pairs) + ", }"
    return "{" + ", ".join(pairs) + "}"

value_strat = st.recursive(
    scalar_value,
    lambda children: st.one_of(
        make_array(children),
        make_inline_table(children)
    ),
    max_leaves=25
)

# Deep inline table inside array or table
@composite
def nested_inline_table_val(draw):
    depth = draw(st.integers(1, 5))
    val = draw(scalar_value)
    for _ in range(depth):
        k = draw(simple_key)
        trailing = ", " if draw(st.booleans()) else ""
        val = f"{{{k} = {val}{trailing}}}"
    return val

@composite
def key_value_pair(draw):
    k = draw(key_strat)
    v = draw(st.one_of(value_strat, nested_inline_table_val()))
    comment = draw(st.sampled_from(["", " # comment", " # test"]))
    return f"{k} = {v}{comment}"

@composite
def table_header(draw):
    k = draw(key_strat)
    is_array_table = draw(st.booleans())
    comment = draw(st.sampled_from(["", " # comment"]))
    if is_array_table:
        return f"[[{k}]]{comment}"
    return f"[{k}]{comment}"

@composite
def array_table_block(draw):
    k = draw(st.one_of(st.sampled_from(["arr", "items", "t", "a"]), simple_key))
    num_entries = draw(st.integers(2, 4))
    lines = []
    for _ in range(num_entries):
        lines.append(f"[[{k}]]")
        num_kvs = draw(st.integers(1, 4))
        sub_keys = draw(st.lists(st.sampled_from(["id", "val", "name", "x", "y", "meta", "nested"]), min_size=num_kvs, max_size=num_kvs, unique=True))
        for sub_k in sub_keys:
            sub_v = draw(st.one_of(scalar_value, nested_inline_table_val(), value_strat))
            lines.append(f"{sub_k} = {sub_v}")
    return "\n".join(lines)

comment_line = st.sampled_from(["# just a comment", "   # comment", ""])

@composite
def malformed_line(draw):
    return draw(st.sampled_from([
        "key_without_equals",
        "key = ",
        "= value",
        'unclosed_quote = "hello',
        "unclosed_array = [1, 2, 3",
        "unclosed_inline = {a = 1, b = 2",
        'bad_escape = "\\x"',
        "key = { newlines\nnot_allowed = 1 }",
    ]))

@composite
def document(draw):
    lines = draw(st.lists(
        st.one_of(
            key_value_pair(),
            key_value_pair(),
            key_value_pair(),
            table_header(),
            array_table_block(),
            comment_line,
            malformed_line()
        ),
        min_size=1,
        max_size=12
    ))
    return "\n".join(lines)

@composite
def deep_array_doc(draw):
    depth = draw(st.integers(min_value=10_000, max_value=50_000))
    k = draw(simple_key)
    val = "[" * depth + "1" + "]" * depth
    return f"{k} = {val}"

@composite
def deep_inline_table_doc(draw):
    depth = draw(st.integers(min_value=10_000, max_value=50_000))
    k = draw(simple_key)
    val = "{a=" * depth + "1" + "}" * depth
    return f"{k} = {val}"

@composite
def deep_dotted_key_doc(draw):
    depth = draw(st.integers(min_value=10_000, max_value=50_000))
    key_part = "a." * depth + "k"
    return f"{key_part} = 1"

@composite
def many_siblings_doc(draw):
    n = draw(st.integers(min_value=10_000, max_value=30_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)

toml_strategy = st.one_of(
    document(),
    document(),
    document(),
    document(),
    document(),
    document(),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    many_siblings_doc()
)