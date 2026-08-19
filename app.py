import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="한양고속 차량 자산 및 경영 관리 시스템",
    layout="wide"
)

st.title("🚌 한양고속 차량 자산 및 경영 관리 시스템")
st.caption("차량 차령·감가상각 관리, 노선별 운송손익 추정, BEP 및 운행 리스크 진단을 제공합니다.")

st.markdown("---")

# ==========================================
# 1. 사이드바 - 차량 자산 및 운수 실적 입력
# ==========================================
st.sidebar.header("🗓️ 1. 실적 산정 기준")
current_month = st.sidebar.slider("현재 누적 실적 기준 월", min_value=1, max_value=11, value=9)
remaining_months = 12 - current_month

st.sidebar.markdown("---")
st.sidebar.header("🚌 2. 노선/사업부문별 실적")

# 고속/우등 노선부문
with st.sidebar.expander("🛣️ 고속/우등노선 부문", expanded=True):
    express_rev_cum = st.number_input(f"고속노선 누적 수입 (1~{current_month}월)", value=5_500_000_000, step=100_000_000, format="%d")
    express_rev_monthly = st.number_input(f"고속노선 예상 월수입 ({current_month+1}~12월)", value=600_000_000, step=50_000_000, format="%d")
    
    express_exp_cum = st.number_input(f"고속노선 누적 비용 (1~{current_month}월)", value=4_200_000_000, step=100_000_000, format="%d")
    express_exp_monthly = st.number_input(f"고속노선 예상 월비용 ({current_month+1}~12월)", value=450_000_000, step=50_000_000, format="%d")

# 시외/전세/부가사업 부문
with st.sidebar.expander("🚐 시외/전세/터미널 부문", expanded=True):
    other_rev_cum = st.number_input(f"기타사업 누적 수입 (1~{current_month}월)", value=2_200_000_000, step=100_000_000, format="%d")
    other_rev_monthly = st.number_input(f"기타사업 예상 월수입 ({current_month+1}~12월)", value=250_000_000, step=50_000_000, format="%d")
    
    other_exp_cum = st.number_input(f"기타사업 누적 비용 (1~{current_month}월)", value=2_000_000_000, step=100_000_000, format="%d")
    other_exp_monthly = st.number_input(f"기타사업 예상 월비용 ({current_month+1}~12월)", value=220_000_000, step=50_000_000, format="%d")

st.sidebar.markdown("---")
st.sidebar.header("📊 3. 전년도 경영 비교 데이터")
last_year_rev = st.sidebar.number_input("전년도 총 운송수입", value=9_500_000_000, step=100_000_000, format="%d")
last_year_net = st.sidebar.number_input("전년도 당기순이익", value=800_000_000, step=50_000_000, format="%d")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 4. 세금 및 차량 감가상각 설정")
tax_rate = st.sidebar.slider("추정 법인세율 (%)", min_value=0.0, max_value=25.0, value=10.0, step=0.5) / 100
depreciation_rate = st.sidebar.slider("차량 감가상각 충당률 (%)", min_value=5.0, max_value=30.0, value=15.0, step=1.0) / 100

# ==========================================
# 2. 경영 실적 및 차량 자산 연산
# ==========================================
express_rev = express_rev_cum + (express_rev_monthly * remaining_months)
express_exp = express_exp_cum + (express_exp_monthly * remaining_months)
other_rev = other_rev_cum + (other_rev_monthly * remaining_months)
other_exp = other_exp_cum + (other_exp_monthly * remaining_months)

express_profit = express_rev - express_exp
other_profit = other_rev - other_exp

total_revenue = express_rev + other_rev
total_expense = express_exp + other_exp

pre_tax_income = total_revenue - total_expense
tax_amount = max(0.0, pre_tax_income * tax_rate)
estimated_net_income = pre_tax_income - tax_amount

# 감가상각 및 차기 차량 대폐차 적립금
depreciation_amount = estimated_net_income * depreciation_rate if estimated_net_income > 0 else 0
retained_earnings = max(0.0, estimated_net_income - depreciation_amount)

