# Run E reproduction commands

```bash
export PYTHONPATH="$PWD/src"
python -m unittest discover -s tests -v
python -m mana_lab.cli candidate-count
python -m mana_lab.cli deterministic-checks
python -m mana_lab.cli run-e
```

`run-e` performs validation, protected smoke and reporting only. It refuses optimization-enabled configuration and contains no candidate scoring command.
