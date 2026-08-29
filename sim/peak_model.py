# 한결시 폭염·전력 위기 — 피크/정전/온열질환 토이 시뮬레이션
# 목적: 세 전략의 장단점을 '수치'로 뒷받침. 모든 가정에 이유 명시.
# 정밀 예측 아님 → '상대 비교'용 모델. 절대치는 가정 기반.

# ---- 기저 가정(근거) ----
P0   = 900.0   # 여름 평시 피크수요 MW. 가정: 인구45만 중견도시 여름 피크 규모(1인당 냉방기 여름피크 ~2kW급 추정)
CAP0 = 950.0   # 노후 변전 안정공급 한계 MW. 가정: 문제상 "피크가 노후설비 한계 초과→정전" → 한계가 피크에 근접(여유~5.5%)
k    = 0.03    # 기온1℃↑당 피크 상승률. 가정: 냉방수요 기온탄력성 ~3%/℃(일반 범위)
TBASE= 33.0    # 냉방 급증 시작 기온(℃). 가정: 33℃부터 냉방부하 급증
HMAX = 12.0    # 하루 최대 정전시간(h) 상한(초과율 100%일 때)

def peak(T, dT=0.0):            # 유효기온 T에서 피크수요
    return P0*(1 + k*((T-dT)-TBASE))

def outage_h(pk, cap):         # 하루 정전시간(h): 한계 초과율 비례
    if pk <= cap: return 0.0
    o = (pk-cap)/cap
    return min(HMAX, o*100*0.9)   # 초과 1%p당 ~0.9h, 12h 상한

def heat_cases(T, h):          # 하루 온열질환자(명, 도시 전체) — 상대비교용
    heat = 0.6*max(0,(T-TBASE))**1.3   # 폭염 자체
    black = 3.2*h                        # 정전 냉방중단 가중(취약계층 노출)
    return heat + black

# ---- 전략별 효과(가정, 근거) ----
# 전략1 공급: 성숙기 한계 +8%(변전증설+ESS). 단 태양광은 야간/흐린날 기여 제한 → 열대야(S2)엔 +3%만. ESS 피크시프트 -3%.
# 전략2 수요: 성숙기 피크 -12%(DR+단열+누적). 녹지로 유효기온 -1℃. (효과 램프업: 1년 -3% → 10년 -15%)
# 전략3 사람: 피크/한계 불변. 정전 온열가중 -70%(쉼터·우선복구·돌봄) → black*0.3.

def run(name, T, days, night=False):
    # 기저
    pk = peak(T); cap = CAP0; h = outage_h(pk,cap); c = heat_cases(T,h)*days
    base = (pk, cap, h, c)
    # 전략1
    cap1 = CAP0*(1.03 if night else 1.08); pk1 = pk*0.97; h1=outage_h(pk1,cap1); c1=heat_cases(T,h1)*days
    # 전략2 (성숙기)
    pk2 = peak(T, dT=1.0)*0.88; h2=outage_h(pk2,CAP0); c2=heat_cases(T-1.0,h2)*days
    # 전략3
    h3 = h; heat = 0.6*max(0,(T-TBASE))**1.3; c3=(heat + 3.2*h3*0.3)*days
    print(f"\n=== {name}: T_eff={T}℃, {days}일{' (열대야·야간피크 지속)' if night else ''} ===")
    print(f"{'':8}{'피크MW':>8}{'한계MW':>8}{'초과%':>7}{'정전h/일':>9}{'온열질환(누적)':>14}")
    def row(tag,pk,cap,h,c):
        ex=(pk-cap)/cap*100
        print(f"{tag:8}{pk:8.0f}{cap:8.0f}{ex:7.1f}{h:9.1f}{c:14.0f}")
    row("기저",*base)
    row("전략1",pk1,cap1,h1,c1)
    row("전략2",pk2,CAP0,h2,c2)
    row("전략3",pk, CAP0,h3,c3)
    return base,(pk1,cap1,h1,c1),(pk2,CAP0,h2,c2),(pk,CAP0,h3,c3)

# ---- 시나리오 ----
run("S1 단기 극한폭염", T=40.0, days=3)
run("S2 장기 열대야",   T=36.0, days=14, night=True)

# ---- 10년 비용지수(가정, 근거=문제 서술 순: 1 설치·부지 최대 > 3 매년운영 > 2 초기후 저비용) ----
print("\n=== 10년 비용지수(가정) ===  전략1=100 / 전략3=45 / 전략2=60  (문제: 1 설치·부지 부담 / 3 매년 운영비 / 2 장기 낭비절감)")
