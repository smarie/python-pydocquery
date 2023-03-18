# Authors: Sylvain MARIE <sylvain.marie@se.com>
#          + All contributors to <https://github.com/smarie/python-pydocquery>
#
# License: 3-clause BSD, <https://github.com/smarie/python-pydocquery/blob/master/LICENSE>
import re
from typing import Any, Container, Iterable, Union

from .queries import DocElementQuery, FunctionQuery, KnownFunction, Query


def exists(target: DocElementQuery) -> FunctionQuery:
    """Test that a given element exists in the document.

    Parameters
    ----------
    target : DocElementQuery
        The query defining what should be tested for existence.

    Examples
    --------

    Prerequisite: import the various symbols, the functions library, and init the example.

    >>> from se_model_manager import query_base, evaluate_query
    >>> import se_model_manager.queries_lib as ql
    >>> meta = query_base()
    >>> metadata_example = {"a": {"b": 1, "c": None}}

    Basic usage:

    >>> evaluate_query(ql.exists(meta.a.b), metadata_example)
    True
    >>> evaluate_query(ql.exists(meta.d), metadata_example)
    False
    >>> evaluate_query(ql.exists(meta.a.d), metadata_example)
    False

    Note that as opposed to :func:`not_none`, :func:`exists` returns ``True``
    if the value is ``None``:

    >>> evaluate_query(ql.exists(meta.a.c), metadata_example)
    True
    """
    if not isinstance(target, DocElementQuery):
        raise TypeError("The target of the exists() function must be a direct reference to an element in the document.")

    return FunctionQuery(KnownFunction.EXISTS, args=(target,))


def is_none(target: Query):
    """Test that a given element is none.

    Parameters
    ----------
    target : Query
        The query defining what should be tested for none.

    Examples
    --------

    Prerequisite: import the various symbols, the functions library, and init the example.

    >>> from se_model_manager import query_base, evaluate_query
    >>> import se_model_manager.queries_lib as ql
    >>> meta = query_base()
    >>> metadata_example = {"a": {"b": 1, "c": None}}

    Basic usage:

    >>> evaluate_query(ql.is_none(meta.a.b), metadata_example)
    False
    >>> evaluate_query(ql.is_none(meta.a.c), metadata_example)
    True

    When the element is missing, a :exc:`MissingQueryTargetError` is raised, the missing exception is propagated and
    possibly caught as usual.

    >>> evaluate_query(ql.is_none(meta.missing), metadata_example)
    se_model_manager.MISSING
    >>> evaluate_query(ql.is_none(~meta.missing), metadata_example)
    se_model_manager.NEGATED_MISSING
    """
    if not isinstance(target, Query):
        raise TypeError("`target` must be a query")

    return FunctionQuery(KnownFunction.IS_NONE, args=(target,))


# TODO add not_, or_, and_, xor_ so as to be able to document ~, | , & and ^ in doctests as we do below.
#   Besides this could allow for optional parameters changing the way missings are handled.


def binnot(target: Query):
    """The bitwise not ("invert") operator.

    Parameters
    ----------
    target : Query
        The query defining what should be inverted.

    Examples
    --------

    Prerequisite: import the various symbols, the functions library, and init the example.

    >>> from se_model_manager import query_base, evaluate_query
    >>> import se_model_manager.queries_lib as ql
    >>> meta = query_base()
    >>> metadata_example = {"a": {"b": 1, "c": None}, "e": False}

    Basic usage:

    >>> evaluate_query(ql.binnot(meta.e), metadata_example)
    -1
    >>> evaluate_query(ql.binnot(meta.a.b), metadata_example)
    -2
    >>> evaluate_query(ql.binnot(meta.a.c), metadata_example)
    Traceback (most recent call last):
        ...
    TypeError: bad operand type for unary ~: 'NoneType'

    When the element is missing, the missing exception is propagated and possibly caught as usual.

    >>> evaluate_query(ql.binnot(meta.d), metadata_example)
    se_model_manager.MISSING
    >>> evaluate_query(ql.binnot(~meta.d), metadata_example)
    se_model_manager.NEGATED_MISSING
    """
    if not isinstance(target, Query):
        raise TypeError("`target` must be a query")

    return FunctionQuery(KnownFunction.BINNOT, args=(target,))


