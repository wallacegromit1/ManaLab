# Run G Phase 3 pipeline specification

Run G freezes and tests the decision/execution layer but does not authorize or run optimization. `src/mana_lab/phase3_pipeline.py` is the executable stage graph. Each stage reads the preceding immutable manifest, verifies the frozen config hash, and writes deterministic JSON containing its own content hash and explicit no-ranking/no-recommendation flags.

| Stage | Entry point | Required input | Machine-readable output | Safety condition |
|---|---|---|---|---|
| 01 validate | `stage_01_validate` | frozen config, deck, policies, mechanic and metric registries | `01_validate.json` | all hashes and contracts must match |
| 02 enumerate | `stage_02_enumerate` | validated input | `02_enumerate.json` | deterministic features only; count 296,706; C0 once |
| 03 screen | `stage_03_screen` | enumeration manifest and paired selection evidence | `03_screen.json` | C0/protected class retained; low-N and uncertainty retained; no point-estimate elimination |
| 04 medium | `stage_04_medium` | retained candidates and selection seed | `04_medium.json` | exact pairing keys and frozen trial count |
| 05 select finalists | `stage_05_select_finalists` | medium paired results | `05_select_finalists.json` | union rule; C0 retained; target is not a hard cap |
| 06 fresh validation | `stage_06_fresh_validation` | immutable finalist set | `06_fresh_validation.json` | validation seed differs from and is inaccessible to selection |
| 07 robustness | `stage_07_robustness` | confirmatory results | `07_robustness.json` | only frozen labeled policy/model scenarios |
| 08 frontier | `stage_08_frontier` | validation and robustness evidence | `08_frontier.json` | uncertainty-aware direction/tolerance relation; unresolved stays on frontier |
| 09 report | `stage_09_report` | complete manifests | `09_report.json` | raw metrics precede profiles; no match-win inference |

The Run G dry run uses synthetic candidates only. It exercises protected retention, insufficient-evidence retention, unresolved retention, decisive dominance, the seed transition, robustness enumeration, frontier semantics and output provenance. The production configuration remains `PENDING_INDEPENDENT_RUN_H`, and `run_real()` fails closed.

The future authorized execution must use the nonzero trial counts, Holm family-wise control, adaptive validation boundary rule, and stage stop conditions in `RUN_G_PHASE3_FROZEN_CONFIG.yaml`. A later authorization may enable execution; it must not edit profiles or statistical rules after observing results.

