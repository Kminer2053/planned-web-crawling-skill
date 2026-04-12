#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TOOLKIT_SRC = ROOT / "adaptive-web-research"
ADAPTERS_ROOT = ROOT / "agent-adapters"


AGENT_FILES = {
    "claude": [(".claude/commands/adaptive-web-research.md", "claude/.claude/commands/adaptive-web-research.md")],
    "cursor": [(".cursor/rules/adaptive-web-research.mdc", "cursor/.cursor/rules/adaptive-web-research.mdc")],
    "opencode": [(".opencode/commands/adaptive-web-research.md", "opencode/.opencode/commands/adaptive-web-research.md")],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the adaptive-web-research toolkit into another agent environment.")
    parser.add_argument("--agent", required=True, choices=["claude", "cursor", "opencode", "generic", "antigravity"])
    parser.add_argument("--target", required=True, help="Target project directory")
    parser.add_argument("--toolkit-dir", default=".agent-skills/adaptive-web-research", help="Relative install path for the toolkit")
    parser.add_argument("--force", action="store_true", help="Overwrite existing adapter files")
    parser.add_argument("--skip-toolkit", action="store_true", help="Do not copy the toolkit folder")
    return parser.parse_args()


def copy_tree(src: Path, dst: Path, *, force: bool) -> None:
    if dst.exists():
        if force:
            shutil.rmtree(dst)
        else:
            return
    shutil.copytree(src, dst, dirs_exist_ok=not force)


def copy_file(src: Path, dst: Path, *, force: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        raise FileExistsError(f"Destination already exists: {dst}")
    shutil.copy2(src, dst)


def install_generic(target_root: Path, *, force: bool) -> list[Path]:
    src = ADAPTERS_ROOT / "generic/AGENTS.md"
    dest = target_root / "AGENTS.md"
    fallback = target_root / "AGENTS.adaptive-web-research.md"
    if dest.exists() and not force:
        copy_file(src, fallback, force=force)
        return [fallback]
    copy_file(src, dest, force=force)
    return [dest]


def install_agent_files(agent: str, target_root: Path, *, force: bool) -> list[Path]:
    if agent in {"generic", "antigravity"}:
        return install_generic(target_root, force=force)

    installed: list[Path] = []
    for relative_dest, relative_src in AGENT_FILES[agent]:
        src = ADAPTERS_ROOT / relative_src
        dst = target_root / relative_dest
        copy_file(src, dst, force=force)
        installed.append(dst)
    return installed


def main() -> int:
    args = parse_args()
    target_root = Path(args.target).expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    installed_paths: list[Path] = []
    if not args.skip_toolkit:
        toolkit_dest = target_root / args.toolkit_dir
        copy_tree(TOOLKIT_SRC, toolkit_dest, force=args.force)
        installed_paths.append(toolkit_dest)

    installed_paths.extend(install_agent_files(args.agent, target_root, force=args.force))

    print("Installed:")
    for path in installed_paths:
        print(f"- {path}")

    if args.agent == "claude":
        print("Run this in Claude Code: /adaptive-web-research <task>")
    elif args.agent == "opencode":
        print("Run this in OpenCode: /adaptive-web-research <task>")
    elif args.agent == "cursor":
        print("Open Cursor Agent and invoke the project rule or mention the crawling workflow.")
    elif args.agent in {"generic", "antigravity"}:
        print("If the target project already had AGENTS.md, review AGENTS.adaptive-web-research.md and merge it manually.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
