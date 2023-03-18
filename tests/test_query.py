import pytest

import pydocquery.queries_lib as ql
from pydocquery import (
    MISSING,
    InvalidQueryUsageError,
    MissingQueryTargetError,
    Query,
    compile_query,
    evaluate_query,
    query_base,
    NEGATED_MISSING,
)
from pydocquery.queries import FunctionQuery, resolve_element


def get_simple_metadata():
    metadata = {"a": {"b": 1, "c": True}, "d": "hello"}
    return metadata


@pytest.mark.parametrize("find", [resolve_element, evaluate_query])
def test_query_target_find(find):
    """Test that `query_base` works as expected"""

    metadata = get_simple_metadata()

    model = query_base()

    # Test
    assert find(model, metadata) == metadata
    assert find(model.a, metadata) == {"b": 1, "c": True}
    assert find(model.a.b, metadata) == 1
    assert find(model.a.c, metadata) is True
    assert find(model.d, metadata) == "hello"

    # These are equivalent expressions
    # assert is_same_query(model["a"].b, model.a.b)
    # assert is_same_query(model["a"]["b"], model.a.b)
    # assert is_same_query(model.a["b"], model.a.b)
    # assert find(model["a"].b, metadata) == find(model["a"]["b"], metadata) == find(model.a["b"], metadata) == 1

    # Behaviour in case of missing element in document
    if find is resolve_element:
        with pytest.raises(MissingQueryTargetError):
            find(model.e, metadata)
    elif find is evaluate_query:
        assert find(model.e, metadata) is MISSING


def test_identity_query():
    metadata = get_simple_metadata()
    model = query_base()

    query = model == metadata

    assert isinstance(query, Query)
    assert str(query) == "<metadata_root> == {'a': {'b': 1, 'c': True}, 'd': 'hello'}"
    assert repr(query) == (
        "<TwoSidedOperator.EQ: '=='>("
        "DocElementQuery(_path=<metadata_root>), "
        "{'a': {'b': 1, 'c': True}, 'd': 'hello'}"
        ")"
    )


