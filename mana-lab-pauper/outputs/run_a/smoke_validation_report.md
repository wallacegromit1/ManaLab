# NOT A RANKING / NOT AN OPTIMIZATION

These C0 and historical-C1 runs validate mechanics, policies, common-random-number wiring, and logging only. They must not be used to select a mana base.

Trials: **20,000 per scenario/candidate** across all configured play/draw, mulligan, and sequencing combinations.

## Exact-vs-simulation check (C0 raw opening seven)

| Quantity | Exact | Observed | Predeclared tolerance | Pass |
|---|---:|---:|---:|:---:|
| lands=0 | 0.058212163 | 0.057850000 | 0.006622598 | PASS |
| lands=1 | 0.221206218 | 0.226750000 | 0.011739643 | PASS |
| lands=2 | 0.331809326 | 0.323400000 | 0.013318015 | PASS |
| lands=3 | 0.254088223 | 0.255950000 | 0.012313485 | PASS |
| lands=4 | 0.106984515 | 0.107300000 | 0.008742486 | PASS |
| lands=5 | 0.024688734 | 0.024900000 | 0.005000000 | PASS |
| lands=6 | 0.002880352 | 0.003750000 | 0.005000000 | PASS |
| lands=7 | 0.000130469 | 0.000100000 | 0.005000000 | PASS |
| W direct source | 0.474562173 | 0.474300000 | 0.014123821 | PASS |
| U direct source | 0.600879549 | 0.605200000 | 0.013851305 | PASS |
| B direct source | 0.600879549 | 0.596550000 | 0.013851305 | PASS |
| R direct source | 0.399499626 | 0.401100000 | 0.013853510 | PASS |
| joint U+B direct sources | 0.392405791 | 0.392700000 | 0.013810821 | PASS |

Full event-level sufficient statistics are in `smoke_events.csv.gz`; sampled policy action traces are in `smoke_policy_traces.jsonl`; aggregates are in `smoke_summary.json`.

No cross-candidate winner, shortlist, frontier, or recommendation was computed.
