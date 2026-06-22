import re
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    DANGER = "DANGER"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Pattern:
    regex: str
    description: str
    severity: Severity

    def compile(self) -> re.Pattern:
        return re.compile(self.regex)


PATTERNS: list[Pattern] = [
    # API Keys — DANGER
    Pattern(r"sk-[A-Za-z0-9]{20,}", "Anthropic/OpenAI API Key", Severity.DANGER),
    Pattern(r"sk-ant-[A-Za-z0-9\-]{20,}", "Anthropic API Key", Severity.DANGER),
    Pattern(r"ghp_[A-Za-z0-9]{36}", "GitHub Personal Access Token", Severity.DANGER),
    Pattern(r"ghs_[A-Za-z0-9]{36}", "GitHub Server Token", Severity.DANGER),
    Pattern(r"Bearer [A-Za-z0-9\-._~+/]{20,}=*", "Bearer Token", Severity.DANGER),
    Pattern(r"[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]\s*[:=]\s*(?!os\.getenv)(?![A-Za-z_]\w*[,\)\s])(?!\S*\.\.\.)['\"]?\S{8,}", "API Key Assignment", Severity.DANGER),
    Pattern(r"[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]\s*=\s*(?!pypi-)(?![A-Za-z_]\w*[,\)\s])['\"]?\S{4,}", "Password Assignment", Severity.DANGER),
    Pattern(r"[Ss][Ee][Cc][Rr][Ee][Tt]\s*[:=]\s*['\"]?\S{4,}", "Secret Assignment", Severity.DANGER),
    Pattern(r"AKIA[A-Z0-9]{16}", "AWS Access Key ID", Severity.DANGER),
    # LLM 개발 내부 문서 — WARNING
    Pattern(r"CLAUDE\.md", "Claude Code Internal Doc", Severity.WARNING),
    Pattern(r"LESSONS_LEARNED\.md", "Internal Dev Lessons", Severity.WARNING),
    Pattern(r"DEVELOPMENT\.md", "Internal Dev Doc", Severity.WARNING),
    Pattern(r"RESEARCH_[A-Z_]+\.md", "Internal Research Doc", Severity.WARNING),
    Pattern(r"\.env(\.\w+)?$", "Environment File", Severity.WARNING),
    # 내부 경로/설정 — INFO
    Pattern(r"/Users/[A-Za-z0-9_\-]+/", "Local User Path", Severity.INFO),
    Pattern(r"localhost:[0-9]{4,5}", "Localhost Reference", Severity.INFO),
]


@dataclass
class Finding:
    file_path: str
    line_number: int
    line_content: str
    pattern: Pattern
    matched_text: str

    @property
    def severity(self) -> Severity:
        return self.pattern.severity

    @property
    def description(self) -> str:
        return self.pattern.description

    def masked_content(self) -> str:
        """민감 값을 마스킹한 라인 반환."""
        return self.line_content.replace(self.matched_text, f"[{self.description}]")
