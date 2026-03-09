---
name: adaptive-web-research
description: 조사형 웹 크롤링과 문서 수집을 위한 유연한 자료수집 skill. 처음 보는 소스를 분석하고 수집 전략을 세운 뒤 HTML, JSON, PDF, 폼 요청, 쿠키, 단순 페이지네이션을 따라가며 재현 가능한 증거와 중간 스냅샷을 남겨야 할 때 사용한다.
---

# 계획형 웹 크롤링

사용자 요청을 받은 뒤 바로 대량 수집에 들어가지 말고, 먼저 소스 구조를 파악하고 증거를 저장하면서 계획을 좁혀간다. 이 skill은 조사형 크롤링을 위해 `urllib` 기반 세션, HTML/JSON/PDF 프로빙, 링크 추적, 단순 페이지네이션 실행기를 제공한다.

## 작업 흐름

1. 조사 목표를 1~3문장으로 정리한다.
2. 가장 공식적인 시작 URL 또는 파일을 찾는다.
3. `scripts/crawlkit.py probe`로 첫 응답의 구조를 확인한다.
4. probe 결과를 근거로 수집 경로를 정한다.
5. 반복 요청이 필요하면 `scripts/run_collection_plan.py`용 계획 파일을 만든다.
6. 결과와 원본 스냅샷 경로를 함께 보고한다.

## 빠른 시작

첫 구조 파악:

```bash
python3 adaptive-web-research/scripts/crawlkit.py probe "https://example.com/list" --output-dir /tmp/example-probe --save-body
```

로컬 HTML 파일 분석:

```bash
python3 adaptive-web-research/scripts/crawlkit.py probe "./sample.html"
```

계획 실행:

```bash
python3 adaptive-web-research/scripts/run_collection_plan.py ./plan.json --output-dir /tmp/example-run
```

## 판단 기준

- HTML이면 제목, 링크, 폼, 표, JSON-LD, 페이지네이션 후보를 먼저 확인한다.
- JSON이면 top-level 타입과 리스트 키를 보고 반복 요청 규칙을 정한다.
- PDF이면 샘플 텍스트와 페이지 수를 확인하고, 필요한 경우 후속 파서를 덧붙인다.
- 쿠키나 POST가 필요하면 `run_collection_plan.py`의 `request` 단계로 먼저 재현한다.
- JS 렌더링 의존이 강하면 우회보다 대체 공식 소스나 숨은 JSON 엔드포인트를 먼저 찾는다.

## 스크립트

- `scripts/crawlkit.py`
  - `probe`: 응답 구조 요약
  - `fetch`: 원본 스냅샷 저장
- `scripts/run_collection_plan.py`
  - `request`, `paginate`, `follow_links` 단계 실행

## 참고 문서

- 자세한 운영 흐름: `references/collection-workflow.md`
- 계획 JSON 예시: `references/plan-schema.md`

## 작업 원칙

- probe 없이 CSS selector나 페이지 구조를 단정하지 말 것
- 응답 원본을 저장하지 않은 채 요약만 남기지 말 것
- 사이트 전용 규칙은 기본 skill에 넣지 말고, 실제 작업 중 필요한 경우 작은 보조 스크립트로 분리할 것
- 수집 결과에는 사용한 URL, 요청 방식, 저장 경로를 같이 남길 것
