# Card and Mana Model

## Core representation
Use reusable primitives rather than deck-name special cases.

### Mana
Represent:
- W/U/B/R/G;
- colorless mana;
- generic costs;
- restricted mana if a card requires it;
- variable/X costs when relevant.

Mana payment must be explicit and conserve resources.

### Lands
Support attributes:
- colors/mana amounts;
- ETB tapped or conditional tapped;
- basic/snow/artifact status;
- land types;
- bounce/return costs;
- sacrifice/search abilities;
- conditional multi-mana production.

### Nonland fixing
Support:
- filters that consume existing mana;
- mana rocks;
- one-shot mana/Treasures;
- search/landcycling;
- draw/selection that changes future access;
- conversion with tap/exhaustion state.

Filtering is not ramp unless the effect actually increases available mana.

## Cost modification
Implement deck-relevant mechanics through a generic payment layer:
- affinity;
- other generic-cost reductions;
- convoke/delve/improvise-like payments if required;
- alternate costs;
- additional costs.

Never reduce colored pips unless the actual mechanic permits it.

## Thresholds
Track relevant battlefield properties:
- artifact count;
- Metalcraft;
- snow permanent/land count;
- Tron/land-name sets;
- other supplied thresholds.

## Artifact lands
An artifact land that entered tapped:
- is unavailable for tapping that turn;
- still exists on the battlefield;
- immediately counts as an artifact for affinity/Metalcraft and other relevant effects.

## Resource-changing spell effects
Mana evaluation must update state after:
- cards drawn;
- artifacts sacrificed;
- lands/artifacts returned to hand;
- permanent deployment;
- search/fetch resolution;
- relevant token creation.

## Card facts
Card mechanics belong in data/config where practical. The engine should interpret mechanics rather than contain hard-coded references to particular Pauper cards.
