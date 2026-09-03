"""Generated strategy - iteration 2, attempt 1.
accepted: True
generated: 2026-09-03T13:48:07.125632+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

# Alphabets and character sets
ASCII_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
UNQUOTED_KEY_CHARS = ASCII_LETTERS + DIGITS + "-_"

NON_ASCII_CHARS = "éàèùâêîôûäëïöüÿçœæñαβγδε☆★€£¥中国語日本語🌍"
SAFE_BASIC_CHARS = ASCII_LETTERS + DIGITS + " !#$%&'()*+,-./:;<=>?@[]^_`{|}~" + NON_ASCII_CHARS
SAFE_LITERAL_CHARS = ASCII_LETTERS + DIGITS + ' "!#$%&()*+,-./:;<=>?@[\\]^_`{|}~' + NON_ASCII_CHARS

# 1. Unicode escape sequences
unicode_escape_strat = st.one_of(
    st.integers(0x0020, 0x007E).map(lambda x: f"\\u{x:04x}"),
    st.integers(0x00A0, 0xD7FF).map(lambda x: f"\\u{x:04X}"),
    st.integers(0x1F600, 0x1F637).map(lambda x: f"\\U{x:08X}"),
    st.sampled_from(["\\n", "\\t", "\\r", "\\\\", "\\\"", "\\b", "\\f"])
)

# 2. Strings with unicode escapes & non-ascii
basic_string_inner = st.lists(
    st.one_of(
        st.text(alphabet=SAFE_BASIC_CHARS, min_size=1, max_size=5),
        unicode_escape_strat
    ),
    min_size=0, max_size=4
).map(lambda parts: "".join(parts))

basic_string_strat = basic_string_inner.map(lambda s: f'"{s}"')
literal_string_strat = st.text(alphabet=SAFE_LITERAL_CHARS, min_size=0, max_size=15).map(lambda s: f"'{s}'")

ml_basic_string_strat = st.lists(
    st.one_of(
        st.text(alphabet=SAFE_BASIC_CHARS + "\n \t", min_size=1, max_size=10),
        unicode_escape_strat
    ),
    min_size=0, max_size=3
).map(lambda parts: f'"""{"".join(parts)}"""')

ml_literal_string_strat = st.text(alphabet=SAFE_LITERAL_CHARS + "\n \t", min_size=0, max_size=20).map(lambda s: f"'''{s}'''")

# Keys with heavy non-ascii representation in quoted variants
unquoted_key_strat = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
quoted_key_strat = st.one_of(
    st.text(alphabet=SAFE_BASIC_CHARS, min_size=1, max_size=10).map(lambda s: f'"{s}"'),
    st.text(alphabet=SAFE_LITERAL_CHARS, min_size=1, max_size=10).map(lambda s: f"'{s}'")
)
simple_key_strat = st.one_of(unquoted_key_strat, quoted_key_strat)
dotted_key_strat = st.lists(simple_key_strat, min_size=2, max_size=4).map(lambda parts: ".".join(parts))
key_strat = st.one_of(simple_key_strat, dotted_key_strat)

# 3. Integers with underscores and overflow
int_underscore_strat = st.one_of(
    st.integers(100, 99999999).map(lambda n: f"{n:_d}"),
    st.integers(-99999999, -100).map(lambda n: f"{n:_d}"),
    st.integers(0, 65535).map(lambda x: f"0x{x:04x}".replace("0x", "0x_")),
    st.integers(0, 255).map(lambda x: f"0b{x:08b}".replace("0b", "0b_"))
)

int_strat = st.one_of(
    st.integers(-9223372036854775808, 9223372036854775807).map(str),
    int_underscore_strat,
    st.sampled_from(["9223372036854775808", "-9223372036854775809", "18446744073709551615"]),
    st.sampled_from(["007", "0123", "00001"]),
    st.integers(0, 65535).map(lambda x: f"0x{x:x}"),
    st.integers(0, 511).map(lambda x: f"0o{x:o}"),
    st.integers(0, 255).map(lambda x: f"0b{x:b}")
)

# Floats, Booleans, Dates/Times
float_strat = st.one_of(
    st.floats(allow_nan=False, allow_infinity=False).map(str),
    st.sampled_from(["inf", "-inf", "nan", "+nan", "+inf", "1e10", "1.5e-3", "1_000.0", "1.0e_2"])
)

bool_strat = st.sampled_from(["true", "false"])

datetime_strat = st.one_of(
    st.tuples(st.integers(1970, 2099), st.integers(1, 12), st.integers(1, 28)).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
    ),
    st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(
        lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"
    ),
    st.tuples(st.integers(1970, 2099), st.integers(1, 12), st.integers(1, 28),
              st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
    ),
    st.just("1979-05-27T00:32:00.9999999999999999999Z")  # Divergence #2
)

scalar_val_strat = st.one_of(
    basic_string_strat,
    literal_string_strat,
    ml_basic_string_strat,
    ml_literal_string_strat,
    int_strat,
    float_strat,
    bool_strat,
    datetime_strat
)

# Single line scalar (no multi-line strings) for inline tables
single_line_scalar_strat = st.one_of(
    basic_string_strat,
    literal_string_strat,
    int_strat,
    float_strat,
    bool_strat,
    datetime_strat
)

@composite
def value_gen(draw, depth=0):
    if depth >= 3:
        return draw(scalar_val_strat)
    return draw(st.one_of(
        scalar_val_strat,
        array_gen(depth=depth + 1),
        inline_table_gen(depth=depth + 1)
    ))

@composite
def single_line_value_gen(draw, depth=0):
    if depth >= 3:
        return draw(single_line_scalar_strat)
    return draw(st.one_of(
        single_line_scalar_strat,
        array_gen(depth=depth + 1),
        inline_table_gen(depth=depth + 1)
    ))

@composite
def array_gen(draw, depth=0):
    elems = draw(st.lists(value_gen(depth=depth + 1), min_size=0, max_size=4))
    trailing = draw(st.sampled_from(["", ","])) if elems else ""
    return f"[{', '.join(elems)}{trailing}]"

@composite
def inline_table_gen(draw, depth=0):
    if draw(st.booleans()) and depth > 0:
        return "{}"
    keys = draw(st.lists(simple_key_strat, min_size=0, max_size=3, unique=True))
    if not keys:
        return "{}"
    pairs = [f"{k} = {draw(single_line_value_gen(depth=depth + 1))}" for k in keys]
    # Divergence #1: trailing comma in inline tables
    trailing = draw(st.sampled_from(["", ","])) if pairs else ""
    return f"{{{', '.join(pairs)}{trailing}}}"

# Documents
comment_text_strat = st.text(alphabet=SAFE_BASIC_CHARS, min_size=1, max_size=15).map(lambda s: f" # {s}")

@composite
def standard_document_gen(draw):
    num_lines = draw(st.integers(1, 10))
    lines = []
    for i in range(num_lines):
        k = draw(key_strat)
        is_type = draw(st.sampled_from(["pair", "pair", "pair", "table", "array_table"]))
        comment = draw(st.sampled_from(["", "", draw(comment_text_strat)]))
        if is_type == "pair":
            v = draw(value_gen())
            lines.append(f"{k} = {v}{comment}")
        elif is_type == "table":
            lines.append(f"[{k}]{comment}")
        else:
            lines.append(f"[[{k}]]{comment}")
    return "\n".join(lines)

# Direct depth construction to exceed limits safely (pushing targets beyond 4000+)
@composite
def deep_array_document_gen(draw):
    depth = draw(st.integers(4000, 6000))
    val = draw(scalar_val_strat)
    open_b = "[" * depth
    close_b = "]" * depth
    return f"deep_arr = {open_b}{val}{close_b}"

@composite
def deep_inline_table_document_gen(draw):
    depth = draw(st.integers(4000, 6000))
    val = draw(scalar_val_strat)
    prefix = "".join([f"k{i} = {{" for i in range(depth)])
    suffix = "}" * depth
    return f"deep_tbl = {prefix}{val}{suffix}"

@composite
def deep_dotted_key_document_gen(draw):
    depth = draw(st.integers(4000, 6000))
    k = ".".join([f"k{i}" for i in range(depth)])
    val = draw(scalar_val_strat)
    return f"{k} = {val}"

@composite
def many_siblings_document_gen(draw):
    count = draw(st.integers(300, 600))
    lines = [f"key_{i} = {i}" for i in range(count)]
    return "\n".join(lines)

empty_document_strat = st.sampled_from([
    "",
    " ",
    "\n\n",
    "# empty document comment",
    "# comment 1\n# comment 2\n"
])

toml_strategy = st.one_of(
    *([standard_document_gen()] * 20),
    empty_document_strat,
    st.just("{}").map(lambda x: f"empty_tbl = {x}"),
    deep_array_document_gen(),
    deep_inline_table_document_gen(),
    deep_dotted_key_document_gen(),
    many_siblings_document_gen()
)