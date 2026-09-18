# Run G changelog

Run G adds the Phase 3 decision/execution layer while preserving the locked 60-card deck, 41 nonlands, 19-land candidate rules, C0 and validated mana/payment semantics.

## Code

- Added `phase3_config.py` for complete-config, hash, seed, profile, output and stop-condition validation.
- Added `phase3_policies.py` for stable policy IDs, versions, content hashes and drift rejection.
- Added `phase3_profiles.py` for transparent profile vectors, practical ties, leave-one-out and substantive de-correlation.
- Added `phase3_metrics.py` for registry-complete aggregation routing, raw-event identity validation, denominator reconstruction, critical-sequence predicates and provenance rows.
- Replaced point-estimate-only dominance in `metrics.py` with direction-, tolerance- and paired-uncertainty-aware evidence classification. The legacy exact-fixture wrapper now refuses to dominate known stochastic metrics from means alone.
- Added `phase3_pipeline.py` with nine fail-closed artifact stages, protected/uncertain screening rules, fresh-validation separation and reproducible synthetic readiness execution.
- Added `phase3_depth.py` with six predeclared planner structural classes and depth 7/8/9 audits.
- Added `phase3_readiness.py` for the one-command machine-readable gate.
- Added `provenance.py` for an allowlisted cache-free content manifest.
- Updated `policies.py` and `simulator.py` so opponent reserve is an independent, explicit policy dimension. `tap_out_development` contributes no reserve preference; every production result records the reserve policy and configured planner bounds.
- Added Metalcraft state to opponent-window events for full-effect interaction aggregation.

## Tests

Added 26 Run G tests across configuration/profile completeness, seed isolation, policy drift, screening safety, uncertainty-aware dominance, dry-run reproducibility, event aggregation and duplicate rejection, mechanics coverage, true tap-out behavior, structural depth stability and cache-free provenance. The original 179 Run E tests remain unchanged and passing.

## Configuration and documentation

Added the concrete frozen Phase 3 config, mechanic registry, pipeline/profile specifications, acceptance matrix, provenance, reproducibility record, no-optimization attestation and readiness report. Trial counts, uncertainty, multiplicity, materiality, robustness, outputs and stop conditions are nonblank and preregistered.

## Production-engine impact

No card, land, payment, cost-reduction, draw, state-transition or candidate-generation semantics changed. The only production-policy change is the new explicit reserve-policy parameter required by F-05; the existing baseline default is preserved, and the alternate tap-out behavior is isolated to a labeled robustness scenario.

