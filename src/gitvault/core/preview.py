"""F4: Push 미리보기 — push 대상 vs .gitignore 제외 파일 시각화."""
import subprocess
from pathlib import Path

from gitvault.utils.git import get_tracked_files, get_untracked_files, is_git_repo


def get_push_preview(repo_path: Path) -> dict:
    """
    push될 파일과 제외될 파일을 분리해서 반환.

    Returns:
        {
            "tracked": [tracked 파일 목록],
            "untracked": [untracked 파일 목록],
            "gitignored": [.gitignore로 제외된 파일 목록],
        }
    """
    if not is_git_repo(repo_path):
        raise ValueError(f"{repo_path}은 git 저장소가 아닙니다.")

    tracked = get_tracked_files(repo_path)
    untracked = get_untracked_files(repo_path)

    # .gitignore로 실제로 제외된 파일 목록
    result = subprocess.run(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    gitignored = [repo_path / line for line in result.stdout.splitlines() if line]

    return {
        "tracked": tracked,
        "untracked": untracked,
        "gitignored": gitignored,
    }
