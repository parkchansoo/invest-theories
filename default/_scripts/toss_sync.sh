#!/bin/bash
# ============================================================
# toss_sync.sh — tossctl 세션을 Obsidian 볼트에 동기화
# ============================================================
# 사용법:
#   ./toss_sync.sh           # 세션 + 데이터 동기화
#   ./toss_sync.sh session   # 세션만 복사 (Cowork에서 직접 API 호출용)
#
# 이 스크립트는 사용자의 로컬 Mac에서 실행합니다.
# tossctl이 설치되어 있고 auth login이 완료된 상태여야 합니다.
#
# 세션 파일이 _trade-data/sessions/toss_session.json에 저장되면,
# Cowork에서 toss_account.py / toss_trade.py가 직접 API를 호출합니다.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VAULT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${VAULT_DIR}/_trade-data/sessions"
TIMESTAMP=$(date +"%Y-%m-%dT%H:%M:%S")

# 색상
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BOLD='\033[1m'
RESET='\033[0m'

mkdir -p "$DATA_DIR"

# tossctl 세션 파일 찾기
find_session_file() {
    local config_dir
    # macOS
    if [[ -d "$HOME/Library/Application Support/tossctl" ]]; then
        config_dir="$HOME/Library/Application Support/tossctl"
    # Linux (XDG)
    elif [[ -d "${XDG_CONFIG_HOME:-$HOME/.config}/tossctl" ]]; then
        config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/tossctl"
    else
        echo ""
        return
    fi

    if [[ -f "$config_dir/toss_session.json" ]]; then
        echo "$config_dir/toss_session.json"
    else
        echo ""
    fi
}

sync_session() {
    echo -e "${YELLOW}[SYNC] tossctl 세션 복사 중...${RESET}"

    local session_path
    session_path=$(find_session_file)

    if [[ -z "$session_path" ]]; then
        echo -e "${RED}[ERROR] tossctl 세션 파일을 찾을 수 없습니다.${RESET}"
        echo "  tossctl auth login을 먼저 실행하세요."
        return 1
    fi

    cp "$session_path" "$DATA_DIR/toss_session.json"
    chmod 600 "$DATA_DIR/toss_session.json"
    echo -e "${GREEN}[OK] 세션 → ${DATA_DIR}/toss_session.json${RESET}"

    # .gitignore에 세션 파일 추가 (보안)
    local gitignore="${VAULT_DIR}/.gitignore"
    if [[ -f "$gitignore" ]]; then
        if ! grep -q "_trade-data/sessions/toss_session.json" "$gitignore" 2>/dev/null; then
            echo "_trade-data/sessions/toss_session.json" >> "$gitignore"
            echo -e "${GREEN}[OK] .gitignore에 세션 파일 제외 추가${RESET}"
        fi
    else
        echo "_trade-data/sessions/toss_session.json" > "$gitignore"
        echo -e "${GREEN}[OK] .gitignore 생성 (세션 파일 제외)${RESET}"
    fi
}

# 메인
echo -e "${BOLD}=== 토스증권 세션 동기화 ===${RESET}"
echo -e "볼트: ${VAULT_DIR}"
echo -e "시간: ${TIMESTAMP}"
echo ""

sync_session

echo ""
echo -e "${GREEN}${BOLD}완료!${RESET} Cowork에서 바로 포지션 조회·매매가 가능합니다."
echo -e "  사용법: python toss_account.py positions"
