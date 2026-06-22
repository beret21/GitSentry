"""패턴 탐지 단위 테스트."""
import pytest
from gitvault.core.patterns import PATTERNS, Severity


def get_pattern(description: str):
    for p in PATTERNS:
        if p.description == description:
            return p
    return None


class TestApiKeyPatterns:
    def test_anthropic_api_key(self):
        p = get_pattern("Anthropic/OpenAI API Key")
        assert p is not None
        assert p.compile().search("sk-abcdefghijklmnopqrstu12345") is not None

    def test_github_token(self):
        p = get_pattern("GitHub Personal Access Token")
        assert p is not None
        assert p.compile().search("ghp_" + "A" * 36) is not None

    def test_no_false_positive_short_sk(self):
        p = get_pattern("Anthropic/OpenAI API Key")
        assert p.compile().search("sk-short") is None


class TestInternalDocPatterns:
    def test_claude_md(self):
        p = get_pattern("Claude Code Internal Doc")
        assert p is not None
        assert p.compile().search("CLAUDE.md") is not None
        assert p.severity == Severity.WARNING

    def test_lessons_learned(self):
        p = get_pattern("Internal Dev Lessons")
        assert p is not None
        assert p.compile().search("LESSONS_LEARNED.md") is not None

    def test_research_doc(self):
        p = get_pattern("Internal Research Doc")
        assert p is not None
        assert p.compile().search("RESEARCH_STOCK_API.md") is not None


class TestPasswordPatterns:
    def test_password_assignment(self):
        p = get_pattern("Password Assignment")
        assert p is not None
        assert p.compile().search("password = mysecretpwd") is not None
        assert p.severity == Severity.DANGER
