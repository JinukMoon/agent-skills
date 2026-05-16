# agent-skills

AI agent skills for computational chemistry and materials science research.

Built for [Claude Code](https://claude.ai/code), but the core scripts are LLM-agnostic Python.

## Available Skills

| Skill | Description |
|-------|-------------|
| [structure-visualizer](skills/structure-visualizer/) | Render atomic/molecular structures as publication-quality PNG (OVITO Tachyon / POV-Ray) |

## Installation

### Claude Code

```bash
/plugin marketplace add JinukMoon/agent-skills
/plugin install structure-visualizer@JinukMoon-agent-skills
```

### Manual

Copy the skill folder into your `~/.claude/skills/` directory:

```bash
git clone https://github.com/JinukMoon/agent-skills.git
cp -r agent-skills/skills/structure-visualizer ~/.claude/skills/
```

## Python Dependencies

Each skill lists its own dependencies in its SKILL.md. For structure-visualizer:

```bash
pip install ovito ase Pillow
```

## License

MIT
