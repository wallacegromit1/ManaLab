# Run C executable policy specification

## Plain-English architecture

At each own-main decision, generate legal land and spell actions from public state. Spell actions cross product the strategically distinct payment results with legal Hawk returns or Bargain sacrifices. Search deterministic action sequences to depth 8. A draw or scry is an information node: score its visible pre-reveal consequences and promised draw count, stop that branch, choose the root action, execute it on the real state, reveal only legal information, then replan.

Payment plans are deduplicated only when tapped sources, tapped Boulders, permanent identities, and remaining colored pool are identical. Target choices are deduplicated only when all relevant permanent state is identical. State search preserves distinct land/spell order shapes.

Baseline scoring is lexicographic: hard own-turn deadlines; preserve one actually payable demanded reply; due executions; artifact development; promised/realized cards; spell count; untapped resources; irreversible land loss. Alternate scoring is tempo-first after hard deadlines. Canonical action keys are the final tie break and never include candidate names.

Opponent behavior is not sampled. End-step events report whether interaction is held, demanded by its configured timing profile, legally payable, preserved, or made unavailable by own-turn spending.

## Pseudocode

```text
while own-main and action budget remains:
    frontier = search(visible state, depth <= 8)
    for each node:
        actions = land plays + spell/payment/target/sacrifice actions
        for action in canonical order:
            preview deterministic costs and public consequences
            if action draws or scries:
                record information node; do not inspect library; stop branch
            else:
                recurse
    choose best terminal tuple under named policy
    execute only its first action on real state
    if draw/scry occurs, reveal legally and mutate zones
    capture post-action snapshot
    re-enter policy from new visible state
```

```text
enumerate_payment_plans(cost):
    enumerate physical source subsets
    enumerate native outputs and at most one use per untapped Boulder
    enumerate generic-mana spending choices
    compute post-payment resource signature
    merge only identical signatures
```
