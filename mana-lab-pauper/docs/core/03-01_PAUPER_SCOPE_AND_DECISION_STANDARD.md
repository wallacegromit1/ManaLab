# Pauper Scope and Decision Standard

## Supported v1 problem
Given a **frozen Pauper deck shell** and an explicit legal candidate mana/fixing pool, determine which mana base(s) best enable the deck to execute its actual spells and sequences on time.

The primary use case is main-deck mana optimization. Post-board mana validation is optional when exact sideboard transformations are supplied.

## Pauper-specific boundaries
Default Constructed assumptions:
- 60-card minimum maindeck, but use the exact supplied deck size;
- normally no more than four copies of a nonbasic/non-basic card by name, subject to current format rules;
- basic lands may exceed four copies;
- only Pauper-legal cards may be proposed.

Do not hard-code a current legality list. Legality/card text should be frozen per run from authoritative current data.

## What is optimized
Possible variables include:
- land identities/counts;
- land count if explicitly allowed;
- fixing artifacts/cards if explicitly allowed;
- mana-source package composition.

Do not modify frozen nonland cards unless the user explicitly broadens the optimization problem.

## What “optimal” means
“Optimal” means strongest under the **best-supported explicitly modeled practical-mana objective**, not highest raw source count and not best match win rate.

The simulator must preserve:
- raw metrics;
- uncertainty;
- policy assumptions;
- sensitivity results.

## Decision labels
### UNIQUE OPTIMUM ESTABLISHED
One exact candidate is materially better and remains robust across reasonable policies/assumptions.

### ROBUST BEST CANDIDATE, NOT UNIQUE
One candidate is the best registration choice, but nearby alternatives remain plausible or some model uncertainty remains.

### NO UNIQUE OPTIMUM ESTABLISHED
Reasonable models/policies disagree, or differences are practically unresolved. Return a small frontier with tradeoffs.

## Conservative rule
When a proposed replacement is not clearly supported, the current registered mana base remains the default benchmark. This is a decision-under-uncertainty rule, not proof the current base is globally optimal.
