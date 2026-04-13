Use the toolkit in `.agent-skills/adaptive-web-research` to handle this research-oriented crawling task.

Task:
$ARGUMENTS

Before collecting broadly:

1. Read `.agent-skills/adaptive-web-research/SKILL.md`.
2. Read `.agent-skills/adaptive-web-research/references/collection-workflow.md`.
3. Identify the most official start URL or file.
4. Probe the source structure first with `python3 .agent-skills/adaptive-web-research/scripts/crawlkit.py probe ...`.
5. If repeated requests are needed, create a JSON plan for `python3 .agent-skills/adaptive-web-research/scripts/run_collection_plan.py ...`.

Working rules:

- Prefer official public sources.
- Do not assume selectors or hidden APIs before probing.
- Save raw snapshots in `tmp/adaptive-web-research/<task-name>/`.
- Report the exact commands, URLs, request methods, and saved paths.
- If the source is a Naver Blog, read `.agent-skills/adaptive-web-research/references/naver-blog.md` and prefer `PostViewBottomTitleListAsync.naver` over assuming that `PostList.naver` already contains the full archive.
- For repeated Naver Blog backups, prefer:
  - `python3 .agent-skills/adaptive-web-research/scripts/crawl_naver_blog_backup.py <blogId> <output-dir>`
  - `python3 .agent-skills/adaptive-web-research/scripts/export_naver_blog_backup.py <backup-dir>`
