#!/usr/bin/env python3
import sys
from pathlib import Path

conf_path = Path(sys.argv[1])
seed_path = Path(sys.argv[2])

if not conf_path.exists():
    conf_path.parent.mkdir(parents=True, exist_ok=True)
    if seed_path.exists():
        content = seed_path.read_text(encoding="utf-8")
    else:
        content = 'color_theme = "themy"\ntheme_background = false\ntruecolor = true\n'
    conf_path.write_text(content, encoding="utf-8")
else:
    lines = conf_path.read_text(encoding="utf-8").splitlines()
    out = []
    found_theme = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("color_theme") and "=" in stripped:
            out.append('color_theme = "themy"')
            found_theme = True
        else:
            out.append(line)
    if not found_theme:
        out.insert(0, 'color_theme = "themy"')
    conf_path.write_text("\n".join(out) + "\n", encoding="utf-8")
