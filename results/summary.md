# Constructed examples

Measured with CPython 3.13.15, zlib 1.3.2, level 9, wbits=15; symmetric minimum-concatenation NCD, unclipped.

These are illustrative fixtures, not empirical validation of NCD as a quality metric.
Low structural distance is an attention signal; only the explicit behavior contracts justify a refactor or regression test.

## Refactoring contracts

- aggregation values: pass
- aggregation policy errors: pass
- resource values and effects: pass
- resource failure cleanup: pass

## Similarity (zlib level 9)

| Pair | Raw NCD | Alpha-normalized NCD |
| --- | ---: | ---: |
| renamed aggregation | 0.2235 | 0.0993 |
| renamed resource protocol | 0.1780 | 0.0870 |
| boundary regression | 0.2051 | 0.0559 |
| mirrored faulty oracle | 0.2650 | 0.0943 |
| contract derived oracle | 0.4841 | 0.1141 |
| padded comments | 0.9658 | 0.0386 |
| padded oracle comments | 0.9488 | 0.0486 |
| padded oracle computation | 0.6730 | 0.5494 |

The comments pair adds only textual surprise; the padded-oracle pair adds retained but candidate-irrelevant literals and computation, increasing measured structural distance without changing verdicts. The boundary pair changes `>` to `>=`; the independent integer-contract oracle uses `>= 11` and rejects that fault despite structural resemblance.

## Three independent-contract mutation scenarios

| Fault | Test | Baseline | Fault |
| --- | --- | --- | --- |
| boundary greater or equal | independent nonboundary examples | pass | survived |
| boundary greater or equal | independent boundary examples | pass | killed |
| boundary greater or equal | contract derived oracle | pass | killed |
| constant canonicalizer | idempotence | pass | survived |
| constant canonicalizer | anchored example | pass | killed |
| missing failure cleanup | successful effects | pass | survived |
| missing failure cleanup | failure cleanup and exception identity | pass | killed |

### Irrelevant novelty: identical verdicts

| Candidate | Original oracle | Padded oracle |
| --- | --- | --- |
| baseline | pass | pass |
| boundary fault | reject | reject |

3/3 injected faults detected; 4/7 applicable test/fault observations killed.
Outside the independent-contract matrix, an intentionally unsound mirrored oracle and faulty implementation *agree* at weight 10 (both return 8); the external contract says 5.
Idempotence alone admits a constant function; the anchor excludes it. Success-only testing misses cleanup after a failed send.

The test fixtures are intentionally small and selected. Neither these ratios nor NCD scores estimate field defect rates.
