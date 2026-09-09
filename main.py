import streamlit as st
import datetime
import requests
import pandas as pd
import pytz

st.title("나의 데이터 과학 포트폴리오")
st.write("반갑습니다! 이제부터 여기에 제 작업을 기록합니다.")
st.write("신재성")
st.write("Hello World!Hello World!Hello World!Hello World!Hello World!Hello World!")


# 페이지 기본 설정 (타이틀, 레이아웃)
st.set_page_config(
    page_title="어제 영화 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 일별 박스오피스 대시보드")

# --- 1. 한국 시간 기준 '어제' 날짜 구하기 ---
# Streamlit Cloud 서버 시계와 상관없이 한국 표준시(KST)를 적용합니다.
kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz)
yesterday_kst = now_kst - datetime.timedelta(days=1)
target_dt = yesterday_kst.strftime("%Y%m%d")  # YYYYMMDD 형태로 변환
formatted_yesterday = yesterday_kst.strftime("%Y년 %m월 %d일")

st.caption(f" 기준 날짜: **{formatted_yesterday}** (한국 시간 기준)")

# --- 2. API 데이터를 불러오고 캐싱하는 함수 ---
# ttl=3600: 1시간 동안 호출 결과를 기억하여 동일한 요청 시 API를 다시 부르지 않습니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(date_str):
    # Streamlit Secrets(비밀 금고)에서 KOBIS API 키 가져오기
    try:
        api_key = st.secrets["KOBIS_KEY"]
    except KeyError:
        return None, "secrets.toml 파일 또는 Streamlit Cloud Secrets에 'KOBIS_KEY'가 설정되지 않았습니다."

    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": api_key,
        "targetDt": date_str
    }

    try:
        response = requests.get(url, timeout=10)
        
        # HTTP 요청 실패 처리
        if response.status_code != 200:
            return None, f"서버 응답 오류 (상태 코드: {response.status_code})"

        data = response.json()

        # KOBIS 특유의 오류 구조(faultInfo) 확인
        if "faultInfo" in data:
            error_msg = data["faultInfo"].get("message", "알 수 없는 오류")
            return None, f"API 오류 응답: {error_msg} (발급받은 인증키를 확인해 주세요.)"

        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        # 목록이 비어있는 경우
        if not daily_list:
            return None, "해당 날짜의 영화 데이터가 존재하지 않거나 데이터 집계 전입니다."

        return daily_list, None

    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 에러가 발생했습니다: {e}"

# --- 3. 데이터 로드 및 시각화 진행 ---
raw_data, error = fetch_box_office_data(target_dt)

# 오류가 있는 경우 안내 메시지 출력
if error:
    st.error(f"⚠️ 데이터를 불러오지 못했습니다.\n\n**확인할 사항:**\n- {error}")
else:
    # JSON 목록을 데이터프레임(표 형태)으로 변환
    df = pd.DataFrame(raw_data)

    # 문자열 숫자를 정수(int)로 변환
    numeric_cols = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 순위 기준으로 정렬
    df = df.sort_values(by="rank", ascending=True)

    # --- 4. 1위 영화 지표 카드 (st.metric) ---
    st.subheader("🥇 어제의 1위 영화")
    top_1 = df.iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric(
        label="🎬 1위 영화명",
        value=top_1["movieNm"],
        delta=f"개봉일: {top_1['openDt']}"
    )
    col2.metric(
        label="👥 어제 관객수",
        value=f"{top_1['audiCnt']:,} 명"
    )
    col3.metric(
        label="🍿 누적 관객수",
        value=f"{top_1['audiAcc']:,} 명"
    )

    st.markdown("---")

    # --- 5. 관객수 상위 5편 막대그래프 ---
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5)

    # Streamlit 기본 막대그래프 활용
    chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
    chart_data.columns = ["어제 관객수"]
    st.bar_chart(chart_data)

    st.markdown("---")

    # --- 6. 전체 박스오피스 순위 표 ---
    st.subheader("📋 박스오피스 순위 목록")

    # 표시할 컬럼 및 이름 지정
    display_df = df[["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
    display_df.columns = ["순위", "영화명", "개봉일", "어제 관객수", "누적 관객수", "스크린수"]

    # 보기 좋게 숫자에 천 단위 쉼표(,) 추가
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "어제 관객수": st.column_config.NumberColumn(format="%d명"),
            "누적 관객수": st.column_config.NumberColumn(format="%d명"),
            "스크린수": st.column_config.NumberColumn(format="%d개"),
            "순위": st.column_config.NumberColumn(format="%d위"),
        },
        hide_index=True
    )
