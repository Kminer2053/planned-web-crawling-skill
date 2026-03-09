#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from crawlkit import Fetcher, RequestSpec, probe_record, write_snapshot

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute a JSON web collection plan.")
    parser.add_argument("plan_path", help="Path to a JSON plan file")
    parser.add_argument("--output-dir", required=True, help="Directory for saved artifacts")
    return parser.parse_args()


def load_plan(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def run_plan(plan: dict[str, Any], *, output_dir: str) -> dict[str, Any]:
    fetcher = Fetcher(user_agent=plan.get("user_agent", "adaptive-web-research/0.1"))
    context: dict[str, Any] = {}
    results: list[dict[str, Any]] = []
    for index, step in enumerate(plan.get("steps", []), start=1):
        step_id = step.get("id") or f"step-{index}"
        step_type = step.get("type")
        if step_type == "request":
            result = run_request_step(fetcher, step, output_dir=output_dir, context=context, step_id=step_id)
        elif step_type == "paginate":
            result = run_paginate_step(fetcher, step, output_dir=output_dir, context=context, step_id=step_id)
        elif step_type == "follow_links":
            result = run_follow_links_step(fetcher, step, output_dir=output_dir, context=context, step_id=step_id)
        else:
            raise ValueError(f"Unsupported step type: {step_type}")
        context[step_id] = result
        results.append(result)
    return {"plan_name": plan.get("name"), "results": results}


def run_request_step(fetcher: Fetcher, step: dict[str, Any], *, output_dir: str, context: dict[str, Any], step_id: str) -> dict[str, Any]:
    spec = RequestSpec(
        url=render_value(step["url"], context),
        method=step.get("method", "GET"),
        headers=render_mapping(step.get("headers", {}), context),
        data=render_value(step.get("data"), context),
        timeout=int(step.get("timeout", 30)),
    )
    record = fetcher.fetch(spec)
    probe = probe_record(record)
    saved = write_snapshot(record, output_dir, step_id, include_body=step.get("save_body", True))
    return {"id": step_id, "type": "request", "probe": probe, "saved": saved}


def run_paginate_step(fetcher: Fetcher, step: dict[str, Any], *, output_dir: str, context: dict[str, Any], step_id: str) -> dict[str, Any]:
    start_page = int(step.get("start_page", 1))
    max_pages = int(step.get("max_pages", 1))
    stop_regex = step.get("stop_when_text_regex")
    page_results = []
    for page in range(start_page, start_page + max_pages):
        url_template = step["url_template"]
        url = render_value(url_template, context, page=page)
        request_step = {
            "url": url,
            "method": step.get("method", "GET"),
            "headers": step.get("headers", {}),
            "data": step.get("data"),
            "timeout": step.get("timeout", 30),
            "save_body": step.get("save_body", True),
        }
        result = run_request_step(fetcher, request_step, output_dir=output_dir, context=context, step_id=f"{step_id}-page-{page}")
        page_results.append(result)
        sample_text = json.dumps(result["probe"], ensure_ascii=False)
        if stop_regex and re.search(stop_regex, sample_text):
            break
    return {"id": step_id, "type": "paginate", "pages": page_results}


def run_follow_links_step(fetcher: Fetcher, step: dict[str, Any], *, output_dir: str, context: dict[str, Any], step_id: str) -> dict[str, Any]:
    if BeautifulSoup is None:
        raise RuntimeError("beautifulsoup4 is required for follow_links steps.")
    source_id = step["from"]
    source = context[source_id]
    body_path = source["saved"]["body_path"]
    if not body_path:
        raise ValueError(f"Step {source_id} does not have a saved HTML body.")
    html = Path(body_path).read_text(encoding="utf-8", errors="replace")
    base_url = source["probe"]["final_url"]
    soup = BeautifulSoup(html, "html.parser")
    selector = step.get("selector", "a[href]")
    text_regex = step.get("text_regex")
    href_regex = step.get("href_regex")
    limit = int(step.get("limit", 5))
    matches = []
    for link in soup.select(selector):
        href = (link.get("href") or "").strip()
        text = " ".join(link.get_text(" ", strip=True).split())
        absolute = urljoin(base_url, href)
        if text_regex and not re.search(text_regex, text):
            continue
        if href_regex and not re.search(href_regex, absolute):
            continue
        matches.append({"text": text, "href": absolute})
        if len(matches) >= limit:
            break
    fetched = []
    for position, match in enumerate(matches, start=1):
        request_step = {
            "url": match["href"],
            "method": step.get("method", "GET"),
            "headers": step.get("headers", {}),
            "timeout": step.get("timeout", 30),
            "save_body": step.get("save_body", True),
        }
        result = run_request_step(fetcher, request_step, output_dir=output_dir, context=context, step_id=f"{step_id}-link-{position}")
        result["match"] = match
        fetched.append(result)
    return {"id": step_id, "type": "follow_links", "matches": matches, "fetched": fetched}


def render_mapping(value: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    return {key: render_value(item, context) for key, item in value.items()}


def render_value(value: Any, context: dict[str, Any], **extra: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        combined = {"context": context, **extra}
        return value.format_map(SafeDict(combined))
    if isinstance(value, dict):
        return {key: render_value(item, context, **extra) for key, item in value.items()}
    if isinstance(value, list):
        return [render_value(item, context, **extra) for item in value]
    return value


class SafeDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def main() -> int:
    args = parse_args()
    plan = load_plan(args.plan_path)
    result = run_plan(plan, output_dir=args.output_dir)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    summary_path = Path(args.output_dir) / "plan-result.json"
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"summary_path": str(summary_path), "steps": len(result["results"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
