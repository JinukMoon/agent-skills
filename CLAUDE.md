# CLAUDE.md

## What this repo is

This repository contains AI agent skills for Claude Code. Skills are grouped by category under `skills/`:

- `skills/research/` — research workflow skills (computational chemistry, papers, slides)
- `skills/life/` — everyday-life automation skills

Each skill is a self-contained folder with a `SKILL.md` and optional scripts.

## How to install skills from this repo

When the user asks to install skills from this repository:

1. Copy the desired skill folders into `~/.claude/skills/` (flat — category folders are for organizing this repo only)
2. Each skill folder should be copied as-is (preserving its directory structure)

Example:
```bash
cp -r skills/research/structure-visualizer ~/.claude/skills/
```

To install ALL skills:
```bash
cp -r skills/research/* skills/life/* ~/.claude/skills/
```

3. After copying, check the skill's `SKILL.md` for Python dependencies and **first-run setup**: every skill asks the user once for any personal settings it needs (paths, author info, companions, conda env) and stores them in local files (e.g. `config.local.json`, `authors.json`, `members.local.json`) next to the installed SKILL.md. These files stay on the user's machine and must never be committed.

## Skill list

### research/

| Skill | Description |
|-------|-------------|
| `structure-visualizer` | Render atomic/molecular structures as publication-quality PNG using OVITO Tachyon |
| `pptx-to-pdf` | Convert PPTX to PDF by rasterizing each slide as a 7K image — renders identically on any machine regardless of installed fonts |
| `paper-reading` | Deep-read a scientific paper PDF and produce full Korean translation + critical review |
| `pre-proof` | Final proofreading / anomaly hunt for manuscripts before submission (10-pass checker) |
| `scientific-paper-coach` | Review or write scientific manuscripts against a 200+-item academic-writing checklist — PASS/FAIL review mode + checklist-first write mode |

### life/

| Skill | Description |
|-------|-------------|
| `snu-tennis-reserve` | Auto-grab SNU tennis court reservations the moment they open (Monday 9:30 KST) via Playwright |
| `snu-etl-video-downloader` | Download SNU eTL/LCMS lecture videos by content_id (parallel, with failure detection) |
| `whisper-transcribe` | Transcribe lecture videos to text with OpenAI Whisper (ffmpeg extraction + GPU pipeline, battle-tested pitfalls included) |
