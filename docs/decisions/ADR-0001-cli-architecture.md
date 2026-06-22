# ADR-0001: CLI 아키텍처 — Typer + Rich

**날짜:** 2026-06-22
**상태:** 결정됨

## 배경
GitVault는 터미널에서 사용하는 보안 감사 도구이므로 CLI 인터페이스가 필수다.

## 결정
Typer + Rich 조합을 사용한다.

## 이유
- 기존 Projects 폴더의 Python CLI 프로젝트(FleetLens_CLI)와 동일한 스택
- Typer: Click 기반, 타입 힌트로 자동 파라미터 파싱
- Rich: 터미널 컬러 테이블, Progress bar — 보안 감사 결과 시각화에 최적

## 대안
- argparse: 너무 저수준
- Click 직접: Typer가 더 적은 코드로 동일 기능
