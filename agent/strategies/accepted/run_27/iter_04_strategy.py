"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-20T17:45:11.732526+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
QUOTED_BASIC_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _!#$%&'()*+,-./:;<=>?@[]^{|}~"
    "éàèüöäñÅØæøåαβγδ汉字こんにちは"
)
QUOTED_LITERAL_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \"_!#$%&()*+,-./:;<=>?@[]^{|}~"
    "éàèüöäñÅØæøåαβγδ汉字こんにちは"
)

# --- Keys ---

unquoted_key = st.text(alphabet=UNQUOTED_ALPHABET, min_size=1, max_size=12)
basic_quoted_key = st.text(
    alphabet=QUOTED_BASIC_ALPHABET, min_size=1, max_size=10
).map(lambda s: f'"{s}"')
literal_quoted_key = st.text(
    alphabet=QUOTED_LITERAL_ALPHABET, min_size=1, max_size=10
).map(lambda s: f"'{s}'")

simple_key = st.one_of(unquoted_key, basic_quoted_key, literal_quoted_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(
    lambda parts: ".".join(parts)
)
key = st.one_of(simple_key, dotted_key)


# --- Scalars ---

integers = st.one_of(
    st.integers(-1000, 1000).map(str),
    st.just("0"),
    st.just("-0"),
    st.just("9223372036854775807"),  # INT64_MAX
    st.just("9223372036854775808"),  # INT64_MAX + 1 (Divergence #3)
    st.just("-9223372036854775808"),  # INT64_MIN
    st.just("-9223372036854775809"),  # INT64_MIN - 1
    st.just("18446744073709551615"),  # UINT64_MAX
    st.just("18446744073709551616"),
    st.just("9999999999999999999999999999999999999999"),  # Extremely large int
    st.integers(1, 999).map(
        lambda i: f"0{i:02d}"
    ),  # Leading zeros (Divergence #4)
    st.integers(0, 0xFFFF).map(lambda i: f"0x{i:x}"),
    st.just("0x7fffffffffffffff"),
    st.just("0xffffffffffffffff"),
    st.integers(0, 0O777).map(lambda i: f"0o{i:o}"),
    st.integers(0, 0B1111).map(lambda i: f"0b{i:b}"),
    st.just("1_000_000"),
)

floats = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.just("inf"),
    st.just("-inf"),
    st.just("nan"),
    st.just("+nan"),
    st.just("1e6"),
    st.just("-2E-3"),
    st.just("3.14159e+10"),
    st.just("1_000.000_1"),
    st.just("1e308"),
    st.just("-1e308"),
    st.just("1e309"),
    st.just("-1e309"),
    st.just("1.7976931348623157e+308"),
    st.just("2.2250738585072014e-308"),
    st.just("1e-999"),
)

basic_string = st.text(
    alphabet=QUOTED_BASIC_ALPHABET, min_size=0, max_size=15
).map(lambda s: f'"{s}"')

literal_string = st.text(
    alphabet=QUOTED_LITERAL_ALPHABET, min_size=0, max_size=15
).map(lambda s: f"'{s}'")

ml_basic_string = st.one_of(
    st.text(alphabet=QUOTED_BASIC_ALPHABET + " \t\n", max_size=25).map(
        lambda s: '"""' + s.replace('"""', '""') + '"""'
    ),
    st.just('"""\nfirst line\nsecond line\n"""'),
    st.just('"""\n\tmultiline string with unicode: 🔥 汉字\n"""'),
    st.just('"""\\\n  trimmed line 1 \\\n  trimmed line 2\\\n"""'),
)

ml_literal_string = st.one_of(
    st.text(alphabet=QUOTED_LITERAL_ALPHABET + " \t\n", max_size=25).map(
        lambda s: "'''" + s.replace("'''", "''") + "'''"
    ),
    st.just("'''\nfirst literal line\nsecond literal line\n'''"),
    st.just("'''C:\\Users\\path\\file.txt'''"),
    st.just("'''\nliteral string with non-ascii: éàè 🔥\n'''"),
)

strings = st.one_of(
    basic_string,
    literal_string,
    ml_basic_string,
    ml_literal_string,
    st.just('"hello\\nworld"'),
    st.just('"foo\\tbar"'),
    st.just('"\\u0041\\u0042"'),
    st.just('"\\U0001F600"'),
    st.just('"\\u0000"'),
    st.just('"\\U0010FFFF"'),
    st.just('"\\b\\f\\n\\r\\t\\\\\\""'),
    st.just('"non_ascii_🔥_文"'),
)

booleans = st.one_of(st.just("true"), st.just("false"))

local_date = st.tuples(
    st.integers(1970, 2030), st.integers(1, 12), st.integers(1, 28)
).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}")

local_time = st.tuples(
    st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}")

local_date_time = st.tuples(
    st.integers(1970, 2030),
    st.integers(1, 12),
    st.integers(1, 28),
    st.integers(0, 23),
    st.integers(0, 59),
    st.integers(0, 59),
).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}")

offset_date_time = st.one_of(
    st.tuples(
        st.integers(1970, 2030),
        st.integers(1, 12),
        st.integers(1, 28),
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
    ).map(
        lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}T{t[3]:02d}:{t[4]:02d}:{t[5]:02d}Z"
    ),
    st.just("1979-05-27T00:32:00.9999999999999999999-07:00"),  # Divergence #2
    st.just("2020-01-01T00:00:00." + "9" * 30 + "Z"),
)

dates_and_times = st.one_of(
    local_date, local_time, local_date_time, offset_date_time
)

scalars = st.one_of(integers, floats, strings, booleans, dates_and_times)


