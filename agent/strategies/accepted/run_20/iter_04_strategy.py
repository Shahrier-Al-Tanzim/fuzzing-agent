"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-19T12:08:45.225993+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
BASIC_STRING_SAFE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!?@#$%^&*()[]=+åäöéèñこんにちは✨"

simple_key_strat = st.one_of(
    st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10),
    st.text(alphabet=BASIC_STRING_SAFE, min_size=1, max_size=10).map(lambda s: f'"{s}"'),
    st.text(alphabet=BASIC_STRING_SAFE, min_size=1, max_size=10).map(lambda s: f"'{s}'"),
    st.sampled_from(['"key_café"', '"キー"', "'key_åäö'"]),
)

dotted_key_strat = st.lists(simple_key_strat, min_size=2, max_size=4).map(lambda parts: ".".join(parts))

full_key_strat = st.one_of(simple_key_strat, dotted_key_strat)

int_strat = st.one_of(
    st.integers(-9223372036854775808, 9223372036854775807).map(str),
    st.sampled_from([
        "9223372036854775808", "-9223372036854775809",
        "18446744073709551615", "99999999999999999999", "-99999999999999999999"
    ]),
    st.sampled_from(["007", "0123", "-005", "000", "0999"]),
    st.integers(0, 65535).map(lambda x: f"0x{x:x}"),
    st.integers(0, 511).map(lambda x: f"0o{x:o}"),
    st.integers(0, 255).map(lambda x: f"0b{x:b}"),
    st.sampled_from(["1_000", "1_000_000", "0x12_34", "0b1101_0010", "0o755_000"]),
)

float_strat = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from([
        "inf", "-inf", "+inf", "nan", "-nan", "+nan",
        "0.0", "-0.0", "1e10", "1.5e-3", "-1.0e+100",
        "1.7976931348623157e+308", "1e+400"
    ]),
)

bool_strat = st.sampled_from(["true", "false"])

string_strat = st.one_of(
    st.text(alphabet=BASIC_STRING_SAFE, min_size=0, max_size=20).map(lambda s: f'"{s}"'),
    st.sampled_from([
        '"hello\\nworld"', '"escaped \\"quote\\""', '"unicode \\u0041"',
        '"bad escape \\z"', '"non_ascii_café"', '"日本語テスト"',
        '"\u00e9\u00e0\u00e7"', '"\\uFFFF"', '"\\U0001F600"'
    ]),
    st.text(alphabet=BASIC_STRING_SAFE, min_size=0, max_size=20).map(lambda s: f"'{s}'"),
    st.text(alphabet=BASIC_STRING_SAFE, min_size=0, max_size=20).map(lambda s: f'"""{s}"""'),
    st.text(alphabet=BASIC_STRING_SAFE, min_size=0, max_size=20).map(lambda s: f"'''{s}'''"),
)

date_strat = st.one_of(
    st.tuples(st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28)).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
    ),
    st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)).map(
        lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"
    ),
    st.sampled_from([
        "1979-05-27T00:32:00.9999999999999999999Z",
        "1979-05-27T00:32:00.123456789123456789-07:00",
        "2023-12-31T23:59:59.999999999Z",
    ]),
    st.tuples(
        st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28),
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
    ).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
    ),
)

scalar_strat = st.one_of(int_strat, float_strat, bool_strat, string_strat, date_strat)

@composite
def inline_table(draw, child_strat):
    kv_pairs = draw(st.lists(
        st.tuples(st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=6), child_strat),
        min_size=0, max_size=3,
        unique_by=lambda x: x[0]
    ))
    body = ", ".join(f"{k} = {v}" for k, v in kv_pairs)
    trailing = draw(st.sampled_from(["", ","])) if kv_pairs else ""
    return "{" + body + trailing + "}"

@composite
def array_val(draw, child_strat):
    elements = draw(st.lists(child_strat, min_size=0, max_size=4))
    trailing = draw(st.sampled_from(["", ","])) if elements else ""
    return "[" + ", ".join(elements) + trailing + "]"

