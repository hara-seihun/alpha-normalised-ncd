"""Scoped Python function normalisation and raw compression-distance scoring.

This is a structural attention signal, not a semantic-equivalence test. The
normaliser deliberately refuses binding forms whose scope is not modelled.
"""

from __future__ import annotations

import ast
import json
import zlib

__all__ = ["UnsupportedSyntax", "normalize", "ncd"]


class UnsupportedSyntax(ValueError):
    """The input is not a function in the supported single-scope subset."""


_STATEMENTS = (
    ast.Return, ast.Assign, ast.AugAssign, ast.Expr, ast.If, ast.For,
    ast.While, ast.Break, ast.Continue, ast.Pass, ast.Raise, ast.Assert, ast.Try,
)
_EXPRESSIONS = (
    ast.Name, ast.Constant, ast.Attribute, ast.Subscript, ast.Slice,
    ast.Call, ast.keyword, ast.BinOp, ast.UnaryOp, ast.BoolOp,
    ast.Compare, ast.IfExp, ast.List, ast.Tuple, ast.Set, ast.Dict,
    ast.Starred, ast.JoinedStr, ast.FormattedValue,
)


def _check_function(node: ast.FunctionDef) -> None:
    if node.type_comment:
        raise UnsupportedSyntax("type comments are unsupported")
    if getattr(node, "type_params", ()):
        raise UnsupportedSyntax("type parameters are unsupported")
    args = node.args
    if args.defaults or any(default is not None for default in args.kw_defaults):
        raise UnsupportedSyntax("parameter defaults are unsupported")
    for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg):
        if arg is not None and arg.type_comment:
            raise UnsupportedSyntax("type comments are unsupported")

    annotations = [arg.annotation for arg in (*args.posonlyargs, *args.args,
                    *args.kwonlyargs, args.vararg, args.kwarg) if arg is not None]
    for statement in [*node.decorator_list, node.returns, *annotations, *node.body]:
        if statement is None:
            continue
        for part in ast.walk(statement):
            if isinstance(part, (ast.operator, ast.unaryop, ast.boolop,
                                 ast.cmpop, ast.expr_context)):
                continue
            if not isinstance(part, _STATEMENTS + _EXPRESSIONS):
                raise UnsupportedSyntax(f"{type(part).__name__} is unsupported")
            if isinstance(part, ast.Try) and (part.handlers or part.orelse):
                raise UnsupportedSyntax("except handlers and try-else are unsupported")
            if isinstance(part, (ast.Assign, ast.For)) and part.type_comment:
                raise UnsupportedSyntax("type comments are unsupported")
            if isinstance(part, ast.Assign) and (
                not part.targets or not all(isinstance(t, ast.Name) for t in part.targets)
            ):
                raise UnsupportedSyntax("only simple name assignment targets are supported")
            if isinstance(part, (ast.For, ast.AugAssign)) and not isinstance(part.target, ast.Name):
                raise UnsupportedSyntax("only simple name assignment targets are supported")
            if isinstance(part, (ast.Name, ast.Attribute, ast.Subscript, ast.List,
                                 ast.Tuple, ast.Starred)) and not isinstance(part.ctx, ast.Load):
                if not isinstance(part, ast.Name) or not isinstance(part.ctx, ast.Store):
                    raise UnsupportedSyntax("deletion and complex assignment targets are unsupported")


def _normalize_function(node: ast.FunctionDef) -> bytes:
    _check_function(node)
    locals_: dict[str, int] = {}

    def bind(name: str) -> None:
        if name not in locals_:
            locals_[name] = len(locals_)

    args = node.args
    for arg in (*args.posonlyargs, *args.args):
        bind(arg.arg)
    if args.vararg:
        bind(args.vararg.arg)
    for arg in args.kwonlyargs:
        bind(arg.arg)
    if args.kwarg:
        bind(args.kwarg.arg)
    for statement in node.body:
        for part in ast.walk(statement):
            if isinstance(part, ast.Assign):
                for target in part.targets:
                    bind(target.id)
            elif isinstance(part, (ast.For, ast.AugAssign)):
                bind(part.target.id)

    def encode(value: object, outer: bool = False) -> object:
        if isinstance(value, ast.Name):
            symbol = (["free", value.id] if outer else
                      ["local", locals_[value.id]] if value.id in locals_ else
                      ["self"] if value.id == node.name else ["free", value.id])
            return ["Name", symbol, type(value.ctx).__name__]
        if isinstance(value, ast.arg):
            return ["arg", locals_[value.arg], encode(value.annotation, outer=True)]
        if isinstance(value, ast.Constant):
            return ["Constant", type(value.value).__name__, repr(value.value)]
        if isinstance(value, ast.AST):
            return [type(value).__name__, *(
                [key, encode(item, outer)] for key, item in ast.iter_fields(value)
                if key not in ("type_comment", "type_params")
            )]
        if isinstance(value, list):
            return [encode(item, outer) for item in value]
        return value

    payload = ["Function", encode(node.args), encode(node.returns, outer=True),
               encode(node.decorator_list, outer=True), encode(node.body)]
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def normalize(source: str) -> bytes:
    """Normalise one synchronous function declaration (no module siblings).

    Parameters and simple assignment/loop targets use scope-wide local slots;
    free names, attribute and keyword names, literal values and operators stay.
    Decorators and annotations retain their outer-scope name spellings.
    Raises SyntaxError for invalid Python and UnsupportedSyntax for excluded forms.
    """
    tree = ast.parse(source, type_comments=True)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise UnsupportedSyntax("expected exactly one synchronous function declaration")
    return _normalize_function(tree.body[0])


def _size(data: bytes) -> int:
    return len(zlib.compress(data, level=9))


def ncd(x: bytes, y: bytes) -> float:
    """Raw symmetric NCD using zlib level 9 and min(C(x+y), C(y+x)).

    No score clipping: compressor overhead can produce scores outside [0, 1].
    This is a finite-window compressor estimate, not Kolmogorov complexity.
    """
    if not isinstance(x, bytes) or not isinstance(y, bytes):
        raise TypeError("ncd expects bytes")
    cx, cy = _size(x), _size(y)
    return (min(_size(x + y), _size(y + x)) - min(cx, cy)) / max(cx, cy)
