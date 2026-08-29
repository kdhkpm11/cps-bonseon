# -*- coding: utf-8 -*-
"""
하루쌤 2.0 — AI 학습코치 판단 엔진 (제17회 CPS 본선)
================================================================
설계 철학(예선 '온라인 신고 AI'와 동일): AI는 '신호'만 읽고, 최종 처리는 '규칙'이 정한다.
  - 일관성: 같은 입력 → 같은 처리 (순수 함수 decide())
  - 학생 보호 최우선: 위험/정서위기 신호 앞에서는 점수 무관하게 사람에게 넘긴다
  - 설명가능성: 모든 처리에 근거 문자열을 남긴다 (GDPR Art.22 '설명·인간재검토권')

근거로 삼은 실제 기술·데이터·사례
  - EdNet (Riiid/산타토익, 78만 학생·1억+ 상호작용, KT1~4): 정답률·풀이시간·힌트 신호 스키마의 실제 근거
  - Knowledge Tracing (BKT/DKT): 상태 라벨 대신 '추세(궤적)'로 학습상태 추적 → 민서 고착·신규A 성장 문제 해소
  - Selective Prediction / Learning to Defer (Madras 2018) + Conformal Prediction(Angelopoulos&Bates):
      불확실하면 자동판단을 '기권'하고 사람에게 → '판단보류/교사검토'.
      전체의 20%를 넘지 못하는 제약 = budget-constrained selective classification
  - OULAD (Open University, 3.2만 학생): '제한 지표로 위험학생 예측 시 인구통계·환경 프록시가 편향 유발'이
      벤치마크로 입증됨 → 접속시간·카메라(환경 프록시) '직접 판단 배제' 원칙의 정량 근거
  - 영국 2020 Ofqual A-level 알고리즘(환경으로 성적 강등), AI 감독시험 Proctorio(카메라 오탐·사생활):
      환경 프록시·카메라 오판의 실제 사고 사례 (하린·태오와 동형)
  - AI Hub 감성대화 말뭉치/웰니스 대화: 자기진단(감정) 신호의 정서 분류·위기 감지·상담 거버넌스 참고
"""

from dataclasses import dataclass, field
from typing import List, Optional

# ─────────────────────────────────────────────────────────────
# 1) 학생 신호 모델 (EdNet 스키마에 대응)
#    사용 신호(직접판단): accuracy(+trend), retry_rate, submit_rate, self_report
#    보조 신호(단독판단 금지): solve_time_z, hint_rate
#    배제 신호(직접판단 X, 기록만): access_min, camera_off  ← 환경 프록시
# ─────────────────────────────────────────────────────────────
@dataclass
class Student:
    id: str
    acc_hist: List[float]          # 최근 정답률 궤적 (KT: 추세를 상태보다 우선)
    retry_rate: float              # 오답 반복률 0~1 (이해 vs 실수)
    submit_rate: float             # 과제 제출률 0~1
    self_report: str               # 자기진단 감정 신호: 'ok'|'tired'|'crisis'|'none'
    solve_time_z: float = 0.0      # 풀이시간 표준화(+면 느림) — 보조
    hint_rate: float = 0.0         # 힌트 사용 정도 0~1 — 보조
    picks_hard_ratio: Optional[float] = None  # 어려운 문제 선택 비율(회피 탐지)
    picks_hard_trend: float = 0.0  # 그 비율의 추세(-면 회피 심화)
    # ── 맥락 플래그(환경/언어): 배제·보정 근거로만, 능력·의지 판단엔 직접 불가
    low_home_resource: bool = False  # 하린류: PC 없음/기기 제약
    home_env_camera: bool = False    # 태오류: 주거환경상 카메라 부담
    reading_slow: bool = False       # 서율류: 읽기속도 느림
    language_barrier: bool = False   # 아민류: 한국어 문장 장벽
    collab_flag: bool = False        # 찬이류: 협업으로 답안 유사
    note: str = ""

def slope(xs: List[float]) -> float:
    """정답률 궤적의 단순 기울기(EWMA 대체, 최근 가중). +면 상승."""
    if len(xs) < 2:
        return 0.0
    return (xs[-1] - xs[0]) / (len(xs) - 1)

