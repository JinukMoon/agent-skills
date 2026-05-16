# agent-skills

AI agent skills for computational chemistry and materials science research.

Built for [Claude Code](https://claude.ai/code), but the core scripts are LLM-agnostic Python.

## Installation

Just tell Claude Code:

> "Install all skills from https://github.com/JinukMoon/agent-skills into my skills."

Claude Code will clone this repo and copy the skills to `~/.claude/skills/`.

Each skill's `SKILL.md` contains its own setup guide (Python dependencies, renderer selection, etc.).

## Available Skills

| Skill | Description |
|-------|-------------|
| [structure-visualizer](skills/structure-visualizer/) | Render atomic/molecular structures as publication-quality PNG (OVITO Tachyon / POV-Ray) |

## Examples (structure-visualizer)

### Molecules

Rendered with OVITO Tachyon, transparent background:

| H2O | NH3 |
|:---:|:---:|
| ![H2O](skills/structure-visualizer/examples/01_H2O_transparent.png) | ![NH3](skills/structure-visualizer/examples/02_NH3_transparent.png) |

| CH4 | CO2 |
|:---:|:---:|
| ![CH4](skills/structure-visualizer/examples/03_CH4_transparent.png) | ![CO2](skills/structure-visualizer/examples/04_CO2_transparent.png) |

| C2H6 | C2H4 |
|:---:|:---:|
| ![C2H6](skills/structure-visualizer/examples/05_C2H6_transparent.png) | ![C2H4](skills/structure-visualizer/examples/06_C2H4_transparent.png) |

| C6H6 | CH3OH |
|:---:|:---:|
| ![C6H6](skills/structure-visualizer/examples/07_C6H6_transparent.png) | ![CH3OH](skills/structure-visualizer/examples/08_CH3OH_transparent.png) |

| HCOOH | CH3CHO |
|:---:|:---:|
| ![HCOOH](skills/structure-visualizer/examples/09_HCOOH_transparent.png) | ![CH3CHO](skills/structure-visualizer/examples/10_CH3CHO_transparent.png) |

### Slabs & Surfaces

| Ru55O / graphene | Ru55O20 / graphene |
|:---:|:---:|
| ![Ru55O](skills/structure-visualizer/examples/11_Ru55O_on_graphene.png) | ![Ru55O20](skills/structure-visualizer/examples/12_Ru55O20_on_graphene.png) |

| Ru147O38 / graphene | Ru309O52 / graphene |
|:---:|:---:|
| ![Ru147O38](skills/structure-visualizer/examples/17_Ru147O38_on_graphene.png) | ![Ru309O52](skills/structure-visualizer/examples/18_Ru309O52_on_graphene.png) |

| CoOOH(001) + N | CoOOH(m101) + NO3 |
|:---:|:---:|
| ![CoOOH_N](skills/structure-visualizer/examples/13_CoOOH_001_N_adsorbate.png) | ![CoOOH_NO3](skills/structure-visualizer/examples/14_CoOOH_m101_NO3_adsorbate.png) |

| ZnO + water | Co2MnO4 + water |
|:---:|:---:|
| ![ZnO_water](skills/structure-visualizer/examples/15_ZnO_water_interface.png) | ![Co2MnO4_water](skills/structure-visualizer/examples/16_Co2MnO4_water_interface.png) |

## License

MIT
