"""Generated strategy - iteration 1, attempt 1.
accepted: True
generated: 2026-08-19T06:40:41.504123+00:00
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

int_scalar = st.one_of(
    st.integers().map(str),
    st.just("9223372036854775808"),
    st.just("-9223372036854775809"),
    st.just("007"),
    st.just("000123"),
    st.integers(0, 0xFFFFFFFF).map(lambda x: f"0x{x:x}"),
    st.integers(0, 0o7777).map(lambda x: f"0o{x:o}"),
    st.integers(0, 0b11111111).map(lambda x: f"0b{x:b}"),
    st.just("1_000_000"),
)

float_scalar = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.just("inf"),
    st.just("-inf"),
    st.just("nan"),
    st.just("+nan"),
    st.just("1e10"),
    st.just("3.14159"),
    st.just("-0.0"),
    st.just("1.0e-10"),
)

bool_scalar = st.sampled_from(["true", "false"])

string_scalar = st.one_of(
    st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=15).map(lambda s: f'"{s}"'),
    st.text(alphabet=SAFE_LITERAL_CHARS, min_size=0, max_size=15).map(lambda s: f"'{s}'"),
    st.just(r'"hello \n world"'),
    st.just(r'"unicode \u0041 \u00e9 \U0001f600"'),
    st.just(r'"non_ascii_café_éàè"'),
    st.just(r'"invalid \z escape"'),
    st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=15).map(lambda s: f'"""\n{s}\n"""'),
    st.text(alphabet=SAFE_LITERAL_CHARS, min_size=0, max_size=15).map(lambda s: f"'''\n{s}\n'''"),
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
        tz = draw(st.sampled_from(["Z", "+00:00", "-05:00", "+02:00"]))
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
def pair(draw, key_prefix=""):
    k = draw(key_strat)
    if key_prefix:
        if k.startswith('"'):
            k = f'"{key_prefix}_' + k[1:]
        elif k.startswith("'"):
            k = f"'{key_prefix}_" + k[1:]
        else:
            k = f"{key_prefix}_{k}"
    v = draw(value_strategy())
    return f"{k} = {v}"


@composite
def comment_line(draw):
    cmt = draw(st.text(alphabet=SAFE_BASIC_CHARS, min_size=0, max_size=20))
    return f"#{cmt}"


@composite
def standard_table(draw, suffix=""):
    k = draw(key_strat)
    if suffix and not k.startswith(('"', "'")):
        k = f"{k}_{suffix}"
    return f"[{k}]"


@composite
def array_table(draw, suffix=""):
    k = draw(key_strat)
    if suffix and not k.startswith(('"', "'")):
        k = f"{k}_{suffix}"
    return f"[[{k}]]"


@composite
def document(draw):
    num_entries = draw(st.integers(min_value=0, max_value=10))
    lines = []
    for idx in range(num_entries):
        kind = draw(st.sampled_from(["pair", "table", "array_table", "comment"]))
        if kind == "pair":
            lines.append(draw(pair(key_prefix=f"k{idx}")))
        elif kind == "table":
            lines.append(draw(standard_table(suffix=str(idx))))
        elif kind == "array_table":
            lines.append(draw(array_table(suffix=str(idx))))
        else:
            lines.append(draw(comment_line()))
    return "\n".join(lines)


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=1_000, max_value=60_000))
    k = draw(unquoted_key)
    return f"{k} = " + "[" * n + "1" + "]" * n


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=1_000, max_value=60_000))
    k = draw(unquoted_key)
    return f"{k} = " + "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=1_000, max_value=60_000))
    return "a." * n + "k = 1"


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=30_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


toml_strategy = st.one_of(
    document(),
    document(),
    document(),
    document(),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    many_siblings(),
)