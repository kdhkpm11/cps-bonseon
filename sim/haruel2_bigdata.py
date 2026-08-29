# -*- coding: utf-8 -*-
"""
하루쌤 2.0 v3 — 빅데이터 종합 의사결정 (다중 앙상블 + Ofqual 가드 + 협의)
================================================================================
'하나의 기법'이 아니라 '여러 소견을 종합'한다. 단, 팀 사례집(dlgywp, 81건)의 교훈을 가드레일로.

다중 소견 (모두 종합, 어느 하나가 단독 확정하지 않음)
  ① 개인 궤적(Knowledge Tracing) — 최근 추세. 【최우선】
  ② 규칙 엔진 — 해석가능한 1차 판단
  ③ 빅데이터 2차소견 — 유사 또래 kNN 다수 경로 (참고, 확정 아님)
  ④ 백분위 위치 — 6천명 레퍼런스 대비 상대 위치
  ⑤ Conformal 애매도 → 20% 예산을 데이터가 캘리브레이션
  ⑥ 학생 목소리/협의 — 목표·맥락 선언, 대화 타협

★ Ofqual 가드레일 (사례집 E): '집단 과거통계로 개인을 확정판단' 금지.
  → 빅데이터(③④)는 교사에게 보이는 '2차 소견'일 뿐, 개인 궤적(①)+목소리(⑥)가 언제나 우선.

근거 데이터·기술
  - EdNet(산타토익 78만명): 신호 스키마 + 레퍼런스 분포의 근거 (여기선 그 분포에 맞춘 합성 6천명)
  - OULAD(3.2만명): 환경 프록시 편향 → 접속·카메라 배제 (사례집 B: Homework Gap·다문화 종단)
  - Selective Prediction/Conformal(Angelopoulos&Bates): 20% 예산의 데이터 캘리브레이션
  - 사례집(dlgywp): A 행동신호오독(Proctorio) · B 취약/언어(Stanford GPT탐지) ·
                    C 라벨고착(Pygmalion·Course Signals) · D 감정(EU AI Act 금지) · E 성적자동산정(Ofqual)
"""
import sys, os, random, math, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from haruel2 import Student, Voice, cohort_minwon, cohort_new, slope, ai_hypothesis, reconcile
random.seed(17)

def clip(x, lo, hi): return max(lo, min(hi, x))

# ── 1) 빅데이터 레퍼런스: EdNet 분포에 맞춘 합성 6천명 ─────────
def gen_population(n=6000):
    pop = []
    for _ in range(n):
        acc = clip(random.gauss(0.68, 0.16), 0.05, 0.99)
        tr = random.gauss(0.0, 0.03)
        retry = clip(random.gauss(0.55 - 0.5 * acc, 0.12), 0.0, 1.0)  # 낮은 정답률 → 높은 오답반복
        sub = clip(random.gauss(0.80, 0.18), 0.0, 1.0)
        pop.append(dict(acc=acc, tr=tr, retry=retry, sub=sub))
    return pop

def pct(vals, p):
    s = sorted(vals); k = (len(s) - 1) * p / 100.0
    lo = int(math.floor(k)); hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)

# ── 2) 데이터가 임계값을 정함 (하드코딩 X) ────────────────────
def calibrate(pop):
    A = [x['acc'] for x in pop]; T = [x['tr'] for x in pop]; R = [x['retry'] for x in pop]
    return dict(acc_low=pct(A, 30), acc_high=pct(A, 70),
                trend_grow=pct(T, 70), retry_high=pct(R, 70),
                acc_sd=statistics.pstdev(A), tr_sd=statistics.pstdev(T),
                retry_sd=statistics.pstdev(R))

# ── 3) 규칙 액션(레퍼런스·또래용): 보정 임계값 사용 ───────────
def rule_action(f, th):
    if f['tr'] >= th['trend_grow']:        return "상향(성장)"
    if f['acc'] < th['acc_low'] and f['retry'] >= th['retry_high']: return "기초(취약)"
    if f['acc'] >= th['acc_high']:         return "심화"
    return "표준"

# ── 4) kNN 또래 2차소견 (참고용, 확정 아님) ───────────────────
def knn_opinion(f, pop, th, k=60):
    def d(x):
        return ((f['acc']-x['acc'])/th['acc_sd'])**2 + ((f['tr']-x['tr'])/th['tr_sd'])**2 \
             + ((f['retry']-x['retry'])/th['retry_sd'])**2
    near = sorted(pop, key=d)[:k]
    acts = [rule_action(x, th) for x in near]
    top = max(set(acts), key=acts.count)
    return top, acts.count(top) / k

