# Run G decision profile specification

The authoritative machine-readable definitions are under `decision_profiles` in `RUN_G_PHASE3_FROZEN_CONFIG.yaml`. Profiles are lexicographic raw-metric vectors, not weighted master scores. Every component fixes its metric, direction, turn set, scenario aggregation, normalization (`none`), missing-data behavior, paired-uncertainty treatment, no-worse tolerance and materiality tolerance.

| Profile | Ordered vector | De-correlated variant |
|---|---|---|
| balanced | spell on-time castability; opponent-turn availability; double-spell success | castability; opponent-turn availability |
| tempo-sensitive | usable untapped mana; realized ETB block rate (lower); double-spell success | usable mana; double-spell success |
| color-consistency | colored-spell on-time castability; joint UB access | colored-spell castability only |
| interaction-sensitive | spell plus held interaction; opponent availability; full-effect Metalcraft interaction | spell plus held interaction only |
| double-spell-sensitive | double-spell success; spell plus held interaction | double-spell success only |
| affinity/value-engine | affinity-spell on-time castability; frozen critical-sequence success | same two functional endpoints; artifact-count proxies remain excluded |

`src/mana_lab/phase3_profiles.py` builds the declared vectors, rejects missing data, performs tolerance-aware lexicographic comparison, and generates every leave-one-component-out and predeclared de-correlated variant. Close or uncertainty-overlapping candidates are retained. Profile conflict is evidence for a frontier, not permission to invent a scalar tie-break.

Overlap control is explicit. Raw color access is not added independently to balanced castability; ETB blockage is removed from the tempo de-correlated variant; artifact count/affinity/Metalcraft proxies are descriptive rather than additive; interaction diagnostics are removed from the interaction de-correlated variant. Target-dependent option metrics never enter a competitive profile.

