# Adaptive Web Research Skill

조사형 웹 크롤링을 위한 Codex skill입니다.

이 저장소는 로컬100 크롤러 프로젝트에서 재사용 가능한 패턴만 분리해서 만든 `adaptive-web-research` skill을 제공합니다. 목적은 AI가 처음 보는 웹 소스를 바로 긁기보다, 먼저 구조를 파악하고 수집 계획을 세운 뒤, 중간 증거와 원본 스냅샷을 남기면서 HTML, JSON, PDF, 폼 POST, 쿠키, 단순 페이지네이션까지 유연하게 대응하게 하는 것입니다.

## 이 skill이 지향하는 방식

일반적인 크롤러는 사이트마다 고정된 selector와 예외 규칙을 빠르게 덧붙이는 방식으로 커지기 쉽습니다. 이 저장소는 반대로, AI가 먼저 자료수집 계획을 세우고 파이썬 유틸리티는 그 계획을 재현 가능하게 실행하는 쪽에 초점을 둡니다.

핵심 관점은 다음과 같습니다.

- 처음 보는 소스라도 곧바로 대량 수집하지 않고 먼저 구조를 진단한다.
- HTML, JSON, PDF, 폼 POST, 쿠키 기반 흐름을 하나의 공통 도구로 다룬다.
- 중간 응답과 원본 스냅샷을 남겨서 나중에 검증과 재실행이 가능하게 만든다.
- 사이트 전용 로직은 최소화하고, 범용 패턴과 단계별 계획을 우선한다.

## 크롤링 방법론

이 skill은 아래 순서로 작동하는 것을 기본 원칙으로 둡니다.

1. 가장 공식적인 시작 URL 또는 파일을 찾는다.
2. `probe`로 첫 응답의 유형과 구조를 파악한다.
3. 응답이 HTML인지, JSON인지, PDF인지, 폼 기반인지에 따라 다음 수집 경로를 정한다.
4. 반복 요청이 필요할 때만 계획 파일을 만들어 단계적으로 실행한다.
5. 결과뿐 아니라 요청 방식, 사용 URL, 저장 경로를 함께 남긴다.

이 접근은 특히 다음 상황에서 유리합니다.

- 공공기관 사이트처럼 HTML과 PDF가 섞여 있는 경우
- 숨은 JSON 엔드포인트나 POST 폼이 있는 경우
- 강한 추측보다 증거 기반 탐색이 중요한 경우
- 크롤링 결과를 다른 사람이 다시 검증해야 하는 경우

## 핵심 기능

### 1. 구조 탐지 중심 `probe`

`adaptive-web-research/scripts/crawlkit.py`의 `probe` 명령은 첫 응답을 받아 다음 정보를 빠르게 요약합니다.

- 응답 종류 판별: HTML, JSON, PDF, text, binary
- HTML 분석: 제목, 메타 설명, 링크, 폼, 표, JSON-LD, 페이지네이션 후보
- JSON 분석: top-level 타입, 주요 키, 리스트 필드 개수
- PDF 분석: 페이지 수와 첫 페이지 텍스트 샘플
- 응답 해시와 스냅샷 저장

즉, “어떻게 긁을지”를 판단하기 위한 정찰 단계입니다.

### 2. 계획 실행기

`adaptive-web-research/scripts/run_collection_plan.py`는 JSON 계획 파일을 순서대로 실행합니다. 현재 지원 단계는 다음과 같습니다.

- `request`: 단일 GET/POST 요청 실행
- `paginate`: 페이지 번호를 바꿔가며 반복 요청
- `follow_links`: 이미 저장한 HTML에서 링크를 골라 후속 요청

이 구조 덕분에 수집 로직을 코드 수정 없이 작은 계획 파일로 조합할 수 있습니다.

### 3. 재현 가능한 증거 저장

이 skill은 요약만 남기지 않고 원본도 같이 저장하는 쪽을 기본값으로 둡니다.

- 응답 본문 저장
- 헤더와 상태코드 저장
- SHA-256 해시 저장
- 어떤 URL을 어떤 방식으로 요청했는지 기록

이렇게 해두면, 이후 선택자 수정이나 데이터 검증이 필요할 때 같은 입력으로 다시 확인할 수 있습니다.

## 실제 작업 흐름 예시

예를 들어 처음 보는 기관 사이트 목록 페이지를 받았다고 가정하면 보통 다음처럼 진행합니다.