# ─────────────────────────────────────────────────────────────
# 2) 표시등(오버라이드) — 점수 무관 우회. 예선 '안전표시/정보충분성표시' 대응
# ─────────────────────────────────────────────────────────────
def flag_emotional_crisis(s: Student) -> bool:
    # 자기진단 위기 신호 → 학생 보호 최우선(교사검토 강제)
    return s.self_report == "crisis"

def flag_overload(s: Student) -> bool:
    # 고성과 + 피로 → 과부하(준호·신규B). 심화·증량 대신 감축/상담
    return s.self_report == "tired" and s.acc_hist[-1] >= 0.85

def flag_context_uncertain(s: Student) -> bool:
    # 판단이 환경/언어 프록시에 의존할 뻔한 경우 → 정보 불충분(자동판단 기권)
    return any([s.low_home_resource, s.home_env_camera, s.reading_slow,
                s.language_barrier])

# ─────────────────────────────────────────────────────────────
# 3) 결정 함수 (3구분) — 순수·결정론적. 우선순위대로 분기.
#    반환: (처리유형, 추천/조치, 근거)
#    처리유형 ∈ {자동추천, 판단보류, 교사검토}
# ─────────────────────────────────────────────────────────────
def decide(s: Student):
    acc = s.acc_hist[-1]
    tr = slope(s.acc_hist)

    # ① 정서위기 → 교사검토 (점수 무관, 학생 보호 최우선)
    if flag_emotional_crisis(s):
        return ("교사검토", "정서적 상담 연계 + 학습량 일시 감축",
                "자기진단 위기신호 → 점수 무관 사람 개입(안전 오버라이드)")

    # ② 과부하(고성과+피로) → 교사검토(번아웃 예방)
    if flag_overload(s):
        return ("교사검토", "심화·증량 중단, 휴식·상담 권고",
                f"정답률 {acc:.0%} 높으나 피로신호 → 과부하 위험, 증량 금지")

    # ③ 협업 유사(부정 오판 방지) → 교사검토(맥락 확인)
    if s.collab_flag:
        return ("교사검토", "부정행위 자동판정 보류, 협업 여부 교사 확인",
                "답안 유사=협업 가능 → 자동 처벌 금지(행동 의도 구분)")

    # ④ 맥락/언어 불확실 → 판단보류 (환경 프록시로 능력·의지 단정 금지)
    if flag_context_uncertain(s):
        why = []
        if s.low_home_resource: why.append("접속·제출은 가정환경 종속(의지 아님)")
        if s.home_env_camera:   why.append("카메라off는 주거환경(집중도 아님)")
        if s.reading_slow:      why.append("풀이시간 김=읽기속도(기초부족 아님)")
        if s.language_barrier:  why.append("문장형 저정답률=언어장벽(수학 아님)")
        # 단, 정답률 자체가 견고하면 표준학습으로 자동 처리(불이익 라벨 배제)
        if acc >= 0.6 and s.retry_rate <= 0.3:
            return ("자동추천", "표준 학습(맥락 보정, 환경 지표 미반영)",
                    "핵심신호(정답률·오답반복) 양호 → 환경 프록시 무시하고 자동")
        return ("판단보류", "환경 지표 제외한 재관측 + 학습환경 지원 제안",
                " / ".join(why))

    # ⑤ 회피 패턴(정답률 높지만 쉬운 것만) → 판단보류(도전 유도)
    if s.picks_hard_ratio is not None and s.picks_hard_ratio < 0.3 and s.picks_hard_trend < 0:
        return ("판단보류", "난이도 상향 '탐색 과제' 소량 제시 후 재관측",
                f"정답률 {acc:.0%} 양호하나 어려운문제 선택 감소 → '문제없음' 오판 방지")

    # ⑥ 다지표 교차 + 추세 → 자동추천 (핵심 경로)
    #    a. 성장 중(추세↑): 낮은 절대값이어도 격려·표준으로 (고착 방지)
    if tr >= 0.03 and s.submit_rate >= 0.6:
        rec = "심화 도전(소량)" if acc >= 0.7 else "표준 학습(상향 유지)"
        return ("자동추천", rec,
                f"정답률 {s.acc_hist[0]:.0%}→{acc:.0%} 상승추세 + 성실 → 성장 반영(라벨 고착 배제)")
    #    b. 이해 취약(정답률↓ & 오답반복↑): 기초/표준 반복
    if acc < 0.6 and s.retry_rate >= 0.4:
        return ("자동추천", "취약개념 기초 반복 + 단계적 표준",
                f"정답률 {acc:.0%}·오답반복 {s.retry_rate:.0%} 일치 → 개념 보강")
    #    c. 안정 고성과: 심화 도전
    if acc >= 0.75 and s.retry_rate <= 0.25:
        return ("자동추천", "심화·프로젝트형 도전",
                f"정답률 {acc:.0%}·낮은 오답반복 일치 → 상향 도전")

    # ⑦ 그 외(신호 상충/애매) → 판단보류
    return ("판단보류", "탐색 과제 제공하며 1~2주 재관측",
            "핵심신호 간 상충/추세 애매 → 자동 단정 대신 관측")

