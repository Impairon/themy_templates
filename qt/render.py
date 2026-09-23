#!/usr/bin/env python3
import json, os, re, sys
from pathlib import Path

module_dir = Path(os.environ.get("THEMY_MODULE_DIR", Path(__file__).parent))
stage_dir = Path(os.environ.get("THEMY_STAGE_DIR", "/tmp/themy-stage"))
palette_path = os.environ.get("THEMY_PALETTE", "")
mode = os.environ.get("THEMY_MODE", "dark")
stage_dir.mkdir(parents=True, exist_ok=True)

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
            return "#%02x%02x%02x" % (int(v["red"]), int(v["blue"]), int(v["green"]))
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

def hex_to_rgb(hex_str, default="255,255,255"):
    if not hex_str: return default
    h = hex_str.lstrip("#")
    if len(h) >= 6:
        try:
            return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"
        except ValueError:
            pass
    return default

# 1. Render themy.conf (qt5ct / qt6ct)
conf_src = module_dir / "colors.conf"
if conf_src.exists():
    def repl(m):
        key = m.group(1).strip()
        v = lookup(key)
        return str(v) if v is not None else "#888888"
    raw = conf_src.read_text(encoding="utf-8")
    rendered_conf = re.sub(r"\{\{\s*([^}]+?)\s*\}\}", repl, raw)
    (stage_dir / "themy.conf").write_text(rendered_conf, encoding="utf-8")

# 2. Render theme.colors (single KDE color-scheme for Dolphin)
c_surface = hex_to_rgb(lookup("surface") or lookup("background"), "19,19,19" if mode == "dark" else "250,250,250")
c_surface_container_low = hex_to_rgb(lookup("surface_container_low"), "27,27,27" if mode == "dark" else "240,240,240")
c_surface_container = hex_to_rgb(lookup("surface_container"), "31,31,31" if mode == "dark" else "235,235,235")
c_on_surface = hex_to_rgb(lookup("on_surface"), "226,226,226" if mode == "dark" else "25,25,25")
c_on_surface_variant = hex_to_rgb(lookup("on_surface_variant"), "198,198,198" if mode == "dark" else "100,100,100")
c_outline = hex_to_rgb(lookup("outline"), "145,145,145" if mode == "dark" else "150,150,150")
c_primary = hex_to_rgb(lookup("primary"), "82,86,169" if mode == "dark" else "74,83,160")
c_secondary = hex_to_rgb(lookup("secondary"), "197,196,221" if mode == "dark" else "93,93,114")
c_tertiary = hex_to_rgb(lookup("tertiary"), "232,185,212" if mode == "dark" else "122,83,103")
c_error = hex_to_rgb(lookup("error"), "255,180,171" if mode == "dark" else "186,26,26")

kde_content = f"""[KDE]
contrast=4

[General]
ColorScheme=theme
Name=theme

[ColorEffects:Disabled]
Color={c_on_surface_variant}
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color={c_outline}
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0

[Colors:Button]
BackgroundAlternate={c_surface}
BackgroundNormal={c_surface}
DecorationFocus={c_primary}
DecorationHover={c_primary}
ForegroundActive={c_on_surface}
ForegroundInactive={c_on_surface_variant}
ForegroundLink={c_tertiary}
ForegroundNegative={c_error}
ForegroundNeutral={c_secondary}
ForegroundNormal={c_on_surface}
ForegroundPositive={c_tertiary}
ForegroundVisited={c_secondary}

[Colors:Complementary]
BackgroundAlternate={c_surface_container}
BackgroundNormal={c_surface}
DecorationFocus={c_primary}
DecorationHover={c_primary}
ForegroundActive={c_on_surface}
ForegroundInactive={c_on_surface_variant}
ForegroundLink={c_tertiary}
ForegroundNegative={c_error}
ForegroundNeutral={c_secondary}
ForegroundNormal={c_on_surface}
ForegroundPositive={c_tertiary}
ForegroundVisited={c_secondary}

[Colors:Header]
BackgroundAlternate={c_surface}
BackgroundNormal={c_surface}
DecorationFocus={c_primary}
DecorationHover={c_primary}
ForegroundActive={c_on_surface}
ForegroundInactive={c_on_surface_variant}
ForegroundLink={c_tertiary}
ForegroundNegative={c_error}
ForegroundNeutral={c_secondary}
ForegroundNormal={c_on_surface}
ForegroundPositive={c_tertiary}
ForegroundVisited={c_secondary}

[Colors:Header][Inactive]
BackgroundAlternate={c_surface}
BackgroundNormal={c_surface}
DecorationFocus={c_primary}
DecorationHover={c_primary}
ForegroundActive={c_on_surface}
ForegroundInactive={c_on_surface_variant}
ForegroundLink={c_tertiary}
ForegroundNegative={c_error}
ForegroundNeutral={c_secondary}
ForegroundNormal={c_on_surface}
ForegroundPositive={c_tertiary}
ForegroundVisited={c_secondary}

[Colors:Selection]
BackgroundAlternate={c_primary}
BackgroundNormal={c_primary}
DecorationFocus={c_primary}
DecorationHover={c_primary}
ForegroundActive={c_on_surface}
ForegroundInactive={c_on_surface_variant}
ForegroundLink={c_tertiary}
ForegroundNegative={c_error}
ForegroundNeutral={c_secondary}
ForegroundNormal={c_on_surface}
ForegroundPositive={c_tertiary}
ForegroundVisited={c_secondary}

[Colors:Tooltip]
BackgroundAlternate={c_surface}
BackgroundNormal={c_surface}
DecorationFocus={c_primary}
DecorationHover={c_primary}
ForegroundActive={c_on_surface}
ForegroundInactive={c_on_surface_variant}
ForegroundLink={c_tertiary}
ForegroundNegative={c_error}
ForegroundNeutral={c_secondary}
ForegroundNormal={c_on_surface}
ForegroundPositive={c_tertiary}
ForegroundVisited={c_secondary}

[Colors:View]
BackgroundAlternate={c_surface_container_low}
BackgroundNormal={c_surface}
DecorationFocus={c_primary}
DecorationHover={c_primary}
ForegroundActive={c_on_surface}
ForegroundInactive={c_on_surface_variant}
ForegroundLink={c_tertiary}
ForegroundNegative={c_error}
ForegroundNeutral={c_secondary}
ForegroundNormal={c_on_surface}
ForegroundPositive={c_tertiary}
ForegroundVisited={c_secondary}

[Colors:Window]
BackgroundAlternate={c_surface}
BackgroundNormal={c_surface}
DecorationFocus={c_primary}
DecorationHover={c_primary}
ForegroundActive={c_on_surface}
ForegroundInactive={c_on_surface_variant}
ForegroundLink={c_tertiary}
ForegroundNegative={c_error}
ForegroundNeutral={c_secondary}
ForegroundNormal={c_on_surface}
ForegroundPositive={c_tertiary}
ForegroundVisited={c_secondary}

[WM]
activeBackground={c_surface}
activeBlend={c_on_surface}
activeForeground={c_on_surface}
inactiveBackground={c_surface}
inactiveBlend={c_on_surface_variant}
inactiveForeground={c_on_surface_variant}
"""

(stage_dir / "theme.colors").write_text(kde_content, encoding="utf-8")
(stage_dir / ".module-ok").write_text("ok\n", encoding="utf-8")
