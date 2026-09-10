import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="영화 관객수 분석 앱", layout="wide")

st.title("🎬 영화 관객수 분석 웹앱")
st.write("영화별 일별 관객수 변화 및 관객 데이터 추이를 분석합니다.")


# =========================================================
# [1. 데이터 불러오기]
# @st.cache_data를 사용하여 앱 시작 시 한 번만 로드하고 재사용합니다.
# =========================================================
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)

    # [2. 날짜 전처리]
    # 결측치가 포함된 행 삭제
    df = df.dropna()

    # '기준일자' 컬럼을 datetime 형식으로 변환
    df["기준일자"] = pd.to_datetime(df["기준일자"])

    # 전체 데이터를 기준일자 오름차순으로 정렬
    df = df.sort_values(by="기준일자")

    return df


# 데이터 로드
df = load_data()


# =========================================================
# [3. 영화 선택 기능]
# - 영화명을 중복 없이 추출하되, 누적관객수가 높은 순서대로 정렬합니다.
# =========================================================
# 영화별 maximum 누적관객수를 구해 내림차순 정렬
movie_order = (
    df.groupby("영화명")["누적관객수"].max().sort_values(ascending=False).index
)

# 사이드바에서 영화 선택
selected_movie = st.sidebar.selectbox("영화를 선택하세요:", movie_order)

# 선택한 영화 데이터 필터링
movie_df = df[df["영화명"] == selected_movie]


# =========================================================
# [4. 첫 번째 그래프: 선 그래프 (일별 관객수)]
# =========================================================
st.markdown("---")
st.header("📊 섹션 1: 일별 관객수 추이 분석")

# Plotly 선 그래프 생성
fig_line = px.line(
    movie_df,
    x="기준일자",
    y="해당일관객수",
    title=f"'{selected_movie}'의 일별 관객수 변화",
    labels={"기준일자": "날짜", "해당일관객수": "해당일 관객수(명)"},
    markers=True,
)

# 그래프 출력
st.plotly_chart(fig_line, use_container_width=True)

# 그래프 하단 설명 란
st.caption(
    f"💡 **이 그래프로 알 수 있는 것:** '{selected_movie}'의 개봉 이후 상영 기간 동안 일별 관객수 증감 추이와 흥행 피크 시점을 확인할 수 있습니다."
)


# =========================================================
# [5. 두 번째 그래프: 영역 차트 (누적 관객수)]
# =========================================================
st.markdown("---")
st.header("📈 섹션 2: 누적 관객수 추이 분석")

# Plotly 영역 차트(Area Chart) 생성
fig_area = px.area(
    movie_df,
    x="기준일자",
    y="누적관객수",
    title=f"'{selected_movie}'의 누적 관객수 변화",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)"},
)

# 영역 차트 색상 및 스타일 살짝 조정 (선명하게 보기 위함)
fig_area.update_traces(fillcolor="rgba(31, 119, 180, 0.3)")

# 그래프 출력
st.plotly_chart(fig_area, use_container_width=True)

# 그래프 하단 설명 란
st.caption(
    f"💡 **이 그래프로 알 수 있는 것:** '{selected_movie}'의 상영 기간에 따른 누적 관객수의 성장 곡선과 최종 누적 관객수 도달 속도를 시각적으로 파악할 수 있습니다."
)
