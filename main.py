import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# 영역 차트 색상 및 스타일 살짝 조정
fig_area.update_traces(fillcolor="rgba(31, 119, 180, 0.3)")

# 그래프 출력
st.plotly_chart(fig_area, use_container_width=True)

# 그래프 하단 설명 란
st.caption(
    f"💡 **이 그래프로 알 수 있는 것:** '{selected_movie}'의 상영 기간에 따른 누적 관객수의 성장 곡선과 최종 누적 관객수 도달 속도를 시각적으로 파악할 수 있습니다."
)


# =========================================================
# [6. 세 번째 그래프: 다중 선그래프 (장기 흥행 TOP 5 영화 비교)]
# =========================================================
st.markdown("---")
st.header("🏆 섹션 3: 20일 이상 TOP 10 유지 영화 중 누적 관객수 TOP 5 비교")

# 1) 영화별 TOP 10 등장 일수 계산
movie_days = df.groupby("영화명")["기준일자"].count()

# 2) 등장 일수가 20일 이상인 영화 목록만 필터링
qualified_movies = movie_days[movie_days >= 20].index

# 3) 조건에 맞는 영화 중 최대 누적관객수가 가장 높은 상위 5개 영화 선택
top5_long_running = (
    df[df["영화명"].isin(qualified_movies)]
    .groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .head(5)
    .index
)

# 4) 해당 5개 영화 데이터만 필터링
top5_df = df[df["영화명"].isin(top5_long_running)]

# Plotly 다중 선그래프 생성 (`color="영화명"` 옵션으로 각 영화별 색상 및 범례 구분)
fig_multi = px.line(
    top5_df,
    x="기준일자",
    y="누적관객수",
    color="영화명",
    title="TOP 10 20일 이상 유지 영화 중 누적 관객수 TOP 5의 추이 비교",
    labels={
        "기준일자": "날짜",
        "누적관객수": "누적 관객수(명)",
        "영화명": "영화 제목",
    },
)

# 그래프 출력
st.plotly_chart(fig_multi, use_container_width=True)

# 그래프 하단 설명 란
st.caption(
    "💡 **이 그래프로 알 수 있는 것:** 단기 반짝 흥행에 그치지 않고 박스오피스 TOP 10에 20일 이상 차트인한 주요 장기 흥행작 5편의 누적 관객수 증가 속도와 최종 성적 차이를 비교해 볼 수 있습니다."
)


# =========================================================
# [7. 네 번째 그래프: 이동평균선 (전체 박스오피스 7일 이동평균)]
# =========================================================
st.markdown("---")
st.header("📉 섹션 4: 박스오피스 전체 일별 관객수 및 7일 이동평균 추이")

# 1) 기준일자별 TOP 10 영화 전체의 해당일관객수 합계 계산
daily_total = df.groupby("기준일자")["해당일관객수"].sum().reset_index()

# 2) 7일 이동평균(Rolling Mean) 계산
daily_total["7일이동평균"] = (
    daily_total["해당일관객수"].rolling(window=7, min_periods=1).mean()
)

# 3) Plotly graph_objects를 활용하여 연한 원본 선과 진한 이동평균 선을 겹쳐서 그리기
fig_ma = go.Figure()

# 원본 일별 관객수 합계 (연하고 얇은 선)
fig_ma.add_trace(
    go.Scatter(
        x=daily_total["기준일자"],
        y=daily_total["해당일관객수"],
        mode="lines",
        name="일별 관객수 합계 (원본)",
        line=dict(color="rgba(180, 180, 180, 0.6)", width=1.5),
    )
)

# 7일 이동평균선 (진하고 두꺼운 선)
fig_ma.add_trace(
    go.Scatter(
        x=daily_total["기준일자"],
        y=daily_total["7일이동평균"],
        mode="lines",
        name="7일 이동평균",
        line=dict(color="#1f77b4", width=3),
    )
)

# 레이아웃 설정
fig_ma.update_layout(
    title="박스오피스 TOP 10 전체 일별 관객수 합계 및 7일 이동평균",
    xaxis_title="날짜",
    yaxis_title="관객수(명)",
    hovermode="x unified",
)

# 그래프 출력
st.plotly_chart(fig_ma, use_container_width=True)

# 그래프 하단 설명 란
st.caption(
    "💡 **이 그래프로 알 수 있는 것:** 주말/평일 간 관객수 변동(일별 노이즈)을 평탄화하여, 전체 극장가 관객 흐름의 대세 상승·하강 국면과 성수기/비성수기 트렌드를 명확하게 파악할 수 있습니다."
)


