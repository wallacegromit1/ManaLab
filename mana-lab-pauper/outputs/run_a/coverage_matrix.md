# Run A coverage matrix

| Required mechanic | Status |
|---|---|
| `artifact_lands` | IMPLEMENTED + TESTED |
| `etb_tapped_lands` | IMPLEMENTED + TESTED |
| `explicit_colored_and_generic_payment` | IMPLEMENTED + TESTED |
| `giant_boulder_scry_2` | IMPLEMENTED + TESTED |
| `giant_boulder_filtering_and_tap_state` | IMPLEMENTED + TESTED |
| `artifact_count` | IMPLEMENTED + TESTED |
| `affinity_for_artifacts` | IMPLEMENTED + TESTED |
| `metalcraft` | IMPLEMENTED + TESTED |
| `etb_draw` | IMPLEMENTED + TESTED |
| `leaves_battlefield_draw` | IMPLEMENTED + TESTED |
| `triggered_ability_queue_minimal` | IMPLEMENTED + TESTED |
| `artifact_return_to_hand` | IMPLEMENTED + TESTED |
| `additional_cost_sacrifice` | IMPLEMENTED + TESTED |
| `sacrifice_resource_loss` | IMPLEMENTED + TESTED |
| `token_creation_and_blood_token` | IMPLEMENTED + TESTED |
| `draw_order_state_updates` | IMPLEMENTED + TESTED |
| `opponent_turn_resource_availability` | IMPLEMENTED + TESTED |
| `same_turn_multi_spell` | IMPLEMENTED + TESTED |
| `london_mulligan_and_bottoming` | IMPLEMENTED + TESTED |
| `play_draw_difference` | IMPLEMENTED + TESTED |

All required mechanics have direct unit fixtures. Target-dependent late abilities are option-only as frozen in the model specification.

## Objective-risk controls

- No default master score exists.
- No generic tapland penalty exists.
- No fixed opponent-turn Boulder credit exists.
- Historical C1 is marked regression-only.
- Overlap families: `{"artifact_affinity_metalcraft": ["artifact_count", "affinity_reduction", "Metalcraft"], "boulder_and_castability": ["Boulder_rescue", "castability"], "color_and_castability": ["color_access", "castability"], "metalcraft_full_effect": ["Metalcraft", "full_effect_interaction"], "mulligan_early_castability": ["mulligan_quality", "early_castability"], "spell_miss_etb_unavailable": ["spell_miss", "ETB_block", "unavailable_mana"]}`
