# Pauper Mechanics Coverage Checklist

This is a planning checklist, not a requirement to implement every mechanic before the first deck.

## Tier 1 — expected early support
- ordinary basics/nonbasics
- ETB tapped lands
- artifact lands
- snow lands
- dual/multicolor lands
- filter mana
- artifact-based filtering
- card draw
- simple cost reduction / affinity
- Metalcraft/artifact thresholds
- bounce/return of lands/artifacts
- sacrifice of mana-relevant permanents
- opponent-turn held interaction
- London mulligan

## Tier 2 — implement when a deck needs them
- fetch/search lands
- landcycling
- bounce lands
- Treasures/one-shot mana
- conditional multi-mana lands / Tron
- land-type-dependent production
- basic-land search
- mana rocks
- convoke
- delve
- improvise
- alternate/additional mana costs
- modal double-faced cards if Pauper-legal/currently relevant
- cost-changing permanents

## Coverage rule
Each deck spec must list `mechanics_required`.

For each required mechanic classify:
- IMPLEMENTED + TESTED
- IMPLEMENTED, NEEDS TEST
- NOT IMPLEMENTED
- NOT MATERIAL

A decision-relevant `NOT IMPLEMENTED` mechanic prevents unique-optimum certification.
