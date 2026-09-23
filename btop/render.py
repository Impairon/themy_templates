#!/usr/bin/env python3
import json, os, re, sys
from pathlib import Path

tmpl_path, out_path, palette_path, mode = sys.argv[1:5]

palette_data = {}
if Path(palette_path).exists():
    try:
        palette_data = json.loads(Path(palette_path).read_text(encoding="utf-8"))
    except Exception:
        palette_data = {}

def clean_hex(v):
    if not v:
        return None
    if isinstance(v, dict):
        for k in ("hex", "color", "hex_stripped", "value", "default"):
            if k in v:
                res = clean_hex(v[k])
                if res: return res
        if all(k in v for k in ("red", "green", "blue")):
            return f"#{int(v['red']):02x}{int(v['green']):02x}{int(v['blue']):02x}"
        return None
    if isinstance(v, str):
        s = v.strip().strip("'").strip('"')
        if s.startswith("#") and len(s) in (4, 7, 9):
            return s[:7]
        if len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s):
            return f"#{s}"
    return None

def resolve(role):
    r = role.lower().strip()
    for prefix in ("colors.", "color."):
        if r.startswith(prefix):
            r = r[len(prefix):]
    for suffix in (".default.hex", ".hex", ".default", ".value"):
        if r.endswith(suffix):
            r = r[:-len(suffix)]
    if r.startswith(f"{mode}."):
        r = r[len(mode)+1:]

    colors_obj = palette_data.get("colors", palette_data) if isinstance(palette_data, dict) else palette_data

    if isinstance(colors_obj, dict):
        for m in (mode, "dark" if mode == "light" else "light", "default"):
            if m in colors_obj and isinstance(colors_obj[m], dict):
                c = clean_hex(colors_obj[m].get(r))
                if c: return c
        c = clean_hex(colors_obj.get(r))
        if c: return c

    def deep(obj, target):
        if isinstance(obj, dict):
            if target in obj:
                c = clean_hex(obj[target])
                if c: return c
            for v in obj.values():
                c = deep(v, target)
                if c: return c
        return None

    c = deep(palette_data, r)
    if c: return c

    fallbacks = {
        "surface_container": ["surface_container_high", "surface_variant", "surface", "background"],
        "surface_container_high": ["surface_container", "surface_variant", "surface", "background"],
        "surface_container_highest": ["surface_container_high", "surface_variant", "surface"],
        "outline_variant": ["outline", "surface_variant"],
        "on_surface_variant": ["outline", "on_surface"],
        "on_background": ["on_surface"],
        "background": ["surface"],
        "proc_misc": ["secondary", "tertiary", "primary"],
        "hi_fg": ["tertiary", "secondary", "primary"],
    }
    for alt in fallbacks.get(r, []):
        c = resolve(alt)
        if c: return c

    if "on_" in r or "fg" in r:
        return "#e2e2e2" if mode == "dark" else "#1b1b1f"
    if "bg" in r or "surface" in r or "background" in r:
        return "#121212" if mode == "dark" else "#fdfcff"
    return "#c0c1ff" if mode == "dark" else "#4a58a9"

raw = Path(tmpl_path).read_text(encoding="utf-8")
rendered = re.sub(r"\{\{\s*([^}]+?)\s*\}\}", lambda m: resolve(m.group(1).strip()), raw)

out = Path(out_path)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(rendered, encoding="utf-8")
