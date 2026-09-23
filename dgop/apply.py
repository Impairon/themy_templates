#!/usr/bin/env python3
import os, shutil, sys
from pathlib import Path

stage_dir = Path(os.environ.get("THEMY_STAGE_DIR", "/tmp/themy-stage"))
rendered_colors = stage_dir / "colors.json"

config_home = Path(os.environ.get("DGOP_CONFIG_HOME") or (Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "dgop"))
config_home.mkdir(parents=True, exist_ok=True)

target_file = config_home / "colors.json"
if rendered_colors.exists():
    shutil.copy2(rendered_colors, target_file)
    print(f"[dgop] Applied theme colors to {target_file}")
else:
    print(f"[dgop] Warning: {rendered_colors} not found to apply", file=sys.stderr)
