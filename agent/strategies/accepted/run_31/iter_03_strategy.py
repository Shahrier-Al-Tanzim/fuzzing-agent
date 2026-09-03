"""Generated strategy - iteration 3, attempt 1.
accepted: True
generated: 2026-08-21T12:25:34.356481+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_ASCII = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ =.,/?:;!@#$%^&*()[]{}|~`"
NON_ASCII_CHARS = "éàèùâêîôûäëïöüÿçñßαβγδεζηθικλμνξοπρστυφχψω中文日本語한국어äöüß🎉🚀"

unquoted_key_strat = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12)
quoted_key_strat = st.text(alphabet=SAFE_ASCII + NON_ASCII_CHARS, min_size=0, max_size=10).map(lambda s: f'"{s}"')
literal_key_strat = st.text(alphabet=SAFE_ASCII + NON_ASCII_CHARS, min_size=0, max_size=10).map(lambda s: f"'{s}'")

simple_key_strat = st.one_of(unquoted_key_strat, quoted_key_strat, literal_key_strat)
dotted_key_strat = st.lists(simple_key_strat, min_size=2, max_size=4).map(lambda parts: ".".join(parts))
key_strat = st.one_of(simple_key_strat, dotted_key_strat)

escapes_strat = st.one_of(
    st.just('\\"'), st.just('\\\\'), st.just('\\b'), st.just('\\f'),
    st.just('\\n'), st.just('\\r'), st.just('\\t'),
    st.just('\\u0000'), st.just('\\u0020'), st.just('\\u000A'), st.just('\\u00FF'),
    st.just('\\uFFFF'), st.just('\\U00000020'), st.just('\\U0001F600'), st.just('\\U0010FFFF')
)

basic_string_strat = st.lists(
    st.one_of(
        st.text(alphabet=SAFE_ASCII + NON_ASCII_CHARS, min_size=1, max_size=10),
        escapes_strat
    ),
    min_size=0, max_size=8
).map(lambda parts: f'"{ "".join(parts) }"')

ml_basic_string_strat = st.lists(
    st.one_of(
        st.text(alphabet=SAFE_ASCII + NON_ASCII_CHARS + "\n\t", min_size=1, max_size=10),
        escapes_strat,
        st.just("\\\n"),
        st.just("\\\r\n")
    ),
    min_size=0, max_size=8
).map(lambda parts: f'"""{ "".join(parts) }"""')

literal_string_strat = st.text(alphabet=SAFE_ASCII + NON_ASCII_CHARS, min_size=0, max_size=15).map(lambda s: f"'{s}'")
ml_literal_string_strat = st.text(alphabet=SAFE_ASCII + NON_ASCII_CHARS + "\n\t", min_size=0, max_size=25).map(lambda s: f"'''{s}'''")

string_value_strat = st.one_of(basic_string_strat, ml_basic_string_strat, literal_string_strat, ml_literal_string_strat)

int_value_strat = st.one_of(
    st.integers().map(str),
    st.just("0"),
    st.just("9223372036854775807"),
    st.just("-9223372036854775808"),
    st.just("9223372036854775808"),
    st.just("-9223372036854775809"),
    st.just("007"),
    st.just("0123"),
    st.integers(0, 0xFFFFFFFF).map(lambda x: f"0x{x:x}"),
    st.integers(0, 0o77777).map(lambda x: f"0o{x:o}"),
    st.integers(0, 0b11111111).map(lambda x: f"0b{x:b}"),
    st.just("1_000_000"),
    st.just("0x_a_b_c"),
    st.just("0b1_0_1_0")
)

float_value_strat = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.just("inf"), st.just("-inf"), st.just("+inf"),
    st.just("nan"), st.just("-nan"), st.just("+nan"),
    st.just("1.0"), st.just("1e10"), st.just("-2E-3"), st.just("3.14_15_92"),
    st.just("1.0e+308"), st.just("1.0e-308"), st.just("1e999999999")
)

bool_value_strat = st.one_of(st.just("true"), st.just("false"))

frac_sec_strat = st.integers(1, 25).map(lambda n: "." + "9" * n)

date_time_value_strat = st.one_of(
    st.tuples(
        st.integers(1000, 9999), st.integers(1, 12), st.integers(1, 28),
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"),
    st.tuples(
        st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28),
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59),
        frac_sec_strat
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}{t[6]}-07:00"),
    st.just("1979-05-27T00:32:00.9999999999999999999-07:00"),
    st.just("1979-05-27T07:32:00.1234567890123456789"),
    st.just("1979-05-27T07:32:00"),
    st.just("1979-05-27"),
    st.just("07:32:00.123456"),
    st.just("00:00:00")
)

scalar_val = st.one_of(string_value_strat, int_value_strat, float_value_strat, bool_value_strat, date_time_value_strat)

@composite
def value_recursive(draw, depth=0):
    if depth >= 3:
        return draw(scalar_val)
    choice = draw(st.integers(0, 2))
    if choice == 0:
        return draw(scalar_val)
    elif choice == 1:
        elems = draw(st.lists(value_recursive(depth=depth+1), min_size=0, max_size=4))
        trailing = draw(st.one_of(st.just(""), st.just(", "))) if elems else ""
        return f"[{', '.join(elems)}{trailing}]"
    else:
        keys = draw(st.lists(unquoted_key_strat, min_size=0, max_size=3))
        kvs = []
        for k in keys:
            v = draw(value_recursive(depth=depth+1))
            kvs.append(f"{k} = {v}")
        trailing = draw(st.one_of(st.just(""), st.just(", "))) if kvs else ""
        return f"{{{', '.join(kvs)}{trailing}}}"

@composite
def empty_document(draw):
    return draw(st.one_of(
        st.just(""),
        st.just("   \n\n\t\n"),
        st.just("# Empty TOML document with only comments\n# Another comment line\n"),
        st.just("   # comment with non-ascii: 🎉中文   \n")
    ))

@composite
def duplicate_key_document(draw):
    base_k = draw(unquoted_key_strat)
    val1 = draw(scalar_val)
    val2 = draw(scalar_val)
    val3 = draw(scalar_val)
    lines = [
        f"{base_k} = {val1}",
        f"[table_a]",
        f"{base_k} = {val2}",
        f"[table_b]",
        f"{base_k} = {val3}",
        f"[[arr_table]]",
        f"{base_k} = {val1}",
        f"[[arr_table]]",
        f"{base_k} = {val2}"
    ]
    return "\n".join(lines)

@composite
def non_ascii_document(draw):
    k1 = draw(st.one_of(
        st.text(alphabet=NON_ASCII_CHARS, min_size=1, max_size=8).map(lambda s: f'"{s}"'),
        st.text(alphabet=NON_ASCII_CHARS, min_size=1, max_size=8).map(lambda s: f"'{s}'")
    ))
    v1 = draw(basic_string_strat)
    v2 = draw(ml_basic_string_strat)
    v3 = draw(st.text(alphabet=NON_ASCII_CHARS, min_size=1, max_size=15).map(lambda s: f'"{s}"'))
    lines = [
        f"{k1} = {v1}",
        f"unicode_key = {v2}",
        f"utf8_key = {v3}",
        f"# Non-ascii comment: 🚀 🎉 中文 test"
    ]
    return "\n".join(lines)

@composite
def escaped_strings_document(draw):
    num_entries = draw(st.integers(3, 8))
    lines = []
    for i in range(num_entries):
        k = draw(unquoted_key_strat)
        v = draw(st.one_of(basic_string_strat, ml_basic_string_strat))
        lines.append(f"{k}_{i} = {v}")
    return "\n".join(lines)

@composite
def complex_inline_table_document(draw):
    k = draw(key_strat)
    num_kvs = draw(st.integers(2, 6))
    kvs = []
    for i in range(num_kvs):
        ik = draw(unquoted_key_strat)
        iv = draw(st.one_of(basic_string_strat, date_time_value_strat, int_value_strat, float_value_strat))
        kvs.append(f"{ik}_{i} = {iv}")
    trailing = draw(st.one_of(st.just(""), st.just(", ")))
    return f"{k} = {{ " + ", ".join(kvs) + trailing + " }}"

@composite
def date_time_stress_document(draw):
    num_entries = draw(st.integers(2, 6))
    lines = []
    for i in range(num_entries):
        k = draw(unquoted_key_strat)
        v = draw(date_time_value_strat)
        lines.append(f"{k}_{i} = {v}")
    return "\n".join(lines)

@composite
def table_realloc_document(draw):
    num_tables = draw(st.integers(30, 80))
    lines = []
    for i in range(num_tables):
        lines.append(f"[t_{i}]")
        lines.append(f"val = {i}")
        lines.append(f"[[arr_{i % 5}]]")
        lines.append(f"item = {i}")
    return "\n".join(lines)

@composite
def standard_document(draw):
    lines = []
    num_items = draw(st.integers(1, 10))
    for _ in range(num_items):
        item_type = draw(st.integers(0, 2))
        if item_type == 0:
            k = draw(key_strat)
            v = draw(value_recursive())
            comment = draw(st.one_of(st.just(""), st.just(" # comment")))
            lines.append(f"{k} = {v}{comment}")
        elif item_type == 1:
            k = draw(key_strat)
            comment = draw(st.one_of(st.just(""), st.just(" # comment")))
            lines.append(f"[{k}]{comment}")
        else:
            k = draw(key_strat)
            comment = draw(st.one_of(st.just(""), st.just(" # comment")))
            lines.append(f"[[{k}]]{comment}")
    return "\n".join(lines)

@composite
def deep_array_document(draw):
    n = draw(st.integers(1000, 30000))
    k = draw(key_strat)
    return f"{k} = " + ("[" * n) + "1" + ("]" * n)

@composite
def deep_inline_table_document(draw):
    n = draw(st.integers(300, 2500))
    k = draw(key_strat)
    open_parts = ["a = { "] * n
    close_parts = [" }"] * n
    trailing = draw(st.one_of(st.just(""), st.just(", ")))
    return f"{k} = " + "".join(open_parts) + "x = 1" + trailing + "".join(close_parts)

@composite
def wide_table_document(draw):
    num_keys = draw(st.integers(100, 800))
    table_name = draw(key_strat)
    lines = [f"[{table_name}]"]
    for i in range(num_keys):
        lines.append(f"key_{i} = {i}")
    return "\n".join(lines)

@composite
def wide_inline_table_document(draw):
    num_keys = draw(st.integers(200, 1000))
    k = draw(key_strat)
    kvs = [f"k_{i} = {i}" for i in range(num_keys)]
    trailing = draw(st.one_of(st.just(""), st.just(", ")))
    return f"{k} = {{ " + ", ".join(kvs) + trailing + " }}"

@composite
def deep_dotted_key_document(draw):
    depth = draw(st.integers(50, 300))
    parts = [draw(unquoted_key_strat) for _ in range(depth)]
    dotted_key = ".".join(parts)
    val = draw(scalar_val)
    return f"{dotted_key} = {val}"

@composite
def large_string_escapes_document(draw):
    k = draw(key_strat)
    num_repeats = draw(st.integers(500, 5000))
    pattern_list = draw(st.lists(escapes_strat, min_size=1, max_size=6))
    pattern = "".join(pattern_list)
    content = pattern * num_repeats
    return f'{k} = "{content}"'

@composite
def divergence_cases_document(draw):
    k1 = draw(key_strat)
    k2 = draw(key_strat)
    k3 = draw(key_strat)
    k4 = draw(key_strat)
    lines = [
        f"{k1} = {{ x = 1, y = 2, }}",
        f"{k2} = 1979-05-27T00:32:00.9999999999999999999-07:00",
        f"{k3} = 9223372036854775808",
        f"{k4} = 007"
    ]
    return "\n".join(lines)

toml_strategy = st.one_of(
    *[standard_document() for _ in range(25)],
    *[escaped_strings_document() for _ in range(3)],
    *[complex_inline_table_document() for _ in range(3)],
    *[date_time_stress_document() for _ in range(3)],
    *[table_realloc_document() for _ in range(2)],
    duplicate_key_document(),
    empty_document(),
    non_ascii_document(),
    deep_array_document(),
    deep_inline_table_document(),
    wide_table_document(),
    wide_inline_table_document(),
    deep_dotted_key_document(),
    large_string_escapes_document(),
    divergence_cases_document()
)