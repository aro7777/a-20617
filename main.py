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
    page_title="영화 박스오피스 대시보드",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 일별 박스오피스 대시보드")

# --- 1. 한국 시간 기준 '어제' 날짜 계산 ---
kst_tz = pytz.timezone("Asia/Seoul")
now_kst = datetime.datetime.now(kst_tz)
yesterday_kst = (now_kst - datetime.timedelta(days=1)).date()

# --- 2. 날짜 선택 달력 (최대 날짜: 어제) ---
selected_date = st.date_input(
    label="📅 조회할 날짜를 선택하세요 (집계는 어제 날짜까지만 가능합니다)",
    value=yesterday_kst,
    max_value=yesterday_kst,
    min_value=datetime.date(2003, 11, 11)  # KOBIS 데이터 시작 시점 근처
)

# API 조회용 날짜 문자열 (YYYYMMDD) 및 표시용 문자열 (YYYY년 MM월 DD일)
target_dt = selected_date.strftime("%Y%m%d")
formatted_selected_date = selected_date.strftime("%Y년 %m월 %d일")

st.caption(f"기준 날짜: **{formatted_selected_date}** (한국 시간 기준)")


# --- 3. API 데이터를 불러오는 함수 (캐싱 적용) ---
@st.cache_data(ttl=3600)
def fetch_box_office_data(date_str):
    # Streamlit Secrets에서 API 키 가져오기
    try:
        raw_key = st.secrets["KOBIS_KEY"]
        api_key = str(raw_key).strip()
    except KeyError:
        return None, "secrets.toml 또는 Streamlit Cloud Secrets에 'KOBIS_KEY'가 설정되지 않았습니다."

    url = f"https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json?key={api_key}&targetDt={date_str}"

    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None, f"서버 응답 오류 (상태 코드: {response.status_code})"

        data = response.json()

        # KOBIS 오류 구조 확인
        if "faultInfo" in data:
            error_msg = data["faultInfo"].get("message", "알 수 없는 오류")
            return None, f"API 오류 응답: {error_msg} (인증키를 확인해 주세요.)"

        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])

        # 목록이 비어 있는 경우 안내 메시지 지정
        if not daily_list:
            return None, "그날은 아직 집계 전입니다."

        return daily_list, None

    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 에러가 발생했습니다: {e}"


# --- 4. 데이터 로드 및 전처리 ---
raw_data, error = fetch_box_office_data(target_dt)

if error:
    # 데이터가 비어 있거나 오류 발생 시 안내
    if error == "그날은 아직 집계 전입니다.":
        st.warning(f"⚠️ {error}")
    else:
        st.error(f"⚠️ 데이터를 불러오지 못했습니다.\n\n{error}")
else:
    df = pd.DataFrame(raw_data)

    # 문자열 숫자를 정수(int)로 변환
    numeric_cols = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 순위 기준으로 정렬
    df = df.sort_values(by="rank", ascending=True)

    # --- 5. 1위 영화 지표 카드 ---
    st.subheader(f"🥇 {formatted_selected_date}의 1위 영화")
    top_1 = df.iloc[0]

    # 1위 영화명에 100만 관객 표시 적용
    top_1_title = top_1["movieNm"]
    if top_1["audiAcc"] >= 1000000:
        top_1_title += " 🏆"

    col1, col2, col3 = st.columns(3)
    col1.metric(
        label="🎬 1위 영화명",
        value=top_1_title,
        delta=f"개봉일: {top_1['openDt']}"
    )
    col2.metric(
        label="👥 당일 관객수",
        value=f"{top_1['audiCnt']:,} 명"
    )
    col3.metric(
        label="🍿 누적 관객수",
        value=f"{top_1['audiAcc']:,} 명"
    )

    st.markdown("---")

    # --- 6. 관객수 상위 5편 막대그래프 ---
    st.subheader("📊 관객수 상위 5개 영화")
    top_5_df = df.head(5)
    chart_data = top_5_df.set_index("movieNm")[["audiCnt"]]
    chart_data.columns = ["당일 관객수"]
    st.bar_chart(chart_data)

    st.markdown("---")

    # --- 7. 전체 박스오피스 순위 표 가공 ---
    st.subheader("📋 박스오피스 상세 순위")

    # [조건] 순위 증감(rankInten) 화살표 표시 가공 함수
    def format_rank_inten(val):
        if val > 0:
            return f"🔺 {val}"  # 순위 상승 (빨간 위 화살표)
        elif val < 0:
            return f"🔹 {abs(val)}"  # 순위 하락 (파란 아래 화살표)
        else:
            return "-"  # 변동 없음

    # [조건] 누적 관객수 100만 명 이상 트로피 이모지 추가 함수
    def format_movie_title(row):
        title = row["movieNm"]
        if row["audiAcc"] >= 1000000:
            return f"{title} 🏆"
        return title

    # 표에 사용할 데이터프레임 복사 및 가공
    display_df = df.copy()
    display_df["movieNm_formatted"] = display_df.apply(format_movie_title, axis=1)
    display_df["rankInten_formatted"] = display_df["rankInten"].apply(format_rank_inten)

    # 컬럼 추출 및 이름 변경
    display_df = display_df[
        ["rank", "rankInten_formatted", "movieNm_formatted", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
    ]
    display_df.columns = ["순위", "순위 증감", "영화명", "개봉일", "당일 관객수", "누적 관객수", "스크린수"]

    # 표 출력
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "순위": st.column_config.NumberColumn(format="%d위"),
            "당일 관객수": st.column_config.NumberColumn(format="%d명"),
            "누적 관객수": st.column_config.NumberColumn(format="%d명"),
            "스크린수": st.column_config.NumberColumn(format="%d개"),
        },
        hide_index=True
    )
