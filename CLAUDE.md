# CLAUDE.md

## What this repo is

This repository contains AI agent skills for Claude Code. Each skill is a self-contained folder under `skills/` with a `SKILL.md` and optional scripts.

## How to install skills from this repo

When the user asks to install skills from this repository:

1. Copy the desired skill folders from `skills/` into `~/.claude/skills/`
2. Each skill folder should be copied as-is (preserving its directory structure)

Example:
```bash
cp -r skills/structure-visualizer ~/.claude/skills/
```

To install ALL skills:
```bash
cp -r skills/* ~/.claude/skills/
```

3. After copying, check the skill's `SKILL.md` for any Python dependencies that need to be installed (e.g., `pip install ovito ase Pillow`).

## Skill list

| Skill | Description |
|-------|-------------|
| `structure-visualizer` | Render atomic/molecular structures as publication-quality PNG using OVITO Tachyon |
| `pptx-to-pdf` | Convert PPTX to PDF by rasterizing each slide as a 7K image — renders identically on any machine regardless of installed fonts |
| `paper-reading` | Deep-read a scientific paper PDF and produce full Korean translation + critical review |
| `pre-proof` | Final proofreading / anomaly hunt for manuscripts before submission (10-pass checker) |
