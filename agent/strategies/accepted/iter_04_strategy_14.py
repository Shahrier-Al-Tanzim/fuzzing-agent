"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-19T07:21:52.467022+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_KEY_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
SAFE_BASIC_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ =+!@#$%^&*()/?,<>;:~`|[]éàèùâêîôûäëïöüÿçñßαβγδεζηθικλμνξοπρστυφχψω中国語🤖🚀✨"
SAFE_LITERAL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ =+!@#$%^&*()/?,<>;:~`|[]\\\"éàèùâêîôûäëïöüÿçñßαβγδεζηθικλμνξοπρστυφχψω中国語🤖🚀✨"

unquoted_key = st.text(alphabet=UNQUOTED_KEY_CHARS, min_size=1, max_size=10)
quoted_key = st.one_of(
    st.text(alphabet=SAFE_BASIC_CHARS, min_size=1, max_size=10).map(lambda s: f'"{s}"'),
    st.text(alphabet=SAFE_LITERAL_CHARS, min_size=1, max_size=10).map(lambda s: f"'{s}'"),
    st.just('"café"'),
    st.just('"ñ_key"'),
    st.just('"key_🚀"'),
)
simple_key = st.one_of(unquoted_key, quoted_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(lambda parts: ".".join(parts))
key_strat = st.one_of(simple_key, dotted_key)

extreme_ints = st.sampled_from([
    "9223372036854775808",
    "-9223372036854775809",
    "18446744073709551615",
    "-9223372036854775808",
    "9223372036854775807",
    "007",
    "000123",
    "000",
    "01",
    "999999999999999999999999999999",
    "-999999999999999999999999999999",
])

int_scalar = st.one_of(
    st.integers().map(str),
    extreme_ints,
    st.integers(0, 0xFFFFFFFF).map(lambda x: f"0x{x:x}"),
    st.integers(0, 0o7777).map(lambda x: f"0o{x:o}"),
    st.integers(0, 0b11111111).map(lambda x: f"0b{x:b}"),
    st.just("1_000_000"),
)

float_scalar = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from([
        "inf", "-inf", "+inf", "nan", "-nan", "+nan",
        "1e1000", "-1e1000", "1e-1000", "0.0", "-0.0",
        "1.0e-10", "3.141592653589793238462643383279"
    ]),
)

bool_scalar = st.sampled_from(["true", "false"])

string_scalar = st.one_of(
    st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=20).map(lambda s: f'"{s}"'),
    st.text(alphabet=SAFE_LITERAL_CHARS, min_size=0, max_size=20).map(lambda s: f"'{s}'"),
    st.just(r'"hello \n world"'),
    st.just(r'"unicode \u0041 \u00e9 \U0001f600"'),
    st.just(r'"non_ascii_café_éàè"'),
    st.just(r'"invalid \z escape"'),
    st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=20).map(lambda s: f'"""\n{s}\n"""'),
    st.text(alphabet=SAFE_LITERAL_CHARS, min_size=0, max_size=20).map(lambda s: f"'''\n{s}\n'''"),
)


@composite
def datetime_scalar(draw):
    y = draw(st.integers(1970, 2038))
    m = draw(st.integers(1, 12))
    d = draw(st.integers(1, 28))
    h = draw(st.integers(0, 23))
    mi = draw(st.integers(0, 59))
    s = draw(st.integers(0, 59))
    frac = draw(
        st.one_of(
            st.just(""),
            st.integers(0, 999).map(lambda x: f".{x:03d}"),
            st.just(".9999999999999999999"),
            st.text(alphabet="0123456789", min_size=10, max_size=30).map(lambda digits: f".{digits}"),
        )
    )
    fmt = draw(st.sampled_from(["date", "time", "datetime", "offset"]))
    if fmt == "date":
        return f"{y:04d}-{m:02d}-{d:02d}"
    elif fmt == "time":
        return f"{h:02d}:{mi:02d}:{s:02d}{frac}"
    elif fmt == "datetime":
        return f"{y:04d}-{m:02d}-{d:02d}T{h:02d}:{mi:02d}:{s:02d}{frac}"
    else:
        tz = draw(st.sampled_from(["Z", "+00:00", "-05:00", "+02:00", "+12:45"]))
        return f"{y:04d}-{m:02d}-{d:02d}T{h:02d}:{mi:02d}:{s:02d}{frac}{tz}"


scalar_val = st.one_of(
    int_scalar, float_scalar, bool_scalar, string_scalar, datetime_scalar()
)


