# Run C reproduction

```bash
export PYTHONPATH="$PWD/src"
python -m unittest discover -s tests -v
python -m mana_lab.run_c_validation
```

The command performs exact enumeration only for count/invariant checks and uses only C0 plus the historical regression fixture for non-ranking smoke validation.
