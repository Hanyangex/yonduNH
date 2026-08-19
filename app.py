import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="한양고속 차량 자산 및 정기검사 관리 시스템",
    layout="wide"
)

st.title("🚌 한양고속 차량 자산 및 정기검사 관리 시스템")
st.caption("보유 차량의 최초등록일 기준 잔여 차령 계산 및 정기검사 만료 임박 알림을 제공합니다.")

st.markdown("---")

# ==========================================
# 1. 사이드바 - 설정
# ==========================================
st.sidebar.header("⚙️ 차령 및 검사 관리 설정")
legal_limit_years = st.sidebar.number_input("법정 기본 차령 (년)", min_value=1, max_value=15, value=10)
inspection_warning_days = st.sidebar.number_input("정기검사 임박 기준 (일)", min_value=7, max_value=90, value=30)

st.sidebar.markdown("---")
st.sidebar.info("💡 **차령 상태 분류 기준**\n- **대폐차 대상**: 잔여 차령 1년 이하\n- **정기점검 필요**: 잔여 차령 2~3년\n- **양호**: 잔여 차령 4년 이상")

# ==========================================
# 2. 차량 자산 파일 업로드 및 자동 계산 함수
# ==========================================
def calculate_bus_asset(df, max_years, alert_days):
    required_cols = {"차량번호", "차종", "담당 노선", "최초등록일", "정기검사유효일자"}
    if not required_cols.issubset(set(df.columns)):
        return None, f"엑셀 파일에 다음 필수 열이 포함되어야 합니다: {', '.join(required_cols)}"

    df["최초등록일"] = pd.to_datetime(df["최초등록일"])
    df["정기검사유효일자"] = pd.to_datetime(df["정기검사유효일자"])
    
    today = datetime.now()
    current_year = today.year

    # 1. 잔여 차령 계산
    df["잔여 차령(년)"] = df["최초등록일"].apply(lambda d: max(0, max_years - (current_year - d.year)))
    
    # 2. 차령 상태 자동 분류
    def get_status(remaining_years):
        if remaining_years <= 1:
            return "대폐차 대상"
        elif remaining_years <= 3:
            return "정기점검 필요"
        else:
            return "양호"

    df["상태"] = df["잔여 차령(년)"].apply(get_status)

    # 3. 정기검사 남은 일수(D-Day) 및 상태 계산
    df["검사 남은일수"] = (df["정기검사유효일자"] - today).dt.days

    def get_inspection_status(days):
        if days < 0:
            return "검사 초과"
        elif days <= alert_days:
            return "검사 임박"
        else:
            return "검사 여유"

    df["정기검사 상태"] = df["검사 남은일수"].apply(get_inspection_status)

    # 날짜 포맷팅
    df["최초등록일"] = df["최초등록일"].dt.strftime("%Y-%m-%d")
    df["정기검사유효일자"] = df["정기검사유효일자"].dt.strftime("%Y-%m-%d")

    return df, None

