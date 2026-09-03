"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-08-21T09:22:08.683484+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

ALPHA_NUM_DASH_UNDERSCORE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'()*+,-./:;<=>?@[]^_`{|}~ "
LITERAL_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!\"#$%&()*+,-./:;<=>?@[]^_`{|}~ "

unquoted_key_strat = st.text(alphabet=ALPHA_NUM_DASH_UNDERSCORE, min_size=1, max_size=10)
quoted_key_strat = st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=10).map(lambda s: f'"{s}"')
simple_key_strat = st.one_of(unquoted_key_strat, quoted_key_strat)

@composite
def dotted_key_strat(draw):
    parts = draw(st.lists(simple_key_strat, min_size=2, max_size=4))
    return ".".join(parts)

key_strat = st.one_of(simple_key_strat, dotted_key_strat())

bool_strat = st.sampled_from(["true", "false"])

int_strat = st.one_of(
    st.integers().map(str),
    st.sampled_from([
        "0", "-0", "9223372036854775807", "-9223372036854775808",
        "9223372036854775808", "-9223372036854775809", "18446744073709551615"
    ]),
    st.sampled_from(["00", "07", "007", "0123", "-05"]),
    st.sampled_from(["0xDEADBEEF", "0x1234_5678", "0o755", "0o0_7", "0b1101_0010", "1_000_000", "+99_999"])
)

float_strat = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from([
        "0.0", "-0.0", "inf", "-inf", "+inf", "nan", "-nan", "+nan",
        "1.0e+99", "1e-5", "3.14159_26535", "1_0.0_1"
    ])
)

string_strat = st.one_of(
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=10).map(lambda s: f'"{s}"'),
    st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=10).map(lambda s: f"'{s}'"),
    st.text(alphabet=BASIC_STR_CHARS + "\n ", min_size=0, max_size=15).map(lambda s: f'"""{s}"""'),
    st.text(alphabet=LITERAL_STR_CHARS + "\n ", min_size=0, max_size=15).map(lambda s: f"'''{s}'''"),
    st.sampled_from([
        '"hello\\nworld"', '"escaped \\" quote"', '"unicode \\u0041 \\U0001F600"',
        '"bad escape \\z"', '"invalid unicode \\uGGGG"'
    ])
)

@composite
def datetime_strat(draw):
    y = draw(st.integers(1970, 2099))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 31))
    h = draw(st.integers(0, 23))
    mi = draw(st.integers(0, 59))
    s = draw(st.integers(0, 59))
    frac = draw(st.sampled_from(["", ".123", ".9999999999999999999", ".000000001"]))
    offset = draw(st.sampled_from(["", "Z", "+00:00", "-08:00", "+05:30"]))
    delim = draw(st.sampled_from(["T", "t", " "]))
    
    kind = draw(st.sampled_from(["full", "local_dt", "date", "time"]))
    if kind == "full":
        return f"{y:04d}-{m:02d}-{d:02d}{delim}{h:02d}:{mi:02d}:{s:02d}{frac}{offset}"
    elif kind == "local_dt":
        return f"{y:04d}-{m:02d}-{d:02d}{delim}{h:02d}:{mi:02d}:{s:02d}{frac}"
    elif kind == "date":
        return f"{y:04d}-{m:02d}-{d:02d}"
    else:
        return f"{h:02d}:{mi:02d}:{s:02d}{frac}"

scalar_value = st.one_of(bool_strat, int_strat, float_strat, string_strat, datetime_strat())

@composite
def toml_value(draw, depth=0):
    if depth >= 30:
        return draw(scalar_value)
    
    kind = draw(st.sampled_from(["scalar", "array", "inline"]))
    if kind == "scalar":
        return draw(scalar_value)
    elif kind == "array":
        num_elems = draw(st.integers(0, 4))
        elems = [draw(toml_value(depth=depth + 1)) for _ in range(num_elems)]
        comma = draw(st.sampled_from([", ", ",", ", \n", ""])) if elems else ""
        return f"[{', '.join(elems)}{comma}]"
    else:
        num_pairs = draw(st.integers(0, 4))
        pairs = []
        for _ in range(num_pairs):
            k = draw(key_strat)
            v = draw(toml_value(depth=depth + 1))
            pairs.append(f"{k} = {v}")
        trailing_comma = draw(st.sampled_from([", ", "", ","])) if pairs else ""
        return f"{{{', '.join(pairs)}{trailing_comma}}}"

@composite
def deep_array_value(draw, depth=0):
    if depth >= 200:
        return draw(scalar_value)
    choice = draw(st.integers(1, 3))
    if choice == 1:
        val = draw(deep_array_value(depth=depth + 1))
        return f"[{val}]"
    elif choice == 2:
        k = draw(key_strat)
        val = draw(deep_array_value(depth=depth + 1))
        return f"{{{k} = {val}}}"
    else:
        return draw(scalar_value)

@composite
def key_value_pair(draw, deep=False):
    k = draw(key_strat)
    v = draw(deep_array_value()) if deep else draw(toml_value())
    eq = draw(st.sampled_from([" = ", "=", "  =  "]))
    return f"{k}{eq}{v}"

@composite
def table_header(draw):
    k = draw(key_strat)
    is_array_table = draw(st.booleans())
    if is_array_table:
        return f"[[{k}]]"
    else:
        return f"[{k}]"

comment_strat = st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(lambda s: f"# {s}")

malformed_line_strat = st.sampled_from([
    "key = ",
    "= value",
    "key value",
    "[unclosed_table",
    "[[unclosed_array_table",
    "{ unclosed = inline",
    "\"unclosed_string = 123",
    "key = { a = 1, b = 2, }"
])

@composite
def document_builder(draw, deep_bias=False):
    num_lines = draw(st.integers(0, 15))
    lines = []
    dup_key = draw(key_strat)
    
    for _ in range(num_lines):
        line_type = draw(st.sampled_from([
            "pair", "pair", "table", "comment", "blank", "dup_pair", "malformed"
        ]))
        
        if line_type == "pair":
            lines.append(draw(key_value_pair(deep=deep_bias)))
        elif line_type == "dup_pair":
            v = draw(toml_value())
            lines.append(f"{dup_key} = {v}")
        elif line_type == "table":
            lines.append(draw(table_header()))
        elif line_type == "comment":
            lines.append(draw(comment_strat))
        elif line_type == "blank":
            lines.append("")
        elif line_type == "malformed":
            lines.append(draw(malformed_line_strat))
            
    return "\n".join(lines)

toml_strategy = st.one_of(
    document_builder(deep_bias=False),
    document_builder(deep_bias=True),
    st.just("")
)