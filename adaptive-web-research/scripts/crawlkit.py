#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener
import http.cookiejar

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None


DEFAULT_USER_AGENT = "adaptive-web-research/0.1"


@dataclass
class RequestSpec:
    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    data: Optional[dict[str, Any] | list[Any] | str] = None
    timeout: int = 30


@dataclass
class ResponseRecord:
    url: str
    final_url: str
    status: int
    headers: dict[str, str]
    body: bytes
    fetched_at: str
    content_type: Optional[str]

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.body).hexdigest()

    def text(self) -> str:
        charset = "utf-8"
        if self.content_type:
            match = re.search(r"charset=([^\s;]+)", self.content_type, re.I)
            if match:
                charset = match.group(1).strip("\"'")
        return self.body.decode(charset, errors="replace")


class Fetcher:
    def __init__(self, *, user_agent: str = DEFAULT_USER_AGENT) -> None:
        self.user_agent = user_agent
        self._opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def fetch(self, spec: RequestSpec) -> ResponseRecord:
        parsed = urlparse(spec.url)
        if parsed.scheme in {"", "file"}:
            return self._read_local_file(spec.url)

        headers = {"User-Agent": self.user_agent, **spec.headers}
        body: Optional[bytes] = None
        if spec.data is not None:
            if isinstance(spec.data, dict):
                body = urlencode({k: "" if v is None else str(v) for k, v in spec.data.items()}).encode("utf-8")
                headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
            elif isinstance(spec.data, list):
                body = json.dumps(spec.data, ensure_ascii=False).encode("utf-8")
                headers.setdefault("Content-Type", "application/json")
            elif isinstance(spec.data, str):
                body = spec.data.encode("utf-8")
            else:
                raise TypeError(f"Unsupported request data type: {type(spec.data)!r}")

        request = Request(spec.url, headers=headers, data=body, method=spec.method.upper())
        with self._opener.open(request, timeout=spec.timeout) as response:
            raw_headers = {key: value for key, value in response.headers.items()}
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset()
            if charset:
                content_type = f"{content_type}; charset={charset}"
            return ResponseRecord(
                url=spec.url,
                final_url=response.geturl(),
                status=getattr(response, "status", 200),
                headers=raw_headers,
                body=response.read(),
                fetched_at=datetime.now(timezone.utc).isoformat(),
                content_type=content_type,
            )

    def _read_local_file(self, url: str) -> ResponseRecord:
        if url.startswith("file://"):
            path = Path(urlparse(url).path)
        else:
            path = Path(url)
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return ResponseRecord(
            url=str(path),
            final_url=str(path.resolve()),
            status=200,
            headers={"Content-Length": str(len(body))},
            body=body,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            content_type=content_type,
        )


def sniff_kind(record: ResponseRecord) -> str:
    content_type = (record.content_type or "").lower()
    final_url = record.final_url.lower()
    if "json" in content_type or final_url.endswith(".json"):
        return "json"
    if "html" in content_type or final_url.endswith((".html", ".htm")):
        return "html"
    if "pdf" in content_type or final_url.endswith(".pdf"):
        return "pdf"
    if content_type.startswith("text/"):
        return "text"
    return "binary"


def probe_record(record: ResponseRecord, *, link_limit: int = 20) -> dict[str, Any]:
    kind = sniff_kind(record)
    payload: dict[str, Any] = {
        "kind": kind,
        "status": record.status,
        "url": record.url,
        "final_url": record.final_url,
        "content_type": record.content_type,
        "bytes": len(record.body),
        "sha256": record.sha256,
        "fetched_at": record.fetched_at,
    }
    if kind == "html":
        payload["html"] = probe_html(record.text(), record.final_url, link_limit=link_limit)
    elif kind == "json":
        payload["json"] = probe_json(record.text())
    elif kind == "pdf":
        payload["pdf"] = probe_pdf(record.body)
    elif kind == "text":
        payload["text"] = {"sample": record.text()[:1000]}
    return payload


def probe_html(html: str, base_url: str, *, link_limit: int = 20) -> dict[str, Any]:
    if BeautifulSoup is None:
        raise RuntimeError("beautifulsoup4 is required for HTML probing.")
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for node in soup.select("a[href]"):
        href = (node.get("href") or "").strip()
        text = normalize_space(node.get_text(" ", strip=True))
        links.append(
            {
                "text": text[:160],
                "href": urljoin(base_url, href),
                "raw_href": href,
            }
        )
        if len(links) >= link_limit:
            break
    forms = []
    for form in soup.select("form"):
        form_fields = []
        for field in form.select("input[name], select[name], textarea[name]"):
            tag_name = field.name
            field_type = field.get("type") if tag_name == "input" else tag_name
            form_fields.append(
                {
                    "name": field.get("name"),
                    "type": field_type or tag_name,
                    "value": field.get("value"),
                }
            )
        forms.append(
            {
                "action": urljoin(base_url, form.get("action") or ""),
                "method": (form.get("method") or "GET").upper(),
                "fields": form_fields[:20],
            }
        )
    json_ld = []
    for script in soup.select('script[type="application/ld+json"]'):
        snippet = normalize_space(script.get_text(" ", strip=True))
        if snippet:
            json_ld.append(snippet[:400])
    table_summaries = []
    for table in soup.select("table"):
        rows = table.select("tr")
        header_cells = [normalize_space(cell.get_text(" ", strip=True)) for cell in table.select("th")]
        table_summaries.append(
            {
                "rows": len(rows),
                "headers": header_cells[:10],
            }
        )
    text_sample = normalize_space(soup.get_text(" ", strip=True))[:1200]
    return {
        "title": normalize_space(soup.title.get_text(" ", strip=True)) if soup.title else None,
        "meta_description": read_meta_description(soup),
        "links": links,
        "forms": forms,
        "tables": table_summaries[:10],
        "table_count": len(table_summaries),
        "json_ld_count": len(json_ld),
        "json_ld_samples": json_ld[:5],
        "pagination_candidates": detect_pagination_links(links),
        "text_sample": text_sample,
    }


