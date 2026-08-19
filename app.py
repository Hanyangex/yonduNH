import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import io
import os

# 0. 데이터 저장 파일 경로 설정
DATA_FILE = "saved_bus_data.csv"

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="한양고속 차량 자산 및 정기검사 관리 시스템",
    layout="wide"
)

st.title("🚌 한양고속 차량 자산 및 정기검사 관리 시스템")
st.caption("보유 차량의 차령만료일 및 정기검사 기간(전 3개월 ~ 후 1개월) 임박 알림을 제공합니다.")

st.markdown("---")

# ==========================================
# 1. 사이드바 - 설정 및 데이터 관리
# ==========================================
st.sidebar.header("⚙️ 차령 및 검사 관리 설정")
age_warning_days = st.sidebar.number_input("차령만료 임박 기준 (일)", min_value=30, max_value=365, value=180)

st.sidebar.markdown("---")

# 데이터 초기화 버튼
if st.sidebar.button("🔄 저장된 데이터 초기화"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    if "bus_data" in st.session_state:
        del st.session_state["bus_data"]
    st.sidebar.success("저장된 데이터가 삭제되고 기본값으로 초기화되었습니다.")
    st.rerun()

st.sidebar.info("💡 **정기검사 기준**\n- 검사 가능/임박: 만료일 전 90일(3개월) ~ 후 30일(1개월)\n- 검사 초과: 만료일 후 30일 경과")

# ==========================================
# 2. 차량 자산 파일 업로드 및 검사 계산 함수
# ==========================================
def calculate_bus_asset(df, age_alert_days):
    # 필수 열에 '차령만료일' 추가 [수정]
    required_cols = {"차량번호", "차종", "담당 노선", "최초등록일", "차령만료일", "정기검사유효일자"}
    if not required_cols.issubset(set(df.columns)):
        return None, f"엑셀 파일에 다음 필수 열이 포함되어야 합니다: {', '.join(required_cols)}"

    df = df.copy()
    
    # 날짜 데이터 변환
    df["최초등록일"] = pd.to_datetime(df["최초등록일"])
    df["차령만료일"] = pd.to_datetime(df["차령만료일"])  # [수정] 직접 데이터에서 로드
    df["정기검사유효일자"] = pd.to_datetime(df["정기검사유효일자"])
    
    today = datetime.now()

    # 1. 차령만료 남은 일수 계산 (직접 넣은 차령만료일 기준) [수정]
    df["차령 남은일수"] = (df["차령만료일"] - today).dt.days

    # 차령 만료 상태
    def get_age_status(days):
        if days < 0:
            return "차령 만료"
        elif days <= age_alert_days:
            return "차령 임박"
        else:
            return "양호"

    df["차령 상태"] = df["차령 남은일수"].apply(get_age_status)

    # 2. 정기검사 기간 및 상태 계산
    df["검사 남은일수"] = (df["정기검사유효일자"] - today).dt.days

    def get_inspection_status(days_diff):
        if days_diff < -30:
            return "검사 초과"
        elif -30 <= days_diff <= 90:
            return "검사 임박"
        else:
            return "검사 여유"

    df["정기검사 상태"] = df["검사 남은일수"].apply(get_inspection_status)

    # 문자열 날짜 포맷 변환
    df["최초등록일"] = df["최초등록일"].dt.strftime("%Y-%m-%d")
    df["차령만료일"] = df["차령만료일"].dt.strftime("%Y-%m-%d")
    df["정기검사유효일자"] = df["정기검사유효일자"].dt.strftime("%Y-%m-%d")

    return df, None

# 기본 샘플 데이터 (차령만료일 직접 포함) [수정]
default_bus_df = pd.DataFrame({
    "차량번호": ["경기70아 1001", "경기70아 1002", "경기70아 1003", "경기70아 1004", "경기70아 1005", "경기70아 1006"],
    "차종": ["유니버스 익스프레스", "그랜버드 실크로드", "유니버스 노블", "그랜버드 이노베이션", "유니버스 노블", "그랜버드 실크로드"],
    "담당 노선": ["서울 - 부산", "서울 - 광주", "서울 - 대구", "서울 - 대전", "서울 - 전주", "서울 - 당진"],
    "최초등록일": ["2017-03-15", "2018-08-20", "2020-11-10", "2022-05-01", "2024-01-15", "2016-09-01"],
    "차령만료일": ["2027-03-15", "2028-08-20", "2030-11-10", "2032-05-01", "2034-01-15", "2026-09-01"],
    "정기검사유효일자": ["2026-08-25", "2026-09-10", "2026-08-10", "2026-11-30", "2027-01-15", "2026-09-02"]
})

# ==========================================
# 3. 엑셀 업로드 및 영구 데이터 저장 처리
# ==========================================
st.subheader("📂 1. 차량목록 엑셀 업로드 및 자동 저장")

col_up1, col_up2 = st.columns([2, 1])

with col_up1:
    uploaded_file = st.file_uploader("차량목록 엑셀(.xlsx) 또는 CSV(.csv) 파일을 업로드하세요", type=["xlsx", "csv"])

with col_up2:
    # 샘플 다운로드 양식에 차령만료일 열 추가 [수정]
    sample_df = pd.DataFrame({
        "차량번호": ["충남70아 1001", "충남70아 1002", "충남70아 1003"],
        "차종": ["유니버스 노블", "그랜버드 이노베이션", "유니버스 익스프레스"],
        "담당 노선": ["서울 - 태안", "서울 - 서산", "서울 - 당진"],
        "최초등록일": ["2016-05-10", "2021-03-15", "2024-02-01"],
        "차령만료일": ["2026-05-10", "2031-03-15", "2034-02-01"],
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

# 1) 파일 업로드 발생 시 -> 로컬 데이터 파일 저장
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)

        _, err_msg = calculate_bus_asset(raw_df, age_warning_days)
        if err_msg:
            st.error(err_msg)
        else:
            raw_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            st.success(f"총 {len(raw_df)}대의 차량 데이터가 사이트(서버)에 영구 저장되었습니다!")
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

# 2) 저장된 데이터를 불러오거나 기본 데이터 로드
if os.path.exists(DATA_FILE):
    current_raw_df = pd.read_csv(DATA_FILE)
    bus_data, _ = calculate_bus_asset(current_raw_df, age_warning_days)
else:
    bus_data, _ = calculate_bus_asset(default_bus_df, age_warning_days)

st.session_state["bus_data"] = bus_data

st.markdown("---")

# ==========================================
# 4. 차령만료 및 정기검사 알림 카드
# ==========================================
col_card1, col_card2 = st.columns(2)

# --- 4-1. 차령만료 임박 카드 ---
with col_card1:
    st.subheader("🚌 차령만료 임박 / 만료 알림")
    urgent_ages = bus_data[bus_data["차령 상태"].isin(["차령 만료", "차령 임박"])].sort_values("차령 남은일수")

    if urgent_ages.empty:
        st.success("✅ 차령만료가 임박하거나 초과된 차량이 없습니다.")
    else:
        for _, row in urgent_ages.iterrows():
            days = row["차령 남은일수"]
            if days < 0:
                st.error(
                    f"🚨 **[차령 만료] {row['차량번호']}**\n\n"
                    f"- **차종/노선**: {row['차종']} ({row['담당 노선']})\n"
                    f"- **차령만료일**: {row['차령만료일']}\n"
                    f"- **상태**: 만료일 {abs(days)}일 경과"
                )
            else:
                st.warning(
                    f"⚠️ **[차령 임박] {row['차량번호']}**\n\n"
                    f"- **차종/노선**: {row['차종']} ({row['담당 노선']})\n"
                    f"- **차령만료일**: {row['차령만료일']}\n"
                    f"- **상태**: D-{days}일 남음"
                )

# --- 4-2. 정기검사 임박 카드 ---
with col_card2:
    st.subheader("🔔 정기검사 임박 / 초과 알림 (전 3개월 ~ 후 1개월)")
    urgent_inspections = bus_data[bus_data["정기검사 상태"].isin(["검사 초과", "검사 임박"])].sort_values("검사 남은일수")

    if urgent_inspections.empty:
        st.success("✅ 정기검사가 임박하거나 초과된 차량이 없습니다.")
    else:
        for _, row in urgent_inspections.iterrows():
            days = row["검사 남은일수"]
            if days < -30:
                st.error(
                    f"🚨 **[검사기한 초과] {row['차량번호']}**\n\n"
                    f"- **차종/노선**: {row['차종']} ({row['담당 노선']})\n"
                    f"- **유효일자**: {row['정기검사유효일자']}\n"
                    f"- **상태**: 허용기간(후 1개월) {abs(days) - 30}일 초과"
                )
            else:
                st.warning(
                    f"⚠️ **[검사기간 연장/임박] {row['차량번호']}**\n\n"
                    f"- **차종/노선**: {row['차종']} ({row['담당 노선']})\n"
                    f"- **유효일자**: {row['정기검사유효일자']}\n"
                    f"- **상태**: 기준일 기준 D{'-' if days >= 0 else '+'}{abs(days)}일"
                )

st.markdown("---")

# ==========================================
# 5. 차량 자산 현황 요약
# ==========================================
st.subheader("📊 3. 보유 자산 현황 요약")

total_count = len(bus_data)
age_urgent_count = len(urgent_ages)
inspection_urgent_count = len(urgent_inspections)
good_count = len(bus_data[(bus_data["차령 상태"] == "양호") & (bus_data["정기검사 상태"] == "검사 여유")])

m1, m2, m3, m4 = st.columns(4)
m1.metric("총 보유 차량", f"{total_count} 대")
m2.metric("차령만료 임박/만료", f"{age_urgent_count} 대", delta_color="inverse")
m3.metric("검사 임박/초과 차량", f"{inspection_urgent_count} 대", delta_color="inverse")
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
        options=["차령 만료", "차령 임박", "양호"],
        default=["차령 만료", "차령 임박", "양호"]
    )

with filter_col2:
    inspection_filter = st.multiselect(
        "검사 상태",
        options=["검사 초과", "검사 임박", "검사 여유"],
        default=["검사 초과", "검사 임박", "검사 여유"]
    )

with filter_col3:
    search_term = st.text_input("차량번호 / 차종 / 노선 검색", "")

# 필터링 적용
filtered_df = bus_data[
    bus_data["차령 상태"].isin(status_filter) &
    bus_data["정기검사 상태"].isin(inspection_filter)
]

if search_term:
    filtered_df = filtered_df[
        filtered_df["차량번호"].str.contains(search_term, case=False) |
        filtered_df["차종"].str.contains(search_term, case=False) |
        filtered_df["담당 노선"].str.contains(search_term, case=False)
    ]

# 주요 열 순서 정리
display_cols = ["차량번호", "차종", "담당 노선", "최초등록일", "차령만료일", "차령 상태", "정기검사유효일자", "정기검사 상태"]
st.dataframe(filtered_df[display_cols], use_container_width=True)