# --- Recursive Values (Arrays and Inline Tables) ---


@composite
def array_val(draw, child_strat):
    elems = draw(st.lists(child_strat, max_size=5))
    trailing = draw(st.booleans())
    if elems and trailing:
        return f"[{', '.join(elems)},]"
    return f"[{', '.join(elems)}]"


@composite
def inline_table_val(draw, child_strat):
    pairs = draw(st.lists(st.tuples(simple_key, child_strat), max_size=4))
    seen = set()
    pair_strs = []
    for idx, (k, v) in enumerate(pairs):
        if k in seen:
            if k.endswith('"'):
                k = f'{k[:-1]}_{idx}"'
            elif k.endswith("'"):
                k = f"{k[:-1]}_{idx}'"
            else:
                k = f"{k}_{idx}"
        seen.add(k)
        pair_strs.append(f"{k} = {v}")
    # Divergence #1: Trailing comma in inline table
    trailing = draw(st.booleans())
    if pair_strs and trailing:
        return "{" + ", ".join(pair_strs) + ",}"
    return "{" + ", ".join(pair_strs) + "}"


value_strategy = st.recursive(
    scalars,
    lambda children: st.one_of(
        array_val(children),
        inline_table_val(children),
    ),
    max_leaves=12,
)


# --- Structured Document Generation ---


@composite
def pair_line(draw, key_suffix="", val_strat=None):
    k = draw(key)
    if key_suffix:
        if k.endswith('"'):
            k = k[:-1] + key_suffix + '"'
        elif k.endswith("'"):
            k = k[:-1] + key_suffix + "'"
        else:
            k = k + key_suffix
    v = draw(val_strat if val_strat is not None else value_strategy)
    comment = draw(
        st.one_of(
            st.just(""),
            st.just(" # comment"),
            st.just(" # 🔥 unicode comment"),
        )
    )
    return f"{k} = {v}{comment}"


@composite
def root_section(draw, sec_idx):
    num_pairs = draw(st.integers(min_value=1, max_value=4))
    return "\n".join(
        [draw(pair_line(key_suffix=f"_r{sec_idx}_{i}")) for i in range(num_pairs)]
    )


@composite
def standard_table_section(draw, sec_idx):
    header_key = draw(key)
    if header_key.endswith('"'):
        header_key = header_key[:-1] + f"_t{sec_idx}" + '"'
    elif header_key.endswith("'"):
        header_key = header_key[:-1] + f"_t{sec_idx}" + "'"
    else:
        header_key = header_key + f"_t{sec_idx}"

    comment = draw(st.one_of(st.just(""), st.just(" # comment")))
    lines = [f"[{header_key}]{comment}"]

    num_pairs = draw(st.integers(min_value=1, max_value=4))
    for i in range(num_pairs):
        lines.append(draw(pair_line(key_suffix=f"_p{sec_idx}_{i}")))
    return "\n".join(lines)


@composite
def array_table_section(draw, sec_idx):
    header_key = draw(key)
    if header_key.endswith('"'):
        header_key = header_key[:-1] + f"_at{sec_idx}" + '"'
    elif header_key.endswith("'"):
        header_key = header_key[:-1] + f"_at{sec_idx}" + "'"
    else:
        header_key = header_key + f"_at{sec_idx}"

    num_entries = draw(st.integers(min_value=1, max_value=3))
    lines = []
    for entry in range(num_entries):
        comment = draw(st.one_of(st.just(""), st.just(" # comment")))
        lines.append(f"[[{header_key}]]{comment}")
        num_pairs = draw(st.integers(min_value=1, max_value=3))
        for i in range(num_pairs):
            lines.append(
                draw(pair_line(key_suffix=f"_ap{sec_idx}_{entry}_{i}"))
            )
    return "\n".join(lines)


@composite
def comment_section(draw):
    return draw(
        st.one_of(
            st.just("# Section divider"),
            st.just("# UTF-8 header: 🔥 汉字"),
            st.just(""),
        )
    )


@composite
def document(draw):
    # Higher structural variety by combining distinct structural sections
    section_types = draw(
        st.lists(
            st.sampled_from(
                ["root", "table", "array_table", "table", "comment"]
            ),
            min_size=1,
            max_size=6,
        )
    )

    blocks = []
    sec_idx = 0
    for stype in section_types:
        sec_idx += 1
        if stype == "root":
            blocks.append(draw(root_section(sec_idx)))
        elif stype == "table":
            blocks.append(draw(standard_table_section(sec_idx)))
        elif stype == "array_table":
            blocks.append(draw(array_table_section(sec_idx)))
        elif stype == "comment":
            blocks.append(draw(comment_section()))

    return "\n\n".join(blocks)


# --- Extreme Nesting Shapes (Rule 16) ---


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    return "[" * n + "1" + "]" * n


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    return "{a=" * n + "1" + "}" * n


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    return "a." * n + "k"


@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return "[{a=" * n + "1" + "}]" * n


@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    return '[{"k"=' * n + "1" + "}]" * n


@composite
def deep_val_doc(draw, deep_strat):
    v = draw(deep_strat)
    return f"k = {v}"


@composite
def deep_key_doc(draw, deep_key_strat):
    k = draw(deep_key_strat)
    return f"{k} = 1"


# --- Many Siblings Strategy (Rule 17) ---


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


# --- Final Strategy Composition ---

toml_strategy = st.one_of(
    *([document()] * 25),
    deep_val_doc(deep_array()),
    deep_val_doc(deep_inline_table()),
    deep_key_doc(deep_dotted_key()),
    deep_val_doc(deep_mixed_nesting()),
    deep_val_doc(deep_quoted_mixed()),
    many_siblings(),
)