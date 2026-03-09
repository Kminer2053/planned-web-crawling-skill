# Adaptive Web Research Skill

Reusable Codex skill for research-oriented web crawling.

This repository provides a portable skill folder, `adaptive-web-research`, built from reusable patterns extracted from the Local100 crawler project. It is designed for cases where the agent should inspect an unfamiliar source first, plan collection steps, and save reproducible evidence while working across HTML, JSON, PDFs, forms, cookies, and simple pagination.

## Contents

- `adaptive-web-research/SKILL.md`
- `adaptive-web-research/scripts/crawlkit.py`
- `adaptive-web-research/scripts/run_collection_plan.py`
- `adaptive-web-research/references/`

## Install As A Local Skill

Clone this repository or download it, then copy the skill folder into `~/.codex/skills`:

```bash
mkdir -p ~/.codex/skills
cp -R adaptive-web-research ~/.codex/skills/
```

Restart Codex after copying the folder.

## Install From GitHub

If you want to install from GitHub using Codex skill tooling, use the path to the skill folder inside this repository:

```bash
python3 /Users/hoonsbook/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo Kminer2053/adaptive-web-research-skill \
  --path adaptive-web-research
```

Restart Codex after installation.

## Example Prompt

```text
Use $adaptive-web-research to plan a Local100 crawl starting from https://rcda.or.kr/local100/vote/status.do, probe the source structure first, then propose the exact commands and a JSON collection plan.
```