# =========================================================
# [8. 다섯 번째 그래프: 막대그래프 (월별 총 관객수 합계)]
# =========================================================
st.markdown("---")
st.header("📊 섹션 5: 월별 총 관객수 비교 분석")

# 1) 기준일자에서 '연-월(YYYY-MM)' 문자열 생성
daily_total["연월"] = daily_total["기준일자"].dt.strftime("%Y-%m")

# 2) 월(연-월) 단위로 그룹화하여 해당일관객수 합계 계산
monthly_total = daily_total.groupby("연월")["해당일관객수"].sum().reset_index()

# 3) Plotly 막대그래프 생성
fig_bar = px.bar(
    monthly_total,
    x="연월",
    y="해당일관객수",
    title="월별 총 관객수 합계",
    labels={"연월": "월(연-월)", "해당일관객수": "총 관객수(명)"},
    color_discrete_sequence=["#1f77b4"],
)

# 막대 상단에 수치 표시 및 레이아웃 설정
fig_bar.update_traces(texttemplate="%{y:,.0f}명", textposition="outside")
fig_bar.update_layout(xaxis_type="category")

# 그래프 출력
st.plotly_chart(fig_bar, use_container_width=True)

# 그래프 하단 설명 란
st.caption(
    "💡 **이 그래프로 알 수 있는 것:** 각 월별 총 관객수를 비교하여 연중 영화 시장의 최대 성수기 월과 비성수기 월을 한눈에 파악할 수 있습니다."
)


# =========================================================
# [9. 여섯 번째 그래프: 캘린더 히트맵 (월/주차별 × 요일별)]
# =========================================================
st.markdown("---")
st.header("🗓️ 섹션 6: 월(주차별) × 요일별 관객수 캘린더 히트맵")

# 1) 히트맵 표현을 위한 요일 및 주차 정보 생성
day_names = ["월", "화", "수", "목", "금", "토", "일"]
daily_total["요일_num"] = daily_total["기준일자"].dt.dayofweek
daily_total["요일"] = daily_total["요일_num"].map(lambda x: day_names[x])

# 마우스 호버 시 띄울 날짜 문자열(YYYY-MM-DD)
daily_total["날짜_str"] = daily_total["기준일자"].dt.strftime("%Y-%m-%d")

# Y축에 들어갈 '월(주차별)' 라벨 생성 (예: '2023-05 (18주차)')
daily_total["월_주차"] = daily_total["기준일자"].dt.strftime("%Y-%m (%W주차)")

# 2) 관객수 데이터 피벗 테이블 생성 (행: 월_주차, 열: 요일)
pivot_audience = daily_total.pivot(
    index="월_주차", columns="요일", values="해당일관객수"
)
pivot_audience = pivot_audience.reindex(columns=day_names)  # 월요일 ~ 일요일 순서 고정

# 3) 마우스 호버 시 보여줄 날짜 데이터 피벗 테이블 생성
pivot_dates = daily_total.pivot(
    index="월_주차", columns="요일", values="날짜_str"
)
pivot_dates = pivot_dates.reindex(columns=day_names)

# 4) Plotly go.Heatmap 생성
fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=pivot_audience.values,
        x=pivot_audience.columns,
        y=pivot_audience.index,
        text=pivot_dates.values,
        hovertemplate="<b>날짜: %{text}</b><br>요일: %{x}요일<br>일관객수 합계: %{z:,.0f}명<extra></extra>",
        colorscale="Reds",  # 색상이 진할수록 관객수가 많음
    )
)

# 히트맵 레이아웃 설정
fig_heatmap.update_layout(
    title="월(주차별) × 요일별 박스오피스 관객수 분포",
    xaxis_title="요일 (월요일~일요일)",
    yaxis_title="월 (주차)",
    yaxis=dict(autorange="reversed"),  # 시간이 과거에서 최근 순으로 내려오도록 정렬
)

# 그래프 출력
st.plotly_chart(fig_heatmap, use_container_width=True)

# 그래프 하단 설명 란
st.caption(
    "💡 **이 그래프로 알 수 있는 것:** 주차별·요일별 관객 밀도를 색상의 짙은 정도(진할수록 관객 집중)로 확인하여, 주말 집중도와 특수 공휴일/연휴 시점의 극장가 관객 폭발 구간을 달력 형태로 파악할 수 있습니다."
)
