# Alpha-normalised NCD

## Shared structure for refactoring. Independent evidence for tests.

**Hara Renia Seihun · Research note and executable reference implementation · 24 September 2026**

[Read the paper](paper/paper.md) · [Download the PDF](paper/paper.pdf) · [Reproduced results](results/summary.md) · [References](paper/references.md)

Alpha-normalisation removes arbitrary local naming differences. **Normalized Compression Distance (NCD)** then estimates how much structural information two units share.

- **Refactoring:** two implementations may encode one mechanism under different names. Give that mechanism one owner, while keeping real policy differences explicit.
- **Testing:** a test may encode the implementation a second time. Look for an independent contract, boundary, result, relation or effect that can expose a shared mistake.

> Good tests bring surprising information with respect to what they test—not surprising syntax, but an independent behavioural constraint.

A copied oracle can share the implementation's bug. A short contract-derived assertion can expose it. The score is a way to find things worth examining, not a substitute for deciding what behaviour is correct.

## A concrete testing example

Contract: for nonnegative integer weights, shipping costs 5 through weight 10, and 8 above it.

```python
# Faulty implementation
return 8 if weight >= 10 else 5

# Mirrored expected-value rule: agrees with the same bug
expected = 8 if weight >= 10 else 5

# Independent boundary constraint: rejects that bug
assert shipping_fee(10) == 5
```

Normalising the local names makes a mirrored oracle easier to recognise. The boundary assertion earns its place by distinguishing the faulty implementation, not by maximising textual distance. The examples also show a constant function passing an unanchored metamorphic property, and a success-only effect test missing cleanup on failure.

## Run it

Python 3.10 or later; the analyser and examples use only the standard library. No installation is needed from a checkout:

```sh
git clone https://github.com/hara-seihun/alpha-normalised-ncd.git
cd alpha-normalised-ncd
python3 -m examples.run --output-dir results
python3 -m unittest discover -s tests -v
python3 -m ancd scan examples/refactoring.py --json
```

`results/results.json` contains the measurements and explicit fault-detection denominators. `results/summary.md` is generated from it in the same run. These are constructed, auditable demonstrations—not a production benchmark.

### Compare your own code

```sh
# Recursively scan Python files, rank supported declaration pairs:
python3 -m ancd scan path/to/package --json

# Optional byte 8-gram Jaccard retrieval filter; can miss relevant pairs:
python3 -m ancd scan path/to/package --min-shingle-jaccard 0.4 --json

# Each input file contains exactly one function declaration:
python3 -m ancd compare first_function.py second_function.py --json
```

Without the opt-in filter, scan scores every pair of supported units: quadratic work and output. Start with a focused directory. The scanner recursively includes **all** `.py` files under supplied directories, including tests and generated files; select your scope rather than assuming automatic exclusions. It extracts top-level functions and class methods, not declarations hidden inside module-level control flow.

JSON reports ranked pairs, path/name/line locations, normalised and compressed byte sizes, unsupported declarations, file errors and runtime/compressor metadata. Text output reports skipped declarations and reasons on stderr. File errors return nonzero; unsupported declarations are reported skips, so inspect `skipped` before interpreting scan coverage. The CLI does not infer which function a test exercises or automatically isolate its oracle. Select those comparable mechanisms explicitly.

Python API:

```python
from ancd import normalize, ncd

left = normalize("def first(items):\n    return len(items)\n")
right = normalize("def second(values):\n    return len(values)\n")
assert left == right
print(ncd(left, right))  # finite-compressor self-distance is not necessarily 0
```

## What is measured?

The conventional definition is:

$$\operatorname{NCD}(x,y) = \frac{C(xy)-\min(C(x),C(y))}{\max(C(x),C(y))}.$$

Here `x` and `y` are normalised serialisations. This implementation uses **`min(C(x+y), C(y+x))`** for a symmetric concatenation score. `C` is the byte length of `zlib.compress(data, level=9)` with the default zlib wrapper and 32 KiB window (`wbits=15`). There is no delimiter between the self-delimiting JSON representations, no header subtraction and no score clipping. Python and zlib versions are recorded. Compressor overhead, window size, boilerplate and unequal source lengths affect scores; there is no universal cutoff.

