# Model-Risk Lessons from the Rejected v1 Case

The first Strixpatch optimization is a regression case for Mana Lab.

## What went wrong
A prior model reported a high-confidence exact optimum after exhaustive enumeration and very large simulations. Adversarial review found that:
- roughly 90% of the reported C0→C1 composite advantage was associated with an explicit tapland-penalty term;
- removing overlapping/additional terms greatly reduced the gap;
- original sequencing/objective/mulligan implementations were not fully reproducible from the handoff;
- fresh defensible models produced different winners;
- a fresh London comparison left C0 and C1 statistically unresolved;
- nearby minimum-tapland configurations traded white, blue and black reliability in policy-sensitive ways.

## Lessons
1. More trials do not solve an unjustified objective.
2. A composite score can hide double-counting.
3. Sequencing is part of the model, not an implementation detail.
4. Mulligan policy can change ranking.
5. Conditional fixing must include deployment/opportunity cost.
6. Opponent-turn interaction should not be represented by an arbitrary scalar without sensitivity testing.
7. Exhaustive enumeration does not imply exhaustive high-quality evaluation.
8. A selected winner needs fresh validation after search.
9. The correct output may be a frontier.
10. Retaining C0 under uncertainty is not proof C0 is optimal.

## Regression expectation
Mana Lab should be able to ingest the same Strixpatch problem and:
- reproduce deterministic checks;
- make policies executable;
- expose raw outcomes;
- prevent an unsupported “clear mathematical optimum” claim;
- either establish a better-supported winner or honestly return an unresolved frontier.
