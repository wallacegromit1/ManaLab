# Run G reproducibility

From the extracted Run G repository, with the exact Run E parent available:

```bash
PYTHONPATH=src python -m mana_lab.phase3_readiness \
  --root . \
  --config RUN_G_PHASE3_FROZEN_CONFIG.yaml \
  --parent-zip /home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip
```

The command performs only readiness work: parent/deck/config/policy/mechanic integrity, the full unit suite, deterministic candidate enumeration/counting, C0 uniqueness, profile and metric contract validation, the six-class planner-depth audit, cache-free provenance reconciliation and two identical synthetic dry runs. It writes `outputs/run_g/readiness/readiness_result.json` and exits nonzero on failure.

Environment used for Run G: Python 3.14.7 and PyYAML 6.0.3 on Linux. No internet access was used. The untouched parent first produced 179 passing tests. The patched repository produced 205 passing tests before final readiness execution.

Selection, validation and replicate seeds are frozen and mutually distinct. Trial pairing uses scenario, replicate, trial and play/draw identity. Candidate labels and iteration order do not enter seed derivation. The validation seed is unavailable to screening and finalist selection.

`outputs/run_g/source_config_manifest.json` is generated from an explicit allowlist of Python source, tests, YAML configs, the frozen Run G config, the mechanic registry and `pyproject.toml`. Caches and generated outputs cannot enter it. Its content-tree hash is the source version marker for the archive.

