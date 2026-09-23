#!/usr/bin/env python3
import json, os, re, sys
from pathlib import Path

module_dir = Path(os.environ.get("THEMY_MODULE_DIR", Path(__file__).parent))
stage_dir = Path(os.environ.get("THEMY_STAGE_DIR", "/tmp/themy-stage"))
palette_path = os.environ.get("THEMY_PALETTE", "")
mode = os.environ.get("THEMY_MODE", "dark")

stage_dir.mkdir(parents=True, exist_ok=True)
src_file = module_dir / "templates" / f"{mode}.json"
if not src_file.exists():
    src_file = module_dir / "templates" / "dark.json"

dst_file = stage_dir / "colors.json"

data = {}
if palette_path and Path(palette_path).exists():
    try:
        data = json.loads(Path(palette_path).read_text(encoding="utf-8"))
    except Exception:
        pass

def extract_color(v):
    if isinstance(v, str):
        v = v.strip()
        if v.startswith("#") or (len(v) in (6, 8) and all(c in "0123456789abcdefABCDEF" for c in v)):
            return v if v.startswith("#") else "#" + v
        return v
    if isinstance(v, dict):
        for k in ("hex", "color", "hex_stripped"):
            if k in v:
                return extract_color(v[k])
        if all(k in v for k in ("red", "green", "blue")):
            return "#%02x%02x%02x" % (int(v["red"]), int(v["green"]), int(v["blue"]))
        if "default" in v:
            return extract_color(v["default"])
    return None

def lookup(path):
    cur = data
    parts = path.split(".")
    found_exact = True
    for part in parts:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            found_exact = False
            break
    if found_exact and cur is not None:
        c = extract_color(cur)
        if c: return c
        if not isinstance(cur, (dict, list)): return str(cur)

    role_parts = [p for p in parts if p not in ("colors", "default", "hex", "themy", "dark", "light")]
    role = role_parts[0] if role_parts else parts[-1]
    colors_dict = data.get("colors") if isinstance(data, dict) and isinstance(data.get("colors"), dict) else data

    for m in (mode, "dark" if mode == "light" else "light", "default", "amoled"):
        if isinstance(colors_dict, dict) and m in colors_dict and isinstance(colors_dict[m], dict):
            val = extract_color(colors_dict[m].get(role))
            if val: return val

    if isinstance(colors_dict, dict) and role in colors_dict:
        val = extract_color(colors_dict[role])
        if val: return val

    def deep_search(node):
        if isinstance(node, dict):
            if role in node:
                c = extract_color(node[role])
                if c: return c
            for v in node.values():
                res = deep_search(v)
                if res: return res
        elif isinstance(node, list):
            for item in node:
                res = deep_search(item)
                if res: return res
        return None
    return deep_search(data)

missing = []
def repl(m):
    key = m.group(1).strip()
    v = lookup(key)
    if v is None:
        fallbacks = {
            "primary": "#c0c1ff" if mode == "dark" else "#4a53a0",
            "on_primary": "#222578" if mode == "dark" else "#ffffff",
            "primary_container": "#3a3d8f" if mode == "dark" else "#dfe0ff",
            "secondary": "#c5c4dd" if mode == "dark" else "#5d5d72",
            "tertiary": "#e8b9d4" if mode == "dark" else "#7a5367",
            "surface": "#131313" if mode == "dark" else "#fcf8ff",
            "surface_container": "#131313" if mode == "dark" else "#f0ebf4",
            "surface_container_high": "#1f1f1f" if mode == "dark" else "#e5e0e9",
            "on_surface": "#e2e2e2" if mode == "dark" else "#1b1b21",
            "on_surface_variant": "#c6c6c6" if mode == "dark" else "#46464f",
            "error": "#ffb4ab" if mode == "dark" else "#ba1a1a",
        }
        for f_role, f_val in fallbacks.items():
            if f_role in key:
                return f_val
        missing.append(key)
        return "#ffffff"
    return str(v)

raw = src_file.read_text(encoding="utf-8")
text = re.sub(r"\{\{\s*([^}]+?)\s*\}\}", repl, raw)

dst_file.parent.mkdir(parents=True, exist_ok=True)
dst_file.write_text(text, encoding="utf-8")
(stage_dir / ".module-ok").write_text("ok\n", encoding="utf-8")
