"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-08-20T06:15:31.745151+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!?@#$%^&*()[]=+|"

unquoted_key = st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=15)
quoted_key = st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=15).map(lambda s: f'"{s}"')
simple_key = st.one_of(unquoted_key, quoted_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(lambda parts: ".".join(parts))
key_strat = st.one_of(simple_key, dotted_key)

scalar_value = st.one_of(
    st.integers(min_value=-9223372036854775808, max_value=9223372036854775807).map(str),
    st.sampled_from(["9223372036854775808", "-9223372036854775809", "007", "0123"]),
    st.integers(0, 65535).map(hex),
    st.integers(0, 65535).map(oct),
    st.integers(0, 65535).map(bin),
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from(["inf", "-inf", "+inf", "nan", "+nan", "1e10", "1.0e-5"]),
    st.sampled_from(["true", "false"]),
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(lambda s: f'"{s}"'),
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(lambda s: f"'{s}'"),
    st.sampled_from(['"hello\\nworld"', '"val\\twith\\tescapes"', '"bad\\zescape"', '"""multi\nline"""']),
    st.tuples(
        st.integers(1970, 2038), st.integers(1, 12), st.integers(1, 28),
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"),
    st.just("1979-05-27T00:32:00.9999999999999999999Z"),
    st.tuples(st.integers(1970, 2038), st.integers(1, 12), st.integers(1, 28)).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}")
)

@composite
def recursive_value(draw, depth=0):
    if depth >= 3:
        return draw(scalar_value)
    
    choice = draw(st.integers(1, 3))
    if choice == 1:
        return draw(scalar_value)
    elif choice == 2:
        elems = draw(st.lists(recursive_value(depth=depth + 1), min_size=0, max_size=4))
        body = ", ".join(elems)
        if draw(st.booleans()) and elems:
            body += ","
        return f"[{body}]"
    else:
        keys = draw(st.lists(simple_key, min_size=0, max_size=4))
        pairs = []
        for k in keys:
            v = draw(recursive_value(depth=depth + 1))
            pairs.append(f"{k} = {v}")
        body = ", ".join(pairs)
        if draw(st.booleans()) and pairs:
            body += ","
        return f"{{{body}}}"

value_strategy = recursive_value()

@composite
def key_value_pair(draw):
    k = draw(key_strat)
    v = draw(value_strategy)
    comment = draw(st.one_of(st.just(""), st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=10).map(lambda c: f" # {c}")))
    return f"{k} = {v}{comment}"

@composite
def table_header(draw):
    k = draw(key_strat)
    comment = draw(st.one_of(st.just(""), st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=10).map(lambda c: f" # {c}")))
    if draw(st.booleans()):
        return f"[{k}]{comment}"
    else:
        return f"[[{k}]]{comment}"

@composite
def document(draw):
    lines = draw(st.lists(st.one_of(key_value_pair(), table_header()), min_size=0, max_size=10))
    return "\n".join(lines)

@composite
def deep_array(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    return f"v = {'[' * n}1{']' * n}"

@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    return f"v = {'{a=' * n}1{'}' * n}"

@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    return f"{'a.' * n}k = 1"

@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return f"v = {'[{a=' * n}1{'}]' * n}"

@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)

toml_strategy = st.one_of(
    *([document()] * 16),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    deep_mixed_nesting(),
    many_siblings()
)