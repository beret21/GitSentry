# GitSentry — CLAUDE.md

## 프로젝트 정체성

LLM 개발 환경(Claude Code, Codex 등)에서 사람과 AI가 함께 작업할 때 발생하는 GitHub 보안 위험을 자동으로 감사하는 CLI + Claude Code 연동 도구.

**동기**: macTR 개발 중 `git add -A`로 내부 문서(CLAUDE.md, LESSONS_LEARNED.md)가 GitHub에 노출되고, `.gitignore`가 push되어 내부 파일 이름이 공개된 사고에서 출발.

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| CLI | Typer + Rich |
| 패키지 | hatchling + pyproject.toml |
| GitHub API | PyGithub |
| Git 분석 | GitPython + subprocess |
| LLM | Anthropic SDK (선택적) |
| 테스트 | pytest |

## 세션 시작 시 필독 순서

1. 이 파일 (CLAUDE.md)
2. `docs/SECURITY.md` — 감사 규칙 정의
3. `docs/decisions/` — ADR 목록

## 절대 원칙

1. **LLM 없이도 기본 감사(F1-F4)는 완전히 동작** — `--llm` 플래그는 opt-in
2. **감사 결과에 실제 비밀 값 포함 금지** — 항상 마스킹 처리
3. **`gitsentry audit .`로 자가 검증 통과** — 본 프로젝트도 감사 대상
4. **GitHub push는 사용자 명시 요청 시에만**

## 개발 규칙

- 추측 금지 → WebSearch로 공식 문서 확인
- 공식 문서 → 명세 → 구현 순서
- 기존 동작 코드 보호

## 디렉토리 구조

```
src/gitsentry/
├── cli/main.py          # typer 진입점 — 6개 명령
├── core/
│   ├── patterns.py      # 민감 정보 패턴 정의
│   ├── auditor.py       # F1: 현재 감사
│   ├── history.py       # F2: 히스토리 감사
│   ├── scanner.py       # F3: 전체 저장소
│   └── preview.py       # F4: push 미리보기
├── llm/
│   ├── client.py        # F5: Claude API 연동
│   └── skill_gen.py     # F6: 메타 스킬 생성
└── utils/
    ├── git.py           # git 명령 래퍼
    └── github_api.py    # GitHub API 래퍼
```

## 앱 실행 방법

```bash
cd /Users/beret21/Library/CloudStorage/Dropbox/Codes/Projects/GitSentry

# 가상환경 설정 (최초 1회)
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 사용
gitsentry --help
gitsentry audit .
gitsentry preview .
gitsentry history . -n 50
gitsentry pre-push
gitsentry generate-skill .claude/skills/pre-push-audit/

# 테스트
pytest tests/unit/

# 다른 프로젝트에 pre-push 훅 설치
./scripts/install-hook.sh /path/to/other/repo
```

## 로그 / 진단

```bash
# 감사 + Claude 분석
gitsentry audit . --llm

# 전체 저장소 스캔
gitsentry scan --all
```

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-22 | 초기 프로젝트 구조 생성, 6개 기능 구현 완료 (Phase 1-4) |