# ── 5) Conformal 애매도 → 20% 예산 데이터 캘리브레이션 ────────
def ambiguity(f, th):
    # 임계 경계까지의 거리(작을수록 애매) + 신호 상충
    m_low = abs(f['acc'] - th['acc_low']); m_high = abs(f['acc'] - th['acc_high'])
    margin = min(m_low, m_high) / (th['acc_sd'] + 1e-9)
    conflict = 0.0
    if f['acc'] >= th['acc_high'] and f['tr'] < 0: conflict += 0.5   # 고성과인데 하락
    if th['acc_low'] <= f['acc'] < th['acc_high'] and f['retry'] >= th['retry_high']:
        conflict += 0.3
    return clip(1.0 - margin + conflict, 0.0, 2.0)

def conformal_tau(pop, th, budget=0.20):
    scores = sorted(ambiguity(x, th) for x in pop)
    return scores[int((1 - budget) * (len(scores) - 1))]   # 상위 20%가 애매로 잡히는 지점

# ── 6) 앙상블 결정 (개인 궤적·목소리 우선, 빅데이터는 2차소견) ─
def feat(s: Student):
    return dict(acc=s.acc_hist[-1], tr=slope(s.acc_hist), retry=s.retry_rate, sub=s.submit_rate)

def decide_v3(s: Student, pop, th, tau):
    f = feat(s)
    rule = reconcile(s, ai_hypothesis(s))          # ①②⑥ 개인 규칙+목소리(기존 협의 엔진)
    peer, agree = knn_opinion(f, pop, th)          # ③ 빅데이터 2차소견
    amb = ambiguity(f, th)                          # ⑤ 애매도
    p_acc = sum(x['acc'] <= f['acc'] for x in pop) / len(pop)  # ④ 백분위
    # Ofqual 가드: 빅데이터가 개인 판단을 '뒤집지' 못함. 단, 애매+목소리 없을 때만 보류로 끌어올림.
    kind, rec, why, trail = rule
    note = []
    if amb > tau and kind == "자동추천" and not (s.voice.goal or s.voice.context or s.voice.answer):
        # 데이터가 '경계'라 판단 → 자동 대신 학생에게 질문(교사 아님)
        kind, rec = "판단보류", "빅데이터상 경계 → 학생 확인질문 후 결정"
        note.append(f"conformal 애매도 {amb:.2f}>τ{tau:.2f} → 경계로 보류")
    card = dict(id=s.id, kind=kind, rec=rec, why=why,
                peer=f"{peer}({agree:.0%})", pctile=f"상위{(1-p_acc)*100:.0f}%",
                amb=f"{amb:.2f}/τ{tau:.2f}", voice=" · ".join(t for t in trail if "학생" in t) or "—",
                note=" · ".join(note))
    return card

def run(students, title, pop, th, tau):
    print(f"\n{'='*86}\n{title}\n{'='*86}")
    dist = {"자동추천":0,"판단보류":0,"교사검토":0}
    for s in students:
        c = decide_v3(s, pop, th, tau); dist[c['kind']] += 1
        print(f"[{c['id']}] {c['kind']} :: {c['rec']}")
        print(f"     ①개인궤적/규칙: {c['why']}")
        print(f"     ③빅데이터 2차소견(또래 다수): {c['peer']}   ④백분위 {c['pctile']}   ⑤{c['amb']}")
        print(f"     ⑥학생 협의: {c['voice']}" + (f"   ⚠️{c['note']}" if c['note'] else ""))
    n=len(students); df=dist['판단보류']+dist['교사검토']
    print("-"*86)
    print("분포:", " ".join(f"{k} {v}" for k,v in dist.items()),
          f"| 보류+교사 {df}/{n}({df/n:.0%}) [20% {'충족' if df/n<=0.2 else '초과'}]")

if __name__ == "__main__":
    pop = gen_population(6000); th = calibrate(pop); tau = conformal_tau(pop, th, 0.20)
    print(f"[빅데이터 레퍼런스] N={len(pop)} · 보정임계값: "
          f"정답률 하위30%={th['acc_low']:.2f} 상위70%={th['acc_high']:.2f} · "
          f"성장추세≥{th['trend_grow']:+.3f} · conformal τ(20%예산)={tau:.2f}")
    run(cohort_minwon(), "미션3 · v3 빅데이터 종합을 10개 민원에 적용", pop, th, tau)
    run(cohort_new(), "미션4 · 신규 A/B/C 적용", pop, th, tau)
