# Strixpatch Affinity v1.3 — Mana Lab Pauper v1 Model Specification

**Stage:** design freeze / benchmark ingestion only  
**Frozen date:** 2026-09-17  
**Authority:** `benchmarks/90_STRIXPATCH_AFFINITY_V1.3_INPUT.md`  
**Optimization execution:** **NOT AUTHORIZED IN RUN A**

## 1. Benchmark audit

The supplied benchmark reconciles exactly:

- **60 cards total** = 19 variable lands + 41 frozen nonlands.
- **C0 (19):** 3 Ancient Den, 1 Goldmire Bridge, 4 Great Furnace, 2 Mistvault Bridge, 1 Razortide Bridge, 4 Seat of the Synod, 4 Vault of Whispers.
- C0 physical properties: **15 untapped artifact lands / 4 tapped Bridges**; direct source counts **W5 / U7 / B7 / R4**.
- Candidate pool: four untapped mono-color artifact lands at **1–4 copies each** and six tapped two-color Bridges at **0–4 copies each**; exactly **19 total lands**.
- Every candidate land is an artifact; every Bridge enters tapped.

### Exact search-space check

Independent brute-force enumeration and an independent generating-function formulation agree:

`[x^19] (x+x^2+x^3+x^4)^4 (1+x+x^2+x^3+x^4)^6 = 296,706` legal configurations.

At most 16 mono lands are legal, so every configuration needs at least three Bridges. Exactly **56** legal configurations have three Bridges. Bridge-count distribution is:

| Bridges | candidates |
|---:|---:|
| 3 | 56 |
| 4 | 504 |
| 5 | 2,460 |
| 6 | 8,520 |
| 7 | 20,646 |
| 8 | 38,040 |
| 9 | 54,824 |
| 10 | 60,240 |
| 11 | 52,266 |
| 12 | 35,020 |
| 13 | 16,860 |
| 14 | 6,024 |
| 15 | 1,246 |

These are deterministic acceptance targets, **not** optimization results.

## 2. Card/rules freeze

### Legality scope

The benchmark is frozen to **tabletop Pauper as of 2026-09-17**. Wizards made the Zeta downshifts, including **Baleful Strix** and **Dispatch**, legal for tabletop Pauper effective **2026-09-07**. Magic Online does not receive them until its **2026-09-23** update. Consequently, pre-September-23 MTGO data can inform older shell behavior, but cannot be treated as games from this exact frozen 60.

### Rules-critical normalized card facts

The simulator should use structured mechanics, not remembered prose.

| card | frozen mana/rules behavior relevant to Mana Lab |
|---|---|
| Giant's Boulder | Costs `{1}`; artifact; ETB **scry 2**; activation costs `{1}` plus tapping Boulder and produces one mana of any color; this is **filtering, not ramp**; as a noncreature artifact it may use its tap ability the turn it enters if the activation cost can be paid; it cannot activate again until untapped. Late `{7}` + tap + sacrifice destroy mode is preserved in data but not a primary T1–T4 action absent a target fixture. |
| Cryogen Relic | Costs `{1}{U}`; artifact; draws one on **entering** and one on **leaving** the battlefield; `{1}{U}` + sacrifice can stun a tapped creature. Return by Glint Hawk and sacrifice to Bargain/Munitions/self all create the leave trigger. |
| Utrom Monitor | Costs `{4}{U}`; artifact creature; affinity for artifacts reduces only generic mana; flying; mana value does not change with affinity. |
| Dispatch | `{W}` instant; raw effect taps; if Metalcraft is true at resolution, it exiles. Record raw castability and full-effect availability separately. |
| Galvanic Blast | `{R}` instant; base 2 damage; Metalcraft makes it 4. Record raw castability and full-effect availability separately. |
| Baleful Strix | `{U}{B}` artifact creature; requires two colored mana; ETB draw one. |
| Glint Hawk | `{W}`; on ETB it is sacrificed unless an artifact controlled by its controller is returned to hand. Artifact lands are legal return targets. Returning Cryogen produces its leave trigger; returning Boulder permits a later recast/rescry. |
| Reckoner's Bargain | `{1}{B}` instant; sacrificing an artifact or creature is an **additional casting cost**; the sacrifice occurs before the spell resolves and changes artifact/mana state immediately; then Bargain draws two on resolution. |
| Blood Fountain | `{B}` artifact; ETB creates a Blood artifact token. Thus one resolved Fountain normally contributes two artifacts after its trigger resolves. Blood activation costs `{1}`, tap, discard, and sacrifice to draw one. |
| Refurbished Familiar | `{3}{B}` artifact creature with affinity. Its opponent-discard trigger does **not** imply a deterministic draw in a goldfish model. |
| Thoughtcast | `{4}{U}` with affinity; draws two. Colored `{U}` cannot be reduced. |
| Myr Enforcer | `{7}` with affinity. For this exact shell, T2 is a required impossibility/feasibility acceptance fixture rather than an assumed desired window. |
| Nihil Spellbomb | `{1}` artifact; when it goes battlefield→graveyard its trigger can consume `{B}` to draw. A Hawk return to hand does not create that draw trigger. |
| Makeshift Munitions | `{1}{R}` enchantment; activation costs `{1}` and sacrifices an artifact/creature; resource loss is immediate. |