@composite
def value_strategy(draw, max_depth=3):
    if max_depth <= 0:
        return draw(scalar_val)

    choice = draw(st.sampled_from(["scalar", "array", "inline_table"]))
    if choice == "scalar":
        return draw(scalar_val)
    elif choice == "array":
        elems = draw(
            st.lists(
                value_strategy(max_depth=max_depth - 1), min_size=0, max_size=4
            )
        )
        trailing = draw(st.sampled_from(["", ","])) if elems else ""
        return f"[{', '.join(elems)}{trailing}]"
    else:
        keys = draw(st.lists(simple_key, min_size=0, max_size=3))
        vals = [draw(value_strategy(max_depth=max_depth - 1)) for _ in keys]
        pairs = [f"{k} = {v}" for k, v in zip(keys, vals)]
        trailing = draw(st.sampled_from(["", ","])) if pairs else ""
        return f"{{{', '.join(pairs)}{trailing}}}"


@composite
def nested_inline_table(draw, max_depth=5):
    if max_depth <= 0:
        return draw(scalar_val)

    choice = draw(st.sampled_from(["inline_table", "inline_table", "array", "scalar"]))
    if choice == "scalar":
        return draw(scalar_val)
    elif choice == "array":
        elems = draw(st.lists(nested_inline_table(max_depth=max_depth - 1), min_size=1, max_size=3))
        trailing = draw(st.sampled_from(["", ","]))
        return f"[{', '.join(elems)}{trailing}]"
    else:
        num_pairs = draw(st.integers(min_value=1, max_value=3))
        pairs = []
        for i in range(num_pairs):
            k = f"k{i}_{draw(unquoted_key)}"
            v = draw(nested_inline_table(max_depth=max_depth - 1))
            pairs.append(f"{k} = {v}")
        trailing = draw(st.sampled_from(["", ","]))
        return f"{{{', '.join(pairs)}{trailing}}}"


@composite
def array_table_with_nested_inline(draw):
    header_key = draw(unquoted_key)
    num_tables = draw(st.integers(min_value=2, max_value=4))
    lines = []
    for t_idx in range(num_tables):
        lines.append(f"[[{header_key}]]")
        num_keys = draw(st.integers(min_value=1, max_value=3))
        for k_idx in range(num_keys):
            k = f"field_{t_idx}_{k_idx}"
            v = draw(nested_inline_table(max_depth=5))
            lines.append(f"{k} = {v}")
    return "\n".join(lines)


@composite
def comment_line(draw):
    cmt = draw(st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=20))
    return f"#{cmt}"


@composite
def document(draw):
    num_entries = draw(st.integers(min_value=1, max_value=8))
    lines = []
    for idx in range(num_entries):
        kind = draw(st.sampled_from(["pair", "table", "array_table", "comment"]))
        if kind == "pair":
            k = draw(key_strat)
            unique_k = f"p{idx}_{k}" if not k.startswith(('"', "'")) else f'"p{idx}_' + k[1:]
            v = draw(value_strategy())
            lines.append(f"{unique_k} = {v}")
        elif kind == "table":
            k = draw(key_strat)
            unique_k = f"tbl{idx}_{k}" if not k.startswith(('"', "'")) else f'"tbl{idx}_' + k[1:]
            lines.append(f"[{unique_k}]")
            num_pairs = draw(st.integers(min_value=0, max_value=3))
            for p_idx in range(num_pairs):
                pk = draw(unquoted_key)
                pv = draw(value_strategy())
                lines.append(f"{pk}_{p_idx} = {pv}")
        elif kind == "array_table":
            k = draw(unquoted_key)
            unique_k = f"arr{idx}_{k}"
            for _ in range(draw(st.integers(1, 2))):
                lines.append(f"[[{unique_k}]]")
                num_pairs = draw(st.integers(min_value=0, max_value=3))
                for p_idx in range(num_pairs):
                    pk = draw(unquoted_key)
                    pv = draw(nested_inline_table(max_depth=4))
                    lines.append(f"{pk}_{p_idx} = {pv}")
        else:
            lines.append(draw(comment_line()))
    return "\n".join(lines)


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    k = draw(unquoted_key)
    return f"{k} = " + "[" * n + "1" + "]" * n


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    k = draw(unquoted_key)
    return f"{k} = " + "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=1_000, max_value=120_000))
    return "a." * n + "k = 1"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    document(),
    document(),
    document(),
    array_table_with_nested_inline(),
    array_table_with_nested_inline(),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    many_siblings(),
)