#!/usr/bin/env bash
# 자동 동기화 + 겹침 경고 데몬 (즉흥/자율 협업용)
# 준비: 노트북마다 한 번 → git config user.name "본인GitHub아이디"  (이게 식별자)
# 사용: ./sync.sh &            간격 바꾸기: ./sync.sh 10 &
#
# 하는 일 (매 틱):
#  1) 내 변경 커밋 → 2) 남들 것 병합(pull --rebase) → 3) 올림(push)
#  4) 레이더 겹침 감지: 같은 파일을 2대 이상이 '작업중'이면 🟡 경고
#  5) 현재 작업 현황: 3명이 각각 지금 뭘 잡고 있는지 상시 표시(바뀌면)
#  6) 충돌(같은 줄) 시 🟥 경고 + 조율 안내
#  7) 활동 피드: 최근 커밋(누가 무슨 파일)

cd "$(dirname "$0")" || exit 1
INTERVAL="${1:-12}"
WHO="$(git config user.name 2>/dev/null)"
if [ -z "$WHO" ]; then
  echo "  ⚠️ git 사용자 이름 없음 → 'git config user.name \"본인GitHub아이디\"' 먼저 실행"
  WHO="unknown"
fi
# 식별자 = git 사용자 이름을 파일명 안전형으로 (공백→_ , 영숫자/_/- 만)
ID="$(printf '%s' "$WHO" | tr ' ' '_' | tr -cd 'A-Za-z0-9_-')"
[ -z "$ID" ] && ID="user"
echo "[sync] $ID / $WHO · ${INTERVAL}s 간격 · Ctrl+C 종료"
# 내 레이더 파일 자동 생성 (radar/<아이디>.md)
mkdir -p radar
MYRADAR="radar/$ID.md"
if [ ! -e "$MYRADAR" ]; then
  printf '작업중: -\n무엇: -\n상태: 대기\n갱신: -\n' > "$MYRADAR"
  echo "  · 내 레이더 생성: $MYRADAR"
fi

last_feed=""
last_status=""
while true; do
  # 1) 내 변경 저장
  if [[ -n "$(git status --porcelain)" ]]; then
    git add -A
    FILES="$(git diff --cached --name-only | sed 's#.*/##' | tr '\n' ' ')"
    git commit -q -m "$ID $(date +%H:%M:%S): $FILES" 2>/dev/null
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
  # 5) 현재 작업 현황 (매 틱 · 바뀌면 표시)
  STATUS=""
  for f in radar/*.md; do
    [ -e "$f" ] || continue
    case "$(basename "$f")" in _*|README.md) continue;; esac
    id="$(basename "$f" .md)"
    task="$(awk -F': *' '/^작업중:/{print $2; exit}' "$f")"
    what="$(awk -F': *' '/^무엇:/{print $2; exit}' "$f")"
    [ -z "$task" ] && task="-"
    if [ "$task" = "-" ]; then
      STATUS="${STATUS}  ${id}: (대기)\n"
    elif [ -n "$what" ] && [ "$what" != "-" ]; then
      STATUS="${STATUS}  ${id}: ${task}  · ${what}\n"
    else
      STATUS="${STATUS}  ${id}: ${task}\n"
    fi
  done
  if [[ "$STATUS" != "$last_status" ]]; then
    printf "── 현재 작업 ─────────\n"
    printf "%b" "$STATUS"
    last_status="$STATUS"
  fi
  # 7) 활동 피드
  FEED="$(git log --oneline -5 --pretty='%h %s' 2>/dev/null)"
  if [[ "$FEED" != "$last_feed" ]]; then
    echo "── 활동 ──────────────"
    echo "$FEED" | sed 's/^/  /'
    last_feed="$FEED"
  fi
  sleep "$INTERVAL"
done
