"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-20T08:57:49.391743+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-!#$%&()*,./:;<=>?@[]^{|}~"
LITERAL_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-!\"#$%&()*,./:;<=>?@[]^{|}~"
HEX_DIGITS = "0123456789abcdefABCDEF"

unquoted_key = st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=10)
quoted_basic_key = st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=10).map(lambda s: f'"{s}"')
quoted_literal_key = st.text(alphabet=LITERAL_STR_CHARS, min_size=1, max_size=10).map(lambda s: f"'{s}'")

simple_key = st.one_of(unquoted_key, quoted_basic_key, quoted_literal_key)
dotted_key_strat = st.lists(simple_key, min_size=2, max_size=3).map(lambda parts: ".".join(parts))
key_strategy = st.one_of(simple_key, dotted_key_strat)

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

basic_string = st.text(alphabet=BASIC_STR_CHARS, max_size=15).map(lambda s: f'"{s}"')
literal_string = st.text(alphabet=LITERAL_STR_CHARS, max_size=15).map(lambda s: f"'{s}'")
ml_basic_string = st.text(alphabet=BASIC_STR_CHARS + " ", max_size=20).map(lambda s: f'"""{s}"""')
ml_literal_string = st.text(alphabet=LITERAL_STR_CHARS + " ", max_size=20).map(lambda s: f"'''{s}'''")

string_val = st.one_of(basic_string, literal_string, ml_basic_string, ml_literal_string)
single_line_val = st.one_of(integer_val, float_val, bool_val, datetime_val, string_val)


@composite
def value_strategy(draw):
    return draw(st.recursive(
        single_line_val,
        lambda children: st.one_of(
            st.lists(children, max_size=4).map(lambda items: f"[{', '.join(items)}]"),
            st.lists(children, max_size=4).map(lambda items: f"[\n  {',\n  '.join(items)}\n]"),
            st.lists(children, min_size=1, max_size=4).map(lambda items: f"[{', '.join(items)}, ]"),
            st.just("[]"),
            st.lists(children, min_size=1, max_size=3).map(
                lambda items: f"{{{', '.join(f'ik{i} = {v}' for i, v in enumerate(items))}}}"
            ),
            st.lists(children, min_size=1, max_size=3).map(
                lambda items: f"{{{', '.join(f'ik{i} = {v}' for i, v in enumerate(items))}, }}"
            ),
            st.just("{}")
        ),
        max_leaves=10
    ))


@composite
def document(draw):
    lines = []
    if draw(st.booleans()):
        lines.append("# TOML fuzz document")

    sec_id = 0
    kv_id = 0

    num_blocks = draw(st.integers(min_value=1, max_value=5))

    for _ in range(num_blocks):
        block_type = draw(st.sampled_from(["root_kv", "table", "array_table", "comment_only"]))

        if block_type == "comment_only":
            cmt = draw(st.text(alphabet=BASIC_STR_CHARS, max_size=20))
            lines.append(f"# {cmt}")
            continue

        if block_type == "table":
            sec_id += 1
            tbl_key = draw(st.one_of(
                st.just(f"sec_{sec_id}"),
                st.just(f'"section_{sec_id}"'),
                st.just(f"parent_{sec_id}.child"),
                st.just(f"'sec_{sec_id}'")
            ))
            lines.append(f"[{tbl_key}]")
        elif block_type == "array_table":
            sec_id += 1
            arr_key = draw(st.one_of(
                st.just(f"arr_{sec_id}"),
                st.just(f"arr_parent_{sec_id}.sub"),
                st.just(f'"arr_sec_{sec_id}"')
            ))
            lines.append(f"[[{arr_key}]]")

        num_kvs = draw(st.integers(min_value=1, max_value=4))
        for _ in range(num_kvs):
            kv_id += 1
            key_kind = draw(st.sampled_from(["unquoted", "quoted_basic", "quoted_literal", "dotted"]))
            if key_kind == "unquoted":
                k = f"k_{kv_id}"
            elif key_kind == "quoted_basic":
                k = f'"key_{kv_id}"'
            elif key_kind == "quoted_literal":
                k = f"'key_{kv_id}'"
            else:
                k = f"sub_{kv_id}.prop_{kv_id}"

            v = draw(value_strategy())
            line = f"{k} = {v}"
            if draw(st.booleans()):
                line += f" # comment {kv_id}"
            lines.append(line)

    return "\n".join(lines)


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
    *([document()] * 30),
    many_siblings(),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    deep_mixed_nesting(),
    deep_quoted_mixed()
)