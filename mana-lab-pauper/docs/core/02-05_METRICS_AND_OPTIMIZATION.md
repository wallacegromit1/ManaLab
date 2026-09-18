# Metrics and Optimization

## Principle
Record **event-level raw outcomes first**. Aggregate objectives are downstream views.

## Core metrics
Where relevant:
- opening land distribution;
- keep/mulligan rates;
- functional-hand rate;
- color access by turn;
- joint-color access by turn;
- usable untapped mana;
- spell-level on-time castability;
- spell option availability;
- stranded spells;
- realized ETB-tapped delay;
- double-spell success;
- spell + held-interaction success;
- opponent-turn interaction availability;
- unused/unavailable mana;
- fixing/filter/search draw/deploy/activation rates;
- rescue rate and dependency rate;
- artifact/Metalcraft/snow/Tron threshold rates;
- resource loss from bounce/sacrifice/return;
- specific deck-critical sequence success.

## No automatic double counting
A tapland that causes one missed spell can appear in multiple descriptive metrics. Those metrics may all be reported, but a composite objective must not automatically charge the same failure several times.

Every objective component must state:
- event measured;
- why it adds unique decision information;
- overlap with other terms.

Run leave-one-component-out or de-correlated variants.

## Pareto analysis
Treat candidate A as dominating B only when A is no worse on all chosen primary dimensions and materially better on at least one, subject to uncertainty.

Do not use noisy estimates for irreversible elimination unless confidence is sufficient.

## Named profiles
At minimum consider:
- Balanced functionality
- Tempo-sensitive
- Color-consistency
- Interaction-sensitive
- Double-spell-sensitive

Deck-specific profiles are allowed if justified in the deck spec.

## Regret
For each finalist/profile report:
- profile score or metric vector;
- gap/regret to profile winner;
- uncertainty;
- assumptions that cause rank changes.

## Final frontier
If no robust unique winner exists, return the smallest useful set of non-dominated/near-optimal candidates with:
- exact mana base;
- key gains;
- key losses;
- sensitivity conditions;
- practical registration rationale.
