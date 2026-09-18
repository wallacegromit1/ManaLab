# Acceptance Tests

No final optimality claim is allowed until all applicable tests pass.

## A. Input integrity
- [ ] exact deck size correct
- [ ] frozen cards/counts reconcile
- [ ] C0 reconstructs exactly
- [ ] candidate pool/copy limits explicit
- [ ] current card/rules facts frozen

## B. Candidate generation
- [ ] exact search-space count independently checked
- [ ] every candidate satisfies deck-size/count constraints
- [ ] no illegal copies/cards
- [ ] C0 always included

## C. Mechanics
For every used mechanic:
- [ ] unit tests pass
- [ ] mana is conserved
- [ ] colored restrictions honored
- [ ] ETB tapped states correct
- [ ] threshold counts correct
- [ ] state-changing effects update resources correctly

## D. Information/policies
- [ ] no future lookahead
- [ ] land policy executable
- [ ] spell policy executable
- [ ] opponent-turn reserve behavior explicit if relevant
- [ ] baseline London policy fully specified
- [ ] alternate policy tested

## E. Exact-vs-simulation checks
- [ ] opening land counts agree
- [ ] simple source-access checks agree
- [ ] guaranteed/impossible payment fixtures agree
- [ ] simulation differences are within expected sampling error

## F. Statistical integrity
- [ ] common random numbers/paired comparisons used where valid
- [ ] fresh validation randomness after selection
- [ ] uncertainty reported for close differences
- [ ] no tiny-trial shortlist treated as proof
- [ ] practical significance separated from Monte Carlo significance

## G. Objective/model risk
- [ ] raw metrics preserved
- [ ] composite terms precisely defined
- [ ] overlap/double-counting reviewed
- [ ] leave-one-component-out/de-correlated tests run
- [ ] alternate sequencing/mulligan assumptions tested
- [ ] unsupported decision-relevant mechanics disclosed

## H. Final language
- [ ] decision label matches evidence
- [ ] no match-win-rate claim from mana score alone
- [ ] frontier returned if optimum unresolved
- [ ] reproduction commands/configs/seeds included
