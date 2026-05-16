# agent-skills

AI agent skills for computational chemistry and materials science research.

Built for [Claude Code](https://claude.ai/code), but the core scripts are LLM-agnostic Python.

## Available Skills

| Skill | Description |
|-------|-------------|
| [structure-visualizer](skills/structure-visualizer/) | Render atomic/molecular structures as publication-quality PNG (OVITO Tachyon / POV-Ray) |

## Examples (structure-visualizer)

Rendered with OVITO Tachyon, transparent background:

| H2O | NH3 | CH4 | CO2 | C2H6 |
|:---:|:---:|:---:|:---:|:---:|
| ![H2O](skills/structure-visualizer/examples/01_H2O_transparent.png) | ![NH3](skills/structure-visualizer/examples/02_NH3_transparent.png) | ![CH4](skills/structure-visualizer/examples/03_CH4_transparent.png) | ![CO2](skills/structure-visualizer/examples/04_CO2_transparent.png) | ![C2H6](skills/structure-visualizer/examples/05_C2H6_transparent.png) |

| C2H4 | C6H6 | CH3OH | HCOOH | CH3CHO |
|:---:|:---:|:---:|:---:|:---:|
| ![C2H4](skills/structure-visualizer/examples/06_C2H4_transparent.png) | ![C6H6](skills/structure-visualizer/examples/07_C6H6_transparent.png) | ![CH3OH](skills/structure-visualizer/examples/08_CH3OH_transparent.png) | ![HCOOH](skills/structure-visualizer/examples/09_HCOOH_transparent.png) | ![CH3CHO](skills/structure-visualizer/examples/10_CH3CHO_transparent.png) |

## Installation

Just tell Claude Code:

> "https://github.com/JinukMoon/agent-skills 에서 structure-visualizer 스킬 설치해줘"

Claude Code will clone this repo and copy the skill to `~/.claude/skills/`.

Each skill's `SKILL.md` contains its own setup guide (Python dependencies, renderer selection, etc.).

## License

MIT
