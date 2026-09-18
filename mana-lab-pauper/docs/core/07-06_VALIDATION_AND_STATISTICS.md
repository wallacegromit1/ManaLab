# Validation and Statistics

## Deterministic validation first
Where exact math is available, calculate it independently:
- legal candidate-space size;
- land-count distributions;
- hypergeometric opening-hand quantities;
- simple color-source access;
- impossible/guaranteed payment states.

Simulation must agree within sampling error.

## Unit tests
Every mechanic used by a deck requires tests for:
- mana payment;
- tap/untap state;
- ETB tapped behavior;
- filters/mana conservation;
- search/landcycling;
- cost reductions;
- artifact/threshold counting;
- draw effects;
- bounce/sacrifice/return;
- mulligan/bottoming;
- no-lookahead.

## Monte Carlo
Prefer paired/common-random-number comparisons:
- same random deck permutation concept across candidates where valid;
- documented seeds;
- independent selection vs validation seeds.

Report uncertainty for candidate differences, not just standalone means.

## Screening safety
A staged search is allowed, but:
- never eliminate from extremely tiny noisy screens alone;
- force C0 into every serious validation stage;
- force structurally important boundary classes when practical;
- document shortlist rule and false-elimination risk;
- consider coarse full-space estimates plus protected candidate classes.

## Precision
Increase trials adaptively for close finalists.

Do not call a microscopic difference meaningful because millions of trials make its Monte Carlo SE tiny. Practical/model significance is separate.

## Multiple comparisons
Large candidate searches create winner's-curse risk. Finalists must be evaluated on fresh validation randomness after selection.

## Reproducibility
Record:
- code/version hash;
- config hashes;
- seed(s);
- compiler/interpreter versions;
- command lines;
- trial counts;
- outputs.

A third party should be able to recreate the experiment from the repository.
