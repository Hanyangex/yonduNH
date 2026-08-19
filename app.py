import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="농협 종합 가결산 및 경영 진단 시스템",
    layout="wide"
)

st.title("🌾 농협 종합 가결산 및 경영 진단 시스템")
st.caption("누적 실적 기반 연말 추정, 전년대비 비교, 손익분기점(BEP) 및 경영 리스크 진단을 제공합니다.")

st.markdown("---")

# ==========================================
# 1. 사이드바 - 입력 파라미터
# ==========================================
st.sidebar.header("🗓️ 1. 가결산 기준 시점")
current_month = st.sidebar.slider("현재 누적 실적 기준 월", min_value=1, max_value=11, value=9)
remaining_months = 12 - current_month

st.sidebar.markdown("---")
st.sidebar.header("🏢 2. 사업부문별 실적 입력")

# 신용사업
with st.sidebar.expander("💳 신용사업부문", expanded=True):
    credit_rev_cum = st.number_input(f"신용 누적 매출 (1~{current_month}월)", value=4_500_000_000, step=100_000_000, format="%d")
    credit_rev_monthly = st.number_input(f"신용 예상 월매출 ({current_month+1}~12월)", value=500_000_000, step=50_000_000, format="%d")
    
    credit_exp_cum = st.number_input(f"신용 누적 비용 (1~{current_month}월)", value=3_300_000_000, step=100_000_000, format="%d")
    credit_exp_monthly = st.number_input(f"신용 예상 월비용 ({current_month+1}~12월)", value=400_000_000, step=50_000_000, format="%d")

# 경제사업
with st.sidebar.expander("🛒 경제사업부문", expanded=True):
    econ_rev_cum = st.number_input(f"경제 누적 매출 (1~{current_month}월)", value=4_200_000_000, step=100_000_000, format="%d")
    econ_rev_monthly = st.number_input(f"경제 예상 월매출 ({current_month+1}~12월)", value=600_000_000, step=50_000_000, format="%d")
    
    econ_exp_cum = st.number_input(f"경제 누적 비용 (1~{current_month}월)", value=4_000_000_000, step=100_000_000, format="%d")
    econ_exp_monthly = st.number_input(f"경제 예상 월비용 ({current_month+1}~12월)", value=500_000_000, step=50_000_000, format="%d")

st.sidebar.markdown("---")
st.sidebar.header("📊 3. 전년도 실적 비교 데이터")
last_year_rev = st.sidebar.number_input("전년도 총매출", value=11_000_000_000, step=100_000_000, format="%d")
last_year_net = st.sidebar.number_input("전년도 당기순이익", value=1_200_000_000, step=50_000_000, format="%d")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 4. 법인세 및 적립 정책")
tax_rate = st.sidebar.slider("추정 법인세율 (%)", min_value=0.0, max_value=25.0, value=9.0, step=0.5) / 100
reserve_rate = st.sidebar.slider("법정/사업준비 적립률 (%)", min_value=10.0, max_value=50.0, value=20.0, step=1.0) / 100

# ==========================================
# 2. 실적 연산 및 계산 엔진
# ==========================================
# [기능 1] 월별 누적 실적 기반 연말 실적 추정 (Run-rate)
credit_rev = credit_rev_cum + (credit_rev_monthly * remaining_months)
credit_exp = credit_exp_cum + (credit_exp_monthly * remaining_months)
econ_rev = econ_rev_cum + (econ_rev_monthly * remaining_months)
econ_exp = econ_exp_cum + (econ_exp_monthly * remaining_months)

credit_profit = credit_rev - credit_exp
econ_profit = econ_rev - econ_exp

total_revenue = credit_rev + econ_rev
total_expense = credit_exp + econ_exp

pre_tax_income = total_revenue - total_expense
tax_amount = max(0.0, pre_tax_income * tax_rate)
estimated_net_income = pre_tax_income - tax_amount

reserve_amount = estimated_net_income * reserve_rate if estimated_net_income > 0 else 0
retained_earnings = max(0.0, estimated_net_income - reserve_amount)