def probe_json(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if isinstance(data, dict):
        summary = {
            "top_level": "object",
            "keys": list(data.keys())[:30],
        }
        list_counts = {}
        for key, value in data.items():
            if isinstance(value, list):
                list_counts[key] = len(value)
        if list_counts:
            summary["list_counts"] = list_counts
        return summary
    if isinstance(data, list):
        sample_keys: list[str] = []
        if data and isinstance(data[0], dict):
            sample_keys = list(data[0].keys())[:30]
        return {
            "top_level": "array",
            "items": len(data),
            "sample_keys": sample_keys,
        }
    return {
        "top_level": type(data).__name__,
        "value_preview": repr(data)[:200],
    }


def probe_pdf(body: bytes) -> dict[str, Any]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return {"warning": "Install pypdf to inspect PDFs in detail."}
    from io import BytesIO

    reader = PdfReader(BytesIO(body))
    sample = ""
    if reader.pages:
        try:
            sample = normalize_space(reader.pages[0].extract_text() or "")[:1000]
        except Exception:
            sample = ""
    return {
        "pages": len(reader.pages),
        "text_sample": sample,
    }


def read_meta_description(soup: Any) -> Optional[str]:
    tag = soup.select_one('meta[name="description"], meta[property="og:description"]')
    if not tag:
        return None
    content = tag.get("content")
    return normalize_space(content) if content else None


def detect_pagination_links(links: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates = []
    for item in links:
        text = (item.get("text") or "").lower()
        href = item.get("href") or ""
        if re.search(r"\b(next|more|page|older|다음|더보기)\b", text):
            candidates.append(item)
            continue
        parsed = urlparse(href)
        query_keys = {key for key, _ in parse_qsl(parsed.query)}
        if {"page", "p", "offset"} & query_keys:
            candidates.append(item)
    return candidates[:10]


def write_snapshot(record: ResponseRecord, out_dir: str | Path, name: str, *, include_body: bool = True) -> dict[str, str]:
    output_root = Path(out_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "snapshot"
    metadata_path = output_root / f"{safe_name}.json"
    extension = suffix_for_record(record)
    body_path = output_root / f"{safe_name}{extension}"
    metadata = {
        "url": record.url,
        "final_url": record.final_url,
        "status": record.status,
        "headers": record.headers,
        "content_type": record.content_type,
        "fetched_at": record.fetched_at,
        "sha256": record.sha256,
        "body_path": str(body_path.name) if include_body else None,
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    if include_body:
        body_path.write_bytes(record.body)
    return {
        "metadata_path": str(metadata_path),
        "body_path": str(body_path) if include_body else "",
    }


def suffix_for_record(record: ResponseRecord) -> str:
    kind = sniff_kind(record)
    if kind == "html":
        return ".html"
    if kind == "json":
        return ".json.body"
    if kind == "pdf":
        return ".pdf"
    if kind == "text":
        return ".txt"
    return ".bin"


def normalize_space(value: Optional[str]) -> str:
    return " ".join((value or "").split())


def parse_key_value(items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Expected key=value, got: {item}")
        key, value = item.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reusable fetch/probe helpers for adaptive web research.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe_parser = subparsers.add_parser("probe", help="Fetch a source and print a structural summary.")
    probe_parser.add_argument("url", help="HTTP(S), file://, or local file path")
    probe_parser.add_argument("--method", default="GET")
    probe_parser.add_argument("--header", action="append", default=[], help="Repeatable key=value header")
    probe_parser.add_argument("--data", action="append", default=[], help="Repeatable key=value form field")
    probe_parser.add_argument("--output-dir", help="Write fetched artifacts into this directory")
    probe_parser.add_argument("--save-body", action="store_true", help="Save raw response body")
    probe_parser.add_argument("--link-limit", type=int, default=20)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch a source and optionally persist it.")
    fetch_parser.add_argument("url", help="HTTP(S), file://, or local file path")
    fetch_parser.add_argument("--method", default="GET")
    fetch_parser.add_argument("--header", action="append", default=[], help="Repeatable key=value header")
    fetch_parser.add_argument("--data", action="append", default=[], help="Repeatable key=value form field")
    fetch_parser.add_argument("--output-dir", required=True)
    fetch_parser.add_argument("--name", default="snapshot")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fetcher = Fetcher()
    spec = RequestSpec(
        url=args.url,
        method=args.method,
        headers=parse_key_value(args.header),
        data=parse_key_value(args.data) if args.data else None,
    )
    record = fetcher.fetch(spec)
    if args.command == "fetch":
        result = write_snapshot(record, args.output_dir, args.name)
        print(json.dumps({"saved": result, "sha256": record.sha256}, ensure_ascii=False, indent=2))
        return 0

    payload = probe_record(record, link_limit=args.link_limit)
    if args.output_dir:
        payload["saved"] = write_snapshot(record, args.output_dir, "probe", include_body=args.save_body)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