1. `probe`로 목록 페이지를 확인한다.
2. 링크 구조와 폼 필드를 보고 목록형 HTML인지, POST 검색인지, JSON 호출인지 구분한다.
3. 단순 페이지네이션이면 `paginate` 계획을 만든다.
4. 상세 페이지가 필요하면 `follow_links` 단계를 추가한다.
5. 저장된 원본을 기준으로 필요한 후처리 규칙을 나중에 최소한으로 붙인다.

이 순서는 “일단 긁고 나중에 본다”가 아니라, “먼저 구조를 보고 가장 안전한 경로를 고른다”는 철학에 가깝습니다.

## 계획 파일 예시

`run_collection_plan.py`는 아래처럼 간단한 JSON 계획 파일을 실행합니다.

```json
{
  "name": "example-list-crawl",
  "steps": [
    {
      "id": "landing",
      "type": "request",
      "url": "https://example.com/list"
    },
    {
      "id": "details",
      "type": "follow_links",
      "from": "landing",
      "href_regex": "/detail/",
      "limit": 5
    }
  ]
}
```

복잡한 사이트도 이 기본 패턴에서 출발해 단계적으로 넓혀 가는 식으로 다루는 것을 권장합니다.

## 포함 내용

- `adaptive-web-research/SKILL.md`
- `adaptive-web-research/scripts/crawlkit.py`
- `adaptive-web-research/scripts/run_collection_plan.py`
- `adaptive-web-research/references/`

## 로컬 설치

이 저장소를 내려받은 뒤 skill 폴더를 `~/.codex/skills` 아래로 복사합니다.

```bash
mkdir -p ~/.codex/skills
cp -R adaptive-web-research ~/.codex/skills/
```

복사 후 Codex를 재시작합니다.

## GitHub에서 설치

`skill-installer` 기준으로는 저장소 전체가 아니라 `SKILL.md`가 들어있는 폴더 경로를 지정해 설치합니다. 이 저장소의 설치 대상 경로는 `adaptive-web-research` 입니다.

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo Kminer2053/planned-web-crawling-skill \
  --path adaptive-web-research
```

또는 GitHub tree URL을 직접 넘겨도 됩니다.

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --url https://github.com/Kminer2053/planned-web-crawling-skill/tree/main/adaptive-web-research
```

설치 후 Codex를 재시작합니다.

## 다른 에이전트에 설치

이 저장소는 Codex 외에도 Claude Code, Cursor, OpenCode, 그리고 AGENTS.md를 읽는 에이전트에 붙일 수 있도록 어댑터를 포함합니다.

공통 설치 스크립트:

```bash
python3 tools/install_agent_adapter.py --agent <agent> --target /path/to/project
```

예시:

```bash
python3 tools/install_agent_adapter.py --agent claude --target /path/to/project
python3 tools/install_agent_adapter.py --agent cursor --target /path/to/project
python3 tools/install_agent_adapter.py --agent opencode --target /path/to/project
python3 tools/install_agent_adapter.py --agent antigravity --target /path/to/project
```

설치 결과:

- 공통 코어 툴킷: `/path/to/project/.agent-skills/adaptive-web-research`
- Claude Code: `/path/to/project/.claude/commands/adaptive-web-research.md`
- Cursor: `/path/to/project/.cursor/rules/adaptive-web-research.mdc`
- OpenCode: `/path/to/project/.opencode/commands/adaptive-web-research.md`
- AGENTS 호환 에이전트: `/path/to/project/AGENTS.md`

주의:

- Antigravity는 2026-04-12 기준 공식 프로젝트 로컬 규칙 형식을 확인하지 못해서 `AGENTS.md` 기반 어댑터로 처리했습니다.
- 이미 `AGENTS.md`가 있는 프로젝트면 `AGENTS.adaptive-web-research.md`로 저장될 수 있으니 수동 병합이 필요합니다.
- 같은 프로젝트에 여러 어댑터를 설치해도 `.agent-skills/adaptive-web-research` 코어는 재사용됩니다.

## 언제 쓰는가

- 처음 보는 사이트 구조를 분석하면서 수집 전략을 세워야 할 때
- HTML, JSON, PDF, 폼 요청이 섞여 있는 공공/기관 사이트를 다뤄야 할 때
- 크롤링 결과뿐 아니라 중간 응답과 원본 스냅샷도 같이 남겨야 할 때

## 로컬100 테스트 프롬프트

```text
Use $adaptive-web-research to plan a Local100 crawl starting from https://rcda.or.kr/local100/vote/status.do, probe the source structure first, then propose the exact commands and a JSON collection plan.
```
