# Multi-Agent Adapters

이 디렉터리는 `adaptive-web-research` 코어 툴킷을 다른 에이전트 환경에 붙이기 위한 얇은 어댑터 모음이다.

지원 대상:

- Claude Code: `.claude/commands/`
- Cursor: `.cursor/rules/`
- OpenCode: `.opencode/commands/`
- AGENTS.md 호환 에이전트: `AGENTS.md`
- Antigravity: 공식 프로젝트 로컬 규칙 형식을 확인하지 못해 AGENTS.md 어댑터로 설치

권장 설치 방법은 루트의 `tools/install_agent_adapter.py`를 사용하는 것이다.
