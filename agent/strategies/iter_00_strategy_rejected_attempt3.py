"""Generated strategy - iteration 0, attempt 3.
accepted: False
generated: 2026-08-13T07:59:12.899675+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def int_value(draw):
    return str(draw(st.integers(min_value=-2**63, max_value=2**63-1)))

@composite
def float_value(draw):
    return str(draw(st.floats(min_value=-1e100, max_value=1e100)))

@composite
def bool_value(draw):
    return str(draw(st.sampled_from([True, False])))

@composite
def string_value(draw):
    return draw(st.text(max_size=100))

@composite
def key(draw):
    return draw(st.text(max_size=100, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'))

@composite
def pair(draw):
    k = draw(key())
    v = draw(st.one_of(int_value(), float_value(), bool_value(), string_value()))
    return (k, v)

@composite
def table(draw, max_size=10):
    pairs = draw(st.lists(pair(), min_size=0, max_size=max_size))
    return pairs

@composite
def array(draw, max_size=10):
    values = draw(st.lists(st.one_of(int_value(), float_value(), bool_value(), string_value()), min_size=0, max_size=max_size))
    return values

@composite
def inline_table(draw, max_size=10):
    pairs = draw(st.lists(pair(), min_size=0, max_size=max_size))
    return pairs

@composite
def document(draw, max_size=10):
    elements = draw(st.lists(st.one_of(pair(), table(), array(), inline_table()), min_size=0, max_size=max_size))
    return elements

@composite
def toml_string(draw):
    elements = draw(document())
    result = []
    for element in elements:
        if isinstance(element, tuple):
            result.append(f"{element[0]} = {element[1]}")
        elif isinstance(element, list) and all(isinstance(x, tuple) for x in element):
            result.append("{")
            for pair in element:
                result.append(f"  {pair[0]} = {pair[1]}")
            result.append("}")
        elif isinstance(element, list) and all(isinstance(x, str) for x in element):
            result.append("[")
            for value in element:
                result.append(f"  {value}")
            result.append("]")
        elif isinstance(element, list) and all(isinstance(x, list) for x in element):
            result.append("[")
            for inner_list in element:
                result.append("  [")
                for value in inner_list:
                    result.append(f"    {value}")
                result.append("  ]")
            result.append("]")
    return "\n".join(result)

toml_strategy = toml_string()