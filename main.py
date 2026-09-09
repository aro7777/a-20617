import streamlit as st
import datetime
import requests
import pandas as pd
import pytz

st.title("나의 데이터 과학 포트폴리오")
st.write("반갑습니다! 이제부터 여기에 제 작업을 기록합니다.")
st.write("신재성")

# 페이지 기본 설정
st.set_page_config(
    page_title="어제 영화 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 일별 박스오피스 대시보드")

# --- 1. 한국 시간 기준 '어제' 날짜 구하기 ---
kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz)
yesterday_kst = now_kst - datetime.timedelta(days=1)
target_dt = yesterday_kst.strftime("%Y%m%d")
formatted_yesterday = yesterday_kst.strftime("%Y년 %m월 %d일")

st.caption(f" 기준 날짜: **{formatted_yesterday}** (한국 시간 기준)")

# --- 2. API 데이터를 불러오는 함수 ---
# 캐시 문제를 방지하기 위해 테스트 중에는 ttl을 잠시 제외하거나 사이드바에서 캐시를 비울 수 있습니다.
@st.cache_data(ttl=3600)
def fetch_box_office_data(date_str):
    # Streamlit Secrets에서 API 키 가져오기
    try:
        raw_key = st.secrets["KOBIS_KEY"]
        # ★ [핵심 1] 공백 및 줄바꿈 문자 제거
        api_key = str(raw_key).strip()
    except KeyError:
        return None, "secrets.toml 또는 Streamlit Cloud Secrets에 'KOBIS_KEY'가 설정되지 않았습니다."

    # ★ [핵심 2] URL 파라미터 인코딩 이슈를 방지하기 위해 URL 직접 생성
    url = f"https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json?key={api_key}&targetDt={date_str}"

    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None, f"서버 응답 오류 (상태 코드: {response.status_code})"

        data = response.json()

        # KOBIS 오류 구조 확인
        if "faultInfo" in data:
            error_msg = data["faultInfo"].get("message", "알 수 없는 오류")
            # 디버깅을 위해 가져온 키의 앞/뒤 2자리 및 글자수 표시
            key_info = f"입력된 키 길이: {len(api_key)}자 (앞2자리: {api_key[:2]}..., 뒤2자리: ...{api_key[-2:]})"
            return None, f"API 오류 응답: {error_msg}\n\n🔍 **현재 불러온 키 정보:** {key_info}"

        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        if not daily_list:
            return None, "해당 날짜의 영화 데이터가 존재하지 않거나 데이터 집계 전입니다."

        return daily_list, None

    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 에러가 발생했습니다: {e}"

# --- 3. 데이터 로드 및 시각화 ---
raw_data, error = fetch_box_office_data(target_dt)

if error:
    st.error(f"⚠️ 데이터를 불러오지 못했습니다.\n\n{error}")
    st.info("💡 **팁:** 키를 방금 수정하셨다면 우측 상단 `Clear cache`를 누르거나 앱을 다시 로드해 보세요.")
else:
    df = pd.DataFrame(raw_data)

    numeric_cols = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(by="rank", ascending=True)

    # 1위 영화 지표 카드
    st.subheader("🥇 어제의 1위 영화")
    top_1 = df.iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric(label="🎬 1위 영화명", value=top_1["movieNm"], delta=f"개봉일: {top_1['openDt']}")
    col2.metric(label="👥 어제 관객수", value=f"{top_1['audiCnt']:,} 명")
    col3.metric(label="🍿 누적 관객수", value=f"{top_1['audiAcc']:,} 명")

    st.markdown("---")

    # 관객수 상위 5편 막대그래프
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5)
    chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
    chart_data.columns = ["어제 관객수"]
    st.bar_chart(chart_data)

    st.markdown("---")

    # 전체 순위 표
    st.subheader("📋 박스오피스 순위 목록")
    display_df = df[["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]].copy()
    display_df.columns = ["순위", "영화명", "개봉일", "어제 관객수", "누적 관객수", "스크린수"]

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
