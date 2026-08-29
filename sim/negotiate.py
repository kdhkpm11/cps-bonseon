# -*- coding: utf-8 -*-
"""
하루쌤 2.0 — 다중 턴 대화 협상 (학생 ↔ AI, 타협점 수렴)
================================================================
단발 협의를 넘어, AI와 학생이 '왕복 대화'로 절충안을 찾는다.
  - 협상 축 2개: 난이도(level -1기초/0표준/+1심화), 부하(load -1감축/0유지/+1증량)
  - AI는 신호 기반 목표를, 학생은 자기 희망을 제시 → 매 턴 한 발씩 접근 + 안전장치 부착
  - 수렴: 학생 수용 시 '합의'. 근본 충돌(안전)·미수렴 시에만 교사검토.
근거: GDPR Art.22(이의제기·인간개입), 자기조절학습(SRL)의 목표설정·협상,
      선택적 예측(defer 대상을 '교사'가 아니라 우선 '학생'으로 → contestability).
"""
LV = {-1: "기초", 0: "표준", 1: "심화"}
LD = {-1: "감축", 0: "유지", 1: "증량"}
def sgn(x): return (x > 0) - (x < 0)

def negotiate(name, ai_lv, ai_ld, why, wish_lv, wish_ld,
              safety=False, student_caution="", max_turns=4):
    """왕복 대화로 (level, load) 타협. 반환: (대화록, 최종처리, 최종추천)."""
    T = []
    if safety:
        T.append(("AI", f"{name} 학생, 지금은 학습 난이도보다 컨디션이 우선이에요. "
                         "선생님과 함께 이야기하는 게 좋겠어요."))
        return T, "교사검토", "상담 우선(협상 대상 아님)"

    T.append(("AI", f"신호를 보면 '{LV[ai_lv]}·부하 {LD[ai_ld]}'를 추천해요. {why} 어때요?"))
    cur_lv, cur_ld = ai_lv, ai_ld
    turn = 0
    while (cur_lv, cur_ld) != (wish_lv, wish_ld) and turn < max_turns:
        turn += 1
        # 학생: 자기 희망 제시(+주의사항)
        msg = f"저는 '{LV[wish_lv]}·{LD[wish_ld]}'가 좋아요."
        if student_caution and turn == 1:
            msg += f" 다만 {student_caution}"
        T.append(("학생", msg))
        # AI: 한 발 접근 + 학생이 신호보다 세게 밀면 안전장치 부착
        nlv = cur_lv + sgn(wish_lv - cur_lv)
        nld = cur_ld + sgn(wish_ld - cur_ld)
        guards = []
        if nlv > ai_lv:  guards.append("스캐폴딩·힌트 허용")
        if nld > ai_ld:  guards.append("피로도 모니터링")
        if nlv < ai_lv:  guards.append("지루하면 즉시 상향")
        after = f" ({', '.join(guards)}, 2주 뒤 함께 재평가)" if guards else ""
        if (nlv, nld) == (wish_lv, wish_ld):
            T.append(("AI", f"좋아요, '{LV[nlv]}·{LD[nld]}'로 하되{after or ' 진행할게요'}. 이대로 갈까요?"))
        else:
            T.append(("AI", f"그럼 '{LV[nlv]}·{LD[nld]}'로 절충하는 건 어때요?{after}"))
        cur_lv, cur_ld = nlv, nld

    T.append(("학생", "좋아요, 그렇게 해볼게요."))
    return T, "자동추천(합의)", f"{LV[cur_lv]} · 부하 {LD[cur_ld]}"

def show(name, *args, **kw):
    T, kind, rec = negotiate(name, *args, **kw)
    print(f"\n── {name} · 다중 턴 협상 ─────────────────")
    for spk, line in T:
        who = "🤖AI  " if spk == "AI" else "🧑학생"
        print(f"  {who} | {line}")
    print(f"  ▶ 합의: [{kind}] {rec}")

if __name__ == "__main__":
    print("="*66 + "\n대화 타협 데모 (신호 목표 ≠ 학생 희망일 때 절충 수렴)\n" + "="*66)
    # 사례1: 신호는 기초인데 학생은 심화를 원함 → 표준+스캐폴딩으로 타협
    show("하늘", ai_lv=-1, ai_ld=0, why="정답률·오답반복상 기초가 안전해요.",
         wish_lv=1, wish_ld=0, student_caution="쉬운 것만 반복하는 건 지루해요.")
    # 사례2: 준호 — 신호는 감축인데 학생은 성적 유지 걱정 → 부하는 감축하되 질 유지 타협
    show("준호", ai_lv=0, ai_ld=-1, why="정답률은 높지만 피로 신호가 보여요.",
         wish_lv=0, wish_ld=0, student_caution="쉬긴 싫고 성적은 유지하고 싶어요.")
    # 사례3: 유나 — 회피형, 신호 표준인데 학생이 도전 원함 → 심화 합의(빠른 수렴)
    show("유나", ai_lv=0, ai_ld=0, why="지금도 잘하지만 쉬운 문제 위주예요.",
         wish_lv=1, wish_ld=0)
    # 사례4: 안전(정서위기) — 협상 대상 아님 → 교사
    show("소연", ai_lv=0, ai_ld=-1, why="", wish_lv=1, wish_ld=1, safety=True)
