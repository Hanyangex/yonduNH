import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="농협 가결산 및 경영 손익 추정 시스템",
    layout="wide"
)

st.title("🌾 농협 가결산 및 경영 손익 추정 시스템")
st.caption("사업부문별 추정 손익, 적립금 시뮬레이션 및 목표 달성 매출을 역산합니다.")

st.markdown("---")

# ==========================================
# 1. 사이드바 - 실적 및 정책 입력
# ==========================================
st.sidebar.header("🏢 1. 사업부문별 추정 실적")

with st.sidebar.expander("💳 신용사업부문", expanded=True):
    credit_rev = st.number_input("신용 추정 매출 (원)", value=6_000_000_000, step=100_000_000, format="%d")
    credit_exp = st.number_input("신용 추정 비용 (원)", value=4_500_000_000, step=100_000_000, format="%d")

with st.sidebar.expander("🛒 경제사업부문", expanded=True):
    econ_rev = st.number_input("경제 추정 매출 (원)", value=6_000_000_000, step=100_000_000, format="%d")
    econ_exp = st.number_input("경제 추정 비용 (원)", value=5_500_000_000, step=100_000_000, format="%d")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 2. 법인세 및 적립 정책")

tax_rate = st.sidebar.slider("추정 법인세율 (%)", min_value=0.0, max_value=25.0, value=9.0, step=0.5) / 100
reserve_rate = st.sidebar.slider("법정/사업준비 적립률 (%)", min_value=10.0, max_value=50.0, value=20.0, step=1.0) / 100

# 손익 기본 계산
credit_profit = credit_rev - credit_exp
econ_profit = econ_rev - econ_exp
total_revenue = credit_rev + econ_rev
total_expense = credit_exp + econ_exp

pre_tax_income = total_revenue - total_expense
tax_amount = max(0.0, pre_tax_income * tax_rate)
estimated_net_income = pre_tax_income - tax_amount

reserve_amount = estimated_net_income * reserve_rate if estimated_net_income > 0 else 0
retained_earnings = max(0.0, estimated_net_income - reserve_amount)

# ==========================================
# 2. 메인 대시보드
# ==========================================
st.subheader("📊 1. 가결산 추정 요약")

m1, m2, m3, m4 = st.columns(4)
m1.metric("추정 총매출", f"{total_revenue:,.0f} 원")
m2.metric("추정 세전순이익", f"{pre_tax_income:,.0f} 원")
m3.metric("추정 당기순이익", f"{estimated_net_income:,.0f} 원", delta=f"법인세 {tax_amount:,.0f} 원")
m4.metric("법정 적립금", f"{reserve_amount:,.0f} 원", delta=f"사내유보 {retained_earnings:,.0f} 원")

st.markdown("---")

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
    st.markdown("**부문별 순이익 기여도**")
    profit_df = pd.DataFrame({
        "부문": ["신용사업 순이익", "경제사업 순이익"],
        "금액": [max(0, credit_profit), max(0, econ_profit)]
    })
    fig_profit = px.pie(profit_df, values="금액", names="부문", hole=0.4,
                        color_discrete_sequence=["#1f77b4", "#2ca02c"])
    st.plotly_chart(fig_profit, use_container_width=True)

st.markdown("---")

# ==========================================
# 3. [신규] 목표 당기순이익 역산 시뮬레이터 (Goal Seek)
# ==========================================
st.subheader("🎯 2. 목표 당기순이익 달성을 위한 필요 매출 역산")

target_net_income = st.number_input(
    "달성하고자 하는 목표 당기순이익 (원)", 
    value=int(estimated_net_income if estimated_net_income > 0 else 2_000_000_000), 
    step=100_000_000, 
    format="%d"
)

# 역산 로직 (목표 세전이익 = 목표 순이익 / (1 - 법인세율))
required_pre_tax = target_net_income / (1 - tax_rate)
required_total_rev = required_pre_tax + total_expense
additional_rev_needed = required_total_rev - total_revenue

c1, c2 = st.columns(2)
with c1:
    st.info(f"📌 **필요 세전순이익**: {required_pre_tax:,.0f} 원")
with c2:
    if additional_rev_needed <= 0:
        st.success(f"🎉 현재 추정 매출로도 목표 당기순이익을 달성할 수 있습니다! (초과: {abs(additional_rev_needed):,.0f} 원)")
    else:
        st.warning(f"⚠️ 목표 달성을 위해 추가로 필요한 총매출: **{additional_rev_needed:,.0f} 원**")

st.markdown("---")

# ==========================================
# 4. 임원 보고용 요약서 출력
# ==========================================
st.subheader("📑 3. 이사회 및 임원 보고용 가결산 요약서")

report_html = f"""
<div style="border: 2px solid #333; padding: 25px; border-radius: 8px; background-color: #fcfcfc;">
    <h2 style="text-align: center; color: #1a4314; margin-bottom: 20px;">[보고서] 연말 가결산 및 경영손익 추정서</h2>
    <hr style="border: 1px solid #ccc;">
    
    <h3>1. 사업부문별 손익 추정 (단위: 원)</h3>
    <table style="width:100%; border-collapse: collapse; text-align: left; margin-bottom: 20px;">
        <tr style="background-color: #f2f2f2;">
            <th style="padding: 8px; border: 1px solid #ddd;">구분</th>
            <th style="padding: 8px; border: 1px solid #ddd;">신용사업</th>
            <th style="padding: 8px; border: 1px solid #ddd;">경제사업</th>
            <th style="padding: 8px; border: 1px solid #ddd;">합계</th>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>추정 매출</b></td>
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
            <td style="padding: 8px; border: 1px solid #ddd;"><b>부문별 순이익</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{credit_profit:,.0f}</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{econ_profit:,.0f}</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{pre_tax_income:,.0f}</b></td>
        </tr>
    </table>
    
    <h3>2. 최종 이익 추정 및 적립 계획</h3>
    <ul>
        <li><b>세전 순이익:</b> {pre_tax_income:,.0f} 원</li>
        <li><b>추정 법인세 ({tax_rate*100:.1f}%):</b> {tax_amount:,.0f} 원</li>
        <li><b>추정 당기순이익:</b> <span style="color:red; font-weight:bold;">{estimated_net_income:,.0f} 원</span></li>
        <li><b>법정 및 사업적립금 ({reserve_rate*100:.1f}%):</b> {reserve_amount:,.0f} 원</li>
        <li><b>차기 이월 / 사내 유보금:</b> {retained_earnings:,.0f} 원</li>
    </ul>
</div>
"""

st.components.v1.html(report_html, height=450, scrolling=True)