### Trigger/order requirements

The engine needs a minimal trigger queue for decisions that affect future draws/resources. Example: sacrificing Cryogen as Bargain's additional cost triggers Cryogen while Bargain is being cast; after casting is complete the Cryogen trigger is placed above Bargain and resolves first. It is not acceptable to collapse this to “draw three sometime.”

## 3. Real-world 4C Affinity evidence layer

This evidence is **calibration/regression context only**.

A late-August 2026 4C Affinity brewer posted three linked MTGGoldfish iterations (deck IDs **7925924, 7924586, 7928016**) and explicitly described Giant's Boulder as central fixing for a four-color shell with only four tapped lands. The same discussion explicitly identifies Cryogen Relic's leave-the-battlefield trigger as important to Glint Hawk loops. Recent MTGO tracker data also records Giant's Boulder in a small 4C Affinity sample.

The user identifies these as **Junkdog's** lists. Independent search confirms MTGGoldfish user **Junkdog** is an active Pauper deck author and previously published an Izzet Cryogen Relic list, but the indexed Reddit page is under the handle **Visual-Lawyer7861** and I could not independently prove those identities are the same. Preserve the user's attribution as metadata, but do **not** manufacture an identity link.

Use this evidence to justify testing:
- early Boulder deployment and actual filtering opportunity cost;
- fewer-tapland / Boulder-dependent sequencing as a realistic archetype behavior;
- Cryogen → Glint Hawk return/recast lines;
- artifact-count and draw-engine sequencing.

Do **not** use self-reported or tracker win rates as simulator weights, match-win translations, or proof of a land configuration.

## 4. Spell-demand freeze

`Strixpatch_Affinity_v1.3.deck.yaml` contains the machine-readable costs and timing profiles. Timing masses are **subjective demand profiles**, not empirical cast distributions. No per-spell utility weight is frozen here.

Key ambiguity is intentionally represented by named alternates:
- `baseline_practical`
- `interaction_frontloaded`
- `value_development`
- `hawk_tempo`

Run A implements these labels and event definitions. Phase 2 may adjust their exact masses **only through an explicit config change**, never by silently editing code.

## 5. Mechanics coverage gate

| mechanic | required? | current design support | exact behavior needed | tests required | blocking risk |
|---|---|---|---|---|---|
| artifact lands | yes | core primitive specified; implementation pending | land is artifact immediately, including while tapped | artifact-count + payment fixtures | HIGH until tested |
| ETB-tapped Bridges | yes | core primitive specified; implementation pending | enter tapped; cannot make mana that turn; still count as artifacts | tapped-state + threshold fixtures | HIGH |
| explicit colored/generic payment | yes | core primitive specified | conserve W/U/B/R; generic may use any legal mana; colored pips never affinity-reduced | payment matrix | HIGH |
| Boulder filter | yes | core nonland-filter primitive | pay 1, tap Boulder, output exactly 1 any color; net +0 mana | conservation/same-turn/tap fixtures | HIGH |
| Boulder scry 2 | yes | **deck-specific behavior must be added** | reveal only top two; legal bottom/reorder; alter actual library; policy cannot see card 3 | deterministic scry + no-lookahead fixtures | **BLOCKER** |
| affinity | yes | core cost-reduction primitive | reduce generic only by current artifact count at casting | cost table 0..N artifacts | HIGH |
| artifact count / Metalcraft | yes | core threshold primitive | update after every land, token, return, sacrifice, spell resolution | threshold transition fixtures | HIGH |
| draw effects | yes | core state update | draw exact top card(s), update hand/library in order | deterministic library fixtures | HIGH |
| Cryogen leave trigger | yes | needs explicit trigger event | every battlefield leave triggers draw; return and sacrifice included | Hawk/Bargain/Munitions/self-sac cases | **BLOCKER** |
| minimal trigger stack/order | yes | must be implemented for this benchmark | triggered draw generated during costs resolves in correct order | Cryogen+Bargain fixture | **BLOCKER** |
| Glint Hawk return | yes | core bounce/return primitive | enumerate legal artifact target; land or nonland; return updates thresholds/mana | no-target, land, Cryogen, Boulder fixtures | HIGH |
| additional-cost sacrifice | yes | core cost layer | sacrifice occurs while casting and is required for legality | Bargain legality/order fixtures | HIGH |
| Blood token creation | yes | token creation specified in core but implementation pending | Fountain trigger creates artifact token; token has its own tap/sac/draw activation | count + activation fixtures | HIGH |
| opponent-turn availability | yes | core turn-window design | resources must remain untapped; mana is not banked across steps | reserve/tapped-state fixtures | HIGH |
| London mulligan | yes | core design; exact benchmark rules now frozen | draw seven each attempt, fixed stopping rules, deterministic bottom optimizer | hand-size/bottom/no-lookahead fixtures | HIGH |
| play/draw | yes | core design | first player skips T1 draw in two-player game | deterministic turn fixture | MEDIUM |
| late Boulder destroy / Cryogen stun / Munitions target quality | not primary through T4 | option-only unless target fixture provided | expose legal availability, do not invent opponent board value | option-availability fixtures | LOW for Run A; would block claims relying on target value |

