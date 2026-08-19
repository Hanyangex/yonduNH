import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="한양고속 차량 자산 및 차령 관리 시스템",
    layout="wide"
)

st.title("🚌 한양고속 차량 자산 및 차령 관리 시스템")
st.caption("보유 차량의 최초등록일 기준 잔여 차령 계산, 대폐차 및 정기점검 리스크 관리를 제공합니다.")

st.markdown("---")

# ==========================================
# 1. 사이드바 - 설정
# ==========================================
st.sidebar.header("⚙️ 차령 관리 설정")
legal_limit_years = st.sidebar.number_input("법정 기본 차령 (년)", min_value=1, max_value=15, value=10)

st.sidebar.markdown("---")
st.sidebar.info("💡 **상태 분류 기준**\n- **대폐차 대상**: 잔여 차령 1년 이하\n- **정기점검 필요**: 잔여 차령 2~3년\n- **양호**: 잔여 차령 4년 이상")

# ==========================================
# 2. 차량 자산 파일 업로드 및 자동 계산 함수
# ==========================================
def calculate_bus_asset(df, max_years):
    required_cols = {"차량번호", "차종", "담당 노선", "최초등록일"}
    if not required_cols.issubset(set(df.columns)):
        return None, f"엑셀 파일에 다음 필수 열이 포함되어야 합니다: {', '.join(required_cols)}"

    df["최초등록일"] = pd.to_datetime(df["최초등록일"])
    current_year = datetime.now().year

    # 잔여 차령 계산
    df["잔여 차령(년)"] = df["최초등록일"].apply(lambda d: max(0, max_years - (current_year - d.year)))
    
    # 상태 자동 분류
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

# 기본 데이터
default_bus_df = pd.DataFrame({
    "차량번호": ["경기70아 1001", "경기70아 1002", "경기70아 1003", "경기70아 1004", "경기70아 1005", "경기70아 1006"],
    "차종": ["유니버스 익스프레스", "그랜버드 실크로드", "유니버스 노블", "그랜버드 이노베이션", "유니버스 노블", "그랜버드 실크로드"],
    "담당 노선": ["서울 - 부산", "서울 - 광주", "서울 - 대구", "서울 - 대전", "서울 - 전주", "서울 - 당진"],
    "최초등록일": ["2017-03-15", "2018-08-20", "2020-11-10", "2022-05-01", "2024-01-15", "2016-09-01"]
})

# ==========================================
# 3. 엑셀 파일 업로드 섹션
# ==========================================
st.subheader("📂 1. 차량목록 엑셀 업로드")

col_up1, col_up2 = st.columns([2, 1])

with col_up1:
    uploaded_file = st.file_uploader("차량목록 엑셀(.xlsx) 또는 CSV(.csv) 파일을 업로드하세요", type=["xlsx", "csv"])

with col_up2:
    sample_df = pd.DataFrame({
        "차량번호": ["충남70아 1001", "충남70아 1002", "충남70아 1003"],
        "차종": ["유니버스 노블", "그랜버드 이노베이션", "유니버스 익스프레스"],
        "담당 노선": ["서울 - 태안", "서울 - 서산", "서울 - 당진"],
        "최초등록일": ["2016-05-10", "2021-03-15", "2024-02-01"]
    })
    sample_buffer = io.BytesIO()
    with pd.ExcelWriter(sample_buffer, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False)

    st.write(" ")
    st.write(" ")
    st.download_button(
        label="📥 표준 양식 다운로드",
        data=sample_buffer.getvalue(),
        file_name="차량목록_양식.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# 파일 읽기 및 처리
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)

        bus_data, err_msg = calculate_bus_asset(raw_df, legal_limit_years)
        if err_msg:
            st.error(err_msg)
            bus_data, _ = calculate_bus_asset(default_bus_df, legal_limit_years)
        else:
            st.success(f"총 {len(bus_data)}대의 차량 데이터가 업로드되었습니다.")
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        bus_data, _ = calculate_bus_asset(default_bus_df, legal_limit_years)
else:
    bus_data, _ = calculate_bus_asset(default_bus_df, legal_limit_years)

st.markdown("---")

# ==========================================
# 4. 차량 자산 현황 요약 (Metrics & Alert)
# ==========================================
st.subheader("🚨 2. 차량 자산 리스크 현황")

total_count = len(bus_data)
replace_count = len(bus_data[bus_data["상태"] == "대폐차 대상"])
check_count = len(bus_data[bus_data["상태"] == "정기점검 필요"])
good_count = len(bus_data[bus_data["상태"] == "양호"])

m1, m2, m3, m4 = st.columns(4)
m1.metric("총 보유 차량", f"{total_count} 대")
m2.metric("대폐차 대상 차량", f"{replace_count} 대", delta_color="inverse")
m3.metric("정기점검 필요 차량", f"{check_count} 대", delta_color="off")
m4.metric("양호 차량", f"{good_count} 대")

st.markdown("---")

# ==========================================
# 5. 차령 분포 및 데이터 시각화
# ==========================================
st.subheader("📊 3. 보유 차량 차령 분포 분석")

col_chart1, col_chart2 = st.columns([1, 1])

with col_chart1:
    st.markdown("**차량 상태별 비중**")
    status_counts = bus_data["상태"].value_counts().reset_index()
    status_counts.columns = ["상태", "수량"]
    fig_pie = px.pie(
        status_counts, values="수량", names="상태",
        color="상태",
        color_discrete_map={"대폐차 대상": "#d9534f", "정기점검 필요": "#f0ad4e", "양호": "#5cb85c"},
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_chart2:
    st.markdown("**잔여 차령별 차량 대수**")
    fig_bar = px.histogram(
        bus_data, x="잔여 차령(년)", color="상태",
        color_discrete_map={"대폐차 대상": "#d9534f", "정기점검 필요": "#f0ad4e", "양호": "#5cb85c"},
        nbins=legal_limit_years + 1
    )
    fig_bar.update_layout(yaxis_title="차량 수")
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ==========================================
# 6. 상세 차량 목록 조회 및 필터링
# ==========================================
st.subheader("📋 4. 상세 차량 목록 조회")

filter_col1, filter_col2 = st.columns([1, 2])
with filter_col1:
    status_filter = st.multiselect(
        "상태 필터 선택",
        options=["대폐차 대상", "정기점검 필요", "양호"],
        default=["대폐차 대상", "정기점검 필요", "양호"]
    )

with filter_col2:
    search_term = st.text_input("차량번호 또는 차종 검색", "")

# 데이터 필터링 적용
filtered_df = bus_data[bus_data["상태"].isin(status_filter)]
if search_term:
    filtered_df = filtered_df[
        filtered_df["차량번호"].str.contains(search_term, case=False) |
        filtered_df["차종"].str.contains(search_term, case=False) |
        filtered_df["담당 노선"].str.contains(search_term, case=False)
    ]

st.dataframe(filtered_df, use_container_width=True)