def binand(left: Query, right: Query):
    """The bitwise and operator.

    Parameters
    ----------
    left : Query
        The query defining the left term of the bitwise and.
    right : Query
        The query defining the right term of the bitwise and.

    Examples
    --------

    Prerequisite: import the various symbols, the functions library, and init the example.

    >>> from se_model_manager import query_base, evaluate_query
    >>> import se_model_manager.queries_lib as ql
    >>> meta = query_base()
    >>> metadata_example = {"a": {"b": 12, "c": 25}, "e": False}

    Basic usage:

    >>> evaluate_query(ql.binand(meta.a.b, meta.a.c), metadata_example)
    8
    >>> evaluate_query(ql.binand(meta.a.b, 0), metadata_example)
    0

    When an element is missing, the missing exception is propagated and possibly caught as usual.

    >>> evaluate_query(ql.binand(meta.e, meta.missing), metadata_example)
    se_model_manager.MISSING
    >>> evaluate_query(ql.binand(meta.e, ~(meta.missing > 12)), metadata_example)
    se_model_manager.NEGATED_MISSING
    """
    if not isinstance(left, Query) and not isinstance(right, Query):
        raise TypeError("At least one of `left` and `right` members must be a query")

    return FunctionQuery(KnownFunction.BINAND, args=(left, right))


def binor(left: Query, right: Query):
    """The bitwise or operator.

    Parameters
    ----------
    left : Query
        The query defining the left term of the bitwise or.
    right : Query
        The query defining the right term of the bitwise or.

    Examples
    --------

    Prerequisite: import the various symbols, the functions library, and init the example.

    >>> from se_model_manager import query_base, evaluate_query
    >>> import se_model_manager.queries_lib as ql
    >>> meta = query_base()
    >>> metadata_example = {"a": {"b": 12, "c": 25}, "e": False}

    Basic usage:

    >>> evaluate_query(ql.binor(meta.a.b, meta.a.c), metadata_example)
    29
    >>> evaluate_query(ql.binor(meta.a.b, 1), metadata_example)
    13

    When an element is missing, the missing exception is propagated and possibly caught as usual.

    >>> evaluate_query(ql.binor(meta.e, meta.missing), metadata_example)
    se_model_manager.MISSING
    >>> evaluate_query(ql.binor(meta.e, ~(meta.missing > 12)), metadata_example)
    se_model_manager.NEGATED_MISSING
    >>> evaluate_query(~ql.binor(meta.e, ~(meta.missing > 12)), metadata_example)
    se_model_manager.MISSING
    """
    if not isinstance(left, Query) and not isinstance(right, Query):
        raise TypeError("At least one of `left` and `right` members must be a query")

    return FunctionQuery(KnownFunction.BINOR, args=(left, right))


def binxor(left: Query, right: Query):
    """The bitwise xor operator.

    Parameters
    ----------
    left : Query
        The query defining the left term of the bitwise xor.
    right : Query
        The query defining the right term of the bitwise xor.

    Examples
    --------

    Prerequisite: import the various symbols, the functions library, and init the example.

    >>> from se_model_manager import query_base, evaluate_query
    >>> import se_model_manager.queries_lib as ql
    >>> meta = query_base()
    >>> metadata_example = {"a": {"b": 156, "c": 52}, "e": False}

    Basic usage:

    >>> evaluate_query(ql.binxor(meta.a.b, meta.a.c), metadata_example)
    168
    >>> evaluate_query(ql.binxor(meta.a.b, 1), metadata_example)
    157

    When an element is missing, the missing exception is propagated and possibly caught as usual.

    >>> evaluate_query(ql.binxor(meta.e, meta.missing), metadata_example)
    se_model_manager.MISSING
    >>> evaluate_query(ql.binxor(meta.e, ~(meta.missing > 12)), metadata_example)
    se_model_manager.NEGATED_MISSING
    """
    if not isinstance(left, Query) and not isinstance(right, Query):
        raise TypeError("At least one of `left` and `right` members must be a query")

    return FunctionQuery(KnownFunction.BINXOR, args=(left, right))


