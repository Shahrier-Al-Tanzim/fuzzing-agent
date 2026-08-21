"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-08-21T12:21:47.594728+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ =.,/?:;!@#$%^&*()[]{}"

unquoted_key_strat = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12)
quoted_key_strat = st.text(alphabet=SAFE_STR_CHARS, min_size=0, max_size=10).map(lambda s: f'"{s}"')
literal_key_strat = st.text(alphabet=SAFE_STR_CHARS, min_size=0, max_size=10).map(lambda s: f"'{s}'")

simple_key_strat = st.one_of(unquoted_key_strat, quoted_key_strat, literal_key_strat)
dotted_key_strat = st.lists(simple_key_strat, min_size=2, max_size=4).map(lambda parts: ".".join(parts))
key_strat = st.one_of(simple_key_strat, dotted_key_strat)

escapes_strat = st.one_of(
    st.just('\\"'), st.just('\\\\'), st.just('\\b'), st.just('\\f'),
    st.just('\\n'), st.just('\\r'), st.just('\\t'), st.just('\\u0020'),
    st.just('\\U00000020'), st.just('\\z')
)

basic_string_strat = st.lists(
    st.one_of(
        st.text(alphabet=SAFE_STR_CHARS, min_size=1, max_size=5),
        escapes_strat
    ),
    min_size=0, max_size=5
).map(lambda parts: f'"{ "".join(parts) }"')

ml_basic_string_strat = st.text(alphabet=SAFE_STR_CHARS + "\n\r\t", min_size=0, max_size=20).map(lambda s: f'"""{s}"""')
literal_string_strat = st.text(alphabet=SAFE_STR_CHARS, min_size=0, max_size=10).map(lambda s: f"'{s}'")
ml_literal_string_strat = st.text(alphabet=SAFE_STR_CHARS + "\n", min_size=0, max_size=20).map(lambda s: f"'''{s}'''")

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
    st.just("1_000_000")
)

float_value_strat = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.just("inf"), st.just("-inf"), st.just("+inf"),
    st.just("nan"), st.just("-nan"), st.just("+nan"),
    st.just("1.0"), st.just("1e10"), st.just("-2E-3"), st.just("3.14_15_92")
)

bool_value_strat = st.one_of(st.just("true"), st.just("false"))

date_time_value_strat = st.one_of(
    st.tuples(st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28),
              st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
      .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"),
    st.just("1979-05-27T00:32:00.9999999999999999999-07:00"),
    st.just("1979-05-27T07:32:00"),
    st.just("1979-05-27"),
    st.just("07:32:00.123456")
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
        keys = draw(st.lists(key_strat, min_size=0, max_size=3))
        kvs = []
        for k in keys:
            v = draw(value_recursive(depth=depth+1))
            kvs.append(f"{k} = {v}")
        trailing = draw(st.one_of(st.just(""), st.just(", "))) if kvs else ""
        return f"{{{', '.join(kvs)}{trailing}}}"

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
    n = draw(st.integers(500, 4000))
    k = draw(key_strat)
    open_parts = ["{ a = "] * n
    close_parts = ["}"] * n
    return f"{k} = " + "".join(open_parts) + "1" + "".join(close_parts)

@composite
def wide_table_document(draw):
    num_keys = draw(st.integers(100, 800))
    table_name = draw(key_strat)
    lines = [f"[{table_name}]"]
    for i in range(num_keys):
        lines.append(f"key_{i} = {i}")
    return "\n".join(lines)

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
    deep_array_document(),
    deep_inline_table_document(),
    wide_table_document(),
    divergence_cases_document()
)