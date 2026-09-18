# Run C adversarial regressions

| Reproducer | Initial state / prior failure | Expected repaired behavior | Repaired behavior | Test |
|---|---|---|---|---|
| Hidden-library root action | Same public hand/battlefield; different unseen library changed Thoughtcast vs Cryogen | Same current action | PASS | `test_identical_visible_state_different_hidden_library_same_root` |
| Thoughtcast / Strix / Cryogen | Pre-cast branch resolved future draw | Root invariant; later replanning allowed | PASS | `test_*precast_invariant`, `test_*predraw_invariant` |
| Boulder scry | Hidden third card or future outcome influenced decision | Only revealed pair and visible state used | PASS | `test_same_pair_different_hidden_third_same_decision` |
| Payment ordering | Reversing U/R source order changed 1 vs 2 executions | Equivalent permutations yield same reachable outcomes | PASS | `test_battlefield_permutation_invariance` |
| Land shortcut | Two mana with four individually payable spells counted four actions | Count at most executable sequence | PASS | `test_counts_executable_sequences_not_individually_castable_cards` |
| Hawk land replay | Land forced first, so return/replay line absent | Hawk→return→replay represented; Bridge tapped | PASS | `test_hawk_return_replay_*` |
| Boulder opponent window | W source+Boulder could pay Blast in engine but not option checker | Authoritative engine reports payable | PASS | `test_boulder_white_source_makes_blast_payable` |
| Bargain integration | Helpers existed but no complete action | Payment, sacrifice, thresholds, triggers, then draw | PASS | `RunCBargainTests` |
| Reserve semantics | Proxy detached from resources | Held/payable/demand/preserved/spent separated | PASS | `test_interaction_in_hand_distinct_from_payable` |
| Production smoke | 72 full-policy trials among 480,000 rows | Every production validation trial uses production machinery | PASS | `production_smoke_manifest.json` |
