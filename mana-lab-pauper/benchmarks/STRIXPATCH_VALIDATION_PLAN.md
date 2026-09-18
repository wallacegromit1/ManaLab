# Strixpatch Affinity v1.3 — Run A Validation Plan

This plan instantiates `10_ACCEPTANCE_TESTS.md` for the first Mana Lab benchmark. **Passing Run A validates implementation readiness; it does not validate an optimal mana base.**

## A. Input integrity

### A1 — exact deck reconciliation
- Assert nonland copies sum to **41**.
- Assert C0 lands sum to **19**.
- Assert full maindeck sum is **60**.
- Assert every frozen card/count matches `90_STRIXPATCH_AFFINITY_V1.3_INPUT.md` byte-for-semantic-content.

### A2 — C0 reconstruction
Expected exactly:
- Ancient Den 3
- Goldmire Bridge 1
- Great Furnace 4
- Mistvault Bridge 2
- Razortide Bridge 1
- Seat of the Synod 4
- Vault of Whispers 4

Derived fixture: 15 untapped, 4 tapped; W5/U7/B7/R4.

### A3 — legality/card facts
- Freeze tabletop Pauper legality date **2026-09-07** for Baleful Strix and Dispatch.
- Record MTGO implementation date **2026-09-23** and block accidental use of pre-date MTGO “post-Zeta exact-list” labels.
- Card-data tests must match the normalized Giant's Boulder, Cryogen Relic, Utrom Monitor behaviors in the deck YAML.

## B. Candidate generation

### B1 — independent exact count
Implement **two independent** methods:
1. nested/product enumeration under copy bounds;
2. coefficient/DP count for `(x+x²+x³+x⁴)^4(1+x+x²+x³+x⁴)^6` at degree 19.

Both must equal **296,706**.

### B2 — boundary-class checks
- minimum Bridges = **3**;
- exactly **56** candidates at three Bridges;
- bridge-count histogram must equal:
  `3:56, 4:504, 5:2460, 6:8520, 7:20646, 8:38040, 9:54824, 10:60240, 11:52266, 12:35020, 13:16860, 14:6024, 15:1246`.

### B3 — per-candidate invariants
For every enumerated candidate:
- total lands = 19;
- mono counts each in [1,4];
- Bridge counts each in [0,4];
- every listed land belongs to candidate pool;
- all 19 are artifact lands;
- no duplicate configuration key;
- C0 appears exactly once.

## C. Mechanics/unit tests

### C1 — mana conservation/payment
- Untapped mono land taps once for its one color.
- Bridge enters tapped and cannot contribute mana on entry turn.
- Generic costs can use legal colored mana; colored pips cannot be paid by wrong color.
- Affinity reduces generic cost only; never `{U}`, `{B}`, `{W}`, or `{R}`.
- Mana pools empty at normal step/phase boundaries; opponent reserve is represented by untapped resources, not carried mana.

### C2 — artifact land and threshold state
- A newly entered tapped Bridge immediately increases artifact count.
- Metalcraft becomes true exactly at artifact count >=3 and false again after resource-changing return/sacrifice drops below 3.
- Tapping an artifact does not stop it counting for affinity/Metalcraft.

### C3 — Giant's Boulder filter
Fixture with two untapped lands and Boulder in hand:
1. pay one land to cast Boulder;
2. Boulder resolves untapped and counts as artifact;
3. use second land to pay `{1}`, tap Boulder, create exactly one chosen color;
4. assert **no net mana increase** from the filter conversion itself;
5. assert Boulder cannot activate a second time that turn without an untap effect;
6. assert Boulder untaps normally next turn.

Separate fixture: one land casts Boulder and leaves no mana to activate it immediately.

### C4 — Boulder scry 2
Use deterministic library `[A,B,C,D,...]`:
- expose exactly A and B;
- test keep A/B order, B/A order, bottom A, bottom B, bottom both;
- confirm actual library order changes accordingly;
- policy decision must be identical for two libraries sharing A/B but differing at C and below;
- after bottom-both, policy cannot condition on the new unknown top card;
- returning and recasting Boulder creates a second independent scry event.

