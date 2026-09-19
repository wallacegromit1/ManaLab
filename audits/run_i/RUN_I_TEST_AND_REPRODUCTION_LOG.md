# Run I test and reproduction log

## Proven, independently readable CI baseline

GitHub Actions run [35419552827](https://github.com/wallacegromit1/ManaLab/actions/runs/35419552827),
head `95b1de1716aa1c658ed62274e02f6a9b55886c83`, passed:

- untouched Run E archive: **179 / 179 tests**;
- untouched Run G archive: **205 / 205 tests**;
- working-tree Run I: **218 / 218 tests**;
- deterministic 296,706 candidates; C0 once; three-Bridge class 56;
- candidate-neutral pipeline and identical clean-run scientific manifest;
- Run E / Run G archive SHA-256 `sha256sum -c`.

**Important**: after that green head, new raw-event persistence, stricter
dependency/typed-stage checks and predicate tests were committed.
Those new changes require a subsequent CI run before any updated count
or scientific content-tree hash is claimed. Consult the draft PR's
latest-head Actions status. This document is not a claim that every
Run I authorization acceptance has passed.

## Reproduce frozen parent archives

```bash
set -euo pipefail
echo "82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71  archives/Mana_Lab_Pauper_v1_Run_E.zip" | sha256sum -c -
echo "ca7f2ed96cfc0a19041304af4d29bdbb4bf9c9b3908d10f35ffadb0599813e9d  archives/Mana_Lab_Pauper_v1_Run_G.zip" | sha256sum -c -
mkdir -p /tmp/manalab-e /tmp/manalab-g
unzip -q archives/Mana_Lab_Pauper_v1_Run_E.zip -d /tmp/manalab-e
unzip -q archives/Mana_Lab_Pauper_v1_Run_G.zip -d /tmp/manalab-g
(cd /tmp/manalab-e/mana-lab-pauper && PYTHONPATH=src python -m unittest discover -s tests -v)
(cd /tmp/manalab-g/mana-lab-pauper && PYTHONPATH=src python -m unittest discover -s tests -v)
```

## Reproduce Run I working tree safely

Run in a clean checkout of the named Run I branch or pinned commit:

```bash
cd mana-lab-pauper
python -m pip install PyYAML
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from mana_lab.phase3_config import load_phase3_config
from mana_lab.phase3_pipeline import Phase3Pipeline
cfg=load_phase3_config("RUN_G_PHASE3_FROZEN_CONFIG.yaml")
with TemporaryDirectory() as left, TemporaryDirectory() as right:
    a=Phase3Pipeline(Path(".").resolve(),cfg,left).run_real()
    b=Phase3Pipeline(Path(".").resolve(),cfg,right).run_real()
    assert a["manifest_hash"] == b["manifest_hash"]
    assert not a["ranking_produced"] and not a["recommendation_produced"]
    print(a)
PY
```

This command is a candidate-neutral machinery validation. It does not
run the configured full selection/validation trial budgets and must not
be presented as Stage 3 authorization.

Source/control: `.github/workflows/run-i-ci.yml`.
No Run H authority/reference/evidence artifact may be regenerated in place.
