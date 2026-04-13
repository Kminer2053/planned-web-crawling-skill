# 계획형 웹 크롤링 지침

이 프로젝트에는 `.agent-skills/adaptive-web-research` 경로에 범용 웹 자료수집 툴킷이 설치되어 있다고 가정한다.

## 기본 절차

1. `.agent-skills/adaptive-web-research/SKILL.md`를 읽는다.
2. `.agent-skills/adaptive-web-research/references/collection-workflow.md`를 읽는다.
3. 공식 공개 소스를 우선해서 시작 URL 또는 파일을 고른다.
4. `python3 .agent-skills/adaptive-web-research/scripts/crawlkit.py probe ...`로 구조를 먼저 확인한다.
5. 반복 요청이 필요하면 JSON 계획 파일을 만들고 `run_collection_plan.py`로 실행한다.

## 원칙

- probe 이전에는 HTML 구조, API, 페이지네이션 규칙을 단정하지 않는다.
- 넓게 수집하기 전에 소스 종류가 HTML, JSON, PDF, 폼 POST 중 무엇인지 먼저 판별한다.
- 원본 스냅샷은 `tmp/adaptive-web-research/<task-name>/`에 저장한다.
- 최종 결과에는 URL, 요청 방식, 저장 경로를 함께 남긴다.
- 네이버 블로그는 `.agent-skills/adaptive-web-research/references/naver-blog.md` 를 먼저 읽고, `PostList.naver` 만으로 전체 글 목록을 판단하지 않는다.
- 네이버 블로그 전체 백업은 `PostViewBottomTitleListAsync.naver` 커서를 따라 복원하거나, 포함된 보조 스크립트를 우선 사용한다.

## 주요 명령

```bash
python3 .agent-skills/adaptive-web-research/scripts/crawlkit.py probe "<url>" --output-dir "tmp/adaptive-web-research/probe" --save-body
python3 .agent-skills/adaptive-web-research/scripts/run_collection_plan.py "./plan.json" --output-dir "tmp/adaptive-web-research/run"
python3 .agent-skills/adaptive-web-research/scripts/crawl_naver_blog_backup.py "<blogId>" "tmp/adaptive-web-research/naver-blog"
python3 .agent-skills/adaptive-web-research/scripts/export_naver_blog_backup.py "tmp/adaptive-web-research/naver-blog"
```
