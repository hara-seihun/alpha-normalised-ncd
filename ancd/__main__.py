"""Command-line scanner for review candidates in Python files."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys
import zlib

from . import UnsupportedSyntax, _normalize_function, _size, ncd, normalize


def _files(paths: list[str]) -> tuple[list[Path], list[dict[str, str]]]:
    files: set[Path] = set()
    errors: list[dict[str, str]] = []
    for item in paths:
        path = Path(item).resolve()
        if path.is_file() and path.suffix == ".py":
            files.add(path)
        elif path.is_dir():
            files.update(p.resolve() for p in path.rglob("*.py") if p.is_file())
        else:
            errors.append({"path": str(path), "error": "not a Python file or directory"})
    return sorted(files), errors


def _declarations(body: list[ast.stmt], prefix: str = ""):
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield prefix + node.name, node
        elif isinstance(node, ast.ClassDef):
            yield from _declarations(node.body, prefix + node.name + ".")


def _shingles(data: bytes, width: int = 8) -> set[bytes]:
    return {data[i:i + width] for i in range(max(1, len(data) - width + 1))}


def _jaccard(left: set[bytes], right: set[bytes]) -> float:
    return len(left & right) / len(left | right) if left or right else 1.0


def _policy() -> dict:
    return {"normalization": "python-ast-scoped-v1", "python": sys.version.split()[0],
            "compressor": {"name": "zlib", "level": 9, "wbits": 15,
                           "build_version": zlib.ZLIB_VERSION,
                           "runtime_version": zlib.ZLIB_RUNTIME_VERSION},
            "concatenation": "min(C(x+y), C(y+x))", "score": "raw_unclipped_ncd"}


def scan(paths: list[str], min_shingle_jaccard: float = 0.0) -> dict:
    """Scan top-level functions and class methods; skipped units remain visible."""
    files, errors = _files(paths)
    units: list[dict] = []
    skipped: list[dict] = []
    encoded: list[bytes] = []
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path), type_comments=True)
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append({"path": str(path), "error": str(exc)})
            continue
        for name, node in _declarations(tree.body):
            location = {"path": str(path), "name": name, "line": node.lineno,
                        "end_line": node.end_lineno}
            if isinstance(node, ast.AsyncFunctionDef):
                skipped.append({**location, "reason": "AsyncFunctionDef is unsupported"})
                continue
            try:
                data = _normalize_function(node)
            except UnsupportedSyntax as exc:
                skipped.append({**location, "reason": str(exc)})
                continue
            units.append({**location, "normalized_bytes": len(data), "compressed_bytes": _size(data)})
            encoded.append(data)

    pairs: list[dict] = []
    filtered = 0
    shingles = [_shingles(data) for data in encoded] if min_shingle_jaccard > 0 else []
    for i in range(len(units)):
        for j in range(i + 1, len(units)):
            if shingles and _jaccard(shingles[i], shingles[j]) < min_shingle_jaccard:
                filtered += 1
                continue
            pairs.append({"left": units[i], "right": units[j], "ncd": ncd(encoded[i], encoded[j])})
    pairs.sort(key=lambda pair: (pair["ncd"], pair["left"]["path"],
                                 pair["left"]["line"], pair["right"]["path"],
                                 pair["right"]["line"]))
    return {"policy": _policy(), "units": units, "pairs": pairs, "skipped": skipped, "errors": errors,
            "total_pairs": len(units) * (len(units) - 1) // 2,
            "filtered_pairs": filtered, "min_shingle_jaccard": min_shingle_jaccard}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ancd", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scan_parser = commands.add_parser("scan", help="rank all supported function pairs in Python files/directories")
    scan_parser.add_argument("paths", metavar="PATH", nargs="+")
    scan_parser.add_argument("--min-shingle-jaccard", type=float, default=0.0,
                             help="opt-in byte 8-gram Jaccard prefilter (may omit low-NCD pairs)")
    scan_parser.add_argument("--json", action="store_true")
    compare_parser = commands.add_parser("compare", help="compare two single-function declaration files")
    compare_parser.add_argument("left", metavar="FILE")
    compare_parser.add_argument("right", metavar="FILE")
    compare_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "scan":
        if not 0 <= args.min_shingle_jaccard <= 1:
            parser.error("--min-shingle-jaccard must be between 0 and 1")
        result = scan(args.paths, args.min_shingle_jaccard)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            for pair in result["pairs"]:
                left, right = pair["left"], pair["right"]
                print(f'{pair["ncd"]:.4f} {left["path"]}:{left["line"]} {right["path"]}:{right["line"]}')
            print(f'{len(result["units"])} units; {len(result["skipped"])} skipped; '
                  f'{result["filtered_pairs"]} pairs filtered; {len(result["errors"])} errors', file=sys.stderr)
            for skipped in result["skipped"]:
                print(f'{skipped["path"]}:{skipped["line"]} {skipped["name"]}: '
                      f'skipped: {skipped["reason"]}', file=sys.stderr)
            for error in result["errors"]:
                print(f'{error["path"]}: {error["error"]}', file=sys.stderr)
        return 1 if result["errors"] else 0

    try:
        left = normalize(Path(args.left).read_text(encoding="utf-8"))
        right = normalize(Path(args.right).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError, UnsupportedSyntax) as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}))
        else:
            print(str(exc), file=sys.stderr)
        return 1
    result = {"policy": _policy(),
              "left": {"path": str(Path(args.left).resolve()), "normalized_bytes": len(left),
                       "compressed_bytes": _size(left)},
              "right": {"path": str(Path(args.right).resolve()), "normalized_bytes": len(right),
                        "compressed_bytes": _size(right)}, "ncd": ncd(left, right)}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f'{result["ncd"]:.4f} {args.left} {args.right}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