# [기능 3] 전년 대비(YoY) 계산
rev_yoy_growth = ((total_revenue - last_year_rev) / last_year_rev * 100) if last_year_rev > 0 else 0
net_yoy_growth = ((estimated_net_income - last_year_net) / last_year_net * 100) if last_year_net > 0 else 0

# ==========================================
# 3. [기능 4] 경영 상태 진단 및 위험 알림 시스템
# ==========================================
st.subheader("🚨 경영 상태 진단 및 리스크 알림")

alert_cols = st.columns(3)
with alert_cols[0]:
    if econ_profit < 0:
        st.error(f"⚠️ **경제사업 적자 주의**: 경제사업부문 손익이 {econ_profit:,.0f}원 적자 예상됩니다.")
    else:
        st.success(f"✅ **경제사업 흑자 유지**: 경제사업 순이익 {econ_profit:,.0f}원")

with alert_cols[1]:
    if net_yoy_growth < 0:
        st.warning(f"📉 **순이익 감소 경보**: 전년 대비 당기순이익이 {abs(net_yoy_growth):.1f}% 감소할 예상입니다.")
    else:
        st.success(f"📈 **순이익 성장 중**: 전년 대비 당기순이익 {net_yoy_growth:.1f}% 증가 예상")

with alert_cols[2]:
    profit_margin = (estimated_net_income / total_revenue * 100) if total_revenue > 0 else 0
    if profit_margin < 5.0:
        st.info(f"💡 **순이익률 관리를 요함**: 현재 추정 매출액 대비 순이익률은 {profit_margin:.1f}%입니다.")
    else:
        st.success(f"✅ **우수한 수익성**: 추정 매출액 대비 순이익률 {profit_margin:.1f}%")

st.markdown("---")

# ==========================================
# 4. 가결산 추정 요약 대시보드 (YoY 포함)
# ==========================================
st.subheader("📊 1. 연말 가결산 손익 추정 대시보드")

m1, m2, m3, m4 = st.columns(4)
m1.metric("추정 총매출", f"{total_revenue:,.0f} 원", delta=f"전년대비 {rev_yoy_growth:+.1f}%")
m2.metric("추정 세전순이익", f"{pre_tax_income:,.0f} 원", delta=f"법인세 {tax_amount:,.0f}원 차감전")
m3.metric("추정 당기순이익", f"{estimated_net_income:,.0f} 원", delta=f"전년대비 {net_yoy_growth:+.1f}%")
m4.metric("법정 적립금", f"{reserve_amount:,.0f} 원", delta=f"사내유보 {retained_earnings:,.0f}원")

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("**사업부문별 매출/비용 손익 비교**")
    biz_df = pd.DataFrame({
        "부문": ["신용사업", "신용사업", "경제사업", "경제사업"],
        "구분": ["매출", "비용", "매출", "비용"],
        "금액": [credit_rev, credit_exp, econ_rev, econ_exp]
    })
    fig_biz = px.bar(biz_df, x="부문", y="금액", color="구분", barmode="group",
                     color_discrete_map={"매출": "#2b5c8f", "비용": "#d9534f"})
    st.plotly_chart(fig_biz, use_container_width=True)

with col2:
    st.markdown("**전년 vs 올해 당기순이익 비교**")
    yoy_df = pd.DataFrame({
        "연도": ["전년도 실적", "올해 추정치"],
        "당기순이익": [last_year_net, estimated_net_income]
    })
    fig_yoy = px.bar(yoy_df, x="연도", y="당기순이익", color="연도",
                     color_discrete_sequence=["#a6a6a6", "#2e7d32"])
    st.plotly_chart(fig_yoy, use_container_width=True)

st.markdown("---")

# ==========================================
# 5. [기능 2] 손익분기점(BEP) 산정 및 분석
# ==========================================
st.subheader("⚖️ 2. 손익분기점(BEP) 및 매출 견딤력 분석")

st.caption("비용 중 고정비 비중을 지정하여 적자를 면하기 위한 최소 필요 매출을 산출합니다.")
fixed_cost_ratio = st.slider("추정 비용 중 고정비 비중 (%)", min_value=10, max_value=90, value=60, step=5) / 100

