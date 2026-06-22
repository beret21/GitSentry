"""F5: Claude API 연동 — 보안 감사 결과 분석."""
import os

from dotenv import load_dotenv


def get_anthropic_client():
    load_dotenv()
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
    return anthropic.Anthropic(api_key=api_key)


def analyze_findings(findings_summary: str) -> str:
    """감사 결과를 Claude에게 전달해 리스크 평가 + 권장 조치 수신."""
    client = get_anthropic_client()

    prompt = f"""당신은 Git 저장소 보안 전문가입니다.
아래는 gitvault 보안 감사 도구가 발견한 결과입니다.

{findings_summary}

다음을 분석해 주세요:
1. 각 DANGER/WARNING 항목의 실제 리스크 수준 평가
2. 즉시 조치가 필요한 항목과 그 이유
3. .gitignore 또는 git history rewrite가 필요한 경우 구체적 방법
4. 향후 재발 방지를 위한 개발 프로세스 권장사항

간결하고 실행 가능한 조치 중심으로 응답해 주세요."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
