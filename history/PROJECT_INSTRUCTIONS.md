# ChatGPT project context

This directory is a local mirror of the ChatGPT project “Mana Lab Optimizer”.

- Treat every file under `sources/` as read-only reference material.
- Do not edit, rename, move, or delete synced project files.
- These files may be replaced the next time a task is created from this ChatGPT project.


## Project instructions

# MANA LAB — PAUPER v1 PROJECT INSTRUCTIONS

## Mission
Build a reproducible Pauper mana-base simulator/optimizer that determines the strongest mana base(s) for a supplied deck while keeping the nonland strategy frozen unless the current task explicitly says otherwise.

Model practical mana functionality—not merely land or colored-source counts—including sequencing, ETB-tapped lands, fixing, filtering, cost reduction, artifact/snow/land-type requirements, draw/search effects, mulligans, own-turn vs opponent-turn mana, double-spelling, and opportunity cost.

If one configuration is robustly superior, recommend one exact mana base. If not, return the smallest defensible frontier of top candidates with quantified strengths, weaknesses, uncertainty, and conditions under which each is preferred.

## Scope
v1 is intentionally limited to **Pauper**. Do not generalize requirements to other formats until Pauper v1 is validated.

Support normal Pauper maindecks and, when requested, post-board configurations. Treat the supplied deck/problem specification as authoritative for exact deck size, land count/range, frozen cards, variable lands, and candidate pool.

Do not redesign the deck merely to make mana easier.

## Authority order
When sources conflict:
1. Current user instruction.
2. Current deck/problem input.
3. Current experiment configuration.
4. Project source specifications.
5. Prior result/audit packages.

Prior analyses are evidence/regression tests, never authority over a new run.

## Card/rules facts
Use supplied frozen card data when present. If material Oracle text, legality, mana ability, timing, or interaction is missing or uncertain, verify it against current authoritative card data before freezing the model. Never silently model remembered text.

## Mode / credit strategy
Prefer **Chat mode** for specification, mathematical design, QA, methodology, interpretation, and adversarial review.

Use **Work mode** when persistent execution materially helps: repository creation, multi-file implementation, tests, debugging, exhaustive enumeration, repeated simulation, result datasets, and packaging.

Do not launch expensive optimization until the model specification and acceptance tests are frozen. Reserve Astra mainly for final adversarial audit or unresolved methodology.

## Scientific rules
1. **Raw measurements before scores.**
2. Every metric/objective term needs a precise event definition.
3. Preserve raw outcomes so alternate objectives can be evaluated without unnecessary reruns.
4. Test correlated penalties for overlap/double-counting.
5. Statistical precision does not repair model misspecification.
6. Never translate simulator-score gaps into match-win-rate points without independent evidence.
7. Separate sampling uncertainty from model uncertainty.
8. Make subjective assumptions explicit and sensitivity-test them.
9. Never force a single winner when the evidence supports a frontier.

## Required simulator architecture
Represent, when relevant:
- physical cards/zones and draw order without future lookahead;
- lands, land drops, tapped state and land types;
- colored/colorless mana and payment;
- mana abilities, filters, conditional sources and one-shot mana;
- ETB-tapped costs;
- card draw/selection/search/landcycling;
- affinity/cost reduction and artifact counts;
- Metalcraft and other mana-relevant thresholds;
- snow requirements;
- bounce/sacrifice/return effects affecting mana;
- opponent-turn held mana/response windows;
- same-turn multi-spell execution;
- mulligans and bottoming.

Policies must be executable and inspectable. “Competent sequencing” is not a specification. Support alternate sequencing/mulligan policies when decisions are uncertain.

Any unsupported mechanic must be flagged. If it could change candidate ranking, it blocks `UNIQUE OPTIMUM ESTABLISHED`.

## Pauper mechanics coverage
The model should be extensible to common Pauper mana systems:
- basics and ordinary colored lands;
- artifact lands and tapped Bridges;
- fetch/search lands and landcycling;
- bounce lands and snow lands;
- filter artifacts/lands;
- Treasures or comparable one-shot mana;
- Tron/conditional multi-mana lands;
- affinity and generic-cost reductions;
- convoke/delve/improvise-like payment when relevant;
- alternate/additional costs that materially affect sequencing.

Implement only mechanics required by the current deck, using reusable abstractions rather than deck-name special cases.

## Primary metrics
Report interpretable outcomes before aggregate objectives:
- land/keep/mulligan distributions;
- color and joint-color access by turn;
- usable untapped mana;
- spell-level on-time castability;
- stranded spells;
- realized ETB-tapped delays;
- opponent-turn interaction availability;
- double-spell / spell+interaction success;
- unused/unavailable mana;
- fixing/search/filter deployment, rescue and dependency;
- artifact/Metalcraft/snow/other threshold rates;
- relevant resource loss from bounce/sacrifice/return.

## Optimization method
A. Freeze deck, candidate pool, rules and policies.  
B. Exact enumeration/deterministic calculations where feasible.  
C. Safe dominance/Pareto filtering only when mathematically justified.  
D. Medium paired simulation for surviving and forced candidates.  
E. High-precision paired validation for finalists.  
F. Robustness tests across sequencing, mulligans, play/draw, spell timing, mechanic assumptions and objective profiles.  
G. Final decision or unresolved frontier.

Never eliminate a candidate solely from extremely noisy tiny-trial screening. Keep the current mana base as a mandatory benchmark. Use independent selection/validation seeds and document screening risk.

## Decision framework
Do not rely on one opaque master score. Compare finalists using raw metrics plus named profiles such as:
- balanced functionality;
- tempo-sensitive;
- color-consistency;
- interaction-sensitive;
- double-spell-sensitive;
- deck-specific profiles justified by the frozen deck.

Use Pareto dominance and regret across profiles. A candidate that wins only because of one subjective weight is not a robust optimum.

## Validation gate
Before final optimization require:
- unit tests for all mana-relevant mechanics used;
- exact deck/candidate-space count checks;
- deterministic hypergeometric/combinatorial checks where applicable;
- simulation agreement with exact checks within sampling error;
- no-lookahead and mana-conservation/payment tests;
- alternate sequencing and mulligan policies;
- de-correlated/leave-one-component-out objective tests;
- independent seeds;
- paired candidate differences with Monte Carlo uncertainty;
- reproducible commands, configs and hashes.

Failed validation blocks optimality claims.

## Decision labels
Use exactly one:

**UNIQUE OPTIMUM ESTABLISHED**  
One exact mana base is materially/statistically superior under the best-supported model and robust to reasonable policy/model variation.

**ROBUST BEST CANDIDATE, NOT UNIQUE**  
One configuration is the best practical registration choice, but credible alternatives remain close or some model uncertainty remains.

**NO UNIQUE OPTIMUM ESTABLISHED**  
Defensible assumptions produce different winners or important differences are unresolved. Return the smallest useful frontier with exact lists, quantitative tradeoffs and decision-sensitive assumptions.

## Deliverables
Maintain an auditable repository containing:
- frozen deck/card/land configs;
- simulator/optimizer source;
- explicit sequencing/mulligan policies;
- tests/deterministic checks;
- experiment configs/seeds;
- candidate/result tables;
- spell/turn metrics;
- Pareto frontier/robustness matrix;
- methodology/limitations report;
- one-command reproduction instructions;
- final recommendation/frontier report.

Reproducibility, calibrated uncertainty and correct decision logic outrank producing one answer.
