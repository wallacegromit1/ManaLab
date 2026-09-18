# Mana Lab — Pauper v1 — Run G

Mana Lab is a reproducible Pauper mana-base simulation and validation engine. This repository contains the Run G Phase 3 readiness remediation of the frozen Strixpatch Affinity v1.3 benchmark.

## Current phase

**Run G: Phase 3 readiness remediation only.** The program enumerates the full legal candidate space only to verify its exact size and invariants. It does not simulate that space for performance, screen real candidates, select finalists, build a real Pareto frontier, or recommend a mana base.

Run G adds a frozen staged pipeline, decision profiles, uncertainty-aware dominance, policy hashes, mechanic containment and a synthetic dry run. These are explicitly non-ranking diagnostics pending independent Run H authorization.

## Quick start

Python 3.11+ and PyYAML 6+ are required.

```bash
export PYTHONPATH="$PWD/src"
python -m unittest discover -s tests -v
python -m mana_lab.phase3_readiness --root . --config RUN_G_PHASE3_FROZEN_CONFIG.yaml \
  --parent-zip /home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip
```

The concise result is `RUN_G_PHASE3_READINESS_REPORT.md`. Auditable files are written under `outputs/run_g/`.

## Architecture

- `cards.py`: machine-readable deck, card, and land contracts
- `state.py`: physical cards, zones, permanents, stack, turn/phase state
- `mana.py` / `payment.py`: explicit payment, conservation, affinity, and filtering
- `effects.py`: scry, draw, triggers, returns, sacrifices, and token state
- `policies.py` / `mulligan.py`: executable named policies with visible-state boundaries
- `simulator.py`: causal visible-state planning plus deterministic/pairable validation simulation
- `candidates.py`: exact legal enumeration and independent DP count
- `statistics.py` / `metrics.py`: exact checks, uncertainty helpers, and raw event preservation
- `run_e_validation.py`: staged Run E gate, reports, robustness checks, and hard stop
- `phase3_*`: Run G frozen config validation, policies, profiles, aggregation, staged dry run, depth audit and readiness gate

## Phase gate

`RUN_G_PHASE3_FROZEN_CONFIG.yaml` has `optimization_execution_allowed: false` and status `PENDING_INDEPENDENT_RUN_H`. The production execution entry point fails closed. No Run G command performs real candidate scoring or selection.

Run G may declare implementation readiness, but only an independent Run H audit may authorize expensive Phase 3 work.
