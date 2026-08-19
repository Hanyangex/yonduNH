import streamlit as st
import pandas as pd
import plotly.express as px
import io

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="농협 가결산 및 배당 통합 관리 시스템",
    layout="wide"
)

st.title("🌾 농협 가결산 및 조합원 배당 통합 관리 시스템")
st.caption("사업부문별 실적 추정부터 조합원별 엑셀 배당 산정, 보고서 출력까지 한 번에 처리합니다.")

st.markdown("---")

# ==========================================
# [기능 1] 사업부문별 세부 실적 입력 및 합산
# ==========================================
st.sidebar.header("🏢 1. 사업부문별 추정 실적 입력")

with st.sidebar.expander("💳 신용사업부문", expanded=True):
    credit_rev = st.number_input("신용 추정 매출 (원)", value=6_000_000_000, step=100_000_000, format="%d")
    credit_exp = st.number_input("신용 추정 비용 (원)", value=4_500_000_000, step=100_000_000, format="%d")

with st.sidebar.expander("🛒 경제사업부문 (마트/가공/판매 등)", expanded=True):
    econ_rev = st.number_input("경제 추정 매출 (원)", value=6_000_000_000, step=100_000_000, format="%d")
    econ_exp = st.number_input("경제 추정 비용 (원)", value=5_500_000_000, step=100_000_000, format="%d")

# 전체 실적 합산
total_revenue = credit_rev + econ_rev
total_expense = credit_exp + econ_exp

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 2. 배당 및 적립 정책 설정")

tax_rate = st.sidebar.slider("추정 법인세율 (%)", min_value=0.0, max_value=25.0, value=9.0, step=0.5) / 100
reserve_rate = st.sidebar.slider("법정/사업준비 적립률 (%)", min_value=10.0, max_value=50.0, value=20.0, step=1.0) / 100
capital_div_rate = st.sidebar.slider("목표 출자배당률 (%)", min_value=0.0, max_value=10.0, value=3.5, step=0.1) / 100

# ==========================================
# 2. 손익 및 배당 기본 계산
# ==========================================
pre_tax_income = total_revenue - total_expense
tax_amount = max(0.0, pre_tax_income * tax_rate)
estimated_net_income = pre_tax_income - tax_amount

reserve_amount = estimated_net_income * reserve_rate if estimated_net_income > 0 else 0
distributable_income = max(0.0, estimated_net_income - reserve_amount)

# ==========================================
# [기능 2] 엑셀(CSV) 업로드 및 전체 조합원 일괄 계산
# ==========================================
st.subheader("📂 1. 전체 조합원 명단 업로드 및 배당 일괄 계산")

st.markdown("""
* **업로드 엑셀 파일 필수 열(Column) 명칭**: `조합원명`, `출자금`, `이용고실적`
* 샘플 데이터가 없으시면 아래 '샘플 양식 다운로드'를 활용해 보세요.
""")

# 샘플 데이터 생성 버튼
sample_df = pd.DataFrame({
    "조합원명": ["홍길동", "김농협", "이사업", "박배당", "최출자"],
    "출자금": [10000000, 5000000, 20000000, 15000000, 8000000],
    "이용고실적": [3000000, 8000000, 2000000, 12000000, 5000000]
})

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    sample_df.to_excel(writer, index=False)

