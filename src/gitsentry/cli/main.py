import json as _json
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from gitsentry.core.patterns import Severity

app = typer.Typer(
    name="gitsentry",
    help="LLM 개발 환경의 GitHub 보안 감사 도구",
    no_args_is_help=True,
)
console = Console()

SEVERITY_COLORS = {
    Severity.DANGER: "red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}

# preview 인간 출력에서 생략할 노이즈 최상위 디렉토리
PREVIEW_NOISE_DIRS = {
    ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", "node_modules", "dist", "build", ".git",
}


class OutputFormat(str, Enum):
    human = "human"
    json = "json"


@app.command()
def audit(
    path: Path = typer.Argument(Path("."), help="감사할 로컬 저장소 경로"),
    deep: bool = typer.Option(False, "--deep", help=".gitignore 파일도 포함해서 검사"),
    llm: bool = typer.Option(False, "--llm", help="Claude API로 결과 분석 요청"),
    fmt: OutputFormat = typer.Option(OutputFormat.human, "--format", help="출력 형식 (human|json)"),
):
    """F1: 현재 저장소 공개 파일 보안 감사."""
    from gitsentry.core.auditor import audit_repo, summarize

    repo_path = path.resolve()
    findings = audit_repo(repo_path, deep=deep)
    result = summarize(findings)

    if fmt == OutputFormat.json:
        typer.echo(_json.dumps({
            "path": str(repo_path),
            "summary": {
                "total": result["total"],
                "danger": result["danger"],
                "warning": result["warning"],
                "info": result["info"],
            },
            "findings": [
                {
                    "file": f.file_path,
                    "line": f.line_number,
                    "content": f.masked_content(),
                    "type": f.description,
                    "severity": f.severity.value,
                }
                for f in result["findings"]
            ],
        }, ensure_ascii=False, indent=2))
    else:
        console.print(f"[bold]감사 중:[/bold] {repo_path}")
        _print_findings_table(result["findings"])
        _print_summary(result)
        if llm and findings:
            _run_llm_analysis(result)

    if result["danger"] > 0:
        raise typer.Exit(code=1)


@app.command()
def history(
    path: Path = typer.Argument(Path("."), help="감사할 로컬 저장소 경로"),
    max_commits: int = typer.Option(200, "--max-commits", "-n", help="검사할 최대 커밋 수"),
    llm: bool = typer.Option(False, "--llm", help="Claude API로 결과 분석 요청"),
    fmt: OutputFormat = typer.Option(OutputFormat.human, "--format", help="출력 형식 (human|json)"),
):
    """F2: Git 커밋 히스토리 보안 감사."""
    from gitsentry.core.history import audit_history

    repo_path = path.resolve()
    findings = audit_history(repo_path, max_commits=max_commits)

    if fmt == OutputFormat.json:
        typer.echo(_json.dumps({
            "path": str(repo_path),
            "total": len(findings),
            "findings": [
                {
                    "commit": f.commit_hash,
                    "file": f.file_path,
                    "content": f.masked_content(),
                    "type": f.description,
                    "severity": f.severity.value,
                }
                for f in findings
            ],
        }, ensure_ascii=False, indent=2))
        return

    console.print(f"[bold]히스토리 감사 중:[/bold] {repo_path} (최대 {max_commits}개 커밋)")
    if not findings:
        console.print("[green]히스토리에서 민감 정보를 발견하지 못했습니다.[/green]")
        return

    table = Table(title=f"히스토리 감사 결과 ({len(findings)}건)")
    table.add_column("커밋", style="dim")
    table.add_column("파일")
    table.add_column("내용 (마스킹)")
    table.add_column("유형")
    table.add_column("위험도")

    for f in findings:
        color = SEVERITY_COLORS[f.severity]
        table.add_row(
            f.commit_hash,
            f.file_path,
            f.masked_content()[:80],
            f.description,
            f"[{color}]{f.severity.value}[/{color}]",
        )
    console.print(table)

    if llm and findings:
        _run_llm_analysis_raw(_format_findings_for_llm(findings))


@app.command()
def scan(
    all_repos: bool = typer.Option(False, "--all", help="계정 전체 저장소 감사"),
    repo: Optional[str] = typer.Option(None, "--repo", help="특정 저장소 (owner/repo)"),
    fmt: OutputFormat = typer.Option(OutputFormat.human, "--format", help="출력 형식 (human|json)"),
):
    """F3: GitHub 원격 저장소 감사."""
    if not all_repos and not repo:
        console.print("[red]--all 또는 --repo owner/repo 옵션을 지정하세요.[/red]")
        raise typer.Exit(code=1)

    if all_repos:
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from gitsentry.core.scanner import scan_all_repos

        if fmt == OutputFormat.human:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
                task = progress.add_task("저장소 스캔 중...", total=None)
                findings = scan_all_repos(
                    progress_callback=lambda name: progress.update(task, description=f"스캔 중: {name}")
                )
        else:
            findings = scan_all_repos()

        if fmt == OutputFormat.json:
            typer.echo(_json.dumps({
                "total": len(findings),
                "findings": [
                    {
                        "repo": f.repo,
                        "file": f.file_path,
                        "type": f.description,
                        "severity": f.severity.value,
                    }
                    for f in findings
                ],
            }, ensure_ascii=False, indent=2))
            return

        if not findings:
            console.print("[green]전체 저장소에서 민감 정보를 발견하지 못했습니다.[/green]")
            return

        table = Table(title=f"전체 저장소 감사 결과 ({len(findings)}건)")
        table.add_column("저장소")
        table.add_column("파일")
        table.add_column("유형")
        table.add_column("위험도")

        for f in findings:
            color = SEVERITY_COLORS[f.severity]
            table.add_row(f.repo, f.file_path, f.description, f"[{color}]{f.severity.value}[/{color}]")
        console.print(table)


@app.command()
def preview(
    path: Path = typer.Argument(Path("."), help="미리보기할 로컬 저장소 경로"),
    fmt: OutputFormat = typer.Option(OutputFormat.human, "--format", help="출력 형식 (human|json)"),
):
    """F4: Push 대상 vs 제외 파일 시각화."""
    from gitsentry.core.preview import get_push_preview

    repo_path = path.resolve()
    result = get_push_preview(repo_path)

    tracked = result["tracked"]
    untracked = result["untracked"]
    gitignored = result["gitignored"]

    def rel(f: Path) -> Path:
        return f.relative_to(repo_path) if f.is_absolute() else f

    if fmt == OutputFormat.json:
        # JSON: 노이즈 필터 없이 전체 데이터 반환
        typer.echo(_json.dumps({
            "push": [str(rel(f)) for f in tracked],
            "untracked": [str(rel(f)) for f in untracked],
            "gitignored": [str(rel(f)) for f in gitignored],
            "summary": {
                "push_count": len(tracked),
                "untracked_count": len(untracked),
                "gitignored_count": len(gitignored),
            },
        }, ensure_ascii=False, indent=2))
        return

    # human: 노이즈 디렉토리 생략, 대신 묶어서 요약 표시
    def is_noise(f: Path) -> bool:
        r = rel(f)
        return any(part in PREVIEW_NOISE_DIRS for part in r.parts) if r.parts else False

    gitignored_clean = [f for f in gitignored if not is_noise(f)]
    noise_count = len(gitignored) - len(gitignored_clean)

    table = Table(title="Push 미리보기")
    table.add_column("상태")
    table.add_column("파일")

    for f in tracked:
        table.add_row("[green]PUSH됨[/green]", str(rel(f)))
    for f in untracked:
        table.add_row("[yellow]UNTRACKED[/yellow]", str(rel(f)))
    for f in gitignored_clean:
        table.add_row("[dim]제외됨[/dim]", str(rel(f)))
    if noise_count > 0:
        table.add_row("[dim]제외됨[/dim]", f"[dim]... 외 {noise_count}개 (.venv 등 노이즈 생략)[/dim]")

    console.print(table)
    console.print(
        f"\n[green]PUSH됨: {len(tracked)}[/green]  "
        f"[yellow]UNTRACKED: {len(untracked)}[/yellow]  "
        f"[dim]제외됨: {len(gitignored)} (노이즈 {noise_count}개 생략 표시)[/dim]"
    )


@app.command(name="pre-push")
def pre_push(
    path: Path = typer.Argument(Path("."), help="감사할 저장소 경로"),
):
    """F5: Pre-push 훅 — push 전 자동 보안 감사."""
    from gitsentry.core.auditor import audit_repo, summarize

    repo_path = path.resolve()
    findings = audit_repo(repo_path)
    result = summarize(findings)

    if result["danger"] > 0:
        console.print(f"[bold red]DANGER: {result['danger']}건의 심각한 보안 문제 발견 — push 중단 권고[/bold red]")
        _print_findings_table([f for f in findings if f.severity == Severity.DANGER])
        raise typer.Exit(code=1)
    elif result["warning"] > 0:
        console.print(f"[yellow]WARNING: {result['warning']}건의 경고 발견[/yellow]")
        _print_findings_table([f for f in findings if f.severity == Severity.WARNING])
        proceed = typer.confirm("계속 push하시겠습니까?")
        if not proceed:
            raise typer.Exit(code=1)
    else:
        console.print("[green]보안 검사 통과 ✓[/green]")


@app.command(name="generate-skill")
def generate_skill(
    output_dir: Path = typer.Argument(
        Path(".claude/skills/pre-push-audit"),
        help="SKILL.md를 저장할 디렉토리",
    ),
):
    """F6: Claude Code pre-push-audit 메타 스킬 생성."""
    from gitsentry.llm.skill_gen import generate_skill as gen

    skill_path = gen(output_dir.resolve())
    console.print(f"[green]스킬 생성 완료:[/green] {skill_path}")
    console.print("Claude Code에서 [bold]/pre-push-audit[/bold] 명령으로 사용할 수 있습니다.")


def _print_findings_table(findings) -> None:
    if not findings:
        return
    table = Table(title=f"감사 결과 ({len(findings)}건)")
    table.add_column("파일")
    table.add_column("라인", justify="right")
    table.add_column("내용 (마스킹)", no_wrap=False)
    table.add_column("유형")
    table.add_column("위험도")

    for f in findings:
        color = SEVERITY_COLORS[f.severity]
        table.add_row(
            str(Path(f.file_path).name),
            str(f.line_number),
            f.masked_content()[:80],
            f.description,
            f"[{color}]{f.severity.value}[/{color}]",
        )
    console.print(table)


def _print_summary(result: dict) -> None:
    console.print(
        f"\n합계: [bold]{result['total']}[/bold]건  "
        f"[red]DANGER: {result['danger']}[/red]  "
        f"[yellow]WARNING: {result['warning']}[/yellow]  "
        f"[cyan]INFO: {result['info']}[/cyan]"
    )


def _run_llm_analysis(result: dict) -> None:
    _run_llm_analysis_raw(_format_findings_for_llm(result["findings"]))


def _run_llm_analysis_raw(summary_text: str) -> None:
    from gitsentry.llm.client import analyze_findings

    console.print("\n[bold]Claude 분석 중...[/bold]")
    with console.status("Claude API 요청 중..."):
        analysis = analyze_findings(summary_text)
    console.print("\n[bold underline]Claude 분석 결과[/bold underline]")
    console.print(analysis)


def _format_findings_for_llm(findings) -> str:
    lines = [f"총 {len(findings)}건 발견\n"]
    for f in findings:
        lines.append(
            f"- [{f.severity.value}] {getattr(f, 'file_path', '')} "
            f"(라인 {getattr(f, 'line_number', '?')}): "
            f"{f.description} — {f.masked_content()[:60]}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    app()
