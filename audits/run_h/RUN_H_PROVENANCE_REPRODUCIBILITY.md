# Run H provenance and reproduction

**F-08 PASS (package identity only).**

Run G expected = observed `ca7f2ed96cfc0a19041304af4d29bdbb4bf9c9b3908d10f35ffadb0599813e9d`. Run E expected = observed `82d1dcd663de5a8bcb2d9917271fba264c509bdff8b45d1920b9f97ccf0d0c71`. ZIP test reports no corrupt member. Independently regenerated manifest exactly matches all **78** allowlisted source/config/test/project files, with no cache or generated entry. Content tree: `0fbc3204571a8df35e4ed27887a79c2ae5bdfc73371f4354cde53e17617ecffc`. Full file map: evidence/provenance.json.

Fresh A and B gates each pass 205 tests; parent passes 179. Source/config/test/report files outside outputs remain byte-identical before/after. Dry-run JSON ordinary byte hashes agree across A/B, without needing content normalization. Runtime duration/path strings in test/gate logs are not claimed byte-identical. Full logs and command arrays are retained.

The legacy Run E manifest retained inside history has stale cache entries; it is not the Run G current identity. New allowlist/source tree repairs that F-08 defect. ZIP hash identifies archive bytes; tree hash identifies selected immutable content and excludes its own output manifest, avoiding circularity. Actual executable policy source is included. A changed source byte is detected by file/tree validation, even if registry prose is unchanged. Pipeline-stage lineage still fails independently under H-01/H-05.

## Reproduce safely

Requires Python 3 and PyYAML. Retain exact input ZIPs; audit archive intentionally does not duplicate the large production inputs. Place this audit directory in a workspace as run_h_audit. Put Run G ZIP at workspace root. The helper defaults to Run E at /home/monkeyd/Documents/Mana_Lab_Pauper_v1_Run_E.zip; adjust only the audit helper PARENT path if using another host. Extract G into fresh run_h_work/a and run_h_work/b and E into run_h_work/parent (each ZIP contains mana-lab-pauper). Never extract over production or synced sources.

```sh
PYTHONDONTWRITEBYTECODE=1 python run_h_audit/audit_helpers.py reproduce
PYTHONDONTWRITEBYTECODE=1 python run_h_audit/audit_helpers.py adversarial
PYTHONDONTWRITEBYTECODE=1 python run_h_audit/supplemental_checks.py
```

The helper's reproduce mode runs the shipped one-command readiness gate in each fresh extract and the parent unittest suite. adversarial mode writes only external evidence/temp artifacts and performs no candidate performance screening. Contract FAIL records are expected audit findings; inspect JSON rather than interpreting process exit zero as production readiness. Generation helper build_reports.py uses original run_f_audit references as its authority source; packaged authority/ holds verbatim copies and their hashes for independent reading. Reference source copies are exact evidence, not an alternate repaired implementation.

Evidence limitations: independent enumeration order is checked as identity-set invariance; production performance candidate-order invariance cannot be established without a production pipeline. C0 label invariance is verified for two identical trials. Selection/validation end-to-end isolation and every-stage protected retention are blocked by missing implementation, not passed by assertion.
