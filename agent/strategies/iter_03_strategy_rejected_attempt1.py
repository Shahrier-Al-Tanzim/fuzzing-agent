"""Generated strategy - iteration 3, attempt 1.
accepted: False
generated: 2026-08-20T08:48:39.408580+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-!#$%&'()*+,-./:;<=>?@[]^_`{|}~éàçüöäß"
LITERAL_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-!\"#$%&()*+,-./:;<=>?@[]^_`{|}~éàçüöäß"
HEX_DIGITS = "0123456789abcdefABCDEF"

unquoted_key = st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=10)
quoted_basic_key = st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=10).map(lambda s: f'"{s}"')
quoted_literal_key = st.text(alphabet=LITERAL_STR_CHARS, min_size=0, max_size=10).map(lambda s: f"'{s}'")

simple_key = st.one_of(unquoted_key, quoted_basic_key, quoted_literal_key)


@composite
def dotted_key_gen(draw):
    parts = draw(st.lists(simple_key, min_size=2, max_size=4))
    return ".".join(parts)


key_gen = st.one_of(simple_key, dotted_key_gen())

dec_int = st.one_of(
    st.integers().map(str),
    st.just("0"),
    st.just("-0"),
    st.just("9223372036854775807"),
    st.just("-9223372036854775808"),
    st.just("9223372036854775808"),
    st.just("-9223372036854775809"),
    st.just("007"),
    st.just("0123"),
    st.just("1_000_000"),
    st.just("+99")
)
hex_int = st.one_of(
    st.text(alphabet=HEX_DIGITS, min_size=1, max_size=8).map(lambda h: f"0x{h}"),
    st.just("0x0"),
    st.just("0xDEADBEEF"),
    st.just("0xfe"),
    st.just("0x1_2_3")
)
oct_int = st.text(alphabet="01234567", min_size=1, max_size=8).map(lambda o: f"0o{o}")
bin_int = st.text(alphabet="01", min_size=1, max_size=16).map(lambda b: f"0b{b}")
integer_val = st.one_of(dec_int, hex_int, oct_int, bin_int)

float_val = st.one_of(
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.just("0.0"), st.just("-0.0"), st.just("inf"), st.just("-inf"),
    st.just("nan"), st.just("+nan"), st.just("1e10"), st.just("1.5e-3"),
    st.just("3.141_592")
)

bool_val = st.sampled_from(["true", "false"])

date_str = st.tuples(st.integers(1970, 2099), st.integers(1, 12), st.integers(1, 28)).map(
    lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
)
time_secfrac = st.one_of(
    st.integers(0, 999999).map(lambda n: f".{n:06d}"),
    st.just(".9999999999999999999"),
    st.just("")
)
time_str = st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59), time_secfrac).map(
    lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}{t[3]}"
)
offset_str = st.one_of(st.just("Z"), st.just("+00:00"), st.just("-05:00"), st.just("+05:30"))

offset_date_time = st.tuples(date_str, st.sampled_from(["T", "t", " "]), time_str, offset_str).map(
    lambda t: f"{t[0]}{t[1]}{t[2]}{t[3]}"
)
local_date_time = st.tuples(date_str, st.sampled_from(["T", "t", " "]), time_str).map(
    lambda t: f"{t[0]}{t[1]}{t[2]}"
)
local_date = date_str
local_time = time_str

datetime_val = st.one_of(offset_date_time, local_date_time, local_date, local_time)

escapes = st.sampled_from(["\\n", "\\t", "\\\"", "\\\\", "\\b", "\\f", "\\r", "\\u0041", "\\U0001F600", "\\u4e00"])
basic_string_inner = st.lists(
    st.one_of(st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=5), escapes),
    max_size=5
).map(lambda parts: "".join(parts))
basic_string = basic_string_inner.map(lambda s: f'"{s}"')
literal_string = st.text(alphabet=LITERAL_STR_CHARS, max_size=15).map(lambda s: f"'{s}'")
ml_basic_string = st.text(alphabet=BASIC_STR_CHARS + " \n", max_size=20).map(lambda s: f'"""{s}"""')
ml_literal_string = st.text(alphabet=LITERAL_STR_CHARS + " \n", max_size=25).map(
    lambda s: f"'''{s.replace('\'\'\'', '\'\' \'')}'''"
)

string_val = st.one_of(basic_string, literal_string, ml_basic_string, ml_literal_string)
scalar_val = st.one_of(integer_val, float_val, bool_val, datetime_val, string_val)


@composite
def inline_table_gen(draw, child_strategy):
    n = draw(st.integers(min_value=0, max_value=4))
    if n == 0:
        return "{}"
    pairs = []
    for _ in range(n):
        k = draw(simple_key)
        v = draw(child_strategy)
        pairs.append(f"{k} = {v}")
    if draw(st.booleans()):
        return f"{{{', '.join(pairs)}, }}"
    return f"{{{', '.join(pairs)}}}"


@composite
def array_gen(draw, child_strategy):
    n = draw(st.integers(min_value=0, max_value=4))
    if n == 0:
        return "[]"
    items = [draw(child_strategy) for _ in range(n)]
    if draw(st.booleans()):
        body = ",\n  ".join(items)
        if draw(st.booleans()):
            body += ","
        return f"[\n  {body}\n]"
    else:
        body = ", ".join(items)
        if draw(st.booleans()):
            body += ","
        return f"[{body}]"


@composite
def value_strategy(draw):
    return draw(st.recursive(
        scalar_val,
        lambda children: st.one_of(
            array_gen(children),
            inline_table_gen(children),
        ),
        max_leaves=10
    ))


@composite
def table_header(draw):
    k = draw(key_gen)
    if draw(st.booleans()):
        return f"[[{k}]]"
    return f"[{k}]"


@composite
def document(draw):
    if draw(st.booleans()):
        return draw(st.one_of(st.just(""), st.just("# Empty document\n"), st.just("# Comment\n# Header\n")))

    lines = []

    if draw(st.booleans()):
        lines.append("# Root configuration")

    num_root_kv = draw(st.integers(min_value=0, max_value=4))
    for _ in range(num_root_kv):
        k = draw(key_gen)
        v = draw(value_strategy())
        fmt = draw(st.sampled_from(["plain", "comment", "spaces"]))
        if fmt == "comment":
            lines.append(f"{k} = {v} # comment")
        elif fmt == "spaces":
            lines.append(f"  {k}   =   {v}  ")
        else:
            lines.append(f"{k} = {v}")

    num_sections = draw(st.integers(min_value=0, max_value=4))
    for _ in range(num_sections):
        if lines and draw(st.booleans()):
            lines.append("")
        header = draw(table_header())
        if draw(st.booleans()):
            lines.append(f"{header} # section comment")
        else:
            lines.append(header)

        num_kv = draw(st.integers(min_value=0, max_value=4))
        for _ in range(num_kv):
            k = draw(key_gen)
            v = draw(value_strategy())
            fmt = draw(st.sampled_from(["plain", "comment", "spaces"]))
            if fmt == "comment":
                lines.append(f"{k} = {v} # comment")
            elif fmt == "spaces":
                lines.append(f"  {k}   =   {v}  ")
            else:
                lines.append(f"{k} = {v}")

    return "\n".join(lines)


@composite
def malformed_doc(draw):
    return draw(st.one_of(
        st.just("key = \"unclosed string"),
        st.just("key = [1, 2, 3"),
        st.just("key = {a = 1"),
        st.just("key value_without_equals"),
        st.just("key = \nvalue_on_newline"),
        st.just("[table\nkey = 1"),
        st.just("[[array_table\nkey = 1"),
        st.just("key = {a = 1\nb = 2}"),
        st.just("a = 1\na = 2"),
    ))


@composite
def many_siblings(draw):
    n = draw(st.integers(min_value=10_000, max_value=60_000))
    lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
    return "\n".join(lines)


@composite
def deep_array(draw):
    n = draw(st.integers(min_value=60_000, max_value=100_000))
    return f"deep_arr = {'[' * n}1{']' * n}"


@composite
def deep_inline_table(draw):
    n = draw(st.integers(min_value=85_000, max_value=115_000))
    return f"deep_tbl = {'{a=' * n}1{'}' * n}"


@composite
def deep_dotted_key(draw):
    n = draw(st.integers(min_value=100_000, max_value=130_000))
    return "a." * n + "k = 1"


@composite
def deep_mixed_nesting(draw):
    n = draw(st.integers(min_value=60_000, max_value=80_000))
    return f"deep_mix = {'[{a=' * n}1{'}]' * n}"


@composite
def deep_quoted_mixed(draw):
    n = draw(st.integers(min_value=20_000, max_value=45_000))
    prefix = '[{"k"=' * n
    suffix = "}]" * n
    return f"deep_qmix = {prefix}1{suffix}"


toml_strategy = st.one_of(
    *([document()] * 20),
    *([malformed_doc()] * 2),
    many_siblings(),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    deep_mixed_nesting(),
    deep_quoted_mixed()
)