### C5 — affinity cost table
For artifact counts 0..8 assert:
- Thoughtcast total generic portion = `max(0,4-a)` plus mandatory U;
- Refurbished Familiar = `max(0,3-a)` plus mandatory B;
- Utrom Monitor = `max(0,4-a)` plus mandatory U;
- Myr Enforcer = `max(0,7-a)` generic only.

Assert prior artifact creature resolution can reduce a later spell in the same turn.

### C6 — exact-shell Myr Enforcer early fixture
Programmatically search all legal no-opponent own-turn sequences through T2 from the frozen shell and assert a T2 Myr Enforcer cast is impossible under normal one-land-per-turn play. If Work finds a legal counterexample, it must STOP and report the exact sequence rather than changing the expected result silently.

### C7 — Metalcraft interaction
- Dispatch with artifact count 0/1/2: raw W castable if paid, but full-effect flag false.
- Dispatch with artifact count >=3 at resolution: full-effect flag true.
- Galvanic Blast similarly exposes raw castability and 2-vs-4-damage state.
- Do not equate Metalcraft at casting with guaranteed Metalcraft at resolution in any fixture that changes artifacts on stack.

### C8 — Cryogen Relic
- resolve Cryogen -> draw exactly one top card;
- Hawk returns Cryogen -> Cryogen leave trigger draws one;
- Bargain sacrifices Cryogen as additional cost -> leave trigger generated;
- Munitions sacrifices Cryogen -> leave trigger generated;
- Cryogen's own activation sacrifices it -> leave trigger generated;
- moving Cryogen between non-battlefield zones must not spuriously create the leave trigger.

### C9 — trigger ordering: Cryogen + Bargain
With known library `[A,B,C,...]`:
1. cast Bargain sacrificing Cryogen as additional cost;
2. place Cryogen leave trigger above Bargain after casting completes;
3. Cryogen trigger resolves and draws A;
4. Bargain resolves and draws B then C.

Assert final hand/library exactly. “Draw three” without order is a failing simplification.

### C10 — Glint Hawk
- no artifact after Hawk resolves -> its trigger causes Hawk sacrifice;
- artifact land is a legal return target;
- returning an artifact land removes its mana/artifact contribution and returns the physical card to hand;
- returning Cryogen triggers its leave draw and leaves Hawk in play;
- returning Boulder removes its artifact/tap state; a later recast gets a fresh scry;
- returning a permanent is not an additional casting cost and occurs only on trigger resolution.

### C11 — Bargain additional cost
- Bargain cannot be cast without a legal artifact/creature to sacrifice;
- sacrifice happens during casting before resolution;
- sacrificing an artifact land reduces land/artifact resources immediately;
- sacrificing Cryogen invokes C9 ordering;
- sacrifice choice must be explicit in action log.

### C12 — Blood Fountain / Blood token
- Fountain resolves, then ETB trigger produces one Blood artifact token;
- after trigger, Fountain + Blood contribute two artifacts if both remain;
- Blood activation requires `{1}`, tap, one discarded card, and sacrifice; draw occurs only after paying all costs;
- same Blood cannot pay two sacrifice costs.

### C13 — Nihil Spellbomb
- battlefield→graveyard creates optional B payment opportunity to draw;
- Hawk return to hand does not create the trigger;
- paying B is an explicit mana payment, not free card draw.

### C14 — Refurbished Familiar
- affinity/payment correct;
- baseline goldfish must **not** auto-draw from its ETB trigger because opponent hand state is unspecified.

### C15 — play/draw
- two-player player-on-play skips draw on own T1;
- player-on-draw draws on own T1;
- all-play/all-draw/mixed scenarios produce the expected cards-seen counts.

## D. Policies / no-lookahead

### D1 — land policy determinism
Same visible state + same policy + same candidate => same land choice and tie-break result across repeated runs.

### D2 — policy invariance across candidates
Policy source code/config is identical for every candidate. Candidate identity may change legal actions/resources, but must not branch to candidate-name-specific heuristics.

### D3 — hidden-library sentinel
Construct paired libraries identical in all currently known positions but different later. Until a later card becomes legally known, land/spell/mulligan decisions must be identical.

### D4 — scry boundary
Two libraries with same top two and different third cards must make identical Boulder scry choices.

### D5 — mulligan no-lookahead
Keep/mulligan and bottom decisions can use only the currently drawn seven, legal deck priors/frozen parameters, and public information. They must not depend on the post-bottom future order.