# 전년 대비 증감
rev_yoy_growth = ((total_revenue - last_year_rev) / last_year_rev * 100) if last_year_rev > 0 else 0
net_yoy_growth = ((estimated_net_income - last_year_net) / last_year_net * 100) if last_year_net > 0 else 0

# ==========================================
# 3. [개선] 보유 버스 자산 파일 업로드 및 자동 계산 함수
# ==========================================
def calculate_bus_asset(df):
    # 필수 컬럼 검증
    required_cols = {"차량번호", "차종", "담당 노선", "최초등록일"}
    if not required_cols.issubset(set(df.columns)):
        return None, f"엑셀 파일에 다음 필수 열이 포함되어야 합니다: {', '.join(required_cols)}"

    # 날짜 형식을 datetime으로 변환
    df["최초등록일"] = pd.to_datetime(df["최초등록일"])
    current_year = datetime.now().year

    # 잔여 차령 자동 계산 (기본 법정 차령 10년 기준)
    df["잔여 차령(년)"] = df["최초등록일"].apply(lambda d: max(0, 10 - (current_year - d.year)))
    
    # 상태 자동 계산 함수
    def get_status(remaining_years):
        if remaining_years <= 1:
            return "대폐차 대상"
        elif remaining_years <= 3:
            return "정기점검 필요"
        else:
            return "양호"

    df["상태"] = df["잔여 차령(년)"].apply(get_status)
    df["최초등록일"] = df["최초등록일"].dt.strftime("%Y-%m-%d")
    return df, None

# 기본 가상 데이터 (업로드 전 표출용)
default_bus_df = pd.DataFrame({
    "차량번호": ["경기70아 1001", "경기70아 1002", "경기70아 1003", "경기70아 1004", "경기70아 1005"],
    "차종": ["유니버스 익스프레스", "그랜버드 실크로드", "유니버스 노블", "그랜버드 이노베이션", "유니버스 노블"],
    "담당 노선": ["서울 - 부산", "서울 - 광주", "서울 - 대구", "서울 - 대전", "서울 - 전주"],
    "최초등록일": ["2017-03-15", "2018-08-20", "2020-11-10", "2022-05-01", "2024-01-15"]
})
bus_data, _ = calculate_bus_asset(default_bus_df)

# ==========================================
# 4. 리스크 알림 대시보드
# ==========================================
st.subheader("🚨 보유 버스 자산 상태 및 운행 리스크 알림")

alert_cols = st.columns(3)
with alert_cols[0]:
    if other_profit < 0:
        st.error(f"⚠️ **기타노선 적자 경고**: 시외/전세 부문 손익이 {other_profit:,.0f}원 적자 예상됩니다.")
    else:
        st.success(f"✅ **기타노선 흑자 유지**: 기타 부문 순이익 {other_profit:,.0f}원")

with alert_cols[1]:
    # 자동 계산된 대폐차 대상 차량 수 연동
    aging_buses = len(bus_data[bus_data["상태"] == "대폐차 대상"])
    if aging_buses > 0:
        st.warning(f"🚍 **차령 만료 예정 차량**: 대폐차 대상 버스가 **{aging_buses}대** 존재합니다.")
    else:
        st.success("✅ **차량 자산 양호**: 차령 만료 임박 버스 없음")

with alert_cols[2]:
    profit_margin = (estimated_net_income / total_revenue * 100) if total_revenue > 0 else 0
    if profit_margin < 5.0:
        st.info(f"💡 **수익성 개선 필요**: 매출 대비 순이익률이 {profit_margin:.1f}%로 원가(유류비/정비비) 관리가 필요합니다.")
    else:
        st.success(f"✅ **우수한 수익 구조**: 매출 대비 순이익률 {profit_margin:.1f}%")

st.markdown("---")

# ==========================================
# 5. 연말 운송손익 추정 대시보드
# ==========================================
st.subheader("📊 1. 연말 운송손익 및 경영 대시보드")