# 기본 테스트용 데이터
default_bus_df = pd.DataFrame({
    "차량번호": ["경기70아 1001", "경기70아 1002", "경기70아 1003", "경기70아 1004", "경기70아 1005", "경기70아 1006"],
    "차종": ["유니버스 익스프레스", "그랜버드 실크로드", "유니버스 노블", "그랜버드 이노베이션", "유니버스 노블", "그랜버드 실크로드"],
    "담당 노선": ["서울 - 부산", "서울 - 광주", "서울 - 대구", "서울 - 대전", "서울 - 전주", "서울 - 당진"],
    "최초등록일": ["2017-03-15", "2018-08-20", "2020-11-10", "2022-05-01", "2024-01-15", "2016-09-01"],
    "정기검사유효일자": ["2026-08-25", "2026-09-10", "2026-08-10", "2026-11-30", "2027-01-15", "2026-09-02"]
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
        "최초등록일": ["2016-05-10", "2021-03-15", "2024-02-01"],
        "정기검사유효일자": ["2026-09-01", "2026-10-15", "2027-03-20"]
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

# 파일 처리
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)

        bus_data, err_msg = calculate_bus_asset(raw_df, legal_limit_years, inspection_warning_days)
        if err_msg:
            st.error(err_msg)
            bus_data, _ = calculate_bus_asset(default_bus_df, legal_limit_years, inspection_warning_days)
        else:
            st.success(f"총 {len(bus_data)}대의 차량 데이터가 업로드되었습니다.")
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
        bus_data, _ = calculate_bus_asset(default_bus_df, legal_limit_years, inspection_warning_days)
else:
    bus_data, _ = calculate_bus_asset(default_bus_df, legal_limit_years, inspection_warning_days)

st.markdown("---")

# ==========================================
# 4. 정기검사 알림 카드 (신규 기능)
# ==========================================
st.subheader("🔔 2. 정기검사 임박 / 초과 알림 카드")

urgent_inspections = bus_data[bus_data["정기검사 상태"].isin(["검사 초과", "검사 임박"])].sort_values("검사 남은일수")

if urgent_inspections.empty:
    st.success("✅ 현재 정기검사가 임박하거나 초과된 차량이 없습니다.")
else:
    # 카드를 3열 배치
    cols = st.columns(3)
    for idx, (_, row) in enumerate(urgent_inspections.iterrows()):
        col = cols[idx % 3]
        days = row["검사 남은일수"]
        
        with col:
            if days < 0:
                st.error(
                    f"🚨 **[검사 기한 초과] {row['차량번호']}**\n\n"
                    f"- **차종/노선**: {row['차종']} ({row['담당 노선']})\n"
                    f"- **유효일자**: {row['정기검사유효일자']}\n"
                    f"- **상태**: {abs(days)}일 초과됨"
                )
            else:
                st.warning(
                    f"⚠️ **[검사 임박] {row['차량번호']}**\n\n"
                    f"- **차종/노선**: {row['차종']} ({row['담당 노선']})\n"
                    f"- **유효일자**: {row['정기검사유효일자']}\n"
                    f"- **상태**: D-{days}일 남음"
                )

st.markdown("---")

# ==========================================
# 5. 차량 자산 현황 요약 (Metrics)
# ==========================================
st.subheader("📊 3. 보유 자산 및 검사 현황 요약")

total_count = len(bus_data)
replace_count = len(bus_data[bus_data["상태"] == "대폐차 대상"])
inspection_urgent_count = len(urgent_inspections)
good_count = len(bus_data[(bus_data["상태"] == "양호") & (bus_data["정기검사 상태"] == "검사 여유")])

m1, m2, m3, m4 = st.columns(4)
m1.metric("총 보유 차량", f"{total_count} 대")
m2.metric("대폐차 대상 차량", f"{replace_count} 대", delta_color="inverse")
m3.metric("검사 임박/초과 차량", f"{inspection_urgent_count} 대", delta=f"{inspection_warning_days}일 이내", delta_color="inverse")
m4.metric("양호 및 정상 차량", f"{good_count} 대")

st.markdown("---")

# ==========================================
# 6. 상세 차량 목록 조회 및 필터링
# ==========================================
st.subheader("📋 4. 상세 차량 목록 조회")

filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])

with filter_col1:
    status_filter = st.multiselect(
        "차령 상태",
        options=["대폐차 대상", "정기점검 필요", "양호"],
        default=["대폐차 대상", "정기점검 필요", "양호"]
    )

with filter_col2:
    inspection_filter = st.multiselect(
        "검사 상태",
        options=["검사 초과", "검사 임박", "검사 여유"],
        default=["검사 초과", "검사 임박", "검사 여유"]
    )

with filter_col3:
    search_term = st.text_input("차량번호 / 차종 / 노선 검색", "")

# 필터링
filtered_df = bus_data[
    bus_data["상태"].isin(status_filter) &
    bus_data["정기검사 상태"].isin(inspection_filter)
]

if search_term:
    filtered_df = filtered_df[
        filtered_df["차량번호"].str.contains(search_term, case=False) |
        filtered_df["차종"].str.contains(search_term, case=False) |
        filtered_df["담당 노선"].str.contains(search_term, case=False)
    ]

st.dataframe(filtered_df, use_container_width=True)