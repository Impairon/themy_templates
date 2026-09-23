# Themy Custom Module Template

This directory contains a complete example for a *themy template*

---

## File Structure

```text
~/.config/themy/modules/<module-name>/
├── module.conf          # Module metadata (name, ID, version, description)
├── render               # Executable: transforms templates using active palette
├── apply                # Executable: installs generated files into target locations
├── backup               # Executable: backs up current user config before applying
├── restore              # Executable: rolls back files if apply fails
├── doctor               # Executable: checks prerequisites for 'themy doctor'
└── templates/           # Configuration templates with color placeholders
    ├── dark.conf
    └── light.conf
```

---

## The Module Example

When the user runs `themy apply` or changes wallpapers:

1. **`doctor`** *(optional)*: Checked during `themy doctor` to verify system dependencies.
2. **`backup`**: Called before changes. Saves existing target configs into `$THEMY_BACKUP_DIR`.
3. **`render`**: Themy sets `$THEMY_PALETTE` and `$THEMY_STAGE_DIR`. The hook parses the template and writes output files to `$THEMY_STAGE_DIR`. On success, it writes `ok` to `$THEMY_STAGE_DIR/.module-ok`.
4. **`apply`**: Copies files from `$THEMY_STAGE_DIR` into target destinations (e.g. `~/.config/<app>/`).
5. **`restore`**: If any step in the pipeline fails, Themy invokes `restore` to revert every target file back to its pre-apply state.

---

## Standard Environment Variables

| Variable | Purpose | Example |
| :--- | :--- | :--- |
| `THEMY_STAGE_DIR` | Temporary scratch dir for rendered output | `/tmp/themy-stage` |
| `THEMY_PALETTE` | Full JSON path of active Matugen palette | `~/.config/themy/cache/palettes/...json` |
| `THEMY_MODE` | Active theme mode | `dark` or `light` |
| `THEMY_MODULE_DIR` | Root folder of this specific module | `~/.config/themy/modules/example` |
| `THEMY_BACKUP_DIR` | Temp directory for rollback snapshots | `/tmp/themy-backup-XXXXXX` |
| `THEMY_XDG_CONFIG_HOME` | Target user configuration directory | `~/.config` |
| `XDG_DATA_HOME` | Target user data directory | `~/.local/share` |

---

## Available Palette Tokens

In templates, you can use standard Matugen tokens:

- `{{ colors.surface.default.hex }}` or `{{ surface }}`: Base background
- `{{ colors.on_surface.default.hex }}` or `{{ on_surface }}`: Primary text / foreground
- `{{ colors.primary.default.hex }}` or `{{ primary }}`: Main theme accent
- `{{ colors.secondary.default.hex }}` or `{{ secondary }}`: Secondary accent
- `{{ colors.tertiary.default.hex }}` or `{{ tertiary }}`: Highlight / badge color
- `{{ colors.outline.default.hex }}` or `{{ outline }}`: Borders and separators
- `{{ colors.error.default.hex }}` or `{{ error }}`: Warning / error state

---

## Testing Your New Module

```bash
# 1. Enable your module
themy module enable <module-name>

# 2. Check diagnostic health
themy doctor

# 3. Apply the theme
themy apply
```
