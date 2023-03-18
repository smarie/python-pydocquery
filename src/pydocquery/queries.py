#  © 2021 - 2021 Schneider Electric Industries SAS. All rights reserved.
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, Tuple, TypeVar, Union


class RootError(Exception):
    """The parent class of all exceptions raised in this package."""


SimplePrimitive = Optional[Union[str, int, float]]
"""The type hint for a leaf entry (deep inside possibly nested dicts) in the :class:`Metadata` dictionary."""

NestedPrimitive = Union[SimplePrimitive, Dict[str, "NestedPrimitive"]]  # type: ignore
"""The type hint for an entry in the :class:`Metadata` dictionary. Itself can be a dictionary, possibly nested."""

Metadata = Dict[str, NestedPrimitive]  # type: ignore
"""The type hint for metadata that you may :class:`StorageProvider.store` and :class:`StorageProvider.retrieve`."""


class QueryError(RootError):
    """Base class of query-related errors"""


class MissingQueryTargetError(QueryError):
    """Raised when a query target can not be resolved on a document because it is missing from the document.

    Such an error can go through a "not" operator, in that case it will switch its truth value from False to True.
    """

    def __init__(self, missingpath: Tuple[str, ...]):
        self.missingpath = missingpath
        self.truth_value = False

    def __bool__(self):
        return self.truth_value

    def negate(self):
        """Change the truth value of this exception, typically when using the 'not' operator"""
        self.truth_value = not self.truth_value

    def to_object(self):
        """Convert this exception into one of the two singletons (they have the same truth value)"""
        return NEGATED_MISSING if self.truth_value else MISSING

    def __str__(self):
        path = ".".join(("<metadata_root>",) + self.missingpath)
        return f"Path {path!r} cannot be found in document."


class InvalidQueryUsageError(QueryError):
    """Raised when :class:`Query` objects are not used correctly."""

    def __str__(self):
        return (
            "Invalid Query usage. Query objects can not be used in multi-operator operations such as `a < b < c`, "
            "nor using and/or/nor/in, nor being hashed or used in a hash-requiring operation. Please use "
            "single-operator functions assembled with bitwise operators e.g. `(a < b) & (b < c)`, and use "
            "`import se_model_manager.queries_lib as ql` in order to find known functions such as `ql.exists()`"
        )


