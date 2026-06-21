"""Import the plugin against an installed AstrBot checkout."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path


def main() -> None:
    """Load the plugin module and assert its registered class is available."""
    workspace = Path(os.environ["GITHUB_WORKSPACE"])
    plugin_path = workspace / "main.py"
    spec = importlib.util.spec_from_file_location("tataru_compat_smoke", plugin_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load plugin module specification")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "TataruPlugin"):
        raise RuntimeError("TataruPlugin was not exported after import")
    print("astrbot_import_smoke=ok")


if __name__ == "__main__":
    main()
