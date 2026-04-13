#!/usr/bin/env python3

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from html import unescape
from pathlib import Path


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def build_opener(blog_id: str):
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ("User-Agent", USER_AGENT),
        ("Referer", f"https://blog.naver.com/PostList.naver?blogId={blog_id}&from=postList"),
    ]
    return opener


def fetch_text(opener, url: str) -> str:
    with opener.open(url, timeout=30) as resp:
        return resp.read().decode("utf-8", "ignore")


def fetch_json(opener, url: str):
    with opener.open(url, timeout=30) as resp:
        return json.load(resp)


def strip_tags(html: str) -> str:
    html = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?>.*?</style>", " ", html)
    html = re.sub(r"(?is)<noscript.*?>.*?</noscript>", " ", html)
    text = re.sub(r"(?is)<[^>]+>", "\n", html)
    text = unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_latest_cursor(html: str, blog_id: str):
    latest_log_no = None
    for match in re.finditer(
        rf'/PostView\.naver\?blogId={re.escape(blog_id)}&logNo=(\d+)', html
    ):
        latest_log_no = match.group(1)
        break

    if not latest_log_no:
        raise RuntimeError("Could not find latest logNo from the post list page.")

    publish_match = re.search(r'<span class="se_publishDate">([^<]+)</span>', html)
    published_raw = " ".join(publish_match.group(1).split()) if publish_match else ""

    if published_raw:
        latest_dt = datetime.strptime(published_raw, "%Y. %m. %d. %H:%M")
        latest_sort_ms = str(int(latest_dt.timestamp() * 1000))
    else:
        latest_sort_ms = str(int(time.time() * 1000))

    return latest_log_no, latest_sort_ms


def crawl_blog(blog_id: str, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    posts_dir = output_dir / "posts"
    raw_dir.mkdir(exist_ok=True)
    posts_dir.mkdir(exist_ok=True)

    opener = build_opener(blog_id)

    list_url = f"https://blog.naver.com/PostList.naver?blogId={blog_id}&from=postList"
    list_html = fetch_text(opener, list_url)
    latest_log_no, latest_sort_ms = parse_latest_cursor(list_html, blog_id)

    seen = {}
    page_cursor = (latest_log_no, latest_sort_ms)
    pages = []

    for _ in range(500):
        log_no, sort_date = page_cursor
        qs = urllib.parse.urlencode(
            {
                "blogId": blog_id,
                "logNo": log_no,
                "showPreviousPage": "true",
                "sortDateInMilli": sort_date,
            }
        )
        url = f"https://blog.naver.com/PostViewBottomTitleListAsync.naver?{qs}"
        data = fetch_json(opener, url)
        pages.append({"url": url, "response": data})
        if not data.get("success"):
            raise RuntimeError(f"List API failed: {url}")

        for item in data.get("postList") or []:
            log_no_value = str(item["logNo"])
            seen[log_no_value] = {
                "logNo": log_no_value,
                "title": urllib.parse.unquote_plus(item.get("filteredEncodedTitle", "")),
                "addDate": item.get("addDate", ""),
                "commentCount": item.get("commentCount", ""),
                "openType": item.get("openType"),
            }

        candidates = []
        if data.get("hasPreviousPage") and data.get("previousIndexLogNo") and data.get("previousIndexSortDate"):
            candidates.append((str(data["previousIndexLogNo"]), str(data["previousIndexSortDate"])))
        if data.get("hasNextPage") and data.get("nextIndexLogNo") and data.get("nextIndexSortDate"):
            candidates.append((str(data["nextIndexLogNo"]), str(data["nextIndexSortDate"])))

        next_cursor = None
        for candidate in candidates:
            if candidate[0] not in seen:
                next_cursor = candidate
                break
        if not next_cursor:
            break

        page_cursor = next_cursor
        time.sleep(0.15)

    posts = sorted(seen.values(), key=lambda item: item["logNo"], reverse=True)

    for item in posts:
        log_no = item["logNo"]
        post_url = f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
        html = fetch_text(opener, post_url)
        raw_path = raw_dir / f"{log_no}.html"
        text_path = posts_dir / f"{log_no}.txt"
        raw_path.write_text(html, encoding="utf-8")
        text_path.write_text(strip_tags(html), encoding="utf-8")

        title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        title = unescape(title_match.group(1)).strip() if title_match else ""

        item["resolvedTitle"] = title or item["title"]
        item["url"] = post_url
        item["rawPath"] = str(raw_path)
        item["textPath"] = str(text_path)
        time.sleep(0.15)

    manifest = {
        "blogId": blog_id,
        "backedUpAt": datetime.now().isoformat(timespec="seconds"),
        "postCount": len(posts),
        "posts": posts,
        "listPagesPath": str(output_dir / "list-pages.json"),
    }

    (output_dir / "list-pages.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "output_dir": str(output_dir),
        "latest_log_no": latest_log_no,
        "post_count": len(posts),
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: crawl_naver_blog_backup.py <blog_id> <output_dir>", file=sys.stderr)
        sys.exit(1)
    result = crawl_blog(sys.argv[1], Path(sys.argv[2]))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
