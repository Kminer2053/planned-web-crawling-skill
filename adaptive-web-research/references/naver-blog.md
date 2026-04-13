# Naver Blog Notes

네이버 블로그는 일반적인 정적 목록 페이지처럼 보이지만 실제로는 프레임셋, 상세 페이지, 하단 비동기 목록이 섞여 있다. 다른 사이트와 같은 방식으로 `PostList.naver` HTML만 읽고 끝내면 전체 게시물 수집에 실패할 수 있다.

## Recommended Flow

1. 먼저 `https://blog.naver.com/<blogId>` 또는 `https://blog.naver.com/PostList.naver?blogId=<blogId>&from=postList` 를 `probe`한다.
2. 최신 글의 `logNo` 와 게시 시각을 확인한다.
3. 전체 게시물 목록은 `PostViewBottomTitleListAsync.naver` 로 따라간다.
4. 응답의 `previousIndexLogNo` 와 `nextIndexLogNo` 중 아직 보지 않은 커서를 계속 따라간다.
5. 각 `logNo` 에 대해 `PostView.naver?blogId=<blogId>&logNo=<logNo>` 를 저장한다.
6. 필요하면 원본 HTML을 후처리해 CSV/XLSX로 정리한다.

## Why This Matters

- `PostList.naver` 는 최신 글 일부만 보여줄 수 있다.
- 모바일/PC 페이지 모두 초기 셸만 주는 경우가 있다.
- 실제 “전체글 보기” 목록은 `PostViewBottomTitleListAsync.naver` 에서 JSON으로 내려올 수 있다.
- 네이버 블로그는 페이지 방향 포인터가 구간마다 다르게 보일 수 있어서 `previous` 만 고정 추적하면 놓치는 글이 생길 수 있다.

## Async List Endpoint

형태:

```text
https://blog.naver.com/PostViewBottomTitleListAsync.naver?blogId=<blogId>&logNo=<logNo>&showPreviousPage=true&sortDateInMilli=<epoch_ms>
```

응답 필드 예시:

- `postList`
- `hasPreviousPage`
- `previousIndexLogNo`
- `previousIndexSortDate`
- `hasNextPage`
- `nextIndexLogNo`
- `nextIndexSortDate`

이 엔드포인트를 쓸 때는 한 방향만 고정해서 따라가지 말고, `previous` 와 `next` 중 아직 방문하지 않은 커서를 우선 선택한다.

## Helper Scripts

툴킷에는 네이버 블로그 전체 백업과 후처리를 위한 보조 스크립트가 포함되어 있다.

- `scripts/crawl_naver_blog_backup.py <blog_id> <output_dir>`
- `scripts/export_naver_blog_backup.py <backup_dir>`

예시:

```bash
python3 .agent-skills/adaptive-web-research/scripts/crawl_naver_blog_backup.py loconomy tmp/naver-blog/loconomy
python3 .agent-skills/adaptive-web-research/scripts/export_naver_blog_backup.py tmp/naver-blog/loconomy
```

## Reporting

최종 보고에는 아래를 같이 남긴다.

- 시작 URL
- 사용한 비동기 목록 엔드포인트
- 저장 폴더 경로
- 수집한 게시물 수
- 후처리 산출물 경로 (`posts.csv`, `links.csv`, `blog_backup.xlsx` 가능 시)