**Run-A interpretation:** design support exists, but implementation status remains pending. No optimization certification is allowed until every HIGH/BLOCKER item is implemented and tested.

## 6. Policy freeze

### Information boundary

Policies can use current hand, battlefield, graveyard/exile when relevant, known scry cards, public state, and frozen deck knowledge. They may never inspect unseen future library cards.

### Land policy — baseline `baseline_hand_demand`

For each legal land play, enumerate the legal current-turn action sequences available from the visible state and compare land choices lexicographically:
1. maximize due/overdue **functional** actions this turn;
2. preserve one opponent-turn interaction option when the reserve rule applies;
3. maximize current usable untapped mana;
4. maximize colors demanded by visible in-horizon spells;
5. when the tuple above is tied, prefer using a Bridge in a slack window if it improves known-hand future color coverage;
6. stable canonical land-name tie break.

No future draw is inspected.

### Land policy — alternate `alternate_tempo_untapped`

1. maximize current untapped mana;
2. maximize due-current-turn functional actions;
3. maximize known-hand color coverage;
4. stable canonical tie break.

This is intentionally less tapland-accommodating and stress-tests ranking sensitivity.

### Spell/action policy

Generate legal action sequences rather than using card-name shortcuts. The baseline lexicographic objective is:
1. execute maximum due/overdue proactive spell demands;
2. maximize end-of-main artifact count;
3. maximize cards legally drawn/selected this turn;
4. preserve baseline opponent-turn reserve;
5. maximize remaining untapped resources;
6. minimize irreversible loss of mana-producing lands;
7. stable canonical action tie break.

Rules:
- interaction is not auto-cast without a target/demand fixture;
- Boulder activation may be used only through legal payment and tap state;
- Blood/Munitions/Cryogen-stun/Nihil activations are option metrics unless a target/action fixture authorizes use;
- Bargain may be evaluated as an end-step draw action only when it has a legal sacrifice; baseline does not sacrifice a land merely to increase goldfish card velocity when a nonland sacrifice is unavailable;
- Glint Hawk enumerates artifact return targets; no hard-coded “always bounce Cryogen” rule is permitted.

Alternate sequencing is tempo-first/tap-out and deliberately relaxes the reserve constraint.

### Boulder scry policy

The top two cards are **legally known** after scry begins; the third card is not. Baseline need score:
- highest: solves a visible next-land-drop or missing-color need for a due-by-next-turn held spell;
- next: due-by-next-turn spell projected castable from visible resources;
- next: other in-horizon draw/development or artifact-engine card;
- zero: current visible state marks the card excess/outside horizon.

Bottom zero-score cards; keep/order positive-score cards by descending need score, then stable tie break. Alternate prioritizes land stability before spell timing. Any implementation that checks the unknown card beneath the scry pair fails the gate.

### Opponent-turn reserve

Baseline preserves untapped permanents sufficient for **one** held interactive option when a current opponent-window demand exists and preserving it does not miss a hard own-turn deadline. It never pre-floats mana. Alternate is tap-out development. Regardless of policy, record counterfactual availability for Blast, Dispatch, and Bargain.

### London mulligan

Baseline `baseline_functional_london`:
- each mulligan draws a fresh seven;
- at prospective final sizes 7/6/5, keep only if the seven contains 2–4 lands and visible-land sequencing can provide two usable mana in an own-T2 main phase without assuming a future draw;
- at final size 4, keep automatically;
- after keeping, bottom exactly the mulligan count using exhaustive subset selection and the frozen lexicographic rule in the YAML.