@pytest.mark.parametrize(
    "op_enum, op_str, stdlib_action, rop_enum, rop_str",
    [
        ("LT", "<", "complement", "GT", ">"),
        ("LE", "<=", "complement", "GE", ">="),
        ("EQ", "==", "revert", None, None),
        ("NE", "!=", "revert", None, None),
        ("ADD", "+", "idle", None, None),
        ("SUB", "-", "idle", None, None),
        ("MUL", "*", "idle", None, None),
        # ("MATMUL", "@", "idle", None, None, False),
        ("TRUEDIV", "/", "idle", None, None),
        ("FLOORDIV", "//", "idle", None, None),
        ("MOD", "%", "idle", None, None),
        ("POW", "**", "idle", None, None),
        ("LSHIFT", "<<", "idle", None, None),
        ("RSHIFT", ">>", "idle", None, None),
    ],
)
def test_query_two_sided_op(op_enum, op_str, stdlib_action, rop_enum, rop_str):
    """"""
    metadata = {"a": {"b": 1, "c": True}, "d": "hello"}
    model = query_base()

    def op_fun(x, y):
        return eval(f"x {op_str} y")

    # do "model.d [<,>,==,!=,...] 'foo'"
    q1 = op_fun(model.a.b, 12)
    assert repr(q1) == f"<TwoSidedOperator.{op_enum}: '{op_str}'>(DocElementQuery(_path=<metadata_root>.a.b), 12)"
    assert str(q1) == f"<metadata_root>.a.b {op_str} 12"

    # check that the query works
    element_to_test = resolve_element(model.a.b, metadata)
    expected_result = op_fun(element_to_test, 12)
    res = compile_query(q1)(metadata)
    res2 = evaluate_query(q1, metadata)
    assert res == res2 == expected_result

    # Missing behaviour one side
    res_missing = evaluate_query(q1, {})
    assert res_missing is MISSING

    # It works in both directions, but the python language may revert the operation automatically
    q2 = op_fun(42, model.a.b)
    if stdlib_action == "idle":
        # Python does not modify the operation
        assert repr(q2) == f"<TwoSidedOperator.{op_enum}: '{op_str}'>(42, DocElementQuery(_path=<metadata_root>.a.b))"
        assert str(q2) == f"42 {op_str} <metadata_root>.a.b"

    elif stdlib_action == "revert":
        # Python reverts the operation by just changing the arguments order
        assert repr(q2) == f"<TwoSidedOperator.{op_enum}: '{op_str}'>(DocElementQuery(_path=<metadata_root>.a.b), 42)"
        assert str(q2) == f"<metadata_root>.a.b {op_str} 42"

    elif stdlib_action == "complement":
        # Python replaces the operation with the complement
        def rop_fun(x, y):
            return eval(f"x {rop_str} y")

        q2r = rop_fun(model.a.b, 42)

        # Assess that the representation of q1r is correct
        assert (
            repr(q2r) == f"<TwoSidedOperator.{rop_enum}: '{rop_str}'>(DocElementQuery(_path=<metadata_root>.a.b), 42)"
        )
        assert str(q2r) == f"<metadata_root>.a.b {rop_str} 42"
        # Now make sure that q2 was correctly converted to the reverted query q1r
        assert repr(q2) == repr(q2r)
        assert str(q2) == str(q2r)
    else:
        raise ValueError(stdlib_action)

    # Make sure that this second query works
    element_to_test = resolve_element(model.a.b, metadata)
    expected_result = op_fun(42, element_to_test)
    res = compile_query(q2)(metadata)
    res2 = evaluate_query(q2, metadata)
    assert res == res2 == expected_result

    # Missing behaviour again
    res_missing = evaluate_query(q2, {})
    assert res_missing is MISSING

    # Queries can be used in both sides
    q3 = op_fun(model.a.b, model.a.c)
    assert (
        repr(q3)
        == f"<TwoSidedOperator.{op_enum}: '{op_str}'>(DocElementQuery(_path=<metadata_root>.a.b), DocElementQuery(_path=<metadata_root>.a.c))"
    )
    assert str(q3) == f"<metadata_root>.a.b {op_str} <metadata_root>.a.c"
    if rop_str is not None:
        q3r = rop_fun(model.a.b, model.a.c)
        assert (
            repr(q3r)
            == f"<TwoSidedOperator.{rop_enum}: '{rop_str}'>(DocElementQuery(_path=<metadata_root>.a.b), DocElementQuery(_path=<metadata_root>.a.c))"
        )
        assert str(q3r) == f"<metadata_root>.a.b {rop_str} <metadata_root>.a.c"

    # Missing both side
    res_missing = evaluate_query(q3, {})
    assert res_missing is MISSING


def test_boolean_and():
    metadata = {"a": {"b": 1, "c": True}, "d": "hello", "e": 12}
    meta = query_base()

    q1 = meta.a.c & meta.d
    assert (
        repr(q1)
        == "<TwoSidedOperator.AND: 'and'>(DocElementQuery(_path=<metadata_root>.a.c), DocElementQuery(_path=<metadata_root>.d))"
    )
    assert str(q1) == "<metadata_root>.a.c and <metadata_root>.d"
    assert (
        evaluate_query(q1, metadata) == "hello"
    )  # Strange but normal, see https://stackoverflow.com/a/68896273/7262247
    # False-resolving
    assert evaluate_query(None & meta.a.b, metadata) is None
    assert evaluate_query(meta.d & None, metadata) is None
    # Missing
    assert evaluate_query(meta.missing & meta.d, metadata) is MISSING
    assert evaluate_query(meta.d & meta.missing, metadata) is MISSING
    # This is not the bitwise operation
    assert 12 & 25 == 8
    assert 12 and 25 == 25
    assert evaluate_query(meta.e & 25, metadata) == 25


