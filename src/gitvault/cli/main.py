from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from gitvault.core.patterns import Severity

app = typer.Typer(
    name="gitvault",
    help="LLM 개발 환경의 GitHub 보안 감사 도구",
    no_args_is_help=True,
)
console = Console()

SEVERITY_COLORS = {
    Severity.DANGER: "red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}


@app.command()
def audit(
    path: Path = typer.Argument(Path("."), help="감사할 로컬 저장소 경로"),
    deep: bool = typer.Option(False, "--deep", help=".gitignore 파일도 포함해서 검사"),
    llm: bool = typer.Option(False, "--llm", help="Claude API로 결과 분석 요청"),
):
    """F1: 현재 저장소 공개 파일 보안 감사."""
    from gitvault.core.auditor import audit_repo, summarize

    repo_path = path.resolve()
    console.print(f"[bold]감사 중:[/bold] {repo_path}")

    with console.status("파일 스캔 중..."):
        findings = audit_repo(repo_path, deep=deep)

    result = summarize(findings)
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
):
    """F2: Git 커밋 히스토리 보안 감사."""
    from gitvault.core.history import audit_history

    repo_path = path.resolve()
    console.print(f"[bold]히스토리 감사 중:[/bold] {repo_path} (최대 {max_commits}개 커밋)")

    with console.status("커밋 히스토리 분석 중..."):
        findings = audit_history(repo_path, max_commits=max_commits)

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
        summary_text = _format_findings_for_llm(findings)
        _run_llm_analysis_raw(summary_text)


@app.command()
def scan(
    all_repos: bool = typer.Option(False, "--all", help="계정 전체 저장소 감사"),
    repo: Optional[str] = typer.Option(None, "--repo", help="특정 저장소 (owner/repo)"),
):
    """F3: GitHub 원격 저장소 감사."""
    from rich.progress import Progress, SpinnerColumn, TextColumn

    if not all_repos and not repo:
        console.print("[red]--all 또는 --repo owner/repo 옵션을 지정하세요.[/red]")
        raise typer.Exit(code=1)

    if all_repos:
        from gitvault.core.scanner import scan_all_repos
        findings = []

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task("저장소 스캔 중...", total=None)

            def on_progress(repo_name: str):
                progress.update(task, description=f"스캔 중: {repo_name}")

            findings = scan_all_repos(progress_callback=on_progress)

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
            table.add_row(
                f.repo,
                f.file_path,
                f.description,
                f"[{color}]{f.severity.value}[/{color}]",
            )
        console.print(table)


@app.command()
def preview(
    path: Path = typer.Argument(Path("."), help="미리보기할 로컬 저장소 경로"),
):
    """F4: Push 대상 vs 제외 파일 시각화."""
    from gitvault.core.preview import get_push_preview

    repo_path = path.resolve()
    result = get_push_preview(repo_path)

    tracked = result["tracked"]
    untracked = result["untracked"]
    gitignored = result["gitignored"]

    table = Table(title="Push 미리보기")
    table.add_column("상태")
    table.add_column("파일")

    for f in tracked:
        rel = f.relative_to(repo_path) if f.is_absolute() else f
        table.add_row("[green]PUSH됨[/green]", str(rel))

    for f in untracked:
        rel = f.relative_to(repo_path) if f.is_absolute() else f
        table.add_row("[yellow]UNTRACKED[/yellow]", str(rel))

    for f in gitignored:
        rel = f.relative_to(repo_path) if f.is_absolute() else f
        table.add_row("[dim]제외됨(.gitignore)[/dim]", str(rel))

    console.print(table)
    console.print(
        f"\n[green]PUSH됨: {len(tracked)}[/green]  "
        f"[yellow]UNTRACKED: {len(untracked)}[/yellow]  "
        f"[dim]제외됨: {len(gitignored)}[/dim]"
    )


@app.command(name="pre-push")
def pre_push(
    path: Path = typer.Argument(Path("."), help="감사할 저장소 경로"),
):
    """F5: Pre-push 훅 — push 전 자동 보안 감사."""
    from gitvault.core.auditor import audit_repo, summarize

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
    from gitvault.llm.skill_gen import generate_skill as gen

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
    summary_text = _format_findings_for_llm(result["findings"])
    _run_llm_analysis_raw(summary_text)


def _run_llm_analysis_raw(summary_text: str) -> None:
    from gitvault.llm.client import analyze_findings

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
