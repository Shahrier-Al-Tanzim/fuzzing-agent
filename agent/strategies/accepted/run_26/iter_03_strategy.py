"""Generated strategy - iteration 3, attempt 2.
accepted: True
generated: 2026-08-20T08:50:24.186911+00:00
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

key_strategy = st.one_of(unquoted_key, quoted_basic_key, quoted_literal_key)

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
single_line_val = st.one_of(integer_val, float_val, bool_val, datetime_val, basic_string, literal_string)


@composite
def value_strategy(draw):
    return draw(st.recursive(
        single_line_val,
        lambda children: st.one_of(
            st.lists(children, max_size=4).map(lambda items: f"[{', '.join(items)}]"),
            st.just("[]"),
            st.lists(single_line_val, min_size=1, max_size=3).map(
                lambda items: f"{{{', '.join(f'ik{i} = {v}' for i, v in enumerate(items))}}}"
            ),
            st.lists(single_line_val, min_size=1, max_size=3).map(
                lambda items: f"{{{', '.join(f'ik{i} = {v}' for i, v in enumerate(items))}, }}"
            ),
            st.just("{}")
        ),
        max_leaves=10
    ))


@composite
def document(draw):
    lines = []

    # Root level keys with guaranteed unique names
    num_root_kv = draw(st.integers(min_value=1, max_value=4))
    for k_idx in range(num_root_kv):
        k = f"root_key_{k_idx}"
        v = draw(value_strategy())
        lines.append(f"{k} = {v}")

    # Section tables with guaranteed unique names
    num_sections = draw(st.integers(min_value=0, max_value=3))
    for s_idx in range(num_sections):
        header_type = draw(st.sampled_from(["table", "array_table"]))
        if header_type == "table":
            lines.append(f"[section_{s_idx}]")
        else:
            lines.append(f"[[arr_section_{s_idx}]]")

        num_kv = draw(st.integers(min_value=1, max_value=4))
        for k_idx in range(num_kv):
            k = f"sec_k_{s_idx}_{k_idx}"
            v = draw(value_strategy())
            lines.append(f"{k} = {v}")

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