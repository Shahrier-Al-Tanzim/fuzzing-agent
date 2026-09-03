"""Generated strategy - iteration 2, attempt 2.
accepted: True
generated: 2026-08-16T15:20:11.457605+00:00
"""
from hypothesis import strategies as st
from hypothesis.strategies import composite

@composite
def key(draw):
    return draw(st.one_of(
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.text(min_size=1, max_size=10).map(lambda x: x)
    ))

@composite
def dotted_key(draw):
    return draw(st.text(min_size=1, max_size=10) + st.text(min_size=1, max_size=10, alphabet='._'))

@composite
def unquoted_key(draw):
    return draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'))

@composite
def value(draw):
    return draw(st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1).map(str),
        st.floats(min_value=-1e10, max_value=1e10).map(str),
        st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
        st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'"),
        st.booleans().map(lambda x: 'true' if x else 'false'),
        st.tuples(st.integers(1970, 2100), st.integers(1, 12), st.integers(1, 28))
            .map(lambda t: f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"),
        st.tuples(st.integers(0, 23), st.integers(0, 59), st.integers(0, 59))
            .map(lambda t: f"{t[0]:02d}:{t[1]:02d}:{t[2]:02d}"),
        st.recursive(
            st.one_of(st.integers(min_value=-2**63, max_value=2**63-1).map(str),
                       st.floats(min_value=-1e10, max_value=1e10).map(str),
                       st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
                       st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'")),
            lambda x: st.lists(x).map(lambda y: f"[{', '.join(y)}]"),
            max_leaves=100
        ),
        st.recursive(
            st.one_of(st.integers(min_value=-2**63, max_value=2**63-1).map(str),
                       st.floats(min_value=-1e10, max_value=1e10).map(str),
                       st.text(min_size=1, max_size=10).map(lambda x: f'"{x}"'),
                       st.text(min_size=1, max_size=10).map(lambda x: f"'{x}'")),
            lambda x: st.dictionaries(key(), x).map(lambda y: f"{{{', '.join(f'{k} = {v}' for k, v in y.items())}}}"),
            max_leaves=100
        )
    ))

@composite
def pair(draw):
    return f"{draw(key())} = {draw(value())}"

@composite
def table(draw):
    return draw(st.one_of(
        key().map(lambda k: f"[{k}]"),
        key().map(lambda k: f"[[{k}]]")
    ))

@composite
def document(draw):
    elements = draw(st.lists(st.one_of(pair(), table())))
    return "\n".join(elements)

@composite
def array(draw, depth=0):
    if depth >= 20000:
        return draw(value())
    return draw(st.one_of(
        value(),
        array(depth=depth + 1), array(depth=depth + 1),
        array(depth=depth + 1), array(depth=depth + 1)
    ))

@composite
def inline_table(draw, depth=0):
    if depth >= 20000:
        return draw(value())
    return draw(st.one_of(
        value(),
        inline_table(depth=depth + 1), inline_table(depth=depth + 1),
        inline_table(depth=depth + 1), inline_table(depth=depth + 1)
    ))

@composite
def document_depth_biased(draw):
    elements = draw(st.lists(st.one_of(
        pair(),
        table(),
        pair().map(lambda p: p.replace(" = ", " = [") + "]"),
        pair().map(lambda p: p.replace(" = ", " = {") + "}")
    )))
    return "\n".join(elements)

toml_strategy = st.one_of(document(), document_depth_biased())