def test_boolean_and():
    metadata = {"a": {"b": 1, "c": True}, "d": "hello", "e": 12}
    meta = query_base()

    q1 = meta.a.c & meta.d
    assert (
        repr(q1)
        == "<TwoSidedOperator.AND: 'and'>(DocElementQuery(_path=<metadata_root>.a.c), DocElementQuery(_path=<metadata_root>.d))"
    )
    assert str(q1) == "<metadata_root>.a.c and <metadata_root>.d"
    assert (
        evaluate_query(q1, metadata) == "hello"
    )  # Strange but normal, see https://stackoverflow.com/a/68896273/7262247
    # False-resolving
    assert evaluate_query(None & meta.a.b, metadata) is None
    assert evaluate_query(meta.d & None, metadata) is None
    # Missing
    assert evaluate_query(meta.missing & meta.d, metadata) is MISSING
    assert evaluate_query(meta.d & meta.missing, metadata) is MISSING
    # This is not the bitwise operation
    assert 12 & 25 == 8
    assert 12 and 25 == 25
    assert evaluate_query(meta.e & 25, metadata) == 25


def test_boolean_or():
    metadata = {"a": {"b": 1, "c": False}, "d": "hello", "e": 12}
    meta = query_base()

    q1 = meta.d | meta.a.c
    assert (
        repr(q1)
        == "<TwoSidedOperator.OR: 'or'>(DocElementQuery(_path=<metadata_root>.d), DocElementQuery(_path=<metadata_root>.a.c))"
    )
    assert str(q1) == "<metadata_root>.d or <metadata_root>.a.c"
    assert (
        evaluate_query(q1, metadata) == "hello"
    )  # Strange but normal, see https://stackoverflow.com/a/68896273/7262247
    # False-resolving
    assert evaluate_query(meta.a.c | "ho", metadata) == "ho"
    assert evaluate_query(meta.a.c | None, metadata) is None
    # Missing
    assert evaluate_query(meta.missing | meta.d, metadata) == "hello"
    assert evaluate_query(meta.d | meta.missing, metadata) == "hello"
    assert evaluate_query(meta.missing2 | meta.missing, metadata) is MISSING
    # This is not the bitwise operation
    assert 12 | 25 == 29
    assert 12 or 25 == 12
    assert evaluate_query(meta.e | 25, metadata) == 12


def test_boolean_xor():
    meta = query_base()
    with pytest.raises(InvalidQueryUsageError):
        meta.a ^ 12


@pytest.mark.parametrize(
    "op_enum, op_str",
    [
        ("POS", "+"),
        ("NEG", "-"),
    ],
)
def test_query_one_sided_op(op_enum, op_str):

    metadata = {"a": {"b": 1, "c": True}, "d": "hello"}
    model = query_base()

    def op_fun(x):
        return eval(f"{op_str} x")

    # do "[+, -, ~...] model.d"
    q1 = op_fun(model.a.b)
    assert repr(q1) == f"<OneSidedOperator.{op_enum}: '{op_str}'>(DocElementQuery(_path=<metadata_root>.a.b))"
    assert str(q1) == f"{op_str} <metadata_root>.a.b"

    # check that the query works - nominal
    element_to_test = resolve_element(model.a.b, metadata)
    expected_result = op_fun(element_to_test)
    res = compile_query(q1)(metadata)
    res2 = evaluate_query(q1, metadata)
    assert res == res2 == expected_result

    # check that the query works - missing
    res2 = evaluate_query(q1, metadata={})
    assert res2 is MISSING


def test_not_and_invert():
    """Test the special case of using the invert operator on booleans vs. numbers"""

    metadata = dict(a=0, b=1, c=1.0, d=False, e=True)
    meta = query_base()

    assert (not 0) is True
    assert ~0 == -1
    assert evaluate_query(~meta.a, metadata) is True

    assert (not 1) is False
    assert ~1 == -2
    assert evaluate_query(~meta.b, metadata) is False

    assert (not 1.0) is False
    with pytest.raises(TypeError):
        ~1.0
    assert evaluate_query(~meta.c, metadata) is False