### Conservative, explicitly scoped normalisation

`ancd.normalize` parses one synchronous function and serialises its AST as compact ASCII JSON:

- Parameters and simple local assignment/loop targets receive ordered, function-wide binding slots; repeated references retain their identity.
- The declaration name is omitted; a direct reference to it is represented as a self slot unless shadowed by a local binding.
- Free names, attribute names, keyword labels, literals, operators and control structure are retained.
- Decorators and annotations retain outer-name spellings. Comments and formatting disappear. **Docstrings remain string constants**, so use consistent documentation when comparing structural units.
- The supported subset includes ordinary expressions, branches, simple loops and `try/finally`.
- Nested functions, lambdas, comprehensions, defaults, imports, `global`/`nonlocal`, destructuring, `with`, exception handlers, async constructs, type comments and type parameters are explicitly unsupported.

This is a deliberately small single-function scope model, not a production Python semantic analyser. Python can observe names through keyword calls and reflection, and free names may resolve differently at runtime. Consistent renaming in this representation therefore does not establish semantic equivalence. The general method can use language-specific front ends; this repository implements Python only. It does **not** erase literals or API identities in an aggressive shape mode.

## Examples and their contracts

| Example | Structural question | Independent evidence |
|---|---|---|
| Invoice totals / shipment weights | Repeated aggregation and validation mechanism | Exact totals, missing-count handling and distinct validation messages |
| Invoice / label rendering | Repeated acquire–use–release protocol | Return values, effect order and cleanup on body failure |
| Shipping fee | Does an expected-value rule repeat the same boundary mistake? | Contract values at 0, 10 and 11 |
| String canonicalisation | Is idempotence sufficient? | An independently specified nonempty anchor rejects the constant function |
| Publishing through a resource | Does success-only testing miss an exceptional path? | Close exactly once and preserve the original exception on failure |

The test-design examples also compare irrelevant novelty and a useful, structurally similar oracle. See the generated results for the actual scores and verdicts. Mutation matrices name their injected faults; killing this finite set is not a general correctness proof.

A practical sequence is **retrieve → inspect contracts/provenance → refactor or strengthen an oracle → exercise independent constraints**. Do not automatically delete a test because it resembles the implementation, or prefer one because it is textually exotic.

## Paper and reproduction

The paper sources are [`paper/paper.md`](paper/paper.md) and [`paper/references.md`](paper/references.md). The PDF also includes the generated demonstration results. Building it requires **Pandoc, XeLaTeX and the DejaVu Sans Mono font**:

```sh
make reproduce    # regenerate examples, run the small suite, build PDF
# Or, with existing results:
make paper
```

The PDF is committed and attached to the [versioned GitHub release](https://github.com/hara-seihun/alpha-normalised-ncd/releases), so reading it requires no TeX installation. Reproduction targets identical measurements under the recorded runtime; PDF metadata can differ between builds.

### Research scope

NCD, identifier-normalised clone detection and compression-based test diversity are established techniques. In particular, prior work applies NCD to both buggy-clone retrieval and test-suite selection. This note proposes a **joint engineering attention workflow**, with independently sourced behavioural evidence as the bridge between refactoring and test design. It does not claim those ingredients were invented here. See the [bibliography](paper/references.md) for the direct prior art and the paper for an evaluation agenda.

## Ownership, citation and publication

Maintained by Hara Renia Seihun. This repository owns the paper, reference analyser, fixtures and checked-in results; it needs no service, credentials or external dataset to run. `CITATION.cff` supplies citation metadata. Code, paper and examples are available under the [MIT licence](LICENSE). AI assistance was used for drafting and implementation.

To publish an update: run `make reproduce`, review the generated changes, commit the source/results/PDF together, publish the current commit with `git push origin HEAD:main`, and create a versioned GitHub release attaching `paper/paper.pdf` with `--target "$(git rev-parse HEAD)"`. An agent workspace may use its own branch, so `git push origin main` would publish the wrong local ref. Git history and GitHub releases are the recovery source; local Python caches are disposable.
