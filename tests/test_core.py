import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from ancd import UnsupportedSyntax, ncd, normalize
from ancd.__main__ import main, scan


class NormalizationTests(unittest.TestCase):
    def test_scoped_renaming_and_source_noise(self):
        left = '''def first(a, b):
    result = a + b  # incidental
    return result
'''
        right = '''def second(x, y):
    total=x+y
    return total
'''
        self.assertEqual(normalize(left), normalize(right))

    def test_preserves_structure_and_external_names(self):
        base = normalize("def f(x):\n    return lib.apply(x.value, scale=2)\n")
        for changed in (
            "def f(x):\n    return other.apply(x.value, scale=2)\n",
            "def f(x):\n    return lib.apply(x.other, scale=2)\n",
            "def f(x):\n    return lib.apply(x.value, factor=2)\n",
            "def f(x):\n    return lib.apply(x.value, scale=3)\n",
            "def f(x):\n    return lib.apply(x.value + 1, scale=2)\n",
        ):
            with self.subTest(changed=changed):
                self.assertNotEqual(base, normalize(changed))

    def test_local_vs_free_and_recursive_self(self):
        self.assertNotEqual(normalize("def f(x):\n    return x\n"),
                            normalize("def f(x):\n    return y\n"))
        self.assertEqual(normalize("def f(n):\n    return f(n - 1)\n"),
                         normalize("def g(m):\n    return g(m - 1)\n"))
        self.assertNotEqual(normalize("def f(n):\n    return f(n - 1)\n"),
                            normalize("def f(n):\n    return other(n - 1)\n"))

    def test_annotations_are_outer_scope_and_try_finally_is_supported(self):
        left = "def f(x: T) -> T:\n    try:\n        return x\n    finally:\n        close()\n"
        right = "def g(y: T) -> T:\n    try:\n        return y\n    finally:\n        close()\n"
        self.assertEqual(normalize(left), normalize(right))
        self.assertNotEqual(normalize(left), normalize(right.replace("T", "U")))
        self.assertNotEqual(normalize(left), normalize(right.replace("close()", "finish()")))

    def test_scope_wide_binding_even_before_assignment(self):
        self.assertEqual(normalize("def f():\n    print(x)\n    x = 1\n"),
                         normalize("def g():\n    print(y)\n    y = 1\n"))

    def test_rejects_unmodelled_scopes_and_binding(self):
        for source in (
            "def f(x):\n    return [y for y in x]\n",
            "def f(x):\n    def nested():\n        return x\n    return nested()\n",
            "def f(x):\n    a, b = x\n",
            "def f(x=1):\n    return x\n",
            "def f(x):\n    global y\n    return y\n",
            "def f(x):\n    x = 1 # type: int\n    return x\n",
            "def f(x):\n    try:\n        return x\n    except Exception:\n        return None\n",
            "async def f(x):\n    return x\n",
            "def f(x):\n    return (lambda z: z)(x)\n",
        ):
            with self.subTest(source=source), self.assertRaises(UnsupportedSyntax):
                normalize(source)

    def test_only_one_function_and_syntax_error(self):
        with self.assertRaises(UnsupportedSyntax):
            normalize("def a(): pass\ndef b(): pass\n")
        with self.assertRaises(SyntaxError):
            normalize("def a(: pass")


class ScoringAndCliTests(unittest.TestCase):
    def test_ncd_symmetric_deterministic_and_unclipped(self):
        x, y = normalize("def a(x): return x + 1"), normalize("def b(z): return z * 2")
        self.assertEqual(ncd(x, y), ncd(y, x))
        self.assertEqual(ncd(x, x), ncd(x, x))
        with self.assertRaises(TypeError):
            ncd("source", y)

    def test_scan_locations_sizes_skips_and_json_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.py").write_text("def a(x):\n    return x + 1\n\nclass C:\n    def method(y):\n        return y + 1\n")
            (root / "b.py").write_text("async def async_unit(x):\n    return x\n")
            result = scan([directory])
            self.assertEqual(len(result["units"]), 2)
            self.assertEqual(result["units"][1]["name"], "C.method")
            self.assertEqual(result["units"][1]["line"], 5)
            self.assertGreater(result["units"][0]["compressed_bytes"], 0)
            self.assertEqual(result["total_pairs"], 1)
            self.assertEqual(result["filtered_pairs"], 0)
            self.assertEqual(len(result["pairs"]), 1)
            self.assertEqual(len(result["skipped"]), 1)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["scan", directory, "--json"]), 0)
            self.assertEqual(json.loads(output.getvalue())["pairs"][0]["ncd"], result["pairs"][0]["ncd"])

    def test_compare_json_and_missing_file_error(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "first.py", Path(directory) / "second.py"
            first.write_text("def one(a): return a + 1")
            second.write_text("def two(b): return b + 1")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["compare", str(first), str(second), "--json"]), 0)
            self.assertIn("normalized_bytes", json.loads(output.getvalue())["left"])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", str(first) + "-missing", "--json"]), 1)


if __name__ == "__main__":
    unittest.main()
