#!/usr/bin/env bash
# 자동 동기화 데몬 — 백그라운드로 띄워두면 계속 pull→commit→push
# 사용: ./sync.sh &         (간격 바꾸려면: ./sync.sh 10 &  ← 10초)
# 전제: '한 파일 = 한 사람' 규칙을 지키면 rebase 충돌이 사실상 안 남.

cd "$(dirname "$0")" || exit 1
INTERVAL="${1:-15}"
WHO="$(git config user.name 2>/dev/null || whoami)"
echo "[sync] start · ${INTERVAL}s 간격 · $WHO · Ctrl+C로 종료"

while true; do
  # 1) 내 변경 먼저 저장
  if [[ -n "$(git status --porcelain)" ]]; then
    git add -A
    git commit -q -m "auto($WHO): $(date +%H:%M:%S)" 2>/dev/null
  fi
  # 2) 남들 것 당겨오기 (충돌 나면 멈추지 말고 알림)
  if ! git pull --rebase -q 2>/dev/null; then
    git rebase --abort 2>/dev/null
    echo "[sync] ⚠️  충돌! 같은 파일을 둘이 고쳤을 수 있음 → 팀에 알리고 담당자가 정리"
  fi
  # 3) 올리기
  git push -q 2>/dev/null && echo "[sync] $(date +%H:%M:%S) ✓ synced"
  sleep "$INTERVAL"
done