m1, m2, m3, m4 = st.columns(4)
m1.metric("추정 총 운송수입", f"{total_revenue:,.0f} 원", delta=f"전년대비 {rev_yoy_growth:+.1f}%")
m2.metric("추정 세전순이익", f"{pre_tax_income:,.0f} 원", delta=f"법인세 {tax_amount:,.0f}원 차감전")
m3.metric("추정 당기순이익", f"{estimated_net_income:,.0f} 원", delta=f"전년대비 {net_yoy_growth:+.1f}%")
m4.metric("차량 대폐차 적립금", f"{depreciation_amount:,.0f} 원", delta=f"유보금 {retained_earnings:,.0f}원")

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("**노선 부문별 수입/비용 비교**")
    biz_df = pd.DataFrame({
        "부문": ["고속/우등", "고속/우등", "시외/전세/기타", "시외/전세/기타"],
        "구분": ["운송수입", "운행비용", "운송수입", "운행비용"],
        "금액": [express_rev, express_exp, other_rev, other_exp]
    })
    fig_biz = px.bar(biz_df, x="부문", y="금액", color="구분", barmode="group",
                     color_discrete_map={"운송수입": "#1f77b4", "운행비용": "#d9534f"})
    st.plotly_chart(fig_biz, use_container_width=True)

with col2:
    st.markdown("**전년 vs 올해 당기순이익 비교**")
    yoy_df = pd.DataFrame({
        "연도": ["전년도 실적", "올해 추정치"],
        "당기순이익": [last_year_net, estimated_net_income]
    })
    fig_yoy = px.bar(yoy_df, x="연도", y="당기순이익", color="연도",
                     color_discrete_sequence=["#a6a6a6", "#2ca02c"])
    st.plotly_chart(fig_yoy, use_container_width=True)

st.markdown("---")

# ==========================================
# 6. 손익분기점(BEP) 분석
# ==========================================
st.subheader("⚖️ 2. 손익분기점(BEP) 및 운행 원가 분석")

st.caption("비용 중 고정비(차량할부금, 고정인건비 등) 비중을 입력하여 적자를 면하기 위한 최소 운송수입을 산출합니다.")
fixed_cost_ratio = st.slider("운행 비용 중 고정비 비중 (%)", min_value=10, max_value=90, value=55, step=5) / 100

fixed_cost = total_expense * fixed_cost_ratio
variable_cost = total_expense * (1 - fixed_cost_ratio)
variable_cost_ratio = variable_cost / total_revenue if total_revenue > 0 else 0

bep_revenue = fixed_cost / (1 - variable_cost_ratio) if (1 - variable_cost_ratio) > 0 else 0
safety_margin = total_revenue - bep_revenue
safety_margin_ratio = (safety_margin / total_revenue * 100) if total_revenue > 0 else 0

bep_col1, bep_col2 = st.columns(2)
with bep_col1:
    st.info(f"📌 **손익분기점(BEP) 필요 수입액**: **{bep_revenue:,.0f} 원**")
    st.caption(f"* 고정비(고정인건비/차량할부): {fixed_cost:,.0f}원 / 변동비(유류비/통행료): {variable_cost:,.0f}원 기준")

with bep_col2:
    if safety_margin >= 0:
        st.success(f"🛡️ **안전지대**: 현재 예상 수입이 손익분기점보다 **{safety_margin:,.0f} 원 ({safety_margin_ratio:.1f}%)** 여유가 있습니다.")
    else:
        st.error(f"🚨 **손익분기점 미달**: 현재 예상 수입이 BEP보다 **{abs(safety_margin):,.0f} 원** 부족합니다.")

st.markdown("---")

# ==========================================
# 7. [신규] 보유 버스 자산 엑셀 업로드 및 자동 계산
# ==========================================
st.subheader("🚌 3. 보유 버스 자산 현황 관리 (엑셀 업로드)")

# 샘플 양식 다운로드 제공
sample_df = pd.DataFrame({
    "차량번호": ["충남70아 1001", "충남70아 1002", "충남70아 1003"],
    "차종": ["유니버스 노블", "그랜버드 이노베이션", "유니버스 익스프레스"],
    "담당 노선": ["서울 - 태안", "서울 - 서산", "서울 - 당진"],
    "최초등록일": ["2016-05-10", "2021-03-15", "2024-02-01"]
})

