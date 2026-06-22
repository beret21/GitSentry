"""F3: 계정 전체 GitHub 저장소 순차 감사."""
from dataclasses import dataclass, field
from pathlib import Path

from gitsentry.utils.github_api import get_file_content, list_user_repos
from gitsentry.core.patterns import PATTERNS, Severity


@dataclass
class RemoteFinding:
    repo: str
    file_path: str
    line_number: int
    line_content: str
    description: str
    severity: Severity
    matched_text: str


def scan_remote_file(repo_name: str, file_path: str, content: str) -> list[RemoteFinding]:
    compiled = [(p, p.compile()) for p in PATTERNS]
    findings = []
    for i, line in enumerate(content.splitlines(), start=1):
        for pattern, regex in compiled:
            m = regex.search(line)
            if m:
                findings.append(RemoteFinding(
                    repo=repo_name,
                    file_path=file_path,
                    line_number=i,
                    line_content=line.strip(),
                    description=pattern.description,
                    severity=pattern.severity,
                    matched_text=m.group(0),
                ))
    return findings


def scan_all_repos(progress_callback=None) -> list[RemoteFinding]:
    """계정 전체 저장소를 GitHub API로 감사."""
    from gitsentry.utils.github_api import get_repo_files

    repos = list_user_repos()
    all_findings: list[RemoteFinding] = []

    SKIP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
                       ".woff", ".woff2", ".ttf", ".pdf", ".zip", ".tar",
                       ".gz", ".dmg", ".exe", ".dylib", ".so", ".pyc"}

    for repo in repos:
        if progress_callback:
            progress_callback(repo["full_name"])
        try:
            files = get_repo_files(repo["full_name"])
            for f in files:
                ext = Path(f["path"]).suffix.lower()
                if ext in SKIP_EXTENSIONS or f["size"] > 1_000_000:
                    continue
                try:
                    content = get_file_content(repo["full_name"], f["path"])
                    findings = scan_remote_file(repo["full_name"], f["path"], content)
                    all_findings.extend(findings)
                except Exception:
                    continue
        except Exception:
            continue

    return all_findings
