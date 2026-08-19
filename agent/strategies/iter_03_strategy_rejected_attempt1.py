"""Generated strategy - iteration 3, attempt 1.
accepted: False
generated: 2026-08-19T10:34:47.108812+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
BASIC_SAFE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&'()*+,-./:;<=>?@[]^_`{|}~"
LITERAL_SAFE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 !#$%&()*+,-./:;<=>?@[\\]^_`{|}~"

NON_ASCII_SAMPLES = [
    "café",
    "résumé",
    "日本語",
    "中文",
    "🐍",
    "öäüß",
    "αβγδ",
    "こんにちは",
    "Ångström",
]

COMMON_KEYS = ["dup_key", "same_key", "k", "name", "title"]

unquoted_key_st = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=12)
quoted_key_st = st.one_of(
    st.text(alphabet=BASIC_SAFE_CHARS, min_size=1, max_size=12).map(
        lambda s: f'"{s}"'
    ),
    st.sampled_from(NON_ASCII_SAMPLES).map(lambda s: f'"{s}"'),
)
simple_key_st = st.one_of(
    unquoted_key_st, quoted_key_st, st.sampled_from(COMMON_KEYS)
)


@composite
def dotted_key_st(draw):
    parts = draw(st.lists(simple_key_st, min_size=2, max_size=4))
    return ".".join(parts)


key_st = st.one_of(simple_key_st, dotted_key_st())


@composite
def valid_basic_string(draw):
    parts = draw(
        st.lists(
            st.one_of(
                st.text(alphabet=BASIC_SAFE_CHARS, min_size=1, max_size=10),
                st.sampled_from(NON_ASCII_SAMPLES),
                st.sampled_from(
                    ["\\\"", "\\\\", "\\b", "\\f", "\\n", "\\r", "\\t"]
                ),
                st.integers(min_value=0x0020, max_value=0x007E).map(
                    lambda x: f"\\u{x:04x}"
                ),
                st.integers(min_value=0x1F600, max_value=0x1F64F).map(
                    lambda x: f"\\U{x:08x}"
                ),
            ),
            min_size=0,
            max_size=4,
        )
    )
    return '"' + "".join(parts) + '"'


@composite
def valid_literal_string(draw):
    s = draw(
        st.one_of(
            st.text(alphabet=LITERAL_SAFE_CHARS, min_size=0, max_size=15),
            st.sampled_from(NON_ASCII_SAMPLES),
        )
    )
    return f"'{s}'"


@composite
def valid_ml_basic_string(draw):
    parts = draw(
        st.lists(
            st.one_of(
                st.text(
                    alphabet=BASIC_SAFE_CHARS + " \n\t", min_size=1, max_size=10
                ),
                st.sampled_from(NON_ASCII_SAMPLES),
                st.sampled_from(
                    ["\\\"", "\\\\", "\\b", "\\f", "\\n", "\\r", "\\t", "\\\n"]
                ),
                st.integers(min_value=0x0020, max_value=0x007E).map(
                    lambda x: f"\\u{x:04x}"
                ),
                st.integers(min_value=0x1F600, max_value=0x1F64F).map(
                    lambda x: f"\\U{x:08x}"
                ),
            ),
            min_size=0,
            max_size=4,
        )
    )
    res = "".join(parts).replace('"""', '" ""')
    return f'"""{res}"""'


@composite
def valid_ml_literal_string(draw):
    s = draw(
        st.one_of(
            st.text(
                alphabet=LITERAL_SAFE_CHARS + " \n\t", min_size=0, max_size=20
            ),
            st.sampled_from(NON_ASCII_SAMPLES),
        )
    )
    s = s.replace("'''", "'' '")
    return f"'''{s}'''"


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
    ]),
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(lambda x: f"0x{x:x}"),
    st.integers(min_value=0, max_value=0xFFFFFFFF).map(lambda x: f"0x{x:X}"),
    st.integers(min_value=0, max_value=0o7777777).map(lambda x: f"0o{x:o}"),
    st.integers(min_value=0, max_value=0B11111111).map(lambda x: f"0b{x:b}"),
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from([
        "inf",
        "-inf",
        "+inf",
        "nan",
        "-nan",
        "+nan",
        "1.0e10",
        "-1.5e-5",
        "+2.3E+4",
        "-0.0",
    ]),
    valid_basic_string(),
    valid_literal_string(),
    valid_ml_basic_string(),
    valid_ml_literal_string(),
    st.tuples(
        st.integers(1970, 2038), st.integers(1, 12), st.integers(1, 28)
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
    st.tuples(
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
    ).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
    st.tuples(
        st.integers(1970, 2038),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda t: (
            f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
        )
    ),
    st.tuples(
        st.integers(1970, 2038),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.sampled_from(["9999999999999999999", "123456789", "5", "000000001"]),
    ).map(
        lambda t: (
            f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{t[6]}Z"
        )
    ),
)


def make_inline_table(kvs, trailing=False):
    seen = set()
    unique_kvs = []
    for k, v in kvs:
        if k not in seen:
            seen.add(k)
            unique_kvs.append(f"{k} = {v}")
    content = ", ".join(unique_kvs)
    if trailing and content:
        content += ", "
    return f"{{{content}}}"


@composite
def value_st(draw):
    def container_extend(base_val):
        kv_pairs = st.tuples(simple_key_st, base_val)
        return st.one_of(
            base_val,
            st.lists(base_val, min_size=0, max_size=4).map(
                lambda elems: f"[{', '.join(elems)}]"
            ),
            st.lists(kv_pairs, min_size=0, max_size=4).map(
                lambda kvs: make_inline_table(kvs, trailing=False)
            ),
            st.lists(kv_pairs, min_size=1, max_size=4).map(
                lambda kvs: make_inline_table(kvs, trailing=True)
            ),
        )

    return draw(st.recursive(scalar_st, container_extend, max_leaves=10))


@composite
def document(draw):
    num_sections = draw(st.integers(min_value=1, max_value=4))
    doc_lines = []

    for _ in range(num_sections):
        sec_type = draw(st.sampled_from(["root", "table", "array_table"]))
        if sec_type == "table":
            k = draw(st.one_of(key_st, st.sampled_from(COMMON_KEYS)))
            doc_lines.append(f"[{k}]")
        elif sec_type == "array_table":
            k = draw(
                st.one_of(
                    st.sampled_from(["arr", "items", "data"] + COMMON_KEYS),
                    key_st,
                )
            )
            doc_lines.append(f"[[{k}]]")

        num_kvs = draw(st.integers(min_value=1, max_value=4))
        seen_keys = set()
        for _ in range(num_kvs):
            key = draw(st.one_of(key_st, st.sampled_from(COMMON_KEYS)))
            if key in seen_keys:
                key = f"{key}_{len(seen_keys)}"
            seen_keys.add(key)

            val = draw(value_st())
            comment = draw(
                st.one_of(
                    st.just(""),
                    st.text(alphabet=BASIC_SAFE_CHARS, min_size=0, max_size=10).map(
                        lambda c: f" # {c}"
                    ),
                    st.sampled_from(NON_ASCII_SAMPLES).map(lambda c: f" # {c}"),
                )
            )
            doc_lines.append(f"{key} = {val}{comment}")

    return "\n".join(doc_lines)


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
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    many_siblings_doc(),
)