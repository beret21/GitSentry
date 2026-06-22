import subprocess
from pathlib import Path


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패: {result.stderr.strip()}")
    return result.stdout


def is_git_repo(path: Path) -> bool:
    try:
        run_git(["rev-parse", "--git-dir"], cwd=path)
        return True
    except (RuntimeError, subprocess.TimeoutExpired):
        return False


def get_tracked_files(repo_path: Path) -> list[Path]:
    """현재 git이 추적하는 파일 목록."""
    output = run_git(["ls-files"], cwd=repo_path)
    return [repo_path / line for line in output.splitlines() if line]


def get_staged_files(repo_path: Path) -> list[Path]:
    """staged(커밋 예정) 파일 목록."""
    output = run_git(["diff", "--cached", "--name-only"], cwd=repo_path)
    return [repo_path / line for line in output.splitlines() if line]


def get_untracked_files(repo_path: Path) -> list[Path]:
    """추적되지 않는 파일 목록 (git status --short 기반)."""
    output = run_git(["status", "--short"], cwd=repo_path)
    untracked = []
    for line in output.splitlines():
        if line.startswith("??"):
            rel_path = line[3:].strip()
            untracked.append(repo_path / rel_path)
    return untracked


def get_commit_log(repo_path: Path, max_count: int = 100) -> list[str]:
    """커밋 해시 목록 (최신순)."""
    output = run_git(["log", f"--max-count={max_count}", "--format=%H"], cwd=repo_path)
    return [h for h in output.splitlines() if h]


def get_commit_diff(repo_path: Path, commit_hash: str) -> str:
    """특정 커밋의 diff 텍스트."""
    return run_git(["show", "--unified=0", commit_hash], cwd=repo_path)


def get_remote_url(repo_path: Path) -> str | None:
    try:
        url = run_git(["remote", "get-url", "origin"], cwd=repo_path)
        return url.strip()
    except RuntimeError:
        return None
