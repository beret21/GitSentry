"""F2: Git 커밋 히스토리 보안 감사."""
import re
from dataclasses import dataclass
from pathlib import Path

from gitvault.core.patterns import PATTERNS, Severity
from gitvault.utils.git import get_commit_diff, get_commit_log, is_git_repo


@dataclass
class CommitFinding:
    commit_hash: str
    file_path: str
    line_content: str
    description: str
    severity: Severity
    matched_text: str

    def masked_content(self) -> str:
        return self.line_content.replace(self.matched_text, f"[{self.description}]")


def audit_history(repo_path: Path, max_commits: int = 200) -> list[CommitFinding]:
    if not is_git_repo(repo_path):
        raise ValueError(f"{repo_path}은 git 저장소가 아닙니다.")

    commits = get_commit_log(repo_path, max_count=max_commits)
    compiled = [(p, p.compile()) for p in PATTERNS]
    findings: list[CommitFinding] = []

    for commit_hash in commits:
        try:
            diff_text = get_commit_diff(repo_path, commit_hash)
        except RuntimeError:
            continue

        current_file = ""
        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current_file = line[6:]
            elif line.startswith("+") and not line.startswith("+++"):
                content = line[1:]
                for pattern, regex in compiled:
                    m = regex.search(content)
                    if m:
                        findings.append(CommitFinding(
                            commit_hash=commit_hash[:8],
                            file_path=current_file,
                            line_content=content.strip(),
                            description=pattern.description,
                            severity=pattern.severity,
                            matched_text=m.group(0),
                        ))

    return findings
