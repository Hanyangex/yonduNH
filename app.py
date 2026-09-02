import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import io
import os

# 0. 데이터 저장 파일 경로 설정 (Google Sheets 연결 실패 시 임시 대체용)
DATA_FILE = "saved_bus_data.csv"
WORKSHEET_NAME = "차량데이터"
REQUIRED_COLUMNS = ["차량번호", "차종", "담당 노선", "취득가액", "최초등록일", "차령만료일", "정기검사유효일자"]

# 0-1. Google Sheets 연동 (업로드한 차량 데이터를 서버(구글시트)에 영구 등록)
try:
    from streamlit_gsheets import GSheetsConnection
    GSHEETS_LIB_AVAILABLE = True
except ImportError:
    GSHEETS_LIB_AVAILABLE = False


@st.cache_resource(show_spinner=False)
def _get_gsheets_connection():
    return st.connection("gsheets", type=GSheetsConnection)


def get_gsheets_connection():
    """secrets.toml(또는 Streamlit Cloud Secrets)에 연결 정보가 있으면 연결 객체를,
    없거나 설정이 잘못되었으면 None을 반환한다."""
    if not GSHEETS_LIB_AVAILABLE:
        return None
    try:
        return _get_gsheets_connection()
    except Exception:
        return None


def load_from_gsheets(conn):
    """시트에서 저장된 차량 데이터를 읽어온다. 실패 시 (None, 오류메시지)를 반환한다."""
    try:
        df = conn.read(worksheet=WORKSHEET_NAME, ttl=0)
        df = df.dropna(how="all")
        return (None if df.empty else df), None
    except Exception as e:
        return None, str(e)


def save_to_gsheets(conn, df):
    conn.update(worksheet=WORKSHEET_NAME, data=df)


# 1. 페이지 기본 설정
st.set_page_config(
    page_title="한양고속 차량 자산 및 정기검사 관리 시스템",
    layout="wide"
)

st.title("🚌 한양고속 차량 자산 및 정기검사 관리 시스템")
st.caption("보유 차량의 차령만료일, 정기검사 기간 및 취득가액 대비 감가상각 자산가치를 조회합니다.")

st.markdown("---")

# ==========================================
# 1. 사이드바 - 설정 및 데이터 관리
# ==========================================
gsheets_conn = get_gsheets_connection()

st.sidebar.header("🔗 서버(Google Sheets) 연결 상태")
if gsheets_conn is not None:
    st.sidebar.success("✅ Google Sheets 서버에 연결되었습니다.\n업로드한 차량 데이터가 시트에 자동 등록됩니다.")
else:
    st.sidebar.warning(
        "⚠️ Google Sheets 서버에 연결되어 있지 않습니다.\n"
        "지금은 이 서버 인스턴스에만 임시로 데이터가 저장되며, 재배포 시 사라질 수 있습니다.\n\n"
        "secrets.toml(또는 Streamlit Cloud의 Secrets 설정)에 연결 정보를 등록하면 "
        "업로드 데이터가 Google Sheets에 영구 등록됩니다. "
        "자세한 방법은 GOOGLE_SHEETS_설정가이드.md 를 참고하세요."
    )

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 차령 및 감가상각 설정")
age_warning_days = st.sidebar.number_input("차령만료 임박 기준 (일)", min_value=30, max_value=365, value=180)

st.sidebar.markdown("---")
st.sidebar.subheader("📉 감가상각 계산 옵션")
depreciation_method = st.sidebar.selectbox("감가상각 방법", ["정액법 (Straight-line)", "정률법 (Declining balance)"])
useful_life = st.sidebar.number_input("내용연수 (년)", min_value=1, max_value=20, value=9, help="버스 등 승합차량의 법정 내용연수 기준")
salvage_rate = st.sidebar.slider("잔존가치율 (%)", min_value=0, max_value=20, value=5, help="정액법 상각 시 최종 잔존가치 비율") / 100.0

st.sidebar.markdown("---")

