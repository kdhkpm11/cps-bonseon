# LANES — 코워크 세션 레인 5개 (장전 후 필요한 것만 활성화)

원리: 세션(레인)이 정확히 5개 정의돼 있고 각자 소유 파일이 겹치지 않는다. 5개를 다 켤 필요는 없다. L1은 항상 켜고, 나머지는 이 문제의 수행 과제를 보고 필요한 것만 켠다.

레인은 "벽"이 아니라 "추천 출발점". 각자 자유롭게 집되 겹침은 radar/ + sync.sh가 경고로 막는다.

## 레인 표

| 레인 | 이름 | 주로 손대는 곳 | 언제 켜나 |
| :-: | :-: | :-: | :-: |
| L1 | 총괄/취합 | SPINE, FINAL, BOARD, 00_problem | 항상 |
| L2 | 원인·갈등 | 01_cause, 05_conflict_effect | 대개 |
| L3 | 대안·선택 | 02_compare, 04_choice_roadmap | 대개 |
| L4 | 모델·시나리오 | 03_scenario | 시뮬 있을 때 |
| L5 | 시각자료 | visuals/ | 대개 |

## 활성화 절차 (Phase 0에서 키잡이가 결정)

1. 00_problem의 수행 과제를 보고 켤 레인을 고른다.
2. 활성 레인 목록을 SPINE 맨 위 "활성 레인:" 줄에 적는다. (예: 활성 레인: L1 L2 L3 L5)
3. 켠 레인만 세션을 연다.

## 세션 시작 프롬프트 (해당 레인 것만 복사해 붙여넣기)

**L1:** 너는 이 리포의 레인 L1(총괄/취합)이다. CLAUDE.md, lanes/L1_orchestrator.md, 00_problem.md를 읽어라. 먼저 수행 과제를 보고 켤 레인을 정해 SPINE.md에 "활성 레인:"과 핵심 전략·가정을 확정하라. 너는 SPINE.md, FINAL.md, BOARD.md, 00_problem.md만 편집한다. 다른 파일은 읽기만. 시작.

**L2:** 너는 이 리포의 레인 L2(원인·갈등)다. CLAUDE.md, lanes/L2_cause_conflict.md, SPINE.md, 00_problem.md를 읽어라. SPINE 기준으로 sections/01_cause.md, sections/05_conflict_effect.md만 편집한다. 다른 파일은 읽기만. 시작.

**L3:** 너는 이 리포의 레인 L3(대안·선택)다. CLAUDE.md, lanes/L3_compare_choice.md, SPINE.md, 00_problem.md를 읽어라. SPINE 기준으로 sections/02_compare.md, sections/04_choice_roadmap.md만 편집한다. 다른 파일은 읽기만. 시작.

**L4:** 너는 이 리포의 레인 L4(모델·시나리오)다. CLAUDE.md, lanes/L4_model_scenario.md, SPINE.md, 00_problem.md를 읽어라. SPINE 기준으로 sections/03_scenario.md만 편집한다. 다른 파일은 읽기만. 시작.

**L5:** 너는 이 리포의 레인 L5(시각자료)다. CLAUDE.md, lanes/L5_visual.md, SPINE.md, 그리고 각 섹션 파일을 읽어라. SPINE·섹션 내용 기준으로 visuals/ 안에서만 파일을 만들어 편집한다. 다른 파일은 읽기만. 시작.