class Query(ABC):
    """A query"""

    __slots__ = ()

    @abstractmethod
    def __init__(self, *args, **kwargs):
        """Instances of this class cant be created, subclassing is mandatory"""

    # Basic see https://docs.python.org/3/reference/datamodel.html#basic-customization

    def __bool__(self):
        raise InvalidQueryUsageError()

    def __hash__(self):
        raise InvalidQueryUsageError()

    def __getitem__(self, item):
        # TODO maybe one day
        #  return FunctionQuery(KnownFunction.GET_ITEM, args=(item,))
        raise InvalidQueryUsageError()

    def __lt__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.LT(self, rhs)

    def __le__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.LE(self, rhs)

    def __eq__(self, rhs: Any) -> "TwoSidedOperation":  # type: ignore
        return TwoSidedOperator.EQ(self, rhs)

    def __ne__(self, rhs: Any):
        return TwoSidedOperator.NE(self, rhs)

    def __gt__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.GT(self, rhs)

    def __ge__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.GE(self, rhs)

    # TODO container ? see https://docs.python.org/3/reference/datamodel.html#emulating-container-types

    # see https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types

    def __add__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.ADD(self, rhs)

    def __radd__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.ADD(rhs, self)

    def __sub__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.SUB(self, rhs)

    def __rsub__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.SUB(rhs, self)

    def __mul__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.MUL(self, rhs)

    def __rmul__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.MUL(rhs, self)

    def __matmul__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.MATMUL(self, rhs)

    def __rmatmul__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.MATMUL(rhs, self)

    def __truediv__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.TRUEDIV(self, rhs)

    def __rtruediv__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.TRUEDIV(rhs, self)

    def __floordiv__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.FLOORDIV(self, rhs)

    def __rfloordiv__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.FLOORDIV(rhs, self)

    def __mod__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.MOD(self, rhs)

    def __rmod__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.MOD(rhs, self)

    # def __divmod__(self, rhs: Any) -> "Query":
    #     return TwoSidedOperator.DIVMOD(self, rhs)
    #
    # def __rdivmod__(self, rhs: Any) -> "Query":
    #     return TwoSidedOperator.RDIVMOD(self, rhs)

    def __pow__(self, rhs: Any, modulo=None) -> "Query":
        if modulo is not None:
            raise NotImplementedError()
        return TwoSidedOperator.POW(self, rhs)

    def __rpow__(self, rhs: Any, modulo=None) -> "Query":
        if modulo is not None:
            raise NotImplementedError()
        return TwoSidedOperator.POW(rhs, self)

    def __lshift__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.LSHIFT(self, rhs)

    def __rlshift__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.LSHIFT(rhs, self)

    def __rshift__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.RSHIFT(self, rhs)

    def __rrshift__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.RSHIFT(rhs, self)

    def __and__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.AND(self, rhs)

    def __rand__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.AND(rhs, self)

    def __xor__(self, rhs: Any) -> "Query":
        # return TwoSidedOperator.XOR(self, rhs)
        raise InvalidQueryUsageError(
            "The boolean xor operator does not exist in python, therefore ^ is not "
            "implemented to keep consistency with & and | semantics (boolean and/or). "
            "Please use `ql.binxor` for the bitwise xor, or explicitly use "
            "`(a & ~b) | (b & ~a)` for the boolean xor."
        )

    def __rxor__(self, rhs: Any) -> "Query":
        # return TwoSidedOperator.XOR(rhs, self)
        raise InvalidQueryUsageError(
            "The boolean xor operator does not exist in python, therefore ^ is not "
            "implemented to keep consistency with & and | semantics (boolean and/or). "
            "Please use `ql.binxor` for the bitwise xor, or explicitly use "
            "`(a & ~b) | (b & ~a)` for the boolean xor."
        )

    def __or__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.OR(self, rhs)

    def __ror__(self, rhs: Any) -> "Query":
        return TwoSidedOperator.OR(rhs, self)

    # one-sided operators

    def __neg__(self) -> "Query":
        return OneSidedOperator.NEG(self)

    def __pos__(self) -> "Query":
        return OneSidedOperator.POS(self)

    def __invert__(self):
        return OneSidedOperator.NOT(self)


class OneSidedOperator(Enum):
    """An operator that only acts on a single operand (the `target`)"""

    NEG = "-"
    POS = "+"
    NOT = "~"

    def __call__(self, target) -> "OneSidedOperation":
        """Factory for the corresponding Query"""
        return OneSidedOperation(operator=self, target=target)


class OneSidedOperation(Query):
    """A query involving a `OneSidedOperator`."""

    __slots__ = ("operator", "target")

    def __init__(self, operator: OneSidedOperator, target: Union[Query, Any]):
        self.operator = operator
        self.target = target

    def __str__(self):
        """Return e.g. '<foo> == "bar"'"""
        return f"{self.operator.value} {maybe_parenthesis(self.target)}"

    def __repr__(self):
        return f"{self.operator!r}({self.target!r})"


class TwoSidedOperator(Enum):
    """An operator that acts on two operands (left and right-hand side)"""

    LT = "<"
    LE = "<="
    EQ = "=="
    NE = "!="
    GT = ">"
    GE = ">="
    ADD = "+"
    SUB = "-"
    MUL = "*"
    MATMUL = "@"
    TRUEDIV = "/"
    FLOORDIV = "//"
    MOD = "%"
    POW = "**"
    LSHIFT = "<<"
    RSHIFT = ">>"
    AND = "and"
    OR = "or"

    def __call__(self, left_hand_side, right_hand_side) -> "TwoSidedOperation":
        """Factory for the corresponding Query"""
        return TwoSidedOperation(operator=self, left_hand_side=left_hand_side, right_hand_side=right_hand_side)


