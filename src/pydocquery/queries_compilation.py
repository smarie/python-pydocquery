# Authors: Sylvain MARIE <sylvain.marie@se.com>
#          + All contributors to <https://github.com/smarie/python-pydocquery>
#
# License: 3-clause BSD, <https://github.com/smarie/python-pydocquery/blob/master/LICENSE>
import re
from typing import Any, Callable, Union

from .queries import (
    DocElementQuery,
    FunctionQuery,
    KnownFunction,
    Metadata,
    MissingQueryTargetError,
    OneSidedOperation,
    OneSidedOperator,
    Query,
    SortingQuery,
    TwoSidedOperation,
    TwoSidedOperator,
    resolve_element,
)


def evaluate_query(q: Query, metadata: Metadata) -> Any:
    """Evaluate a query on the given document.

    This is equivalent to ``compile_query(q)(metadata)``. See :func:`compile_query`.

    Parameters
    ----------
    q : Query
        The query to evaluate against the document.

    metadata : Metadata
        The document to evaluate the query against.

    Returns
    -------
    result : Any
        The result of the query, or :obj:`MISSING` or :obj:`NEGATED_MISSING`.
    """
    return compile_query(q)(metadata)


def compile_query(q: Union[Query, "SortingQuery"]) -> Callable[[Metadata], Any]:
    """
    Generate a function able to execute the query on a piece of :class:`Metadata`.

    Parameters
    ----------
    q : Query
        The query to compile into a callable.

    Returns
    -------
    evaluation_func : Callable[[Metadata], Any]
        A function that takes a metadata document as input, and returns the result of the query.
    """
    # accept top-level sorting queries
    if isinstance(q, SortingQuery):
        q = q.query
    return _compile(q, enforce_type=True, catch_missing_exc=True)


def _compile(
    q: Union[Query, Any], enforce_type: bool = False, catch_missing_exc: bool = False
) -> Callable[[Metadata], Any]:
    """Transform a query into a callable."""

    if not isinstance(q, Query):
        if enforce_type:
            raise TypeError(q)
        else:
            # Return a "constant" function returning the object
            # TODO should we return a copy to ensure non-mutability ?
            def _eval(meta: Metadata) -> Any:
                return q

    elif catch_missing_exc:
        # Compile a non-catching version
        _non_catching_eval = _compile(q, enforce_type=enforce_type, catch_missing_exc=False)

        # Create a catching wrapper
        def _eval(meta: Metadata) -> Any:
            try:
                return _non_catching_eval(meta)
            except MissingQueryTargetError as e:
                return e.to_object()

    elif isinstance(q, OneSidedOperation):
        _eval = compile_one_sided_operator(q.operator, q.target)  # type: ignore

    elif isinstance(q, TwoSidedOperation):
        _eval = compile_two_sided_operator(q.operator, q.left_hand_side, q.right_hand_side)  # type: ignore

    elif isinstance(q, FunctionQuery):
        _eval = compile_known_function(q.function, q.args)  # type: ignore

    elif isinstance(q, DocElementQuery):
        # Simply return the referenced element from the doc
        def _eval(meta: Metadata) -> Any:
            return resolve_element(q, meta)  # type: ignore

    else:
        raise NotImplementedError(type(q))

    return _eval


def compile_one_sided_operator(op: OneSidedOperator, target: Any) -> Callable[[Metadata], Any]:
    """Compile a one-sided operator such as POS (+), NEG (-), NOT (~)."""

    # compile target
    target = _compile(target)

    # create the wrapping callable
    def _eval(meta: Metadata) -> Any:
        if op is OneSidedOperator.NEG:
            return -target(meta)
        elif op is OneSidedOperator.POS:
            return +target(meta)
        elif op is OneSidedOperator.NOT:
            try:
                res = target(meta)
            except MissingQueryTargetError as e:
                # Switch the truth value of the error
                e.negate()
                raise e
            else:
                # Important: since and/not/or can not be overridden, we use the bitwise operators &/~/| to perform the
                # *boolean* logic. So implementation of & is 'and', implementation of | is 'or', and implementation of
                # ~ is 'not'. Users really wishing to access bitwise operations should use ql.bin[and/not/or/xor].
                return not res
        else:
            raise NotImplementedError()

    return _eval


