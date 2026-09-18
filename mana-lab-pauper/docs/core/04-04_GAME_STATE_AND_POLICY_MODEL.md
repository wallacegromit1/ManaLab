# Game State and Policy Model

## State
At minimum track:
- turn and play/draw status;
- library order;
- hand;
- battlefield;
- graveyard/exile when mechanically relevant;
- land drop used/available;
- permanent tapped state;
- mana pool/current payment resources;
- artifact/snow/threshold counts;
- fixing resources and activation state;
- relevant spell status.

## Information boundary
A decision policy may use:
- cards currently known to the player;
- public game state;
- frozen deck knowledge;
- defined strategic priorities.

It may not inspect unseen future library cards.

Add explicit no-lookahead tests.

## Turn windows
Model only windows necessary for the deck, but distinguish:
- own main-phase execution;
- end-step or other own-turn setup where relevant;
- opponent-turn interaction reserve.

Do not replace opponent-turn modeling with an unexplained scalar when the distinction can change candidate ranking.

## Land sequencing
Land-play policies must be executable functions.

Candidate policy families may include:
- current-castability-first;
- future-color-coverage;
- tempo/untapped-first;
- tapland-window-aware;
- deck-specific policy justified by known hand.

Use identical policy definitions across candidate mana bases.

## Spell sequencing
Policies may prioritize:
- survival/interaction;
- current spell demand;
- engine development;
- draw/search setup;
- preservation of opponent-turn interaction.

Policies should be deterministic or reproducibly randomized and inspectable.

## Mulligans
London mulligan policies must specify:
- hand-size stopping rule;
- keep conditions;
- treatment of one-/two-/many-land hands;
- color requirements;
- bottoming order and tie-breaks.

Use at least:
- a baseline fixed policy;
- one credible alternate policy.

Do not allow candidate-specific mulligan rules unless the experiment explicitly studies adaptive mulligans.

## Play/draw
Report:
- all-play;
- all-draw;
- chosen mixed baseline.

## Policy uncertainty
When competent play is ambiguous, test multiple defensible policies and treat ranking instability as model uncertainty rather than searching for a policy that produces a preferred winner.
