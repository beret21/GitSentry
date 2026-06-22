# GitVault — 보안 감사 규칙

## 민감 정보 분류

### DANGER (즉시 차단)
| 유형 | 설명 |
|------|------|
| API Key | Anthropic(`sk-`), OpenAI(`sk-`), GitHub(`ghp_`), AWS(`AKIA`) |
| Bearer Token | Authorization 헤더 토큰 |
| 비밀번호/시크릿 | `password =`, `secret =` 패턴 |
| 환경 파일 | `.env`, `.env.local` 등 |

### WARNING (주의 필요)
| 유형 | 설명 |
|------|------|
| LLM 내부 문서 | CLAUDE.md, LESSONS_LEARNED.md, DEVELOPMENT.md |
| 연구 문서 | RESEARCH_*.md |

### INFO (참고)
| 유형 | 설명 |
|------|------|
| 로컬 경로 | `/Users/username/` 패턴 |
| localhost | `localhost:포트` 참조 |

## 대응 절차

### DANGER 발견 시
1. push 즉시 중단
2. 해당 파일을 .gitignore에 추가
3. 이미 커밋된 경우: `git filter-repo` 또는 orphan branch로 히스토리 정리
4. 노출된 키/비밀번호는 즉시 만료 처리

### WARNING 발견 시
1. 파일이 내부 전용인지 확인
2. .gitignore에 추가 (`git rm --cached <file>`)
3. GitHub에 이미 push된 경우 히스토리 검토

## LLM 개발 환경 특수 규칙

Claude Code + Git 사용 시:
- `CLAUDE.md`, `**/CLAUDE.md` 반드시 .gitignore에 포함
- `.claude/` 디렉토리 전체 제외 (또는 공개 OK인 항목만 선별)
- `git add -A` 사용 금지 — 파일 명시 지정
- push 전 `gitvault pre-push` 실행 권장
