#!/usr/bin/env python3
import os, shutil, subprocess, sys
from pathlib import Path

stage_dir = Path(os.environ.get("THEMY_STAGE_DIR", "/tmp/themy-stage"))
config_home = Path(os.environ.get("THEMY_XDG_CONFIG_HOME") or os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))

def run_optional(cmd):
    """Run an optional command safely without crashing if missing or failing."""
    if not cmd or not shutil.which(cmd[0]):
        return
    try:
        subprocess.run(cmd, capture_output=True, check=False)
    except Exception:
        pass

# 1. Update qt5ct / qt6ct
themy_conf = stage_dir / "themy.conf"
if themy_conf.exists():
    for qt in ("qt5ct", "qt6ct"):
        cfg_file = config_home / qt / f"{qt}.conf"
        colors_dir = config_home / qt / "colors"
        if shutil.which(qt) or cfg_file.exists():
            colors_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(themy_conf, colors_dir / "themy.conf")
            
            # Update [Appearance] in qt.conf
            lines = cfg_file.read_text(encoding="utf-8").splitlines() if cfg_file.exists() else []
            try:
                i = next(idx for idx, l in enumerate(lines) if l.strip() == "[Appearance]")
            except StopIteration:
                if lines and lines[-1].strip(): lines.append("")
                lines.append("[Appearance]")
                i = len(lines) - 1
            
            end = next((j for j in range(i+1, len(lines)) if lines[j].startswith("[")), len(lines))
            body = lines[i+1:end]
            for k, v in [("custom_palette", "true"), ("color_scheme_path", str(colors_dir / "themy.conf"))]:
                for j, l in enumerate(body):
                    if l.startswith(k + "="):
                        body[j] = f"{k}={v}"
                        break
                else:
                    body.append(f"{k}={v}")
            cfg_file.parent.mkdir(parents=True, exist_ok=True)
            cfg_file.write_text("\n".join(lines[:i+1] + body + lines[end:]) + "\n", encoding="utf-8")

# 2. Install single theme.colors to KDE / Dolphin color-schemes directory
scheme_dir = data_home / "color-schemes"
scheme_dir.mkdir(parents=True, exist_ok=True)

themy_colors = stage_dir / "theme.colors"
if not themy_colors.exists():
    for alt in ("Themy.colors", "themyMatugen.colors"):
        if (stage_dir / alt).exists():
            themy_colors = stage_dir / alt
            break

if themy_colors.exists():
    dest_file = scheme_dir / "theme.colors"
    shutil.copy2(themy_colors, dest_file)
    # Remove older redundant duplicates so directory stays completely clean
    for legacy in ("Themy.colors", "themyMatugen.colors", "themy.colors"):
        legacy_path = scheme_dir / legacy
        if legacy_path.exists() and legacy_path.name != "theme.colors":
            try:
                legacy_path.unlink()
            except OSError:
                pass
    print(f"[qt] Exported KDE color scheme to {dest_file}")

# 3. Update ~/.config/kdeglobals so Dolphin immediately loads the scheme
kdeglobals = config_home / "kdeglobals"
lines = kdeglobals.read_text(encoding="utf-8").splitlines() if kdeglobals.exists() else []
try:
    i = next(idx for idx, l in enumerate(lines) if l.strip() == "[General]")
except StopIteration:
    if lines and lines[-1].strip(): lines.append("")
    lines.append("[General]")
    i = len(lines) - 1

end = next((j for j in range(i+1, len(lines)) if lines[j].startswith("[")), len(lines))
body = lines[i+1:end]
found = False
for j, l in enumerate(body):
    if l.startswith("ColorScheme="):
        body[j] = "ColorScheme=theme"
        found = True
        break
if not found:
    body.append("ColorScheme=theme")

kdeglobals.parent.mkdir(parents=True, exist_ok=True)
kdeglobals.write_text("\n".join(lines[:i+1] + body + lines[end:]) + "\n", encoding="utf-8")
print(f"[qt] Set ColorScheme=theme in {kdeglobals}")

# 4. Environment variables
envdir = config_home / "environment.d"
envdir.mkdir(parents=True, exist_ok=True)
envfile = envdir / "themy.conf"

qt5_active = bool(shutil.which("qt5ct"))
qt6_active = bool(shutil.which("qt6ct"))
env_lines = ["# Themy Qt backend selection"]
if qt5_active:
    env_lines.append("QT_QPA_PLATFORMTHEME=qt5ct")
    os.environ["QT_QPA_PLATFORMTHEME"] = "qt5ct"
if qt6_active:
    env_lines.append("QT_QPA_PLATFORMTHEME_QT6=qt6ct")
    os.environ["QT_QPA_PLATFORMTHEME_QT6"] = "qt6ct"
envfile.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

if qt5_active or qt6_active:
    run_optional(["systemctl", "--user", "import-environment", "QT_QPA_PLATFORMTHEME", "QT_QPA_PLATFORMTHEME_QT6"])
    run_optional(["dbus-update-activation-environment", "--systemd", "QT_QPA_PLATFORMTHEME", "QT_QPA_PLATFORMTHEME_QT6"])
