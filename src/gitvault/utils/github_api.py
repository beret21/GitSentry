import os
from pathlib import Path

from dotenv import load_dotenv


def get_github_token() -> str:
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요.")
    return token


def get_github_client():
    from github import Github
    return Github(get_github_token())


def list_user_repos(include_private: bool = True) -> list[dict]:
    g = get_github_client()
    user = g.get_user()
    repos = []
    for repo in user.get_repos():
        repos.append({
            "name": repo.name,
            "full_name": repo.full_name,
            "private": repo.private,
            "url": repo.html_url,
            "clone_url": repo.clone_url,
        })
    return repos


def get_repo_files(full_repo_name: str, path: str = "") -> list[dict]:
    """GitHub 저장소의 파일 목록 반환."""
    g = get_github_client()
    repo = g.get_repo(full_repo_name)
    contents = repo.get_contents(path)
    files = []
    while contents:
        item = contents.pop(0)
        if item.type == "dir":
            contents.extend(repo.get_contents(item.path))
        else:
            files.append({
                "path": item.path,
                "name": item.name,
                "size": item.size,
                "download_url": item.download_url,
            })
    return files


def get_file_content(full_repo_name: str, file_path: str) -> str:
    """GitHub 저장소에서 파일 내용 반환 (base64 디코딩)."""
    g = get_github_client()
    repo = g.get_repo(full_repo_name)
    content = repo.get_contents(file_path)
    return content.decoded_content.decode("utf-8", errors="replace")