class TwoSidedOperation(Query):
    """A query involving a `TwoSidedOperator`."""

    __slots__ = ("operator", "left_hand_side", "right_hand_side")

    def __init__(
        self, operator: TwoSidedOperator, left_hand_side: Union[Query, Any], right_hand_side: Union[Query, Any]
    ):
        self.operator = operator
        self.left_hand_side = left_hand_side
        self.right_hand_side = right_hand_side

    def __str__(self):
        """Return e.g. '<foo> == "bar"'"""
        return (
            f"{maybe_parenthesis(self.left_hand_side)} {self.operator.value} {maybe_parenthesis(self.right_hand_side)}"
        )

    def __repr__(self):
        return f"{self.operator!r}({self.left_hand_side!r}, {self.right_hand_side!r})"


def maybe_parenthesis(q: Any) -> str:
    """Used in string representations for operators, to add parenthesis if needed."""

    if isinstance(q, (OneSidedOperation, TwoSidedOperation)):
        return f"({q})"
    elif isinstance(q, Query):
        return str(q)
    else:
        return repr(q)


Q = TypeVar("Q", bound="DocElementAccessor")


class DocElementAccessor:
    """
    Describes an element in a document, at a given path.
    It can be "executed" on a document with :func:`_resolve_element`.

    The attribute and dict-element accessors return new instances of :class:`DocElementAccessor`.
    """

    __slots__ = ("_path",)
    _path: Tuple[str, ...]

    def __init__(self):
        self._path = ()

    # def __hash__(self):
    #     return hash((type(self),) + self._path)

    def __getattr__(self: Q, item: str) -> Q:
        """Subtarget accessor: Return a new `DocElementAccessor` whose path is `self._path + (item,)`"""
        query = type(self)()
        query._path = self._path + (item,)
        return query

    # this dual expression is a bad idea: we cant disambiguate the user intent when the actual target is e.g. list/dict.
    # Rather create a proper KnownFunction.
    # def __getitem__(self, item: str):
    #     """Alternate syntax for Subtarget accessor, same as `__getattr__`"""
    #
    #     if isinstance(item, str):
    #         return self.__getattr__(item)
    #     else:
    #         return super()


def resolve_element(qt: DocElementAccessor, meta: Metadata) -> Union[Metadata, NestedPrimitive]:
    """Find and return this query target in the given document, or raise `MissingQueryTargetError` if not found.

    This function is provided as a debug/convenience method only. :class:`StorageProvider` implementors may wish
    to implement the query mechanism differently, integrating more closely with e.g. a backend database query
    language.

    Parameters
    ----------
    qt : DocElementAccessor
        The query target.
    meta : Metadata
        The document on which to find this query target.

    Returns
    -------
    result :
        The value of the query target in the ``meta`` document.

    Raises
    ------
    MissingQueryTargetError
        When this query target can not be found on the given document.
    """
    res = meta
    for i, p in enumerate(qt._path):
        try:
            res = res[p]  # type: ignore
        except (KeyError, TypeError):
            raise MissingQueryTargetError(qt._path[0 : (i + 1)])
    return res


class DocElementQuery(DocElementAccessor, Query):
    """A query using a :class:`DocElementAccessor` for the evaluation."""

    def __str__(self):
        return ".".join(("<metadata_root>",) + self._path)

    def __repr__(self):
        return f"{type(self).__name__}(_path={str(self)})"


class _Missing:
    """The 'missing' singleton, used when a query refers to a missing element."""

    __slots__ = ()

    def __lt__(self, other):
        # Always appear smallest in comparisons for sorting, except with self
        return other is not MISSING

    def __gt__(self, other):
        return False

    def __bool__(self):
        return False

    def __repr__(self):
        return "se_model_manager.MISSING"