Alternate `alternate_landcount_london`:
- at final sizes 7/6/5 keep 2–5-land sevens;
- at 4 keep automatically;
- identical bottom optimizer.

These are not claimed to be perfect human mulligans. They are reproducible bracketing policies to test whether candidate ranking depends on the keep rule.

## 7. Metrics freeze

### Primary raw metrics eligible for decision profiles

- spell-level on-time castability by card/turn/profile;
- usable untapped mana by own turn;
- W/U/B/R and joint-UB access by turn;
- opponent-window Blast/Dispatch/Bargain availability;
- full-effect Metalcraft Blast/Dispatch availability;
- double-spell success;
- spell + held-interaction success;
- critical-sequence success;
- mulligan/kept-hand distributions (as decision context, not an automatic penalty term).

### Descriptive/diagnostic by default

- realized ETB-tapped blocks;
- unused mana;
- unavailable mana tied up in tapped lands;
- Boulder deploy/activate/rescue/dependency rates;
- artifact-count and Metalcraft trajectories;
- affinity reduction amounts;
- Cryogen enter/leave draw counts;
- Hawk land/nonland return counts;
- Bargain sacrifice type/resource loss;
- Blood/Nihil/Munitions/Cryogen activated-option rates;
- stranded-spell reason codes.

### Critical deck sequences

Freeze at minimum:
- T2 Strix `{U}{B}`;
- T2 Cryogen + ETB draw;
- T2 Thoughtcast/Familiar/Monitor under actual affinity state;
- T3 Cryogen → Glint Hawk value loop with correct enter/leave draw ordering;
- T3 draw/development + held interaction;
- T3 affinity payoff + held interaction;
- T4 double-spell;
- opponent-window full-effect Dispatch and Blast.

### Double-counting warnings

Do not automatically combine:
- missed spell + ETB delay + unavailable mana;
- color access + castability;
- Boulder rescue + castability gain;
- artifact count + affinity reduction + Metalcraft;
- Metalcraft rate + full-effect Dispatch/Blast;
- mulligan quality + early spell castability.

If a later decision profile uses more than one member of an overlapping family, it must provide a unique-information argument and a leave-one-component-out/de-correlated sensitivity.

## 8. Decision-profile intent

No master score is frozen. Later profiles are metric-vector views:
- **balanced** — broad raw functionality without a single dominant surrogate;
- **tempo-sensitive** — early usable mana/on-time actions/ETB blocking;
- **color-consistency** — W/U/B/R and joint UB, with Boulder dependency shown separately;
- **interaction-sensitive** — opponent-window and full-effect Blast/Dispatch/Bargain;
- **double-spell-sensitive** — T3/T4 multi-action and spell+reserve sequences;
- **affinity-value-engine** — artifact trajectories, affinity-payoff timing, and Cryogen/Hawk/draw-engine sequences.

Pareto and regret analysis belongs to the later execution phase, not Run A.

## 9. Prior-result handling

Prior Sol C1 and prior Astra findings are regression evidence only.

Run A may parse C1 as a fixture and must reproduce deterministic facts:
- C0: W5/U7/B7/R4, 15 untapped/4 Bridges;
- historical C1: W4/U7/B7/R4, 16 untapped/3 Bridges.

It must **not** assert either one wins. The rejected v1 case specifically requires protection against an unvalidated additive tapland penalty, vague sequencing, arbitrary opponent-turn scalar credit, and non-reproducible mulligan behavior.

## 10. Sources frozen for this benchmark

Authoritative/current rules and legality references used at design freeze:
- Wizards/Pauper Format Panel, **On The Zeta Set in Pauper** (2026-09-04).
- Wizards **Teenage Mutant Ninja Turtles Release Notes** for Utrom Monitor.
- Current card-data cross-checks for Giant's Boulder and Cryogen Relic via mtg.wtf.
- Wizards **Innistrad: Crimson Vow Mechanics** for Blood token definition.

Real-world evidence (lower authority; calibration only):
- r/Pauper 4C Giant's Boulder brewing/results thread, 2026-08-25/26.
- MTGGoldfish user-history evidence for `Junkdog`.
- MyMTGO recent 4C Affinity Giant's Boulder usage.

Source URLs are embedded in the YAML packet.

## 11. Design-freeze boundary

This specification is sufficient to build and test Run A. It is **not** authorization to:
- screen 296,706 candidates with Monte Carlo;
- select finalists;
- construct a Pareto frontier;
- recommend a replacement for C0;
- emit any optimality decision label.

Run A ends after implementation, deterministic validation, unit/no-lookahead tests, and small non-ranking smoke simulations.
