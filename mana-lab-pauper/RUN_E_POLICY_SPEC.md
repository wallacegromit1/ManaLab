# Run E executable policy specification

## Baseline precedence

1. Functional hard-deadline executions.
2. Preserve one actually payable demanded opponent-turn reply.
3. Avoid battlefield land, untapped-source and color loss.
4. Functional due executions.
5. Avoid loss of existing artifacts; preserve artifact count.
6. Visible next-turn joint castability and demanded-color coverage, including tapped Bridges.
7. Immediately usable untapped resources.
8. Other functional spell executions.
9. Causal information value.
10. Raw spell casts.
11. Canonical action key only after strategic equality.

## Alternate tempo precedence

Hard deadline, reserve, immediately untapped resources, land preservation, functional due/spell execution, artifact state, future colors, conservative/baseline information value as selected, then canonical tie-break.

## Information nodes

Planning records an unresolved draw/scry count but does not inspect library identities. It continues deterministic actions using only cards known before the reveal. Baseline values draw 1/draw 2/scry 2 as 100/190/80 units; conservative values them 35/60/20. Board objects, payments, sacrifices and retained resources are valued independently by ordinary state terms.

## Functional execution

`spell_cast` is raw. `spell_resolution.functional` requires mandatory resolution completion; Glint Hawk that cannot return an artifact is false. Due/hard/spell execution counters consume only functional outcomes.
