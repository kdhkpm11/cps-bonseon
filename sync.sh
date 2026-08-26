#!/usr/bin/env bash
# 자동 동기화 + 겹침 경고 데몬 (즉흥/자율 협업용)
# 준비: 노트북마다 한 번 → echo nb1 > .nbid   (nb2, nb3 로 각각)
# 사용: ./sync.sh &            간격 바꾸기: ./sync.sh 10 &
#
# 하는 일 (매 틱):
#  1) 내 변경 커밋 → 2) 남들 것 병합(pull --rebase) → 3) 올림(push)
#  4) 레이더 겹침 감지: 같은 파일을 2대 이상이 '작업중'이면 🟡 경고
#  5) 충돌(같은 줄) 시 🟥 경고 + 조율 안내
#  6) 활동 피드: 최근 커밋(누가 무슨 파일)

cd "$(dirname "$0")" || exit 1
INTERVAL="${1:-12}"
NB="$(cat .nbid 2>/dev/null || echo 'nb?')"
WHO="$(git config user.name 2>/dev/null || whoami)"
echo "[sync] $NB / $WHO · ${INTERVAL}s 간격 · Ctrl+C 종료"
[[ "$NB" == "nb?" ]] && echo "  ⚠️ .nbid 없음 → 'echo nb1 > .nbid' 먼저 실행(노트북마다 nb1/nb2/nb3)"

last_feed=""
while true; do
  # 1) 내 변경 저장
  if [[ -n "$(git status --porcelain)" ]]; then
    git add -A
    FILES="$(git diff --cached --name-only | sed 's#.*/##' | tr '\n' ' ')"
    git commit -q -m "$NB($WHO) $(date +%H:%M:%S): $FILES" 2>/dev/null
  fi
  # 2) 병합 + 3) 올림
  if git pull --rebase -q 2>/dev/null; then
    git push -q 2>/dev/null
  else
    CF="$(git diff --name-only --diff-filter=U 2>/dev/null | tr '\n' ' ')"
    git rebase --abort 2>/dev/null
    echo "🟥 [충돌] $CF ← 같은 줄을 둘이 고침. 구두로 '누가 정리할지' 정하고, 한 명이 손 떼기."
  fi
  # 4) 겹침 레이더 (awk로 이식성 있게: 같은 '작업중:' 대상이 2회 이상)
  DUP="$(awk '/^작업중:/{v=$2; if(v!="" && v!="-") c[v]++} END{for(k in c) if(c[k]>1) print k}' radar/*.md 2>/dev/null)"
  if [[ -n "$DUP" ]]; then
    echo "🟡 [겹침] 아래를 2대 이상이 동시 작업 → 같이 만들 거면 서로 다른 소제목에서, 아니면 조율:"
    echo "$DUP" | sed 's/^/    · /'
  fi
  # 6) 활동 피드
  FEED="$(git log --oneline -5 --pretty='%h %s' 2>/dev/null)"
  if [[ "$FEED" != "$last_feed" ]]; then
    echo "── 활동 ──────────────"
    echo "$FEED" | sed 's/^/  /'
    last_feed="$FEED"
  fi
  sleep "$INTERVAL"
done