### D6 — London procedure
For mulligan count `m`:
- a fresh seven is drawn after each mulligan;
- on keep, exactly `m` cards are bottomed;
- resulting hand size = `7-m`;
- baseline and alternate stopping rules match deck YAML;
- all bottom subset ties use deterministic canonical tie breaks.

### D7 — opponent reserve
- own-turn policy preserves untapped sources, never floating mana to next turn;
- tap-out alternate may consume them;
- opponent-window option metric observes actual tapped state.

## E. Exact-vs-simulation checks

### E1 — C0 opening land distribution, raw seven
For `N=60, K=19, n=7`, exact probabilities are:

| lands | probability |
|---:|---:|
| 0 | 0.058212162537 |
| 1 | 0.221206217641 |
| 2 | 0.331809326462 |
| 3 | 0.254088222966 |
| 4 | 0.106984514933 |
| 5 | 0.024688734215 |
| 6 | 0.002880352325 |
| 7 | 0.000130468921 |

A sufficiently large dedicated validation simulation must agree within predeclared binomial Monte Carlo tolerance.

### E2 — raw direct-source draw checks, opening seven
These are **draw-presence**, not usable-source probabilities:
- W5: `P(>=1)=0.474562172527`
- U7: `0.600879549232`
- B7: `0.600879549232`
- R4: `0.399499625745`
- joint U and B, accounting for two Mistvault cards shared between U/B sets: `0.392405791175`.

### E3 — guaranteed/impossible payment fixtures
Include trivial single-state fixtures:
- only Ancient Den available -> can pay W, cannot pay U/B/R;
- only tapped Bridge entered this turn -> cannot pay mana that turn but counts as artifact;
- two untapped lands plus Boulder filter can convert one mana into a needed color but cannot create two net mana;
- one Boulder activation cannot repair two simultaneously missing colored pips for Strix.

## F. Statistical-integrity Run-A checks

Run A performs **no candidate selection**. Smoke simulations exist only to catch implementation mismatch.

- C0 and historical C1 smoke runs use common random numbers where state mapping is valid.
- No result may be described as a winner or shortlist.
- Smoke run trial target: 20,000 per configured scenario/candidate; exact checks take precedence over noisy differences.
- Final-selection seeds remain unused until the later execution phase.
- Code must support fresh post-selection validation seeds before Work Run C/Phase 3 is ever authorized.

## G. Objective/model-risk tests

### G1 — event-level preservation
Every aggregate metric must be reconstructible from event records or documented sufficient statistics.

### G2 — no default opaque master score
Repository must have no enabled default aggregate that sums spell misses, tap delays, unavailable mana, rescue/dependency, etc. into one winner score.

### G3 — overlap registry
Machine-readable or documented overlap families must include:
- `spell_miss / ETB_block / unavailable_mana`
- `color_access / castability`
- `Boulder_rescue / castability`
- `artifact_count / affinity_reduction / Metalcraft`
- `Metalcraft / full_effect_interaction`
- `mulligan_quality / early_castability`

### G4 — prior-v1 regression guardrails
- no fixed “55% opponent-turn Boulder credit” or equivalent scalar exists;
- no additive generic “tapland penalty” is enabled by default;
- sequencing and mulligan policies are named, executable, and logged;
- historical C1 is regression-only and has no priority/preference flag.

### G5 — unsupported mechanic behavior
Any required mechanic marked unimplemented causes Run A to fail. The program must refuse an optimality label if a required decision-relevant mechanic lacks tests.

## H. Reporting/reproducibility

Run A must emit:
- repository tree;
- language/compiler/interpreter/package versions;
- config and code hashes;
- deterministic count outputs;
- complete unit-test report;
- no-lookahead report;
- coverage matrix;
- smoke-validation report with explicit “NOT A RANKING” banner;
- exact rerun commands;
- `run_a_stop_certificate.md` asserting that exhaustive optimization/finalist selection did not run.

## Run-A pass condition

All applicable A–H build-stage tests above pass, all BLOCKER/HIGH mechanics are implemented + tested, deterministic checks match exactly, and no-lookahead failures are zero.

A Run-A pass **opens Phase 2 Chat implementation QA only**. It does not open full optimization automatically.