# 데이터 초기화 버튼
if st.sidebar.button("🔄 저장된 데이터 초기화"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    if gsheets_conn is not None:
        try:
            save_to_gsheets(gsheets_conn, pd.DataFrame(columns=REQUIRED_COLUMNS))
        except Exception as e:
            st.sidebar.error(f"Google Sheets 초기화 중 오류가 발생했습니다: {e}")
    if "bus_data" in st.session_state:
        del st.session_state["bus_data"]
    st.sidebar.success("저장된 데이터가 삭제되고 기본값으로 초기화되었습니다.")
    st.rerun()

st.sidebar.info("💡 **정기검사 기준**\n- 검사 가능/임박: 만료일 전 90일(3개월) ~ 후 30일(1개월)\n- 검사 초과: 만료일 후 30일 경과")

# ==========================================
# 2. 차량 자산 파일 업로드 및 자동 계산 함수
# ==========================================
def calculate_bus_asset(df, age_alert_days, method, life_years, s_rate):
    # 필수 열 확인 ('취득가액' 추가)
    required_cols = {"차량번호", "차종", "담당 노선", "최초등록일", "차령만료일", "정기검사유효일자", "취득가액"}
    if not required_cols.issubset(set(df.columns)):
        return None, f"엑셀 파일에 다음 필수 열이 포함되어야 합니다: {', '.join(required_cols)}"

    df = df.copy()
    
    # 숫자 및 날짜 데이터 타입 변환
    df["취득가액"] = pd.to_numeric(df["취득가액"].astype(str).str.replace(",", ""), errors='coerce').fillna(0)
    df["최초등록일"] = pd.to_datetime(df["최초등록일"])
    df["차령만료일"] = pd.to_datetime(df["차령만료일"])
    df["정기검사유효일자"] = pd.to_datetime(df["정기검사유효일자"])
    
    today = datetime.now()

    # 1. 차령만료 남은 일수 및 상태 계산
    df["차령 남은일수"] = (df["차령만료일"] - today).dt.days

    def get_age_status(days):
        if days < 0:
            return "차령 만료"
        elif days <= age_alert_days:
            return "차령 임박"
        else:
            return "양호"

    df["차령 상태"] = df["차령 남은일수"].apply(get_age_status)

    # 2. 정기검사 남은 일수 및 상태 계산
    df["검사 남은일수"] = (df["정기검사유효일자"] - today).dt.days

    def get_inspection_status(days_diff):
        if days_diff < -30:
            return "검사 초과"
        elif -30 <= days_diff <= 90:
            return "검사 임박"
        else:
            return "검사 여유"

    df["정기검사 상태"] = df["검사 남은일수"].apply(get_inspection_status)

    # 3. 경과 연수(일 기반 float) 및 감가상각 계산
    elapsed_days = (today - df["최초등록일"]).dt.days.clip(lower=0)
    elapsed_years = elapsed_days / 365.25  # 경과 연수

    current_values = []
    accumulated_depreciations = []

    for cost, years in zip(df["취득가액"], elapsed_years):
        if cost <= 0:
            current_values.append(0)
            accumulated_depreciations.append(0)
            continue

        if "정액법" in method:
            # 정액법 계산: 연간 감가상각액 = (취득가액 - 잔존가액) / 내용연수
            salvage_val = cost * s_rate
            annual_dep = (cost - salvage_val) / life_years
            acc_dep = annual_dep * years
            # 잔존가치 이하로 내려가지 않도록 처리
            curr_val = max(salvage_val, cost - acc_dep)
            acc_dep = cost - curr_val
        else:
            # 정률법 계산: 상각률 = 1 - (잔존가율)^(1/내용연수)
            # 세법 기준 상각률 약산 공식 적용 (예: 5년 상각률 ~0.451, 9년 ~0.282)
            rate = 1 - (s_rate if s_rate > 0 else 0.05) ** (1 / life_years)
            curr_val = cost * ((1 - rate) ** years)
            min_val = cost * s_rate
            curr_val = max(min_val, curr_val)
            acc_dep = cost - curr_val

        current_values.append(round(curr_val))
        accumulated_depreciations.append(round(acc_dep))

    df["현재 잔존가치"] = current_values
    df["누적 감가상각액"] = accumulated_depreciations

    # 문자열 날짜 포맷 변환
    df["최초등록일"] = df["최초등록일"].dt.strftime("%Y-%m-%d")
    df["차령만료일"] = df["차령만료일"].dt.strftime("%Y-%m-%d")
    df["정기검사유효일자"] = df["정기검사유효일자"].dt.strftime("%Y-%m-%d")

    return df, None

# 기본 샘플 데이터 (취득가액 포함)
default_bus_df = pd.DataFrame({
    "차량번호": ["경기70아 1001", "경기70아 1002", "경기70아 1003", "경기70아 1004", "경기70아 1005", "경기70아 1006"],
    "차종": ["유니버스 익스프레스", "그랜버드 실크로드", "유니버스 노블", "그랜버드 이노베이션", "유니버스 노블", "그랜버드 실크로드"],
    "담당 노선": ["서울 - 부산", "서울 - 광주", "서울 - 대구", "서울 - 대전", "서울 - 전주", "서울 - 당진"],
    "취득가액": [180000000, 195000000, 210000000, 200000000, 220000000, 175000000],
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
    # 샘플 양식
    sample_df = pd.DataFrame({
        "차량번호": ["충남70아 1001", "충남70아 1002", "충남70아 1003"],
        "차종": ["유니버스 노블", "그랜버드 이노베이션", "유니버스 익스프레스"],
        "담당 노선": ["서울 - 태안", "서울 - 서산", "서울 - 당진"],
        "취득가액": [200000000, 210000000, 190000000],
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

# 1) 파일 업로드 발생 시 저장 (Google Sheets 서버 등록 우선, 실패 시 로컬 임시 저장)
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)

        _, err_msg = calculate_bus_asset(raw_df, age_warning_days, depreciation_method, useful_life, salvage_rate)
        if err_msg:
            st.error(err_msg)
        else:
            if gsheets_conn is not None:
                try:
                    save_to_gsheets(gsheets_conn, raw_df)
                    st.success(f"총 {len(raw_df)}대의 차량 데이터가 Google Sheets 서버에 등록되었습니다!")
                except Exception as e:
                    raw_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                    st.error(f"Google Sheets 등록 중 오류가 발생하여 로컬에 임시 저장했습니다: {e}")
            else:
                raw_df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.warning("Google Sheets 서버가 연결되어 있지 않아 로컬에만 임시 저장되었습니다. (앱 재배포 시 유실될 수 있음)")
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

# 2) 저장된 데이터를 불러오거나 기본 데이터 로드 (Google Sheets 우선 → 로컬 임시파일 → 기본 샘플)
current_raw_df = None
if gsheets_conn is not None:
    current_raw_df, _load_err = load_from_gsheets(gsheets_conn)

if current_raw_df is None and os.path.exists(DATA_FILE):
    current_raw_df = pd.read_csv(DATA_FILE)

if current_raw_df is not None:
    bus_data, _ = calculate_bus_asset(current_raw_df, age_warning_days, depreciation_method, useful_life, salvage_rate)
else:
    bus_data, _ = calculate_bus_asset(default_bus_df, age_warning_days, depreciation_method, useful_life, salvage_rate)

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
                    f"- **현재 잔존가치**: {row['현재 잔존가치']:,} 원\n"
                    f"- **상태**: 만료일 {abs(days)}일 경과"
                )
            else:
                st.warning(
                    f"⚠️ **[차령 임박] {row['차량번호']}**\n\n"
                    f"- **차종/노선**: {row['차종']} ({row['담당 노선']})\n"
                    f"- **차령만료일**: {row['차령만료일']}\n"
                    f"- **현재 잔존가치**: {row['현재 잔존가치']:,} 원\n"
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
# 5. 차량 자산 현황 요약 (자산 가치 추가)
# ==========================================
st.subheader("📊 2. 보유 자산 현황 요약")

total_count = len(bus_data)
total_acquisition = bus_data["취득가액"].sum()
total_current_value = bus_data["현재 잔존가치"].sum()
total_depreciation = bus_data["누적 감가상각액"].sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("총 보유 차량", f"{total_count} 대")
m2.metric("총 취득가액", f"{total_acquisition:,.0f} 원")
m3.metric("현재 자산 평가액(잔존가치)", f"{total_current_value:,.0f} 원")
m4.metric("누적 감가상각액", f"{total_depreciation:,.0f} 원", delta=f"-{(total_depreciation/total_acquisition*100 if total_acquisition else 0):.1f}%", delta_color="inverse")

st.markdown("---")

# ==========================================
# 6. 상세 차량 목록 조회 및 필터링
# ==========================================
st.subheader("📋 3. 상세 차량 자산 및 감가상각 목록")

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

# 표시용 데이터 생성 및 금액 포맷팅
display_df = filtered_df.copy()
display_df["취득가액(원)"] = display_df["취득가액"].apply(lambda x: f"{x:,.0f}")
display_df["현재 잔존가치(원)"] = display_df["현재 잔존가치"].apply(lambda x: f"{x:,.0f}")
display_df["누적 감가상각액(원)"] = display_df["누적 감가상각액"].apply(lambda x: f"{x:,.0f}")

display_cols = [
    "차량번호", "차종", "담당 노선", "최초등록일", "차령만료일", "차령 상태", 
    "취득가액(원)", "현재 잔존가치(원)", "누적 감가상각액(원)", "정기검사유효일자", "정기검사 상태"
]

st.dataframe(display_df[display_cols], use_container_width=True)