def test_query_forbidden_operations():
    meta = query_base()

    with pytest.raises(InvalidQueryUsageError):
        hash(meta)

    with pytest.raises(InvalidQueryUsageError):
        meta and 1

    with pytest.raises(InvalidQueryUsageError):
        (meta.rmse > 1) and (meta.foo == 1)


def test_query_known_functions_exists():
    metadata = get_simple_metadata()
    meta = query_base()

    q1 = ql.exists(meta)
    assert isinstance(q1, FunctionQuery)
    assert repr(q1) == "FunctionQuery(function=KnownFunction.EXISTS, args=(DocElementQuery(_path=<metadata_root>),))"
    assert str(q1) == "EXISTS(<metadata_root>)"
    assert evaluate_query(q1, metadata) is True

    # now lets make several others
    assert evaluate_query(ql.exists(meta.a), metadata) is True
    assert evaluate_query(ql.exists(meta.a.unknown), metadata) is False
    assert evaluate_query(ql.exists(meta.unknown), metadata) is False

    with pytest.raises(TypeError):
        ql.exists((meta.a > 1))


def test_query_missings():
    """Test that the behaviour of and, or, any and all are consistent wrt missing"""

    meta = query_base()

    assert evaluate_query(True & meta.missing, {}) is MISSING  # consistent with python returning right member
    assert (
        evaluate_query(meta.missing & True, {}) is MISSING
    )  # consistent with python returning non-truthy left members directly.
    assert (
        evaluate_query(meta.missing & False, {}) is MISSING
    )  # consistent with python returning non-truthy left members directly.
    assert (
        evaluate_query(False & meta.missing, {}) is False
    )  # consistent with python returning non-truthy left members directly.
    assert evaluate_query(meta.missing & meta.missing2, {}) is MISSING

    assert (
        evaluate_query(True | meta.missing, {}) is True
    )  # consistent with python returning truthy left members directly.
    assert (
        evaluate_query(~meta.missing | True, {}) is NEGATED_MISSING
    )  # consistent with python returning truthy left members directly.

    assert evaluate_query(meta.missing | True, {}) is True  # consistent with python returning right member
    assert evaluate_query(False | meta.missing, {}) is MISSING  # consistent with python returning right member
    assert evaluate_query(False | ~meta.missing, {}) is NEGATED_MISSING  # consistent with python returning right member
    assert evaluate_query(meta.missing | False, {}) is False
    assert evaluate_query(meta.missing | meta.missing2, {}) is MISSING
    assert evaluate_query(~meta.missing | meta.missing2, {}) is NEGATED_MISSING
    assert evaluate_query(meta.missing | ~meta.missing2, {}) is NEGATED_MISSING


def test_query_negated_missing():
    """Test that the not operator handles mising values correctly"""

    # same as in mongodb: https://docs.mongodb.com/manual/reference/operator/query/not/#-not
    meta = query_base()

    q = ~(meta.score > 12)
    assert evaluate_query(q, {"score": 12}) is True
    assert evaluate_query(q, {"score": 13}) is False
    assert evaluate_query(q, {}) is NEGATED_MISSING

    assert evaluate_query(~(meta.score > 12) & True, {}) is True
    assert evaluate_query(True & ~(meta.score > 12), {}) is NEGATED_MISSING

    # same thing as in python: all() is not strictly equivalent to chained 'and'
    assert evaluate_query(ql.all((~(meta.score > 12), True)), {}) is True
    assert evaluate_query(ql.all((True, ~(meta.score > 12))), {}) is True

    assert evaluate_query(~(meta.score > 12) | False, {}) is NEGATED_MISSING
    assert evaluate_query(False | ~(meta.score > 12), {}) is NEGATED_MISSING

    # same thing as in python: any() is not strictly equivalent to chained 'or'
    assert evaluate_query(ql.any((~(meta.score > 12), False)), {}) is True
    assert evaluate_query(ql.any((False, ~(meta.score > 12))), {}) is True