sample_buffer = io.BytesIO()
with pd.ExcelWriter(sample_buffer, engine='openpyxl') as writer:
    sample_df.to_excel(writer, index=False)

st.download_button(
    label="📥 차량목록 샘플 양식 다운로드",
    data=sample_buffer.getvalue(),
    file_name="차량목록_샘플.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

uploaded_file = st.file_uploader("차량목록 엑셀 또는 CSV 파일을 업로드하세요", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df_uploaded = pd.read_csv(uploaded_file)
        else:
            df_uploaded = pd.read_excel(uploaded_file)

        processed_df, err_msg = calculate_bus_asset(df_uploaded)

        if err_msg:
            st.error(err_msg)
        else:
            bus_data = processed_df
            st.success(f"총 {len(bus_data)}대의 차량 데이터가 업로드 및 자동 계산되었습니다!")
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

# 최종 차량 목록 표시
st.dataframe(bus_data, use_container_width=True)

st.markdown("---")

# ==========================================
# 8. 임원 보고용 요약 리포트
# ==========================================
st.subheader("📑 4. 이사회 및 경영진 제출용 요약서")

report_html = f"""
<div style="border: 2px solid #333; padding: 25px; border-radius: 8px; background-color: #fcfcfc;">
    <h2 style="text-align: center; color: #003366; margin-bottom: 20px;">[보고서] 2026년도 고속버스 자산 및 경영손익 가결산서</h2>
    <p style="text-align: right; color: #666;">기준 시점: 1~{current_month}월 누적 + {remaining_months}개월 예상 반영</p>
    <hr style="border: 1px solid #ccc;">
    
    <h3>1. 노선부문별 운송손익 추정 (단위: 원)</h3>
    <table style="width:100%; border-collapse: collapse; text-align: left; margin-bottom: 20px;">
        <tr style="background-color: #f2f2f2;">
            <th style="padding: 8px; border: 1px solid #ddd;">구분</th>
            <th style="padding: 8px; border: 1px solid #ddd;">고속/우등노선</th>
            <th style="padding: 8px; border: 1px solid #ddd;">시외/전세/기타</th>
            <th style="padding: 8px; border: 1px solid #ddd;">합계 (2026년 추정)</th>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>추정 운송수입</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{express_rev:,.0f}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{other_rev:,.0f}</td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{total_revenue:,.0f}</b></td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>추정 운행비용</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;">{express_exp:,.0f}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{other_exp:,.0f}</td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{total_expense:,.0f}</b></td>
        </tr>
        <tr style="background-color: #e6f2ff;">
            <td style="padding: 8px; border: 1px solid #ddd;"><b>부문별 순손익</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{express_profit:,.0f}</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{other_profit:,.0f}</b></td>
            <td style="padding: 8px; border: 1px solid #ddd;"><b>{pre_tax_income:,.0f}</b></td>
        </tr>
    </table>
    
    <h3>2. 주요 경영 지표 및 자산관리 항목</h3>
    <ul>
        <li><b>전년 대비 수입 증감률:</b> {rev_yoy_growth:+.1f}% (전년 총수입: {last_year_rev:,.0f} 원)</li>
        <li><b>추정 당기순이익:</b> <span style="color:red; font-weight:bold;">{estimated_net_income:,.0f} 원</span> (전년 대비 {net_yoy_growth:+.1f}%)</li>
        <li><b>손익분기점(BEP) 필요수입:</b> {bep_revenue:,.0f} 원 (안전율 {safety_margin_ratio:.1f}%)</li>
        <li><b>차량 대폐차 충당금 설정액 ({depreciation_rate*100:.1f}%):</b> {depreciation_amount:,.0f} 원</li>
        <li><b>보유 차량 수:</b> 총 {len(bus_data)}대 (대폐차 대상: {len(bus_data[bus_data["상태"] == "대폐차 대상"])}대)</li>
    </ul>
</div>
"""

st.components.v1.html(report_html, height=520, scrolling=True)