value_strategy = st.recursive(
    scalar_strat,
    lambda children: st.one_of(
        array_val(children),
        inline_table(children)
    ),
    max_leaves=15
)

@composite
def document(draw):
    items = []
    num_items = draw(st.integers(min_value=1, max_value=8))
    table_count = 0
    array_table_count = 0
    for i in range(num_items):
        kind = draw(st.sampled_from(["pair", "pair", "pair", "table", "array_table", "comment"]))
        if kind == "pair":
            k = draw(simple_key_strat)
            if k.startswith('"') and k.endswith('"'):
                k = f'"{k[1:-1]}_{i}"'
            elif k.startswith("'") and k.endswith("'"):
                k = f"'{k[1:-1]}_{i}'"
            else:
                k = f"{k}_{i}"
            v = draw(value_strategy)
            items.append(f"{k} = {v}")
        elif kind == "table":
            table_count += 1
            k = draw(simple_key_strat)
            if k.startswith('"') and k.endswith('"'):
                k = f'"{k[1:-1]}_tbl_{table_count}"'
            elif k.startswith("'") and k.endswith("'"):
                k = f"'{k[1:-1]}_tbl_{table_count}'"
            else:
                k = f"{k}_tbl_{table_count}"
            items.append(f"[{k}]")
            num_pairs = draw(st.integers(min_value=0, max_value=3))
            for j in range(num_pairs):
                pk = f"sub_{j}_{i}"
                pv = draw(value_strategy)
                items.append(f"{pk} = {pv}")
        elif kind == "array_table":
            array_table_count += 1
            k = draw(simple_key_strat)
            if k.startswith('"') and k.endswith('"'):
                k = f'"{k[1:-1]}_arr_{array_table_count}"'
            elif k.startswith("'") and k.endswith("'"):
                k = f"'{k[1:-1]}_arr_{array_table_count}'"
            else:
                k = f"{k}_arr_{array_table_count}"
            items.append(f"[[{k}]]")
            num_pairs = draw(st.integers(min_value=1, max_value=3))
            for j in range(num_pairs):
                pk = f"item_{j}_{i}"
                pv = draw(value_strategy)
                items.append(f"{pk} = {pv}")
        elif kind == "comment":
            c = draw(st.text(alphabet=BASIC_STRING_SAFE, min_size=0, max_size=20))
            items.append(f"# {c}")
    return "\n".join(items)

empty_document_strat = st.sampled_from([
    "",
    "\n",
    "\r\n",
    "# empty file\n",
    "   \n\t\n",
    "# empty document with utf-8 comments åäö\n",
])

@composite
def deep_array_doc(draw):
    n = draw(st.integers(min_value=10_000, max_value=120_000))
    return "deep_arr = " + ("[" * n) + "1" + ("]" * n)

@composite
def deep_inline_table_doc(draw):
    n = draw(st.integers(min_value=10_000, max_value=120_000))
    return "deep_tbl = " + ("{a=" * n) + "1" + ("}" * n)

@composite
def deep_dotted_key_doc(draw):
    n = draw(st.integers(min_value=10_000, max_value=120_000))
    return ("a." * n) + "k = 1"

@composite
def many_siblings_doc(draw):
    n = draw(st.integers(min_value=5_000, max_value=30_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)

@composite
def deep_inline_in_array_table_doc(draw):
    depth = draw(st.integers(min_value=100, max_value=1000))
    center = draw(st.one_of(int_strat, float_strat, string_strat, date_strat))
    val = center
    for _ in range(depth):
        trailing = draw(st.sampled_from(["", ","]))
        val = f"{{k = {val}{trailing}}}"
    return f"[[arr_tbl]]\nitem = {val}"

toml_strategy = st.one_of(
    empty_document_strat,
    document(),
    document(),
    document(),
    document(),
    deep_array_doc(),
    deep_inline_table_doc(),
    deep_dotted_key_doc(),
    many_siblings_doc(),
    deep_inline_in_array_table_doc(),
)