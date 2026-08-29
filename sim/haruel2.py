# -*- coding: utf-8 -*-
"""
하루쌤 2.0 — 협의형(協議) AI 학습코치 (제17회 CPS 본선)
================================================================
창의적 핵심: AI는 '판단'하지 않고 '제안'한다. 최종은 '학생의 목소리와의 합의'다.
  기존 하루쌤의 근본 불만 = "AI가 내 상황을 제대로 이해 못한다".
  → 처방은 신호를 더 잘 읽는 것이 아니라, 학생에게 '말할 권리'를 주는 것.

3층 협의 구조 (신호 → 가설 → 학생 목소리 → 합의)
  1) AI 가설: 신호로 '잠정' 판단 + 확신도 산출 (판단이 아니라 초안)
  2) 학생 목소리(1급 신호):
       - 목표 선언(goal): 도전/휴식/기초 — 행동 프록시로 '추론'하던 의도를 직접 받음
       - 맥락 선언(context): "PC 없음", "한국어 어려움" — 환경 프록시를 학생이 스스로 무효화
       - 이의/응답(answer): 확신 낮으면 교사에게 떠넘기지 않고 학생에게 1문항 질문
  3) 합의(reconcile): 목소리로 가설을 수정·확정. 그래도 위험/미해결이면 교사검토.
  → '판단보류'가 "교사 떠넘기기"에서 "학생과의 대화"로 바뀐다.

근거(실제 기술·데이터·사례)
  - EdNet(산타토익 78만명): 정답률·풀이시간·힌트 신호 스키마
  - Knowledge Tracing(BKT/DKT): 라벨 대신 '추세'로 학습상태 추적
  - Selective Prediction / Learning to Defer(Madras 2018)+Conformal: 20% budget-constrained abstention
      단, 본 설계는 defer 대상을 '교사'가 아니라 우선 '학생'으로 → contestability(이의제기권)
  - OULAD(3.2만명): 환경 프록시 편향 정량근거 → 접속시간·카메라 직접판단 배제
  - Ofqual 2020 A-level / Proctorio: 환경 프록시·카메라 오판 실제 사고(하린·태오와 동형)
  - AI Hub 감성/웰니스: 자기진단 정서분류·상담 거버넌스
  - GDPR Art.22: 자동결정에 대한 '설명·이의·인간재검토' 권리 → 학생 이의제기를 1급 절차로
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ── 학생 목소리(1급 신호) ─────────────────────────────────────
@dataclass
class Voice:
    goal: str = ""       # 'challenge'(도전) | 'rest'(휴식) | 'basics'(기초) | ''(무언)
    context: str = ""    # 맥락 선언(자유): 예 "가정에 PC 없음", "한국어 문장이 어려움"
    answer: str = ""     # 확신 낮을 때 AI 질문에 대한 학생 응답

# ── 학생 신호 모델(EdNet 스키마) ──────────────────────────────
@dataclass
class Student:
    id: str
    acc_hist: List[float]
    retry_rate: float
    submit_rate: float
    self_report: str = "ok"     # 'ok'|'tired'|'crisis'
    solve_time_z: float = 0.0   # 보조(단독판단 금지)
    hint_rate: float = 0.0      # 보조
    picks_hard_ratio: Optional[float] = None
    picks_hard_trend: float = 0.0
    # 배제 신호(직접판단 X, 기록만): access_min, camera_off — 환경 프록시
    voice: Voice = field(default_factory=Voice)
    note: str = ""

def slope(xs: List[float]) -> float:
    return 0.0 if len(xs) < 2 else (xs[-1] - xs[0]) / (len(xs) - 1)

# ── 1) AI 가설 (신호만으로 '잠정' + 확신 + 필요시 질문) ─────────
def ai_hypothesis(s: Student) -> Dict:
    acc, tr = s.acc_hist[-1], slope(s.acc_hist)

    # 안전: 정서위기 → 확신과 무관하게 사람. (학생 목소리로도 못 덮음)
    if s.self_report == "crisis":
        return dict(kind="교사검토", rec="정서 상담 연계 + 학습량 감축",
                    why="자기진단 위기신호(안전 오버라이드)", conf="high", q="")

    # 과부하(고성과+피로): 감축이 정답(자동), 단 학생 확인 권함
    if s.self_report == "tired" and acc >= 0.85:
        return dict(kind="자동추천", rec="증량 중단 → 학습량 감축",
                    why=f"정답률 {acc:.0%}+피로 → 과부하", conf="mid",
                    q="요즘 학습량이 부담되나요? (예=감축 / 아니오=현행 유지)")

    # 회피(고정답률·쉬운 것만): 탐색과제(자동), 학생 의사 확인
    if s.picks_hard_ratio is not None and s.picks_hard_ratio < 0.3 and s.picks_hard_trend < 0:
        return dict(kind="자동추천", rec="난이도 상향 '탐색 과제' 소량",
                    why=f"정답률 {acc:.0%}인데 어려운문제 회피", conf="mid",
                    q="더 어려운 문제에 도전해 볼래요? (예=심화 / 아니오=성공경험 위주)")

    # 성장추세: 낮은 절대값도 상향 격려(고착 배제)
    if tr >= 0.03 and s.submit_rate >= 0.6:
        rec = "심화 도전(소량)" if acc >= 0.7 else "표준 학습(상향 유지)"
        return dict(kind="자동추천", rec=rec,
                    why=f"{s.acc_hist[0]:.0%}→{acc:.0%} 상승추세+성실", conf="high", q="")

    # 이해 취약(정답률↓ & 오답반복↑): 개념 보강(자동)
    if acc < 0.6 and s.retry_rate >= 0.4:
        return dict(kind="자동추천", rec="취약개념 기초 반복 + 단계적 표준",
                    why=f"정답률 {acc:.0%}·오답반복 {s.retry_rate:.0%} 일치", conf="high", q="")

    # 안정 고성과: 심화
    if acc >= 0.75 and s.retry_rate <= 0.25:
        return dict(kind="자동추천", rec="심화·프로젝트형 도전",
                    why=f"정답률 {acc:.0%}·낮은 오답반복", conf="high", q="")

    # 신호 애매(풀이시간 김·정답률 애매 등) → 확신 낮음. 교사 아닌 '학생에게 질문'.
    return dict(kind="질문", rec="", conf="low",
                why=f"정답률 {acc:.0%}·풀이시간 신호 애매 → 단정 불가",
                q="문제가 어려웠나요, 아니면 천천히 정확히 푸는 편인가요? "
                  "(어려움 / 천천히정확 / 한국어문장이어려움)")

# ── 2) 합의: 학생 목소리로 가설을 수정·확정 ───────────────────
def reconcile(s: Student, h: Dict):
    v, trail = s.voice, []

    # 위험(교사검토 안전건)은 목소리로 못 덮음
    if h["kind"] == "교사검토":
        return ("교사검토", h["rec"], h["why"], ["안전 오버라이드: 목소리로 불가"])

    # (a) 맥락 선언 → 환경/언어 프록시 해석을 학생이 무효화
    if v.context:
        trail.append(f"학생 맥락선언: “{v.context}”")
        if any(k in v.context for k in ["PC", "기기", "폰", "집", "환경", "가정"]):
            trail.append("→ 접속·카메라·풀이시간 배제(환경 프록시)")
            if s.acc_hist[-1] >= 0.6 and s.retry_rate <= 0.3:
                return ("자동추천", "표준 학습(환경 지표 미반영)", h["why"],
                        trail + ["→ 핵심신호(정답률·오답반복) 양호 → 환경 배제하고 자동"])
        if any(k in v.context for k in ["한국어", "언어", "문장"]):
            return ("자동추천", "언어 지원(읽기보조)+계산·문장형 분리 측정",
                    h["why"], trail + ["→ 저정답률=언어장벽, 능력 단정 안 함(학생 선언 근거)"])

    # (b) 목표 선언 → 추론하던 의도를 직접 반영 (안전건 제외)
    if v.goal:
        trail.append(f"학생 목표선언: {v.goal}")
        if v.goal == "rest":
            return ("자동추천", "학습량 감축 + 회복 루틴", h["why"],
                    trail + ["→ 학생이 휴식 원함: 고성과여도 증량 안 함"])
        if v.goal == "challenge":
            return ("자동추천", "심화·도전 과제", h["why"],
                    trail + ["→ 학생이 도전 원함: 회피/고착 라벨 해제"])
        if v.goal == "basics":
            return ("자동추천", "기초 개념 재정비", h["why"],
                    trail + ["→ 학생이 기초 원함"])

    # (c) 확신 낮음(질문) → 학생 응답으로 애매성 해소 (교사 아님)
    if h["kind"] == "질문":
        if not v.answer:
            return ("판단보류", "학생에게 확인 질문 발송(응답 대기)", h["why"],
                    trail + [f"질문: {h['q']}", "→ 교사 아닌 학생과 대화로 해소"])
        a = v.answer
        trail.append(f"학생 응답: “{a}”")
        if "한국어" in a or "언어" in a:
            return ("자동추천", "언어 지원(읽기보조)", h["why"], trail + ["→ 언어장벽 확인"])
        if "천천히" in a or "정확" in a:
            return ("자동추천", "표준 학습(속도 페널티 없음)", h["why"], trail + ["→ 능력 정상, 시간 신호 무효"])
        if "어려" in a:
            return ("자동추천", "취약개념 기초 반복", h["why"], trail + ["→ 난이도 조정"])
        return ("판단보류", "응답 불명확, 재질문", h["why"], trail)

    # (d) 목소리 없음 → AI 가설 그대로 확정(단, 학생 확인용 질문은 첨부)
    tail = [f"(확인질문: {h['q']})"] if h["q"] else []
    return (h["kind"], h["rec"], h["why"], trail + tail)

def decide(s: Student):
    return reconcile(s, ai_hypothesis(s))

# ── 3) 20% 예산 (backstop) ────────────────────────────────────
def apply_budget(results, students, cap=0.20):
    n = len(results); limit = max(1, int(n * cap))
    deferred = [i for i, r in enumerate(results) if r[0] in ("판단보류", "교사검토")]
    if len(deferred) <= limit:
        return results, f"보류/교사검토 {len(deferred)}/{n} ≤ 한도 {limit} → 충족"
    protect = {i for i in deferred if students[i].self_report == "crisis"}
    movable = sorted([i for i in deferred if i not in protect],
                     key=lambda i: students[i].acc_hist[-1], reverse=True)
    for i in movable[:len(deferred) - limit]:
        results[i] = ("자동추천", "표준 학습(예산 제약 경계 자동화)", results[i][2],
                      results[i][3] + ["20%예산 초과→경계 자동전환"])
    return results, f"보류/교사검토 {len(deferred)}>{limit} → 경계 자동전환(위기 보호)"

# ── 4) 거버넌스 ───────────────────────────────────────────────
def governance(s: Student):
    if s.self_report in ("crisis", "tired"):
        return "본인=전체 / 교사=위기플래그+요약 / 학부모=원문 금지, '상담 권장'만"
    return "본인=전체 / 교사=요약 / 학부모=학습요약만"

# ── 5) 데이터: 민원 10 + 신규 A/B/C (일부에 학생 목소리 부여) ──
def cohort_minwon():
    return [
        Student("민서", [0.55,0.66,0.74,0.80], 0.15, 0.85, note="고착→회복(상승추세)"),
        Student("준호", [0.90,0.91,0.92,0.92], 0.10, 1.0, self_report="tired",
                voice=Voice(goal="rest", context="매일 심화가 부담됨"), note="과부하"),
        Student("하린", [0.68,0.70,0.69,0.71], 0.20, 0.60,
                voice=Voice(context="집에 PC 없어 폰으로 잠깐 함"), note="환경(접속 프록시)"),
        Student("태오", [0.72,0.73,0.74,0.74], 0.18, 0.90,
                voice=Voice(context="집이 좁아 카메라 켜기 부담"), note="환경(카메라)"),
        Student("서율", [0.70,0.72,0.73,0.75], 0.15, 0.88, solve_time_z=1.6,
                voice=Voice(answer="천천히 정확히 푸는 편"), note="읽기 느림→질문으로 해소"),
        Student("도윤", [0.60,0.66,0.70,0.73], 0.22, 0.85, hint_rate=0.7, note="힌트=학습전략+성장"),
        Student("아민", [0.55,0.58,0.60,0.62], 0.35, 0.9,
                voice=Voice(context="한국어 문장이 어려움"), note="언어장벽(학생 선언)"),
        Student("소연", [0.70,0.71,0.70,0.72], 0.18, 0.85, self_report="crisis", note="정서위기"),
        Student("찬이", [0.74,0.75,0.76,0.77], 0.14, 0.9, note="협업(부정 오판)"),
        Student("유나", [0.86,0.87,0.88,0.88], 0.10, 1.0, picks_hard_ratio=0.15, picks_hard_trend=-0.05,
                voice=Voice(goal="challenge"), note="회피→학생은 도전 원함"),
    ]

def cohort_new():
    return [
        Student("신규A", [0.41,0.48,0.54,0.58], 0.30, 1.0, solve_time_z=1.2, hint_rate=0.6, note="상승추세"),
        Student("신규B", [0.92,0.92,0.92,0.92], 0.08, 0.60, self_report="tired", note="번아웃 신호"),
        Student("신규C", [0.75,0.76,0.76,0.76], 0.15, 0.9, picks_hard_ratio=0.2, picks_hard_trend=-0.06, note="회피"),
    ]

# ── 6) 실행 ───────────────────────────────────────────────────
def run(students, title):
    results = [decide(s) for s in students]
    results, budget = apply_budget(results, students)
    print(f"\n{'='*84}\n{title}\n{'='*84}")
    dist = {"자동추천":0,"판단보류":0,"교사검토":0}
    for s,(kind,rec,why,trail) in zip(students,results):
        dist[kind]+=1
        voice = " · ".join(t for t in trail if "학생" in t) or "—"
        print(f"[{s.id}] {kind} :: {rec}")
        print(f"     신호근거: {why}")
        print(f"     협의(학생목소리): {voice}")
    n=len(students); defer=dist['판단보류']+dist['교사검토']
    print("-"*84)
    print("분포:", " ".join(f"{k} {v}({v/n:.0%})" for k,v in dist.items()),
          f"| 보류+교사 {defer}/{n}({defer/n:.0%}) [20% {'충족' if defer/n<=0.2 else '초과'}]")
    print("예산:", budget)

if __name__ == "__main__":
    run(cohort_minwon(), "미션3 · 협의형 하루쌤 2.0을 10개 민원에 적용")
    run(cohort_new(), "미션4 · 신규 A/B/C 적용")
