# Run C changelog

| Run B ID | Affected files/functions | Old behavior | New behavior | Tests added |
|---|---|---|---|---|
| P1 | `simulator.enumerate_action_sequences`, `choose_next_action`, `execute_action_policy` | Resolved hidden draw/scry outcomes inside choice branches | Stops at information nodes; executes, reveals, and replans | `test_run_c_causal.py` |
| P2 | `payment.enumerate_payment_plans`, `execute_payment` | First legal payment won | Branches by distinct post-payment resources; canonical dedup | `test_run_c_payment_and_sequencing.py` |
| P3 | `policies.choose_land` | Counted individually payable cards | Evaluates reachable sequence outcomes and future joint color coverage | `test_run_c_land_policy.py` |
| P4 | `simulator.generate_legal_actions` | Forced land before spell search | Land is a normal main-phase action; order shapes remain inspectable | Hawk/order fixtures |
| P5 | payment/planner/opponent APIs | Boulder checks diverged; Bargain absent | One payment engine; full Bargain action with payment→sacrifice→draw | Boulder/Bargain fixtures |
| P6 | `policies.make_scry_policy` | Generic heuristic missed visible color unlocks | Missing-color and projected castability first; alternate land-stability policy | scry fixtures |
| P7 | `opponent_window_status`, action scoring | Additive reserve proxy | Explicit held/payable/demand/preserved/spent fields and hard-deadline override | reserve fixtures |
| P8 | simulator events; `metrics.py` | Compact post-spend smoke rows only | Typed raw events and configured desired-window runtime consumer | metric acceptance fixtures |
| P9 | `run_smoke_matrix` | Full policy on only three trials per scenario | Production-policy planner runs on every Run C smoke trial | reproducibility + smoke manifests |
