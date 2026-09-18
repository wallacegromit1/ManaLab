# Benchmark Input — Strixpatch Affinity v1.3

This is the first Mana Lab Pauper v1 regression case.

## Objective
Determine the strongest **19-land mana base(s)** for the exact frozen 41-nonland Strixpatch Affinity v1.3 maindeck.

Do not change nonland counts.

If no robust unique optimum can be established, return the strongest candidate frontier with quantified tradeoffs.

## Current C0 — 19 lands
3 Ancient Den
1 Goldmire Bridge
4 Great Furnace
2 Mistvault Bridge
1 Razortide Bridge
4 Seat of the Synod
4 Vault of Whispers

## Frozen nonlands — 41
3 Baleful Strix
1 Blood Fountain
4 Cryogen Relic
3 Dispatch
4 Galvanic Blast
4 Giant's Boulder
4 Glint Hawk
1 Makeshift Munitions
4 Myr Enforcer
1 Nihil Spellbomb
3 Reckoner's Bargain
4 Refurbished Familiar
4 Thoughtcast
1 Utrom Monitor

## Search space
Four colors: W/U/B/R.

Untapped mono-color artifact lands:
- Ancient Den (W): 1–4
- Seat of the Synod (U): 1–4
- Vault of Whispers (B): 1–4
- Great Furnace (R): 1–4

Tapped artifact duals:
- Razortide Bridge (WU): 0–4
- Goldmire Bridge (WB): 0–4
- Rustvale Bridge (WR): 0–4
- Mistvault Bridge (UB): 0–4
- Silverbluff Bridge (UR): 0–4
- Drossforge Bridge (BR): 0–4

Exactly 19 lands total.

All listed candidate lands are artifacts. Mono lands enter untapped. Bridges enter tapped.

## Required benchmark mechanics
At minimum the model must correctly cover:
- artifact lands;
- ETB-tapped Bridges;
- Giant's Boulder deployment/filtering/tap limits;
- affinity/cost reduction;
- artifact counts;
- Metalcraft;
- Baleful Strix UB payment;
- Dispatch white + Metalcraft distinction;
- Glint Hawk artifact-return sequencing;
- Reckoner's Bargain sacrifice implications where mana-relevant;
- Thoughtcast/Myr Enforcer/Refurbished Familiar/Utrom Monitor affinity;
- Cryogen Relic draw behavior if current Oracle text makes it decision-relevant;
- opponent-turn availability for Blast/Dispatch/Bargain;
- London mulligan;
- play/draw.

## Verification requirement
Before freezing the benchmark implementation, verify current Oracle text and Pauper legality for all nonstandard/newer cards whose mechanics affect the simulation, especially:
- Giant's Boulder
- Cryogen Relic
- Utrom Monitor

Do not rely solely on the prior workbook.

## Historical context
The prior Sol model recommended:
4 Ancient Den
4 Seat of the Synod
4 Vault of Whispers
4 Great Furnace
3 Mistvault Bridge

The subsequent adversarial audit rejected the claim that this was a clear mathematical optimum and recommended retaining C0 under unresolved model risk.

Neither result is authoritative for Mana Lab.
