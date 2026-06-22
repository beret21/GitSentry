# GitSentry

LLM 개발 환경(Claude Code, Codex 등)에서 GitHub push 전 보안 감사 CLI 도구.

## 기능

| 명령 | 설명 |
|------|------|
| `gitsentry audit .` | 현재 저장소 공개 파일 보안 감사 |
| `gitsentry history .` | Git 커밋 히스토리 보안 감사 |
| `gitsentry scan --all` | 계정 전체 GitHub 저장소 감사 |
| `gitsentry preview .` | Push 대상 vs 제외 파일 시각화 |
| `gitsentry pre-push` | Pre-push 훅 수동 실행 |
| `gitsentry generate-skill` | Claude Code 보안 감사 스킬 생성 |

## 설치

```bash
pip install gitsentry

# 업데이트
pip install --upgrade gitsentry
```

> macOS에서 "externally-managed-environment" 오류 시: `pip install gitsentry --break-system-packages`

개발용 설치:

```bash
git clone https://github.com/beret21/GitSentry.git
cd GitSentry
pip install -e ".[dev]"
```

## 빠른 시작

```bash
# 현재 저장소 감사
gitsentry audit .

# Push 전 미리보기
gitsentry preview .

# pre-push 훅 설치
./scripts/install-hook.sh .
```

## 환경 변수 (.env)

```
GITHUB_TOKEN=ghp_your_token    # 원격 저장소 감사에 필요
ANTHROPIC_API_KEY=sk-ant-...   # --llm 옵션 사용 시 필요
```

## 탐지 패턴

**DANGER (push 차단):** API 키(`sk-`, `ghp_`, `AKIA`), 비밀번호, Bearer 토큰

**WARNING (주의):** LLM 내부 문서 (CLAUDE.md, LESSONS_LEARNED.md, DEVELOPMENT.md)
