# ManaLab

Reproducible Pauper mana-base simulation and optimization research, with frozen inputs, source, tests and independent audit evidence.

## Current status

**RUN H AUTHORIZATION — PHASE 3 NOT AUTHORIZED**

Run G reproduces 205 passing tests, but the independent Run H audit leaves F-01–F-07 open. F-08 package provenance passes. Production optimization is not authorized. Publication is not an authorization or a mana-base recommendation.

- [Run H authorization report](audits/run_h/RUN_H_PHASE3_AUTHORIZATION_REPORT.md)
- [Run H defects and required Run I remediation](audits/run_h/RUN_H_DEFECTS.md)
- [Acceptance matrix](audits/run_h/RUN_H_ACCEPTANCE_MATRIX.csv)
- [Run G simulator and reproduction instructions](mana-lab-pauper/README.md)
- [Project specifications](specifications/00_SOURCE_INDEX.md)

## Repository layout

- `mana-lab-pauper/`: complete unmodified Run G package, including code, tests, configs, reports and historical validation outputs.
- `audits/run_h/`: independent audit, helpers, evidence, and reference copies.
- `audits/run_f/`: prior independent audit and evidence (excluding duplicate extraction workspaces).
- `specifications/`: project source specifications and prior reference workbook, copied without changing synced originals.
- `archives/`: exact Run E and Run G inputs, Run H audit ZIP, and detached checksums.
- `history/`: supplied implementation/audit prompts, input supplement and project instructions.

The original archives and audit evidence are preserved byte-for-byte. Historical reports may contain original workstation paths; these are provenance, not portable configuration. Caches, local credentials, temporary extraction workspaces and duplicate build trees are excluded.

## Run the tests

From `mana-lab-pauper/`, with Python 3 and PyYAML installed:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m mana_lab.phase3_readiness --root . --config RUN_G_PHASE3_FROZEN_CONFIG.yaml --parent-zip ../archives/Mana_Lab_Pauper_v1_Run_E.zip
```

The shipped readiness gate returns PASS for its limited checks; that does **not** override Run H's independent authorization failure. Consult the audit before further implementation. Historical reports reflect their own run dates and are not current authorization.

No software license has been selected. Inclusion of card names/rules references does not assert ownership of third-party intellectual property.