def matches(target: Query, regex: Union[str, re.Pattern], flags: int = 0) -> FunctionQuery:
    """
    Test that a string-representing query matches the given regex.

    Parameters
    ----------
    target : Query
        The query defining what will be tested against the regex.

    regex : str
        The regular expression to use for matching.

    flags : int
        Regex flags to pass to ``re.match``.

    Examples
    --------

    Prerequisite: import the various symbols, the functions library, and init the example.

    >>> from se_model_manager import query_base, evaluate_query
    >>> import se_model_manager.queries_lib as ql
    >>> meta = query_base()
    >>> metadata_example = {"a": {"b": 1, "c": None}, "text": "hello", "text2": "2"}

    Basic usage:

    >>> evaluate_query(ql.matches(meta.text, r'he[l_]+o'), metadata_example)
    True
    >>> evaluate_query(ql.matches(meta.text, r'he[l_]+o2'), metadata_example)
    False
    >>> evaluate_query(ql.matches(meta.text + meta.text2, r'he[l_]+o2'), metadata_example)
    True

    As opposed to the python `re.match` method, this returns True even if the match is somewhere in the string
    (so equivalent to `re.search`)

    >>> evaluate_query(ql.matches(meta.text, r'[l_]+o'), metadata_example)
    True

    Of course you can still use ^ and $ to indicate beginning and end of the string, in order to force
    full- , beginning- or ending-match

    >>> evaluate_query(ql.matches(meta.text, r'lo'), metadata_example)
    True
    >>> evaluate_query(ql.matches(meta.text, r'^lo'), metadata_example)
    False
    >>> evaluate_query(ql.matches(meta.text, r'^he'), metadata_example)
    True
    >>> evaluate_query(ql.matches(meta.text, r'lo$'), metadata_example)
    True
    >>> evaluate_query(ql.matches(meta.text, r'he$'), metadata_example)
    False
    >>> evaluate_query(ql.matches(meta.text, r'he'), metadata_example)
    True

    If the target is not of string type, the error is silently caught and turned into a no-match:

    >>> evaluate_query(ql.matches(meta.a, r'^h[l_]+o'), metadata_example)
    False

    Finally, when the target does not exist, the same behaviour as for :func:`not_none` is implemented:

    >>> evaluate_query(ql.matches(meta.missing, r'^h[l_]+o') | True, metadata_example)
    True
    >>> evaluate_query(ql.matches(meta.missing, r'^h[l_]+o') | False, metadata_example)
    False
    >>> evaluate_query(ql.matches(meta.missing, r'^h[l_]+o'), metadata_example)
    se_model_manager.MISSING
    >>> evaluate_query(~ql.matches(meta.missing, r'^h[l_]+o'), metadata_example)
    se_model_manager.NEGATED_MISSING
    """
    if not isinstance(target, Query):
        raise TypeError("`target` must be a query")
    if not isinstance(regex, (str, re.Pattern)):
        raise TypeError("`regex` must be a string or re.Pattern")
    if not isinstance(flags, int):
        raise TypeError("`flags` must be an int")

    return FunctionQuery(KnownFunction.MATCHES, args=(target, regex, flags))


def is_in(item: Union[Any, Query], collection: Union[Container, Query]) -> FunctionQuery:
    """
    Test that an item is present in a collection.

    Parameters
    ----------
    item : Union[Any, Query]
        The item to search for in the collection.

    collection : Union[Container, Query]
        The collection inside which the item should be searched for.

    Examples
    --------

    Prerequisite: import the various symbols, the functions library, and init the example.

    >>> from se_model_manager import query_base, evaluate_query
    >>> import se_model_manager.queries_lib as ql
    >>> meta = query_base()
    >>> metadata_example = {"a": {"b": 1, "c": None}, "text": "hello", "key": "c"}

    Basic usage when the container is a string

    >>> evaluate_query(ql.is_in("ll", meta.text), metadata_example)
    True
    >>> evaluate_query(ql.is_in("li", meta.text), metadata_example)
    False
    >>> evaluate_query(ql.is_in(meta.text, ["hey"]), metadata_example)
    False
    >>> evaluate_query(ql.is_in(meta.text, ["hey", "hello"]), metadata_example)
    True
    >>> evaluate_query(ql.is_in(meta.key, meta.text), metadata_example)
    False

    The container can be a dict:

    >>> evaluate_query(ql.is_in(meta.key, dict(a=0)), metadata_example)
    False
    >>> evaluate_query(ql.is_in(meta.key, meta.a), metadata_example)
    True
    >>> evaluate_query(ql.is_in("d", meta.a), metadata_example)
    False

    When the container or item is missing, the missing exception is propagated and possibly caught as usual.

    >>> evaluate_query(ql.is_in(meta.text, meta.missing), metadata_example)
    se_model_manager.MISSING
    >>> evaluate_query(ql.is_in(meta.missing, meta.text), metadata_example)
    se_model_manager.MISSING
    """
    if not isinstance(collection, Query) and not isinstance(item, Query):
        raise TypeError("At least one of `collection` and `item` must be a query")

    return FunctionQuery(KnownFunction.IS_IN, args=(item, collection))


