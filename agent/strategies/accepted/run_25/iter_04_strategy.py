"""Generated strategy - iteration 4, attempt 1.
accepted: True
generated: 2026-08-20T06:44:37.379056+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

UNQUOTED_CHARS = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)
BASIC_STR_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-./:;!?@#$%^&*()[]=+|"
NON_ASCII_CHARS = "café_Ã¶_日本語_🌍_é_à_ç"

unquoted_key = st.text(alphabet=UNQUOTED_CHARS, min_size=1, max_size=15)
quoted_key = st.text(alphabet=BASIC_STR_CHARS, min_size=1, max_size=15).map(
    lambda s: f'"{s}"'
)
simple_key = st.one_of(unquoted_key, quoted_key)
dotted_key = st.lists(simple_key, min_size=2, max_size=4).map(
    lambda parts: ".".join(parts)
)
key_strat = st.one_of(simple_key, dotted_key)

scalar_value = st.one_of(
    # Integers (standard, overflow past INT64_MAX/MIN, leading zeros, underscores)
    st.integers(
        min_value=-9223372036854775808, max_value=9223372036854775807
    ).map(str),
    st.sampled_from([
        "9223372036854775808",
        "-9223372036854775809",
        "18446744073709551615",
        "007",
        "0123",
        "000",
        "-01",
        "1_000",
        "1_234_567",
        "-10_000",
    ]),
    st.integers(0, 65535).map(hex),
    st.integers(0, 65535).map(oct),
    st.integers(0, 65535).map(bin),
    st.sampled_from(["0x12_34", "0o7_55", "0b1_010"]),
    # Floats
    st.floats(allow_nan=True, allow_infinity=True).map(str),
    st.sampled_from(
        ["inf", "-inf", "+inf", "nan", "+nan", "1e10", "1.0e-5", "0.0", "-0.0"]
    ),
    # Booleans
    st.sampled_from(["true", "false"]),
    # Basic & Literal Strings
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(
        lambda s: f'"{s}"'
    ),
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(
        lambda s: f"'{s}'"
    ),
    # ML_BASIC_STRING & ML_LITERAL_STRING
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(
        lambda s: f'"""{s}"""'
    ),
    st.text(alphabet=BASIC_STR_CHARS, min_size=0, max_size=15).map(
        lambda s: f"'''{s}'''"
    ),
    # Unicode escape strings
    st.sampled_from(
        ['"\\u0041"', '"\\u0000"', '"\\u007F"', '"\\U00000041"', '"hello \\u0021"']
    ),
    # Non-ASCII strings
    st.sampled_from(
        ['"café"', '"日本語"', "'café'", "'こんにちは'", '"\u00e9"', "'''café'''"]
    ),
    # Date & Time types
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
        st.integers(1970, 2038), st.integers(1, 12), st.integers(1, 28)
    ).map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
    st.tuples(
        st.integers(0, 23), st.integers(0, 59), st.integers(0, 59)
    ).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
    st.tuples(
        st.integers(0, 23),
        st.integers(0, 59),
        st.integers(0, 59),
        st.integers(1, 999),
    ).map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}.{t[3]:03d}"),
    # Over-long fractional seconds (Divergence #2)
    st.sampled_from([
        "1979-05-27T00:32:00.9999999999999999999Z",
        "2023-01-01T12:00:00.1234567890123456789+00:00",
    ]),
)


@composite
def recursive_value(draw, depth=0):
  if depth >= 8:
    return draw(scalar_value)

  choice = draw(st.integers(1, 10))
  if choice <= 4:
    return draw(scalar_value)
  elif choice <= 7:
    elems = draw(
        st.lists(recursive_value(depth=depth + 1), min_size=0, max_size=4)
    )
    body = ", ".join(elems)
    if draw(st.booleans()) and elems:
      body += ","
    return f"[{body}]"
  else:
    keys = draw(st.lists(unquoted_key, min_size=0, max_size=4, unique=True))
    pairs = [f"{k} = {draw(recursive_value(depth=depth + 1))}" for k in keys]
    body = ", ".join(pairs)
    # Divergence #1: trailing comma in inline table
    if draw(st.booleans()) and pairs:
      body += ","
    return f"{{{body}}}"


value_strategy = recursive_value()


@composite
def document(draw):
  lines = []
  num_sections = draw(st.integers(1, 6))
  for s in range(num_sections):
    if s > 0 or draw(st.booleans()):
      tbl_key = draw(key_strat)
      is_array_table = draw(st.booleans())
      if is_array_table:
        lines.append(f"[[{tbl_key}]]")
      else:
        lines.append(f"[{tbl_key}]")

    num_entries = draw(st.integers(1, 6))
    keys = draw(
        st.lists(key_strat, min_size=num_entries, max_size=num_entries, unique=True)
    )
    for entry_idx in range(num_entries):
      k = keys[entry_idx]
      v = draw(value_strategy)
      comment = ""
      if draw(st.booleans()):
        c_text = draw(
            st.text(
                alphabet=BASIC_STR_CHARS + NON_ASCII_CHARS,
                min_size=1,
                max_size=10,
            )
        )
        comment = f" # {c_text}"
      lines.append(f"{k} = {v}{comment}")

  return "\n".join(lines)


# Deep accepted strategies pushing depth target to 90000+
@composite
def deep_accepted_array(draw):
  n = draw(st.integers(min_value=5000, max_value=45000))
  val = draw(scalar_value)
  return f"v = {'[' * n}{val}{']' * n}"


@composite
def deep_accepted_inline_table(draw):
  n = draw(st.integers(min_value=5000, max_value=75000))
  val = draw(scalar_value)
  return f"v = {'{a=' * n}{val}{'}' * n}"


@composite
def deep_accepted_dotted_key(draw):
  n = draw(st.integers(min_value=10000, max_value=95000))
  val = draw(scalar_value)
  return f"{'a.' * n}k = {val}"


@composite
def deep_accepted_mixed(draw):
  n = draw(st.integers(min_value=2500, max_value=22000))
  val = draw(scalar_value)
  return f"v = {'[{a=' * n}{val}{'}]' * n}"


# Crash-seeking extreme depth strategies
@composite
def deep_array(draw):
  n = draw(st.integers(min_value=48_000, max_value=100_000))
  return f"v = {'[' * n}1{']' * n}"


@composite
def deep_inline_table(draw):
  n = draw(st.integers(min_value=80_000, max_value=120_000))
  return f"v = {'{a=' * n}1{'}' * n}"


@composite
def deep_dotted_key(draw):
  n = draw(st.integers(min_value=95_000, max_value=130_000))
  return f"{'a.' * n}k = 1"


@composite
def deep_mixed_nesting(draw):
  n = draw(st.integers(min_value=50_000, max_value=90_000))
  return f"v = {'[{a=' * n}1{'}]' * n}"


@composite
def many_siblings(draw):
  n = draw(st.integers(min_value=10_000, max_value=60_000))
  lines = ["[a]"] + [f"k{i} = 1" for i in range(n)]
  return "\n".join(lines)


toml_strategy = st.one_of(
    *([document()] * 16),
    deep_accepted_array(),
    deep_accepted_inline_table(),
    deep_accepted_dotted_key(),
    deep_accepted_mixed(),
    deep_array(),
    deep_inline_table(),
    deep_dotted_key(),
    deep_mixed_nesting(),
    many_siblings(),
)