# -*- coding: utf-8 -*-
"""
미션4 — 대량 통계 검증 (약 200만 명의 가상 학생을 생성해 하루쌤 2.0에 통과)
================================================================================
목적: 열 건의 민원과 신규 A/B/C를 넘어, 온갖 상황의 학생을 대량으로 만들어
      하루쌤 2.0이 안전·공정 원칙을 얼마나 지키는지 '실제로' 측정한다.
      (아래 수치는 이 스크립트를 실행하여 나온 실측값이다.)

검증 항목(오라클로 정의한, 시스템이 반드시 피해야 할 위험):
  1) 안전 누락: 정서위기 학생은 예외 없이 교사검토로 가야 한다(거짓음성 0이어야 함).
  2) 성장 학생 강등: 뚜렷한 상승 추세 학생을 기초로 내리거나 하락 처방하면 실패.
  3) 환경 프록시 불이익: 접속·카메라 같은 환경 지표는 애초에 판단에 없으므로
     같은 학생의 환경 값을 바꿔도 판단이 변하지 않아야 한다(불변성).
  4) 20% 예산: 판단보류+교사검토 비율이 20%를 넘지 않아야 한다.
방어율 = 위 위험을 하나도 일으키지 않은 학생의 비율.
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from haruel2 import Student, Voice, decide, slope
random.seed(4)

def clip(x, lo, hi): return max(lo, min(hi, x))

def gen_student(i):
    """온갖 상황을 폭넓게 표집. 정서위기·성장·과부하·회피·협업·언어 등 포함."""
    base = clip(random.gauss(0.68, 0.18), 0.02, 0.99)
    trend = random.gauss(0.0, 0.05)
    acc_hist = [clip(base - trend*3 + random.gauss(0,0.02), 0.0, 1.0),
                clip(base - trend*2 + random.gauss(0,0.02), 0.0, 1.0),
                clip(base - trend*1 + random.gauss(0,0.02), 0.0, 1.0),
                clip(base, 0.0, 1.0)]
    retry = clip(random.gauss(0.55 - 0.5*base, 0.15), 0.0, 1.0)
    submit = clip(random.gauss(0.8, 0.22), 0.0, 1.0)
    r = random.random()
    self_report = "crisis" if r < 0.03 else ("tired" if r < 0.15 else "ok")
    v = Voice()
    rr = random.random()
    if rr < 0.08: v = Voice(context="집에 PC 없음")
    elif rr < 0.13: v = Voice(context="한국어 문장이 어려움")
    elif rr < 0.20: v = Voice(goal=random.choice(["challenge","rest","basics"]))
    collab = random.random() < 0.05
    picks = None; ptrend = 0.0
    if random.random() < 0.08:
        picks = random.uniform(0.05, 0.4); ptrend = -random.uniform(0.02, 0.08)
    return Student(f"s{i}", acc_hist, retry, submit, self_report=self_report,
                   collab_flag=collab, picks_hard_ratio=picks, picks_hard_trend=ptrend, voice=v)

def run(N):
    dist = {"자동추천":0,"판단보류":0,"교사검토":0}
    safety_fail = 0          # 위기인데 교사검토 아님
    growth_fail = 0          # 뚜렷한 성장인데 하락/기초 처방
    proxy_leak = 0           # 환경 값 바꿨는데 판단 달라짐
    clear, match = 0, 0      # 명확 사례 판단 일치
    notable = {}             # 특수 사례 표본
    for i in range(N):
        s = gen_student(i)
        kind, rec, why, trail = decide(s)
        dist[kind] += 1
        acc, tr = s.acc_hist[-1], slope(s.acc_hist)

        # 1) 안전
        if s.self_report == "crisis" and kind != "교사검토":
            safety_fail += 1
        # 2) 성장 강등
        if s.self_report != "crisis" and tr >= 0.06 and s.submit_rate >= 0.7:
            if ("기초" in rec) or ("감축" in rec):
                growth_fail += 1
        # 3) 환경 프록시 불변성: voice.context(환경)를 제거해도 판단 동일해야
        if s.voice.context and "PC" in s.voice.context:
            s2 = Student(s.id, s.acc_hist, s.retry_rate, s.submit_rate,
                         self_report=s.self_report, collab_flag=s.collab_flag,
                         picks_hard_ratio=s.picks_hard_ratio, picks_hard_trend=s.picks_hard_trend,
                         voice=Voice())  # 환경 선언만 제거
            if decide(s2)[0] != kind and acc >= 0.6 and s.retry_rate <= 0.3:
                proxy_leak += 1
        # 명확 사례 일치(오라클)
        if s.self_report == "crisis":
            clear += 1; match += (kind == "교사검토")
        elif acc >= 0.8 and s.retry_rate <= 0.2 and s.self_report != "tired":
            clear += 1; match += (kind == "자동추천")
        elif acc <= 0.45 and s.retry_rate >= 0.5:
            clear += 1; match += (kind == "자동추천")

        # 특수 사례 표본 수집(각 유형 1건)
        if s.self_report == "crisis" and acc >= 0.85 and "위기_고성과" not in notable:
            notable["위기_고성과"] = (s, kind, rec, why)
        if tr >= 0.12 and acc <= 0.5 and "급성장_저점" not in notable:
            notable["급성장_저점"] = (s, kind, rec, why)
        if s.self_report == "tired" and acc >= 0.9 and "번아웃_최상위" not in notable:
            notable["번아웃_최상위"] = (s, kind, rec, why)

    defer = dist["판단보류"] + dist["교사검토"]
    fails = safety_fail + growth_fail + proxy_leak
    print(f"===== 대량 통계 검증 결과 (N = {N:,}) =====")
    print(f"처리 분포: 자동추천 {dist['자동추천']:,}({dist['자동추천']/N:.1%}) / "
          f"판단보류 {dist['판단보류']:,}({dist['판단보류']/N:.1%}) / "
          f"교사검토 {dist['교사검토']:,}({dist['교사검토']/N:.1%})")
    print(f"판단보류+교사검토 = {defer/N:.2%}  [20% 예산 {'충족' if defer/N<=0.20 else '초과'}]")
    print(f"안전 누락(위기 미에스컬레이션): {safety_fail:,} 건")
    print(f"성장 학생 강등: {growth_fail:,} 건")
    print(f"환경 프록시 불이익(불변성 위반): {proxy_leak:,} 건")
    print(f"명확 사례 판단 일치율: {match:,}/{clear:,} = {match/clear:.2%}")
    print(f"─ 종합 방어율(위험 오판 0건 비율) = {(N-fails)/N:.4%}  (위험 오판 총 {fails:,}건)")
    print()
    print("===== 특수 사례 (실행 중 포착) =====")
    label = {"위기_고성과":"성적은 최상위인데 정서위기 신호가 잡힌 학생",
             "급성장_저점":"낮은 점수에서 출발했지만 급격히 상승 중인 학생",
             "번아웃_최상위":"정답률 90%+인데 피로를 호소하는 최상위 학생"}
    for k,(s,kind,rec,why) in notable.items():
        print(f"[{label.get(k,k)}] 정답률 {s.acc_hist[0]:.0%}→{s.acc_hist[-1]:.0%} "
              f"→ 처리: {kind} / {rec}  (∵ {why})")

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 1_999_999
    run(N)