fixed_cost = total_expense * fixed_cost_ratio
variable_cost = total_expense * (1 - fixed_cost_ratio)
variable_cost_ratio = variable_cost / total_revenue if total_revenue > 0 else 0

# 손익분기점 매출 = 고정비 / (1 - 변동비비율)
bep_revenue = fixed_cost / (1 - variable_cost_ratio) if (1 - variable_cost_ratio) > 0 else 0
safety_margin = total_revenue - bep_revenue
safety_margin_ratio = (safety_margin / total_revenue * 100) if total_revenue > 0 else 0

bep_col1, bep_col2 = st.columns(2)
with bep_col1:
    st.info(f"📌 **손익분기점(BEP) 매출액**: **{bep_revenue:,.0f} 원**")
    st.caption(f"* 고정비: {fixed_cost:,.0f}원 / 변동비: {variable_cost:,.0f}원 기준")

with bep_col2:
    if safety_margin >= 0:
        st.success(f"🛡️ **안전지대 (Safety Margin)**: 현재 추정 매출이 BEP보다 **{safety_margin:,.0f} 원 ({safety_margin_ratio:.1f}%)** 여유가 있습니다.")
    else:
        st.error(f"🚨 **손익분기점 미달**: 현재 추정 매출이 BEP보다 **{abs(safety_margin):,.0f} 원** 부족하여 적자 위험이 있습니다.")

st.markdown("---")

# ==========================================
# 6. 임원 및 이사회 보고용 요약 리포트
# ==========================================
st.subheader("📑 3. 이사회 및 임원 보고용 가결산 요약서")

report_html = f"""
<div style="border: 2px solid #333; padding: 25px; border-radius: 8px; background-color: #fcfcfc;">
    <h2 style="text-align: center; color: #1a4314; margin-bottom: 20px;">[보고서] 2026년도 종합 가결산 및 경영 손익 추정서</h2>
    <p style="text-align: right; color: #666;">기준 시점: 1~{current_month}월 실적 누적 + {remaining_months}개월 추정 반영</p>
    <hr style="border: 1px solid #ccc;">
    
    <h3>1. 총괄 손익 추정 (단위: 원)</h3>
    <table style="width:100%; border-collapse: collapse; text-align: left; margin-bottom: 20px;">
        <tr style="background-color: #f2f2f2;">
            <th style="padding: 8px; border: 1px solid #ddd;">구분</th>
            <th style="padding: 8px; border: 1px solid #ddd;">신용사업부문</th>
            <th style="padding: 8px; border: 1px solid #ddd;">경제사업부문</th>
            <th style="padding: 8px; border: 1px solid #ddd;">합계 (2026년 추정)</th>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>추정 매출액</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{credit_rev:,.0f}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{econ_rev:,.0f}</td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{total_revenue:,.0f}</b></td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>추정 비용</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{credit_exp:,.0f}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{econ_exp:,.0f}</td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{total_expense:,.0f}</b></td>
        </tr>
        <tr style="background-color: #fcf8e3;">
            <td style="padding: 8px; border: 1px solid #ddd;"><b>부문별 순손익</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{credit_profit:,.0f}</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{econ_profit:,.0f}</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{pre_tax_income:,.0f}</b></td>
        </tr>
    </table>
    
    <h3>2. 주요 경영 지표 및 처분 추정</h3>
    <ul>
        <li><b>전년 대비 매출 증감률:</b> {rev_yoy_growth:+.1f}% (전년 총매출: {last_year_rev:,.0f} 원)</li>
        <li><b>추정 당기순이익:</b> <span style="color:red; font-weight:bold;">{estimated_net_income:,.0f} 원</span> (전년 대비 {net_yoy_growth:+.1f}%)</li>
        <li><b>손익분기점(BEP) 매출액:</b> {bep_revenue:,.0f} 원 (안전율 {safety_margin_ratio:.1f}%)</li>
        <li><b>법정 및 사업적립금 ({reserve_rate*100:.1f}%):</b> {reserve_amount:,.0f} 원</li>
        <li><b>차기 이월 유보금:</b> {retained_earnings:,.0f} 원</li>
    </ul>
</div>
"""

st.components.v1.html(report_html, height=500, scrolling=True)