def any(target: Union[Query, Iterable[Query]]):
    """Test that any of the elements in the query, or any of the queries, is True.

    Note that `any((q1, q2))` slightly differs from `q1 | q2` in the sense that it always returns a boolean even in case
    of objects or missings. This is to mimic the existing difference between python `any` and `or`:
    `any((object(), False))` returns `True` while `object() or False` returns `object`.

    Parameters
    ----------
    target : Union[Query, Iterable[Query]]
        If a single query is passed, the element returned by resolving the query will serve as a target for the any().
        If an iterable is passed, each query will be resolved in turn in a lazy fashion, and the first True result
        will result in a True output (False will be returned otherwise). If all queries refer to missing entries,
        a :exc:`MissingQueryTargetError` is raised.

    Examples
    --------

    Prerequisite: import the various symbols, the functions library, and init the example.

    >>> from se_model_manager import query_base, evaluate_query
    >>> import se_model_manager.queries_lib as ql
    >>> meta = query_base()
    >>> metadata_example = {"a": {"b": 1, "c": None}, "items": [False, None]}

    Basic usage:

    >>> evaluate_query(ql.any(meta.items), metadata_example)
    False
    >>> evaluate_query(ql.any(meta.items + [0, 1]), metadata_example)
    True
    >>> evaluate_query(ql.any([meta.a.c, meta.a.b < 1]), metadata_example)
    False
    >>> evaluate_query(ql.any([meta.a.c, meta.a.b < 1, exists(meta.a)]), metadata_example)
    True

    When the global element or an item in the list is missing it is considered as False.

    >>> evaluate_query(ql.any((meta.a.c, meta.missing)), metadata_example)
    False
    >>> evaluate_query(ql.any([meta.a.c, meta.missing, meta.a.b]), metadata_example)
    True

    Negated missings behave as True and the exception is caught and transformed to a boolean (just as `any` always
    guarantees that the result is a bool)

    >>> evaluate_query(ql.any([meta.a.c, meta.missing, ~(meta.missing > 12)]), metadata_example)
    True
    >>> evaluate_query(~ql.any([meta.a.c, meta.missing, ~(meta.missing > 12)]), metadata_example)
    False

    When all elements are missing, this is a missing and is handled as usual:

    >>> evaluate_query(ql.any(meta.missing), metadata_example)
    se_model_manager.MISSING

    """
    if not isinstance(target, Iterable) and not isinstance(target, Query):
        raise TypeError("`target` must be an iterable or a query")

    return FunctionQuery(KnownFunction.ANY, args=(target,))


def all(target: Union[Query, Iterable[Query]]):
    """Test that all of the elements in the query, or all of the queries, is True.

    Note that `all((q1, q2))` slightly differs from `q1 & q2` in the sense that it always returns a boolean even in case
    of objects or missings. This is to mimic the existing difference between python `all` and `and`:
    `all((True, object()))` returns `True` while `True and object()` returns `object`.

    Parameters
    ----------
    target : Union[Query, Iterable[Query]]
        If a single query is passed, the element returned by resolving the query will serve as a target for the all().
        If an iterable is passed, each query will be resolved in turn in a lazy fashion, and the first False result
        will result in a False output (True will be returned otherwise). If all queries refer to missing entries,
        a :exc:`MissingQueryTargetError` is raised.

    Examples
    --------

    Prerequisite: import the various symbols, the functions library, and init the example.

    >>> from se_model_manager import query_base, evaluate_query
    >>> import se_model_manager.queries_lib as ql
    >>> meta = query_base()
    >>> metadata_example = {"a": {"b": 1, "c": False}, "items": [2, True]}

    Basic usage:

    >>> evaluate_query(ql.all(meta.items), metadata_example)
    True
    >>> evaluate_query(ql.all(meta.items + [0, 1]), metadata_example)
    False
    >>> evaluate_query(ql.all([~meta.a.c, meta.a.b >= 1, exists(meta.d)]), metadata_example)
    False
    >>> evaluate_query(ql.all([~meta.a.c, meta.a.b >= 1]), metadata_example)
    True

    When the global element is missing it is considered as missing and is handled according to
    the fallback_mode as usual:

    >>> evaluate_query(ql.all(meta.missing), metadata_example)
    se_model_manager.MISSING
    >>> evaluate_query(~ql.all(meta.missing), metadata_example)
    se_model_manager.NEGATED_MISSING
    >>> evaluate_query(ql.all(~meta.missing), metadata_example)
    se_model_manager.NEGATED_MISSING
    >>> evaluate_query(~ql.all(~meta.missing), metadata_example)
    se_model_manager.MISSING

    When an iterable is passed and that iterable contains a missing, the missing will only be propagated when
    all entries are missing. Otherwise the exception is caught and transformed to a boolean (just as `all` always
    guarantees that the result is a bool)

    >>> evaluate_query(ql.all((meta.a.c, meta.missing)), metadata_example)
    False
    >>> evaluate_query(ql.all([~meta.a.c, meta.missing, meta.a.b]), metadata_example)
    se_model_manager.MISSING

    """
    if not isinstance(target, Iterable) and not isinstance(target, Query):
        raise TypeError("`target` must be an iterable or a query")

    return FunctionQuery(KnownFunction.ALL, args=(target,))


# TODO
# def fragment(self, document: Mapping) -> Query:
#     def test(value):
#         for key in document:
#             if key not in value or value[key] != document[key]:
#                 return False
#
#         return True
#
#     return self._generate_test(
#         lambda value: test(value),
#         ('fragment', freeze(document)),
#         allow_emptypath=True
#     )
