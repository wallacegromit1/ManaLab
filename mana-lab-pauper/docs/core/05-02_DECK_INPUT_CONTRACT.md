# Deck Input Contract

Each analysis starts from a frozen machine-readable specification.

## Required deck fields
- deck name/version;
- format = Pauper;
- exact maindeck size;
- exact current maindeck;
- current mana base (`C0`);
- frozen cards/counts;
- variable mana slots;
- total-land constraint or allowed range;
- candidate land/fixing pool;
- copy-count bounds;
- sideboard/post-board scope, if any;
- play/draw mixture;
- mulligan policies to evaluate;
- target turn horizon.

## Required card facts
For every mana-relevant card:
- exact card name;
- copies;
- Oracle mana cost;
- relevant type/subtype/supertypes;
- mana abilities;
- cost reductions/alternate costs/additional costs;
- draw, selection, search, landcycling or tutor effects;
- bounce/sacrifice/return effects that change mana resources;
- threshold conditions such as artifact count, Metalcraft or snow;
- timing restrictions;
- whether the card requires mana on own turn, opponent turn, or either.

## Spell-demand model
Raw pip counts are only a sanity check.

For each relevant spell, define:
- earliest realistic turn;
- desired cast-window distribution;
- option-value window;
- color/joint-color requirement;
- generic requirement after reductions;
- same-turn follow-up/interaction requirements where relevant;
- strategic urgency profile.

If timing is subjective, use multiple named profiles instead of hiding one guess.

## Candidate-pool contract
Every variable mana source must define:
- name/id;
- legal copy range;
- enters tapped condition;
- mana produced;
- land types/supertypes;
- artifact/snow/basic flags;
- activated/triggered mana-related text;
- search/fetch targets if any;
- restrictions/conditions.

## Unsupported mechanics
If a decision-relevant mechanic is missing from the simulator:
1. flag it;
2. describe likely bias;
3. implement/test it before certification, or
4. cap the final decision at `ROBUST BEST CANDIDATE, NOT UNIQUE` / `NO UNIQUE OPTIMUM ESTABLISHED`.

Never silently approximate a material mechanic.
