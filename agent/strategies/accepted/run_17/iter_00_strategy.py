"""Generated strategy - iteration 0, attempt 1.
accepted: True
generated: 2026-08-19T10:24:11.722220+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'()*+,-./:;<=>?@[]^_`{|}~ "

unquoted_key_st = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12)
quoted_key_st = st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=12).map(lambda s: f'"{s}"')
simple_key_st = st.one_of(unquoted_key_st, quoted_key_st)


@composite
def dotted_key_st(draw):
    parts = draw(st.lists(simple_key_st, min_size=2, max_size=4))
    return ".".join(parts)


key_st = st.one_of(simple_key_st, dotted_key_st())

scalar_st = st.one_of(
    st.sampled_from(["true", "false"]),
    st.integers(min_value=-2**63 - 5, max_value=2**63 + 5).map(str),
    st.sampled_from([
        "9223372036854775808",
        "-9223372036854775809",
        "007",
        "000",
        "+00123",
        "99999999999999999999",
        "1_000_000",
        "0x12_34",
        "0b1010_1010",
    ]),
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(lambda x: f"0x{x:x}"),
    st.integers(min_value=0, max_value=0o7777777).map(lambda x: f"0o{x:o}"),
    st.integers(min_value=0, max_value=0b11111111).map(lambda x: f"0b{x:b}"),
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from(["inf", "-inf", "+inf", "nan", "-nan", "+nan", "1.0e10", "-0.0"]),
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(lambda s: f'"{s}"'),
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(lambda s: f"'{s}'"),
    st.sampled_from([
        '"hello\\nworld"',
        '"tab\\tseparated"',
        '"quote\\"test"',
        '"\\\\escaped"',
        '"\\u0041\\u0042"',
        '"\\U0001F600"',
        '"invalid\\xEscape"',
        '"""multi\nline"""',
        "'''multi\nliteral'''",
    ]),
    st.tuples(st.integers(1970, 2038), st.integers(1, 12), st.integers(1, 28)).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
    ),
    st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(
        lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"
    ),
    st.tuples(
        st.integers(1970, 2038),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"),
    st.tuples(
        st.integers(1970, 2038),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(10000000, 999999999),
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]}Z"),
)


@composite
def value_st(draw):
    def container_extend(base_val):
        return st.one_of(
            base_val,
            st.lists(base_val, min_size=0, max_size=4).map(
                lambda elems: f"[{', '.join(elems)}]"
            ),
            st.lists(st.tuples(simple_key_st, base_val), min_size=0, max_size=4).map(
                lambda kvs: f"{{{', '.join(f'{k} = {v}' for k, v in kvs)}}}"
            ),
            st.lists(st.tuples(simple_key_st, base_val), min_size=1, max_size=4).map(
                lambda kvs: f"{{{', '.join(f'{k} = {v}' for k, v in kvs)}, }}"
            ),
        )

    return draw(st.recursive(scalar_st, container_extend, max_leaves=10))


@composite
def key_value_line(draw):
    k = draw(key_st)
    v = draw(value_st())
    comment = draw(
        st.one_of(
            st.just(""),
            st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=10).map(
                lambda c: f" # {c}"
            ),
        )
    )
    return f"{k} = {v}{comment}"


@composite
def duplicate_key_lines(draw):
    k = draw(simple_key_st)
    v1 = draw(value_st())
    v2 = draw(value_st())
    return f"{k} = {v1}\n{k} = {v2}"


@composite
def table_header(draw):
    k = draw(key_st)
    return f"[{k}]"


@composite
def array_table_header(draw):
    k = draw(key_st)
    return f"[[{k}]]"


@composite
def malformed_line(draw):
    return draw(
        st.sampled_from([
            "key_without_equals",
            'key = "unclosed string',
            "key = [1, 2, ",
            "key = { a = 1, ",
            'key = "\\z invalid escape"',
            " = 123",
            "[unclosed_table",
            "[[unclosed_array_table",
        ])
    )


@composite
def document(draw):
    lines = draw(
        st.lists(
            st.one_of(
                key_value_line(),
                duplicate_key_lines(),
                table_header(),
                array_table_header(),
                malformed_line(),
                st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(
                    lambda c: f"# {c}"
                ),
            ),
            min_size=0,
            max_size=10,
        )
    )
    return "\n".join(lines)


@composite
def deep_array_doc(draw):
    n = draw(st.integers(min_value=1_000, max_value=35_000))
    arr = "[" * n + "1" + "]" * n
    k = draw(simple_key_st)
    return f"{k} = {arr}"


@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=1_000, max_value=35_000))
    tbl = "{a=" * n + "1" + "}" * n
    k = draw(simple_key_st)
    return f"{k} = {tbl}"


@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=1_000, max_value=35_000))
    k = "a." * n + "k"
    return f"{k} = 1"


@composite
def many_siblings_doc(draw):
    n = draw(st.integers(min_value=10_000, max_value=25_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    document(),
    document(),
    document(),
    document(),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    many_siblings_doc(),
)