# ─────────────────────────────────────────────────────────────
# 4) 20% 예산 제약 (selective prediction budget)
#    보류+교사검토가 전체의 20%를 넘으면 '경계 사례'부터 자동추천으로 내림.
#    단, 정서위기(안전 오버라이드) 확정건은 강등 대상에서 제외.
# ─────────────────────────────────────────────────────────────
def apply_budget(results, students, cap=0.20):
    n = len(results)
    limit = max(1, int(n * cap))
    deferred_idx = [i for i, r in enumerate(results) if r[0] in ("판단보류", "교사검토")]
    if len(deferred_idx) <= limit:
        return results, f"보류/교사검토 {len(deferred_idx)}/{n} ≤ 한도 {limit} → 제약 충족"
    # 강등 우선순위: 안전 오버라이드(정서위기)는 보호. 나머지 중 정답률 견고한 순.
    protect = {i for i in deferred_idx if flag_emotional_crisis(students[i])}
    movable = [i for i in deferred_idx if i not in protect]
    movable.sort(key=lambda i: students[i].acc_hist[-1], reverse=True)  # 견고한 것부터 자동화
    need = len(deferred_idx) - limit
    moved = []
    for i in movable[:need]:
        results[i] = ("자동추천", "표준 학습(예산 제약 하 경계사례 자동화)",
                      results[i][2] + " | 20%예산 초과로 경계사례 자동 전환")
        moved.append(students[i].id)
    return results, f"보류/교사검토 {len(deferred_idx)}>한도{limit} → 경계 {moved} 자동 전환(정서위기 보호)"

# ─────────────────────────────────────────────────────────────
# 5) 정보 거버넌스 — 민감정보(자기진단) 수신자·수준
# ─────────────────────────────────────────────────────────────
def governance(s: Student):
    if s.self_report in ("crisis", "tired"):
        return ("본인=전체 / 교사=위기플래그+상담제안(요약) / 학부모=원문 금지, '상담 권장'만",
                "감정 원문의 학부모 직행 차단(소연 신뢰붕괴 방지) — AI Hub 웰니스 거버넌스 참고")
    return ("본인=전체 / 교사=요약 / 학부모=학습요약만", "민감신호 없음")

