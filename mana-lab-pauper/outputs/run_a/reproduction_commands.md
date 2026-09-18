# Reproduction commands

From the repository root:

```bash
export PYTHONPATH="$PWD/src"
python -m unittest discover -s tests -v
python -m mana_lab.cli candidate-count
python -m mana_lab.cli deterministic-checks
python -m mana_lab.cli run-a
```

`run-a` enforces the build/validation phase gate and refuses optimization-enabled configuration.