def compile_two_sided_operator(op: TwoSidedOperator, lhs: Any, rhs: Any) -> Callable[[Metadata], Any]:
    """Compile a one-sided operator such as POS (+), NEG (-), NOT (~)."""

    # compile each side
    left = _compile(lhs)
    right = _compile(rhs)

    # create the wrapping callable
    def _eval(meta: Metadata) -> Any:
        # Note: execute left(meta) and right(meta) in line so that the operation is lazy when possible
        if op is TwoSidedOperator.LT:
            return left(meta) < right(meta)
        elif op is TwoSidedOperator.LE:
            return left(meta) <= right(meta)
        elif op is TwoSidedOperator.EQ:
            return left(meta) == right(meta)
        elif op is TwoSidedOperator.NE:
            return left(meta) != right(meta)
        elif op is TwoSidedOperator.GT:
            return left(meta) > right(meta)
        elif op is TwoSidedOperator.GE:
            return left(meta) >= right(meta)
        elif op is TwoSidedOperator.ADD:
            return left(meta) + right(meta)
        elif op is TwoSidedOperator.SUB:
            return left(meta) - right(meta)
        elif op is TwoSidedOperator.MUL:
            return left(meta) * right(meta)
        elif op is TwoSidedOperator.MATMUL:
            return left(meta) @ right(meta)
        elif op is TwoSidedOperator.TRUEDIV:
            return left(meta) / right(meta)
        elif op is TwoSidedOperator.FLOORDIV:
            return left(meta) // right(meta)
        elif op is TwoSidedOperator.MOD:
            return left(meta) % right(meta)
        elif op is TwoSidedOperator.POW:
            return left(meta) ** right(meta)
        elif op is TwoSidedOperator.LSHIFT:
            return left(meta) << right(meta)
        elif op is TwoSidedOperator.RSHIFT:
            return left(meta) >> right(meta)
        elif op is TwoSidedOperator.AND:
            # Important: since and/not/or can not be overridden, we use the bitwise operators &/~/| to perform the
            # *boolean* logic. So implementation of & is 'and', implementation of | is 'or', and implementation of
            # ~ is 'not'. Users really wishing to access bitwise operations should use ql.bin[and/not/or/xor].

            # Note: the result may not be a boolean. See https://stackoverflow.com/a/68896273/7262247
            try:
                res = left(meta)
                if not res:
                    return res  # same behaviour as python: return the non-truthy object
            except MissingQueryTargetError as e:
                if not e:
                    # only raise if the error is not negated, otherwise proceed
                    raise

            return right(meta)

        elif op is TwoSidedOperator.OR:
            # Important: since and/not/or can not be overridden, we use the bitwise operators &/~/| to perform the
            # *boolean* logic. So implementation of & is 'and', implementation of | is 'or', and implementation of
            # ~ is 'not'. Users really wishing to access bitwise operations should use ql.bin[and/not/or/xor].

            # Special handling of missing here: accept that one side is missing
            try:
                # Is the left side here ? Evaluate
                left_res = left(meta)
            except MissingQueryTargetError as e:
                # Left side is missing, use the error truth value and evaluate the right side alone
                # Note: the result may not be a boolean. See https://stackoverflow.com/a/68896273/7262247
                if e:
                    # the error is negated, this is equivalent to true: raise
                    raise
                return bool(e) or right(meta)
            else:
                # Left side is here, catch any missing on the right side
                # Note: the result may not be a boolean. See https://stackoverflow.com/a/68896273/7262247
                return left_res or right(meta)
        else:
            raise NotImplementedError()

    return _eval


