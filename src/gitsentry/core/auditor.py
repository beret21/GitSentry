"""F1: 현재 저장소 공개 파일 보안 감사."""
import re
from pathlib import Path

from gitsentry.core.patterns import PATTERNS, Finding, Severity
from gitsentry.utils.git import get_tracked_files, is_git_repo

SKIP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
                   ".woff", ".woff2", ".ttf", ".eot", ".pdf", ".zip",
                   ".tar", ".gz", ".dmg", ".exe", ".dylib", ".so"}

# 이 디렉토리/파일은 의도적으로 패턴 문자열을 포함하므로 DANGER 미적용
SKIP_DANGER_DIRS = {"tests"}
SKIP_DANGER_FILES = {".env.example", ".env.sample", ".env.template"}


def audit_file(file_path: Path) -> list[Finding]:
    if file_path.suffix.lower() in SKIP_EXTENSIONS:
        return []
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return []

    findings = []
    compiled = [(p, p.compile()) for p in PATTERNS]
    for i, line in enumerate(text.splitlines(), start=1):
        for pattern, regex in compiled:
            m = regex.search(line)
            if m:
                findings.append(Finding(
                    file_path=str(file_path),
                    line_number=i,
                    line_content=line.strip(),
                    pattern=pattern,
                    matched_text=m.group(0),
                ))

    is_safe_context = (
        any(part in SKIP_DANGER_DIRS for part in file_path.parts) or
        file_path.name in SKIP_DANGER_FILES
    )
    if is_safe_context:
        findings = [f for f in findings if f.severity != Severity.DANGER]

    return findings


def audit_repo(repo_path: Path, deep: bool = False) -> list[Finding]:
    """저장소 감사 — deep=True면 .gitignore 파일 포함."""
    if not is_git_repo(repo_path):
        raise ValueError(f"{repo_path}은 git 저장소가 아닙니다.")

    if deep:
        files = [f for f in repo_path.rglob("*") if f.is_file()
                 and ".git" not in f.parts]
    else:
        files = get_tracked_files(repo_path)

    all_findings: list[Finding] = []
    for f in files:
        all_findings.extend(audit_file(f))
    return all_findings


def summarize(findings: list[Finding]) -> dict:
    danger = [f for f in findings if f.severity == Severity.DANGER]
    warning = [f for f in findings if f.severity == Severity.WARNING]
    info = [f for f in findings if f.severity == Severity.INFO]
    return {
        "total": len(findings),
        "danger": len(danger),
        "warning": len(warning),
        "info": len(info),
        "findings": findings,
    }