st.download_button(
    label="📥 엑셀 샘플 양식 다운로드",
    data=buffer.getvalue(),
    file_name="조합원명단_샘플.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

uploaded_file = st.file_uploader("조합원 명단 엑셀/CSV 파일을 업로드하세요", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        member_df = pd.read_csv(uploaded_file)
    else:
        member_df = pd.read_excel(uploaded_file)

    # 필수 컬럼 체크
    required_cols = {"조합원명", "출자금", "이용고실적"}
    if set(required_cols).issubset(member_df.columns):
        total_capital = member_df["출자금"].sum()
        total_usage_points = member_df["이용고실적"].sum()

        # 배당금 산정
        capital_dividend_total = min(total_capital * capital_div_rate, distributable_income)
        usage_dividend_total = max(0.0, distributable_income - capital_dividend_total)
        unit_usage_div = (usage_dividend_total / total_usage_points) if total_usage_points > 0 else 0

        # 개별 조합원 배당 계산
        member_df["출자배당금"] = member_df["출자금"] * capital_div_rate
        member_df["이용고배당금"] = member_df["이용고실적"] * unit_usage_div
        member_df["총배당금"] = member_df["출자배당금"] + member_df["이용고배당금"]

        st.success(f"총 {len(member_df)}명의 조합원 데이터 처리 완료!")
    else:
        st.error(f"엑셀 파일에 {required_cols} 열이 포함되어 있는지 확인해 주세요.")
        st.stop()
else:
    # 파일 미업로드 시 기본 가상 데이터 사용
    total_capital = 15_000_000_000
    total_usage_points = 8_000_000_000
    capital_dividend_total = min(total_capital * capital_div_rate, distributable_income)
    usage_dividend_total = max(0.0, distributable_income - capital_dividend_total)
    unit_usage_div = (usage_dividend_total / total_usage_points) if total_usage_points > 0 else 0
    member_df = None
    st.info("💡 엑셀 파일을 업로드하지 않으면 기본 추정 총량(출자금 150억 / 이용고 80억)으로 계산됩니다.")

st.markdown("---")

# ==========================================
# 대시보드 및 결과 조회
# ==========================================
st.subheader("📊 2. 가결산 추정 대시보드")

m1, m2, m3, m4 = st.columns(4)
m1.metric("추정 총매출", f"{total_revenue:,.0f} 원")
m2.metric("추정 당기순이익", f"{estimated_net_income:,.0f} 원")
m3.metric("배당가능이익", f"{distributable_income:,.0f} 원")
m4.metric("이용고 pt당 배당액", f"{unit_usage_div:.4f} 원")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("**사업부문별 매출/비용 구성**")
    biz_df = pd.DataFrame({
        "부문": ["신용사업", "신용사업", "경제사업", "경제사업"],
        "구분": ["매출", "비용", "매출", "비용"],
        "금액": [credit_rev, credit_exp, econ_rev, econ_exp]
    })
    fig_biz = px.bar(biz_df, x="부문", y="금액", color="구분", barmode="group",
                     color_discrete_map={"매출": "#2b5c8f", "비용": "#d9534f"})
    st.plotly_chart(fig_biz, use_container_width=True)

with col2:
    st.markdown("**당기순이익 처분 구성비**")
    if estimated_net_income > 0:
        pie_df = pd.DataFrame({
            "구분": ["법정/사업적립금", "출자배당금", "이용고배당금"],
            "금액": [reserve_amount, capital_dividend_total, usage_dividend_total]
        })
        fig_pie = px.pie(pie_df, values="금액", names="구분", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

# 업로드된 조합원 계산 결과 테이블 및 다운로드
if member_df is not None:
    st.markdown("**명단별 계산 결과**")
    st.dataframe(
        member_df.style.format({
            "출자금": "{:,.0f}", "이용고실적": "{:,.0f}",
            "출자배당금": "{:,.0f}", "이용고배당금": "{:,.0f}", "총배당금": "{:,.0f}"
        }),
        use_container_width=True
    )
    
    # 계산 결과 엑셀 다운로드 버튼
    out_buffer = io.BytesIO()
    with pd.ExcelWriter(out_buffer, engine='openpyxl') as writer:
        member_df.to_excel(writer, index=False, sheet_name="배당산정결과")
    
    st.download_button(
        label="📥 전체 조합원 배당 산정 결과(엑셀) 다운로드",
        data=out_buffer.getvalue(),
        file_name="조합원_배당산정_결과.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")

# ==========================================
# [기능 3] 보고서 자동 생성 및 인쇄/PDF 출력
# ==========================================
st.subheader("📑 3. 이사회 및 임원 보고용 가결산 요약서")

report_html = f"""
<div style="border: 2px solid #333; padding: 25px; border-radius: 8px; background-color: #fcfcfc;">
    <h2 style="text-align: center; color: #1a4314; margin-bottom: 20px;">[보고서] 2026년도 연말 가결산 및 배당 추정서</h2>
    <hr style="border: 1px solid #ccc;">
    
    <h3>1. 총괄 손익 추정 (단위: 원)</h3>
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
    </table>
    
    <ul>
        <li><b>세전 순이익:</b> {pre_tax_income:,.0f} 원</li>
        <li><b>추정 법인세 ({tax_rate*100:.1f}%):</b> {tax_amount:,.0f} 원</li>
        <li><b>추정 당기순이익:</b> <span style="color:red; font-weight:bold;">{estimated_net_income:,.0f} 원</span></li>
    </ul>

    <h3>2. 이익처분 및 배당 계획</h3>
    <ul>
        <li><b>법정 및 사업적립금 ({reserve_rate*100:.1f}%):</b> {reserve_amount:,.0f} 원</li>
        <li><b>배당 가능 이익:</b> {distributable_income:,.0f} 원</li>
        <li><b>총 출자배당금 (배당률 {capital_div_rate*100:.1f}%):</b> {capital_dividend_total:,.0f} 원</li>
        <li><b>총 이용고배당금:</b> {usage_dividend_total:,.0f} 원 (1pt당 {unit_usage_div:.4f}원)</li>
    </ul>
</div>
"""

st.components.v1.html(report_html, height=450, scrolling=True)