MISSING = _Missing()


class _NegatedMissing:
    """The 'negated missing' singleton, used when a negated query refers to a missing element."""

    __slots__ = ()

    def __lt__(self, other):
        # Always appear smallest in comparisons, except compared with MISSING or self
        return other is not MISSING and other is not NEGATED_MISSING

    def __gt__(self, other):
        return other is MISSING

    def __bool__(self):
        return True

    def __repr__(self):
        return "se_model_manager.NEGATED_MISSING"


NEGATED_MISSING = _NegatedMissing()


class KnownFunction(Enum):
    """
    A known function in the query language (=everything else except :class:`OneSidedOperator`
    and :class:`TwoSidedOperator`).
    """

    EXISTS = "EXISTS"
    IS_NONE = "IS_NONE"
    BINNOT = "BINNOT"
    BINAND = "BINAND"
    BINOR = "BINOR"
    BINXOR = "BINXOR"
    MATCHES = "MATCHES"
    ANY = "ANY"
    ALL = "ALL"
    IS_IN = "IS_IN"


class FunctionQuery(Query):
    """
    Represents a query using a known function in the :class:`KnownFunction` enum.
    """

    __slots__ = ("function", "args")

    def __init__(self, function: KnownFunction, args: Tuple = ()):
        self.function = function
        self.args = args

    def __str__(self):
        args_and_kwargs = ", ".join((str(a) for a in self.args))
        # if self.kwargs:
        #     args_and_kwargs += ", ".join(f"{k}={v}" for k, v in self.kwargs.items())
        return f"{self.function.value}({args_and_kwargs})"

    def __repr__(self):
        return f"{type(self).__name__}(function={self.function}, args={self.args})"  # , kwargs={self.kwargs})"


def query_base(path: Optional[str] = None) -> DocElementQuery:
    """Utility function to create a query on a document.

    By default this query refers to the root of the document, that is, the whole document.
    An optional ``path`` can be provided to directly position the query to a specific element in the document.
    Note that ``query_base("foo.bar")`` is strictly equivalent to ``query_base().foo.bar`` or
    ``query_base()["foo"]["bar"]``.

    Parameters
    ----------
    path : Optional[str], default: None
        An optional element path, relative to the document root.

    Returns
    -------
    query : DocElementQuery
        A query object
    """
    res = DocElementQuery()
    if path is not None:
        for item in path.split("."):
            res = res[item]
    return res


def is_same_query(q1: Query, q2: Query):
    """Return True if the two queries are the same (note that using the equality operator would create a new query)."""
    return hash_query(q1) == hash_query(q2)


def hash_query(q: Any) -> int:
    """Equivalent of hash(q)."""
    if isinstance(q, OneSidedOperation):
        return hash((type(q), hash_query(q.operator), hash_query(q.target)))
    elif isinstance(q, TwoSidedOperation):
        return hash((type(q), hash_query(q.operator), hash_query(q.left_hand_side), hash_query(q.right_hand_side)))
    elif isinstance(q, DocElementQuery):
        return hash((type(q), q._path))
    elif not isinstance(q, Query):
        return hash(q)
    else:
        raise NotImplementedError(type(q))


class SortingQuery:
    """
    A query + a sorting order (ascending or descending)
    """

    __slots__ = ("query", "is_ascending")

    def __init__(self, query: Query, is_ascending: bool):
        self.query = query
        self.is_ascending = is_ascending

    @property
    def is_descending(self):
        return not self.is_ascending


def Asc(q: Query):
    """Declare that sorting should be done in ascending order with respect to the outcome of query `q`."""
    return SortingQuery(query=q, is_ascending=True)


def Desc(q: Query):
    """Declare that sorting should be done in descending order with respect to the outcome of query `q`."""
    return SortingQuery(query=q, is_ascending=False)
