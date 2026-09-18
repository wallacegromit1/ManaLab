# Run F Reproducibility Record

## Inputs and hashes

- ZIP: `/home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip`
- Expected/observed SHA-256: `82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71`
- Independent canonical candidate-set SHA-256: `d9bff0652d2d449f761205575b63af0db5205c3354705c82302fa8b649de78e3`
- Run F helper: `run_f_audit/audit_helpers.py`

## Environment

- OS/container: Linux workspace supplied by Codex desktop task.
- Python: 3.14.7 (GCC 16.1.1 20260515).
- PyYAML: 6.0.3.
- Package declaration: Python >=3.11; PyYAML >=6.0.
- Web/network: not used.

## Fresh extractions

- `run_f_audit/extract_a`: full tests and protected `run-e` execution.
- `run_f_audit/extract_b`: second independent full-test execution and read-only code audit before later protected trials.
- `run_f_audit/extract_c`: untouched package-manifest reconciliation and line-referenced inspection.

## Commands executed

```bash
sha256sum /home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip
unzip -q /home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip -d run_f_audit/extract_a
unzip -q /home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip -d run_f_audit/extract_b
diff -qr run_f_audit/extract_a run_f_audit/extract_b

cd run_f_audit/extract_a/mana-lab-pauper
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m mana_lab.cli run-e

cd run_f_audit/extract_b/mana-lab-pauper
PYTHONPATH=src python -m unittest discover -s tests

cd /home/monkeyd/.codex/.chatgpt-projects/g-p-6aac55b1902881918f3322dda2a2dfea
python run_f_audit/audit_helpers.py \
  --zip /home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip \
  --repo run_f_audit/extract_b/mana-lab-pauper
```

Additional protected one-trial scripts were run inline to verify candidate-label neutrality, same-seed event equality, and manifest reconciliation. They used C0 only as a protected machinery fixture and did not compare performance across candidates.

## Observed results

- Fresh extraction A: 179 tests passed in 15.266 seconds.
- Fresh extraction B: 179 tests passed in 15.368 seconds.
- Fresh `run-e`: exit 0; 42 focused D-01–D-11 tests pass; protected order-normalized raw events equal.
- No-lookahead suite reported by Run E: 18 tests pass.
- Independent counts: inclusion–exclusion 296,706; recursive 296,706; production set identical.
- Protected label-renamed trial: summaries equal after label removal; raw events exactly equal; 362 events.
- Candidate iteration order: Run E protected smoke normalized raw events exactly equal.
- Untouched manifest audit: 63 packaged source/test/config files; 166 manifest entries; 103 absent cache entries; 103 mismatches.
- Git revision from fresh ZIP: unavailable.

## Audit-only script behavior

`audit_helpers.py` performs no candidate simulation or scoring. It:

- verifies the package hash;
- checks frozen deck/C0 facts;
- computes the search-space count by inclusion–exclusion;
- independently recursively enumerates legal configurations and compares canonical sets;
- reports Phase 3 freeze gaps;
- demonstrates the lower-is-better Pareto counterexample;
- demonstrates that the advertised alternate tap-out policy selects reserve in a protected synthetic tie.

## Expected outputs after remediation

A re-auditable package should add:

- a cache-free source manifest with no extra/missing entries;
- verifiable code/tree identity;
- a separate, complete Phase 3 config;
- a structural dry-run command using only toy/synthetic candidates;
- deterministic raw-event, metric, profile, paired-difference, robustness, Pareto, and report schemas;
- exact hashes for dry-run ordinary content;
- tests proving selection/validation seed separation and no validation leakage.

No real-candidate performance outputs were produced by Run F.