# ─────────────────────────────────────────────────────────────
# 6) 데이터: 10개 민원(J1~J10=민서~유나) + 신규 A/B/C
#    ※ 문제는 질적 서술 → 표면 신호 기반 근사값(가정). 값의 '방향'이 판단을 만든다.
# ─────────────────────────────────────────────────────────────
def cohort_minwon():
    return [
        Student("민서", acc_hist=[0.55, 0.66, 0.74, 0.80], retry_rate=0.15, submit_rate=0.85,
                self_report="ok", note="과거 낮은분류 고착, 실력 회복(상승추세)"),
        Student("준호", acc_hist=[0.90, 0.91, 0.92, 0.92], retry_rate=0.10, submit_rate=1.0,
                self_report="tired", note="고정답률→매일 심화+추가과제→밤늦게(과부하)"),
        Student("하린", acc_hist=[0.68, 0.70, 0.69, 0.71], retry_rate=0.20, submit_rate=0.60,
                self_report="ok", low_home_resource=True, note="PC無, 폰으로 잠깐→접속짧고 제출늦음"),
        Student("태오", acc_hist=[0.72, 0.73, 0.74, 0.74], retry_rate=0.18, submit_rate=0.90,
                self_report="ok", home_env_camera=True, note="주거환경상 카메라off"),
        Student("서율", acc_hist=[0.70, 0.72, 0.73, 0.75], retry_rate=0.15, submit_rate=0.88,
                self_report="ok", solve_time_z=1.6, reading_slow=True, note="읽기 느림, 시간주면 정확"),
        Student("도윤", acc_hist=[0.60, 0.66, 0.70, 0.73], retry_rate=0.22, submit_rate=0.85,
                self_report="ok", hint_rate=0.7, note="힌트 후 노트정리→개선(학습전략)"),
        Student("아민", acc_hist=[0.55, 0.58, 0.60, 0.62], retry_rate=0.35, submit_rate=0.9,
                self_report="ok", language_barrier=True, note="계산OK·문장형 저정답률(언어)"),
        Student("소연", acc_hist=[0.70, 0.71, 0.70, 0.72], retry_rate=0.18, submit_rate=0.85,
                self_report="crisis", note="자기진단 '지치고 힘들다'→부모 직행 신뢰붕괴"),
        Student("찬이", acc_hist=[0.74, 0.75, 0.76, 0.77], retry_rate=0.14, submit_rate=0.9,
                self_report="ok", collab_flag=True, note="모둠 협업→답안 유사=부정 오판"),
        Student("유나", acc_hist=[0.86, 0.87, 0.88, 0.88], retry_rate=0.10, submit_rate=1.0,
                self_report="ok", picks_hard_ratio=0.15, picks_hard_trend=-0.05,
                note="정답률 높으나 쉬운것만·어려운건 회피"),
    ]

def cohort_new():
    return [
        Student("신규A", acc_hist=[0.41, 0.48, 0.54, 0.58], retry_rate=0.30, submit_rate=1.0,
                self_report="ok", solve_time_z=1.2, hint_rate=0.6, note="낮지만 4주 연속 상승"),
        Student("신규B", acc_hist=[0.92, 0.92, 0.92, 0.92], retry_rate=0.08, submit_rate=0.60,
                self_report="tired", solve_time_z=-1.0, note="고정답률·짧은접속·제출60%·피곤 반복"),
        Student("신규C", acc_hist=[0.75, 0.76, 0.76, 0.76], retry_rate=0.15, submit_rate=0.9,
                self_report="ok", picks_hard_ratio=0.2, picks_hard_trend=-0.06,
                note="안정 76%지만 어려운문제 선택 감소·풀어본 유형만"),
    ]

# ─────────────────────────────────────────────────────────────
# 7) 실행 & 출력 (미션3: 민원 / 미션4: 신규)
# ─────────────────────────────────────────────────────────────
def run(students, title):
    results = [decide(s) for s in students]
    results, budget_msg = apply_budget(results, students)
    print(f"\n{'='*78}\n{title}\n{'='*78}")
    print(f"{'학생':<6}{'처리':<8}{'추천/조치':<28}근거")
    print("-" * 78)
    dist = {"자동추천": 0, "판단보류": 0, "교사검토": 0}
    for s, (kind, rec, why) in zip(students, results):
        dist[kind] += 1
        print(f"{s.id:<6}{kind:<8}{rec:<28}{why}")
    n = len(students)
    print("-" * 78)
    print("분포:", " ".join(f"{k} {v}({v/n:.0%})" for k, v in dist.items()))
    defer = dist["판단보류"] + dist["교사검토"]
    print(f"보류+교사검토 = {defer}/{n} ({defer/n:.0%})  [예산 20% {'충족' if defer/n<=0.2 else '초과'}]")
    print("예산처리:", budget_msg)
    # 거버넌스 필요 사례
    gov = [(s.id,) + governance(s) for s in students if s.self_report in ("crisis", "tired")]
    if gov:
        print("\n[정보 거버넌스 — 민감(감정) 신호 학생]")
        for sid, level, why in gov:
            print(f"  {sid}: {level}")
    return results

if __name__ == "__main__":
    run(cohort_minwon(), "미션3 · 하루쌤 2.0을 10개 민원 학생에게 적용")
    run(cohort_new(), "미션4 · 신규 학생 A/B/C에게 적용")
