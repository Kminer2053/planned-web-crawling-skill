# Plan Schema

`run_collection_plan.py`는 다음 형태의 JSON 계획 파일을 실행한다.

## Root Fields

- `name`: 계획 이름
- `user_agent`: 선택값
- `steps`: 순서대로 실행할 배열

## Step Types

### `request`

```json
{
  "id": "landing",
  "type": "request",
  "url": "https://example.com/list",
  "method": "GET",
  "headers": {
    "Referer": "https://example.com/"
  },
  "data": {
    "page": "1"
  },
  "save_body": true
}
```

### `paginate`

```json
{
  "id": "pages",
  "type": "paginate",
  "url_template": "https://example.com/list?page={page}",
  "start_page": 1,
  "max_pages": 5,
  "stop_when_text_regex": "조회 결과가 없습니다"
}
```

### `follow_links`

```json
{
  "id": "detail-pages",
  "type": "follow_links",
  "from": "landing",
  "selector": "a[href]",
  "text_regex": "상세|자세히",
  "href_regex": "/detail/",
  "limit": 10
}
```

## Template Values

문자열 필드는 Python `str.format_map` 방식으로 렌더링된다.

- `{page}`: `paginate` 단계에서 현재 페이지 숫자
- `{context}`: 이전 단계 결과 전체 딕셔너리

실무에서는 복잡한 문자열 템플릿보다, 먼저 단순 URL/폼 요청으로 구조를 확인한 뒤 필요한 부분만 확장하는 편이 안전하다.
