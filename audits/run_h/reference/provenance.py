from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ALLOWLIST_GLOBS = (
    "src/**/*.py",
    "tests/**/*.py",
    "configs/**/*.yaml",
    "RUN_G_PHASE3_FROZEN_CONFIG.yaml",
    "RUN_G_MECHANICS_COVERAGE.csv",
    "pyproject.toml",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_manifest(root: str | Path) -> dict[str, str]:
    root = Path(root).resolve()
    paths: set[Path] = set()
    for pattern in ALLOWLIST_GLOBS:
        paths.update(path for path in root.glob(pattern) if path.is_file())
    result: dict[str, str] = {}
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix()
        if "__pycache__" in relative or relative.endswith((".pyc", ".pyo")):
            raise AssertionError("cache escaped provenance allowlist")
        result[relative] = sha256_file(path)
    return result


def content_tree_hash(manifest: dict[str, str]) -> str:
    payload = "\n".join(f"{name}\0{digest}" for name, digest in sorted(manifest.items()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_manifest(root: str | Path, path: str | Path) -> dict[str, Any]:
    manifest = source_manifest(root)
    value = {
        "allowlist_globs": list(ALLOWLIST_GLOBS),
        "files": manifest,
        "file_count": len(manifest),
        "content_tree_sha256": content_tree_hash(manifest),
    }
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value


def validate_manifest(root: str | Path, path: str | Path) -> bool:
    recorded = json.loads(Path(path).read_text(encoding="utf-8"))
    current = source_manifest(root)
    return recorded.get("files") == current and recorded.get("content_tree_sha256") == content_tree_hash(current)

