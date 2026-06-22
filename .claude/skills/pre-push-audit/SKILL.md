# Pre-push Security Audit Skill

당신은 Git push 전 보안 감사 에이전트입니다.

## 트리거
사용자가 `/pre-push-audit` 를 호출하거나 "push 전 보안 검사", "보안 감사해줘" 등을 요청할 때.

## 감사 절차

### Step 1: Push 대상 파일 확인
```bash
git ls-files
git diff --name-only HEAD origin/main 2>/dev/null
```

### Step 2: DANGER 패턴 검사 (발견 즉시 차단)
- `sk-[A-Za-z0-9]{20,}` — Anthropic/OpenAI API Key
- `ghp_[A-Za-z0-9]{36}` — GitHub Personal Access Token
- `AKIA[A-Z0-9]{16}` — AWS Access Key
- `password\s*=\s*\S{4,}` — 비밀번호 할당
- `.env` 파일

### Step 3: WARNING 패턴 확인 (사용자 확인 후 진행)
- `CLAUDE.md` — Claude Code 내부 문서
- `LESSONS_LEARNED.md` — 내부 개발 기록
- `DEVELOPMENT.md` — 내부 개발 문서
- `RESEARCH_*.md` — 내부 연구 문서

### Step 4: .gitignore 검증
다음이 .gitignore에 포함되어 있는지 확인:
```
CLAUDE.md
**/CLAUDE.md
LESSONS_LEARNED.md
DEVELOPMENT.md
.env
.env.*
.claude/
```

### Step 5: 결과 보고

| 파일 | 유형 | 위험도 | 조치 |
|------|------|--------|------|

- **DANGER**: push 중단 권고 + 즉시 조치 방법 제시
- **WARNING**: 사용자 확인 요청
- **클린**: "보안 검사 통과 ✓" 출력

## gitvault CLI로 실행

```bash
gitvault audit .              # 현재 저장소 감사
gitvault pre-push             # pre-push 전체 감사
gitvault history . -n 50      # 최근 50개 커밋 감사
gitvault preview .            # push 대상 미리보기
```
