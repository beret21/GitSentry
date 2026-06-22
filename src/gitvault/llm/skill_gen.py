"""F6: Claude Code 메타 스킬 자동 생성."""
from pathlib import Path

from gitvault.core.patterns import PATTERNS, Severity


def generate_skill(output_dir: Path) -> Path:
    """pre-push-audit SKILL.md 생성."""
    output_dir.mkdir(parents=True, exist_ok=True)
    skill_path = output_dir / "SKILL.md"

    danger_patterns = [p for p in PATTERNS if p.severity == Severity.DANGER]
    warning_patterns = [p for p in PATTERNS if p.severity == Severity.WARNING]

    danger_list = "\n".join(f"  - `{p.regex}` — {p.description}" for p in danger_patterns)
    warning_list = "\n".join(f"  - `{p.regex}` — {p.description}" for p in warning_patterns)

    content = f"""# Pre-push Security Audit Skill

당신은 Git push 전 보안 감사 에이전트입니다.

## 트리거
Claude Code에서 `/pre-push-audit` 호출 시 실행.
또는 사용자가 "push 전에 보안 검사해줘", "보안 감사" 등을 요청할 때.

## 감사 절차

### Step 1: Push 대상 파일 확인
```bash
git diff --name-only HEAD origin/main 2>/dev/null || git ls-files
```

### Step 2: 민감 정보 패턴 검사

**DANGER 패턴 (즉시 차단):**
{danger_list}

**WARNING 패턴 (주의 필요):**
{warning_list}

### Step 3: .gitignore 설정 검증
다음 파일들이 .gitignore에 포함되어 있는지 확인:
- `CLAUDE.md`, `**/CLAUDE.md`
- `LESSONS_LEARNED.md`, `DEVELOPMENT.md`, `RESEARCH_*.md`
- `.env`, `.env.*`
- `.claude/`

### Step 4: 결과 보고

결과를 아래 형식으로 표시하라:

| 파일 | 라인 | 유형 | 위험도 |
|------|------|------|--------|
| 파일명 | 번호 | 탐지 내용 | DANGER/WARNING/INFO |

### Step 5: 판정

- **DANGER 항목 존재**: push 중단 권고 + 수정 지침 제공
- **WARNING만 존재**: 확인 요청 후 진행 여부 사용자 결정
- **클린**: "보안 검사 통과 ✓" 출력

## 서브에이전트 구성 (하네스 사용 시)

```yaml
agents:
  - name: git-analyst
    role: Git 히스토리 및 diff 분석
    task: 커밋 히스토리에서 민감 정보 탐지

  - name: security-reviewer
    role: 패턴 매칭 및 리스크 평가
    task: 현재 파일 내용에서 패턴 검사

  - name: report-generator
    role: 결과 요약 및 권장 조치
    task: 발견 항목 종합 + 조치 방법 제시
```

## 관련 명령

```bash
gitvault audit .          # 현재 저장소 감사
gitvault history .        # 히스토리 감사
gitvault preview .        # push 대상 미리보기
gitvault pre-push         # pre-push 훅 수동 실행
```
"""
    skill_path.write_text(content, encoding="utf-8")
    return skill_path