def compile_known_function(kf: KnownFunction, args) -> Callable[[Metadata], Any]:
    """Compile a `KnownFunction`."""

    if kf is KnownFunction.EXISTS:
        target_elt: DocElementQuery = args[0]

        # Compile the query (do not use the higher-level compile here)
        ctarget = _compile(target_elt)

        def _eval(meta: Metadata) -> Any:
            try:
                ctarget(meta)
                return True
            except MissingQueryTargetError:
                return False

    elif kf is KnownFunction.IS_NONE:
        target_elt: DocElementQuery = args[0]  # type: ignore

        # Compile the query (do not use the higher-level compile here)
        ctarget = _compile(target_elt)

        def _eval(meta: Metadata) -> Any:
            return ctarget(meta) is None

    elif kf is KnownFunction.BINNOT:
        target_elt: Query = args[0]  # type: ignore

        # Compile the query (do not use the higher-level compile here)
        ctarget = _compile(target_elt)

        def _eval(meta: Metadata) -> Any:
            return ~ctarget(meta)

    elif kf in (KnownFunction.BINAND, KnownFunction.BINOR, KnownFunction.BINXOR):
        left_elt: Query
        right_elt: Query
        left_elt, right_elt = args  # type: ignore

        # Compile the query (do not use the higher-level compile here)
        cleft = _compile(left_elt)
        cright = _compile(right_elt)

        if kf is KnownFunction.BINAND:

            def _eval(meta: Metadata) -> Any:
                return cleft(meta) & cright(meta)

        elif kf is KnownFunction.BINOR:

            def _eval(meta: Metadata) -> Any:
                return cleft(meta) | cright(meta)

        else:
            # kf is KnownFunction.BINXOR:
            def _eval(meta: Metadata) -> Any:
                return cleft(meta) ^ cright(meta)

    elif kf is KnownFunction.MATCHES:
        target: Query
        regex: str
        flags: int
        target, regex, flags = args

        # Compile the query (do not use the higher-level compile here)
        ctarget = _compile(target)

        # Compile the pattern if needed
        cregex: re.Pattern = re.compile(regex, flags=flags)

        def _eval(meta: Metadata) -> Any:
            res = ctarget(meta)
            try:
                return cregex.search(res) is not None
            except TypeError:
                # The target is not a string-like, no-match
                return False

    elif kf is KnownFunction.IS_IN:
        item, container = args

        # Compile both queries (do not use higher-level compile here)
        c_container = _compile(container)
        c_item = _compile(item)

        def _eval(meta: Metadata) -> Any:
            return c_item(meta) in c_container(meta)

    elif kf is KnownFunction.ANY:
        target = args[0]
        if isinstance(target, Query):
            # A single query returning an iterable. Compile it
            ctarget = _compile(target)

            def _eval(meta: Metadata) -> Any:
                res = ctarget(meta)
                return any(res)

        else:
            # Target is an iterable
            # -- special case of len = 0
            if len(target) == 0:
                # Return directly a function evaluating to False
                return lambda meta: False

            # -- compile each item in the iterable
            cargs = tuple(_compile(a) for a in target)

            # -- special missing handling, to be consistent with | operator
            def _eval(meta: Metadata) -> Any:
                all_missing: bool = True
                # Execute all queries except the last one
                for cf in cargs[:-1]:
                    try:
                        if cf(meta):
                            # Early stopping: we found an actual True
                            return True
                        all_missing = False
                    except MissingQueryTargetError as e:
                        if e:
                            # Early stopping: we found an actual True (a negated missing)
                            return True
                # final item
                try:
                    return bool(cargs[-1](meta))
                except MissingQueryTargetError as e2:
                    if e2:
                        # Return: we found an actual True (a negated missing)
                        return True
                    if all_missing:
                        # All previous queries were missing, this one too: raise the error.
                        raise
                    else:
                        # At least one query was not missing, but none was True. Return False
                        return False

    elif kf is KnownFunction.ALL:
        target = args[0]
        if isinstance(target, Query):
            # A single query returning an iterable. Compile it
            ctarget = _compile(target)

            def _eval(meta: Metadata) -> Any:
                res = ctarget(meta)
                return all(res)

        else:
            # Target is an iterable
            # -- special case of len = 0
            if len(target) == 0:
                # Return directly a function evaluating to False
                return lambda meta: False

            # -- compile each item in the iterable
            cargs = tuple(_compile(a) for a in target)

            # -- special missing handling, to be consistent with & operator
            def _eval(meta: Metadata) -> Any:
                # Similar to "return all(c(meta) for c in cargs)" but with proper handling of missing
                all_negated_missing = True
                for c in cargs[:-1]:
                    try:
                        if not c(meta):
                            # Early stopping: we found an actual False
                            return False
                        all_negated_missing = False
                    except MissingQueryTargetError as e:
                        if not e:
                            # Early stopping: we found an actual False (a missing)
                            raise e

                # final item
                try:
                    return bool(cargs[-1](meta))
                except MissingQueryTargetError as e2:
                    if not e2:
                        # Return: we found an actual False (a missing)
                        raise e2
                    elif all_negated_missing:
                        # All previous queries were negated missing, this one too: raise the error.
                        raise
                    else:
                        # All non-missing previous queries were True, but this one is missing. Return True
                        return True

    else:
        raise NotImplementedError(kf)

    return _eval
