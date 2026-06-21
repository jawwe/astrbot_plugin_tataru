"""Validate the repository layout required by AstrBot plugin installation."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = ("main.py", "metadata.yaml", "_conf_schema.json", "requirements.txt")
FORBIDDEN_DIRECTORY_NAMES = {".cache", "__pycache__"}
FORBIDDEN_SUFFIXES = {".db", ".pyc", ".zip"}


def main() -> None:
    """Validate plugin metadata, configuration schema, and tracked artifacts."""
    missing = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit(f"Missing required plugin files: {', '.join(missing)}")

    with (ROOT / "_conf_schema.json").open(encoding="utf-8") as file:
        schema = json.load(file)
    if not isinstance(schema, dict):
        raise SystemExit("_conf_schema.json must contain a JSON object")

    with (ROOT / "metadata.yaml").open(encoding="utf-8") as file:
        metadata = yaml.safe_load(file)
    if not isinstance(metadata, dict):
        raise SystemExit("metadata.yaml must contain a mapping")
    for key in ("name", "display_name", "version", "author", "repo"):
        if not str(metadata.get(key, "")).strip():
            raise SystemExit(f"metadata.yaml is missing required field: {key}")

    version = str(metadata["version"]).strip()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if not re.search(rf"version-{re.escape(version)}-blue", readme):
        raise SystemExit("README version badge does not match metadata.yaml")

    tracked_paths = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT, text=True
    ).split("\0")
    forbidden = []
    for raw_path in tracked_paths:
        if not raw_path:
            continue
        relative_path = Path(raw_path)
        if any(part in FORBIDDEN_DIRECTORY_NAMES for part in relative_path.parts):
            forbidden.append(raw_path)
        elif relative_path.suffix.lower() in FORBIDDEN_SUFFIXES:
            forbidden.append(raw_path)
    if forbidden:
        raise SystemExit(f"Forbidden generated artifacts: {', '.join(forbidden)}")

    print("plugin_layout=ok")


if __name__ == "__main__":
    main()
