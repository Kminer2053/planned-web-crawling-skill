# Adaptive Web Research Skill

조사형 웹 크롤링을 위한 Codex skill입니다.

이 저장소는 로컬100 크롤러 프로젝트에서 재사용 가능한 패턴만 분리해서 만든 `adaptive-web-research` skill을 제공합니다. 목적은 AI가 처음 보는 웹 소스를 바로 긁기보다, 먼저 구조를 파악하고 수집 계획을 세운 뒤, 중간 증거와 원본 스냅샷을 남기면서 HTML, JSON, PDF, 폼 POST, 쿠키, 단순 페이지네이션까지 유연하게 대응하게 하는 것입니다.

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

## 언제 쓰는가

- 처음 보는 사이트 구조를 분석하면서 수집 전략을 세워야 할 때
- HTML, JSON, PDF, 폼 요청이 섞여 있는 공공/기관 사이트를 다뤄야 할 때
- 크롤링 결과뿐 아니라 중간 응답과 원본 스냅샷도 같이 남겨야 할 때

## 로컬100 테스트 프롬프트

```text
Use $adaptive-web-research to plan a Local100 crawl starting from https://rcda.or.kr/local100/vote/status.do, probe the source structure first, then propose the exact commands and a JSON collection plan.
```
