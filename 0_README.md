# CPS 본선 현장 운영 매뉴얼 (3인 팀 · 코워크)

목표: **손으로 쓸 보고서를 빠르게 만든다.** 에이전트는 개조식 뼈대와 손그림 설계도만 뽑고, 우리는 옮겨 적고 그린다. 깃허브로 안 겹치게 나눠 작업하며, 동기화는 데몬이 자동으로 한다.

## 0. 대회 전에 반드시 (집에서 미리)

- 규정상 **노트북·인터넷·AI(코워크) 사용이 허용되는지** 먼저 확인. 안 되면 이 환경 못 씀.
- 한 명이 GitHub **private 리포** 생성 → 2명 collaborator 초대
- 3명 모두 git clone → git config user.name 각자 이름으로 설정 → push 테스트
- ./sync.sh & 띄우고 파일 하나 고쳐 **자동 push/pull 되는지** 3명이 확인
- 코워크 데스크탑에서 이 폴더 열어 CLAUDE.md 인식되는지 확인, 모의고사로 1회 예행
- **키잡이 1명** 정하기 (SPINE·FINAL·시간 담당)

### ⚠️ 윈도우 사용자(2명) — 이걸로 맥과 안 꼬임

- **Git 명령/데몬은 전부 "Git Bash"에서** 실행한다. (Git for Windows에 기본 포함 → sync.sh 그대로 실행됨)
- 클론 직후 한 번: `git config core.autocrlf false` (줄바꿈 꼬임 방지, .gitattributes와 함께)
- 맥 사용자는 한 번: `git config core.precomposeunicode true` (한글 파일명 정규화 일치)
- 파일명은 전부 영문이라 한글 파일명 충돌 걱정 없음.

### 리포 올리기 (한 명만)

```bash
cd ~/Downloads/cps-bonseon
git config user.name "본인이름"
gh repo create cps-bonseon --private --source=. --remote=origin --push
# gh 없으면: GitHub에서 빈 private 리포 → git remote add origin <URL> && git push -u origin main
```

### 나머지 2명 (윈도우는 Git Bash에서)

```bash
git clone <URL> && cd cps-bonseon && git config user.name "본인이름"
```

## 1. 자동 동기화 + 겹침 경고 (핵심)

노트북마다 **한 번만**:

```bash
echo nb1 > .nbid      # 노트북마다 nb1 / nb2 / nb3 로 다르게 (한 번)
./sync.sh &           # 12초마다: 커밋→병합→푸시 + 겹침 경고 + 활동 피드
```

- 이후 git 명령 **손으로 칠 필요 없음.** 파일만 저장하면 데몬이 동기화.
- 새 작업 전, 내 레이더 radar/nbN.md의 "작업중:" 한 줄만 갱신 → 데몬이 남들과 겹치면 🟡 경고.
- 같은 줄 충돌 시 🔥 경고 + 조율 안내. (다른 줄이면 자동 병합됨)
- 진행 확인: 데몬 화면의 "활동 피드"(누가 무슨 파일) 또는 git log --oneline.
- 자율 조율 방식 전체는 PLAYBOOK의 즉흥 모드 참고.

## 2. 일하는 법 (즉흥 모드 요약 · 상세는 PLAYBOOK)

- **방향은 하나로**: Phase 0에서 SPINE 락(핵심 전략+가정+한 방). 안 맞추면 다 어긋남.
- **마무리는 한 명**: 키잡이가 SPINE·FINAL·시간 담당. 나머지 2명은 자유.
- **세션은 5레인 장전, 필요한 것만 켬**(LANES). 레인 = 벽 아닌 출발점.
- **겹침은 시스템이 경고**: 레이더(radar/) + 데몬(sync.sh).
- **확정 즉시 손으로 전사**(안 기다림). 텍스트는 안 느리다, 손이 느리다.
- **잘하려면**: 품질 게이트 2번(QUALITY) — SPINE 락 전 발산, 취합 전 자기채점.

| 레인(추천 출발점) | 주로 손대는 곳 | 켜기 |
| :-: | :-: | :-: |
| L1 총괄/취합 | SPINE, FINAL, BOARD, 00_problem | 항상 |
| L2 원인·갈등 | 01_cause, 05_conflict_effect | 대개 |
| L3 대안·선택 | 02_compare, 04_choice_roadmap | 대개 |
| L4 모델·시나리오 | 03_scenario | 시뮬 있을 때 |
| L5 시각자료 | visuals/ | 대개 |

## 3. 현장 골든룰

1. 새 작업 전 레이더 확인 → 안 겹치는 걸 집고 내 radar/nbN.md에 적기. SPINE은 키잡이만.
2. 저장은 자주 → 데몬이 자주 올린다. git은 손으로 안 침.
3. 확정된 섹션은 바로 손으로 전사 시작(안 기다림).
4. 막히면 말로 즉시 공유. 침묵이 제일 위험.

## 4. 파일 안내

- PLAYBOOK — 사람 3명 작업 분업(즉흥 모드)·전사·감독 루프·속도 올리기 ← 현장 운영 핵심
- QUALITY — 잘하게: 발산·레드팀·자기채점(품질 게이트 2번) ← 점수 올리기
- CONTINGENCY — 대회 중 돌발 대응표 + 제출 직전 점검 ← 사고 나면 여기
- CLAUDE — 코워크 에이전트 공통 지침(폴더 열면 자동)
- LANES — 5개 레인 정의 + 레인별 시작 프롬프트(세션마다 복사)
- PROMPT — 웹/폴더 없이 쓸 때 붙일 마스터 프롬프트
- SPINE — 팀 확정 핵심 + 활성 레인(모든 작업 기준, 키잡이만 수정)
- sections/ — 섹션별 개조식 작성 · visuals/ — 손그림 설계도
- BOARD — 진행판 · FINAL — 최종 취합본 · 00_problem — 문제 원문
- sync.sh — 자동 동기화
