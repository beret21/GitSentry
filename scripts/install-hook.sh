#!/bin/bash
# GitSentry pre-push 훅 설치 스크립트
# 사용법: ./scripts/install-hook.sh [저장소 경로]

REPO_PATH="${1:-.}"
HOOK_PATH="$REPO_PATH/.git/hooks/pre-push"

if [ ! -d "$REPO_PATH/.git" ]; then
    echo "Error: $REPO_PATH 는 git 저장소가 아닙니다."
    exit 1
fi

cat > "$HOOK_PATH" << 'EOF'
#!/bin/bash
# GitSentry pre-push security hook
gitsentry pre-push .
exit $?
EOF

chmod +x "$HOOK_PATH"
echo "pre-push 훅 설치 완료: $HOOK_PATH"
echo "이제 git push 전에 자동으로 보안 감사가 실행됩니다."
