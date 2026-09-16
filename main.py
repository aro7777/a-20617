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
# [9. 여섯 번째 그래프: 캘린더 히트맵 (축 반전: X=월/주차, Y=요일)]
# =========================================================
st.markdown("---")
st.header("🗓️ 섹션 6: 월(주차별) × 요일별 관객수 캘린더 히트맵")

# 1) 히트맵 표현을 위한 요일 및 주차 정보 생성
day_names = ["월", "화", "수", "목", "금", "토", "일"]
daily_total["요일_num"] = daily_total["기준일자"].dt.dayofweek
daily_total["요일"] = daily_total["요일_num"].map(lambda x: day_names[x])

# 마우스 호버 시 띄울 날짜 문자열(YYYY-MM-DD)
daily_total["날짜_str"] = daily_total["기준일자"].dt.strftime("%Y-%m-%d")

# X축에 들어갈 '월(주차별)' 라벨 생성 (예: '2023-05 (18주차)')
daily_total["월_주차"] = daily_total["기준일자"].dt.strftime("%Y-%m (%W주차)")

# 2) 관객수 데이터 피벗 테이블 생성 (행: 요일, 열: 월_주차)
pivot_audience = daily_total.pivot(
    index="요일", columns="월_주차", values="해당일관객수"
)
pivot_audience = pivot_audience.reindex(index=day_names)  # Y축: 월요일 ~ 일요일 순서 고정

# 3) 마우스 호버 시 보여줄 날짜 데이터 피벗 테이블 생성
pivot_dates = daily_total.pivot(
    index="요일", columns="월_주차", values="날짜_str"
)
pivot_dates = pivot_dates.reindex(index=day_names)

# 4) Plotly go.Heatmap 생성 (X축 = 월_주차, Y축 = 요일)
fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=pivot_audience.values,
        x=pivot_audience.columns,
        y=pivot_audience.index,
        text=pivot_dates.values,
        hovertemplate="<b>날짜: %{text}</b><br>월/주차: %{x}<br>요일: %{y}요일<br>일관객수 합계: %{z:,.0f}명<extra></extra>",
        colorscale="Reds",  # 색상이 진할수록 관객수가 많음
    )
)

# 히트맵 레이아웃 설정
fig_heatmap.update_layout(
    title="월(주차별) × 요일별 박스오피스 관객수 분포",
    xaxis_title="월 (주차)",
    yaxis_title="요일 (월요일~일요일)",
    yaxis=dict(autorange="reversed"),  # 위에서 아래로 월요일 -> 일요일 순 정렬
)

# 그래프 출력
st.plotly_chart(fig_heatmap, use_container_width=True)

# 그래프 하단 설명 란
st.caption(
    "💡 **이 그래프로 알 수 있는 것:** 주차별·요일별 관객 밀도를 색상의 짙은 정도(진할수록 관객 집중)로 확인하여, 주말 집중도와 특수 공휴일/연휴 시점의 극장가 관객 폭발 구간을 달력 형태로 파악할 수 있습니다."
)

#///////////////////////////////////////////////////////////////////////////////////////

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="영화 데이터 그래프 도감 2 - 분포와 관계", layout="wide")

st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")


@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)
    # 세로막대 기호(|)로 여러 개 기재된 장르 중 첫 번째 장르만 추출
    df["genre"] = (
        df["genre"].astype(str).apply(lambda x: x.split("|")[0] if x else x)
    )
    # 장르별 10위권 체류일수 순위 및 라벨 생성 (예: '1위: 파묘')
    df["rank_in_genre"] = (
        df.groupby("genre")["days_in_top10"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    df["rank_label"] = (
        df["rank_in_genre"].astype(str) + "위: " + df["movieNm"]
    )
    return df


df = load_data()

# ---------------------------------------------------------
# Section 1: 장르별 영화 편수 (플롯리 도넛 그래프)
# ---------------------------------------------------------
st.header("1. 장르별 영화 편수 분포")

genre_counts = df["genre"].value_counts().reset_index()
genre_counts.columns = ["genre", "count"]

fig_donut = px.pie(
    genre_counts,
    values="count",
    names="genre",
    hole=0.4,
    title="장르별 개봉 영화 비율 및 편수",
)

fig_donut.update_traces(
    textinfo="percent+label",
    hovertemplate="<b>장르: %{label}</b><br>영화 수: %{value}편<br>비율: %{percent}<extra></extra>",
)

st.plotly_chart(fig_donut, use_container_width=True)

st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "전체 개봉 영화 중 어떤 장르가 가장 높은 비중을 차지하는지 한눈에 비교할 수 있으며, 주류 장르와 비주류 장르의 분포 편차를 파악할 수 있습니다."
)

st.divider()

# ---------------------------------------------------------
# Section 2: 장르 및 개별 영화별 총 관객 수 (트리맵)
# ---------------------------------------------------------
st.header("2. 장르 및 개별 영화별 총 관객 수 분포")

fig_treemap = px.treemap(
    df,
    path=[px.Constant("전체 장르"), "genre", "movieNm"],
    values="total_audi",
    title="장르 및 개별 영화별 총 관객 수",
)

fig_treemap.update_traces(
    hovertemplate="<b>%{label}</b><br>총 관객 수: %{value:,.0f}명<extra></extra>"
)

st.plotly_chart(fig_treemap, use_container_width=True)

st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "장르별 전체 관객 규모의 비중과 함께, 각 장르 내부에서 어떤 개별 영화가 흥행을 주도했는지 상대적 크기로 한눈에 파악할 수 있습니다."
)

st.divider()

# ---------------------------------------------------------
# Section 3: 총 관객 수 분포 (히스토그램)
# ---------------------------------------------------------
st.header("3. 총 관객 수 분포 (히스토그램)")

fig_hist = px.histogram(
    df,
    x="total_audi",
    nbins=20,
    title="영화별 총 관객 수 히스토그램",
    labels={"total_audi": "총 관객 수"},
)

fig_hist.update_traces(
    hovertemplate="관객 수 구간: %{x}<br>영화 수: %{y}편<extra></extra>"
)

st.plotly_chart(fig_hist, use_container_width=True)

max_movie = df.loc[df["total_audi"].idxmax()]
max_movie_name = max_movie["movieNm"]
max_movie_audi = max_movie["total_audi"]

under_1m_count = (df["total_audi"] < 1000000).sum()
under_1m_ratio = (under_1m_count / len(df)) * 100

st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    f"- **가장 관객이 많은 영화**: **{max_movie_name}** ({max_movie_audi:,.0f}명)\n"
    f"- **밀집 구간**: 대부분의 영화가 **관객 수 100만 명 미만** 구간({under_1m_count}편, 약 {under_1m_ratio:.1f}%)에 집중되어 있으며, 수백만 명 이상의 흥행작은 극소수에 해당하는 비대칭적 분포를 보입니다."
)

st.divider()

# ---------------------------------------------------------
# Section 4: 개봉일 스크린 수와 총 관객 수의 관계 (산점도)
# ---------------------------------------------------------
st.header("4. 개봉일 스크린 수와 총 관객 수의 관계")

fig_scatter = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    labels={
        "first_scrn": "개봉일 스크린 수",
        "total_audi": "총 관객 수",
        "genre": "장르",
    },
    title="개봉일 스크린 수 vs 총 관객 수 산점도",
)

fig_scatter.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>개봉일 스크린 수: %{x:,.0f}개<br>총 관객 수: %{y:,.0f}명<extra></extra>"
)

st.plotly_chart(fig_scatter, use_container_width=True)

st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "개봉일 스크린 수가 많을수록 총 관객 수 역시 증가하는 강한 양의 상관관계를 보이며, 장르별 초기 스크린 확보 규모와 흥행 실적의 차이를 비교할 수 있습니다."
)

st.divider()

# ---------------------------------------------------------
# Section 5: 장르별 총 관객 수 분포 (박스플롯)
# ---------------------------------------------------------
st.header("5. 주요 장르별 총 관객 수 분포 (박스플롯)")

genre_counts_series = df["genre"].value_counts()
major_genres = genre_counts_series[genre_counts_series >= 10].index
df_major = df[df["genre"].isin(major_genres)]

fig_box = px.box(
    df_major,
    x="genre",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    points="outliers",
    title="영화 10편 이상 개봉 장르의 총 관객 수 분포",
    labels={"genre": "장르", "total_audi": "총 관객 수"},
)

fig_box.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>총 관객 수: %{y:,.0f}명<extra></extra>"
)

st.plotly_chart(fig_box, use_container_width=True)

st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "장르별 관객 수의 중간값과 분포 범위를 비교할 수 있으며, 상자 밖의 이상치 점을 통해 동일 장르 내에서 평균을 크게 상회하는 대형 흥행작을 식별할 수 있습니다."
)

st.divider()

# ---------------------------------------------------------
# Section 6: 스크린 수, 첫 주 관객, 총 관객 수의 관계 (버블 차트)
# ---------------------------------------------------------
st.header("6. 개봉일 스크린 수, 첫 주 관객 수, 총 관객 수의 관계 (버블 차트)")

fig_bubble = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    size="first_week_audi",
    color="genre",
    hover_name="movieNm",
    custom_data=["first_week_audi"],
    size_max=40,
    labels={
        "first_scrn": "개봉일 스크린 수",
        "total_audi": "총 관객 수",
        "first_week_audi": "첫 주 관객 수",
        "genre": "장르",
    },
    title="개봉일 스크린 수 vs 총 관객 수 (버블 크기: 개봉 첫 주 관객 수)",
)

fig_bubble.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>개봉일 스크린 수: %{x:,.0f}개<br>총 관객 수: %{y:,.0f}명<br>첫 주 관객 수: %{customdata[0]:,.0f}명<extra></extra>"
)

st.plotly_chart(fig_bubble, use_container_width=True)

st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "개봉일 스크린 수와 총 관객 수의 상관관계뿐만 아니라, 원의 크기(첫 주 관객 수)를 통해 개봉 초기의 흥행 화력 및 기세가 최종 성적에 미친 영향을 다차원적으로 파악할 수 있습니다."
)

st.divider()

# ---------------------------------------------------------
# Section 7: 제작 국가 및 장르별 영화 편수 (선버스트)
# ---------------------------------------------------------
st.header("7. 제작 국가 및 장르별 영화 편수 분포 (선버스트)")

fig_sunburst1 = px.sunburst(
    df,
    path=["nation", "genre"],
    title="제작 국가 및 장르별 영화 편수",
)

fig_sunburst1.update_traces(
    hovertemplate="<b>%{label}</b><br>영화 수: %{value}편<extra></extra>"
)

st.plotly_chart(fig_sunburst1, use_container_width=True)

st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "영화 제작 국가별 전체 비중과 각 국가 내에서 어떤 장르의 영화가 주로 제작·개봉되었는지 계층적 구조로 파악할 수 있습니다."
)

st.divider()

# ---------------------------------------------------------
# Section 8: 장르별 10위권 체류일수 Top 10 영화 분포 (선버스트)
# ---------------------------------------------------------
st.header("8. 10위권에 오래 남은 영화는 어떤 장르가 많은가")

# 장르 내부 체류일수 순위가 1위~10위인 영화만 필터링
df_top10_in_genre = df[df["rank_in_genre"] <= 10]

fig_sunburst2 = px.sunburst(
    df_top10_in_genre,
    path=["genre", "rank_label"],
    values="days_in_top10",
    title="장르별 10위권 체류일수 상위 10개(1~10위) 영화 분포",
)

fig_sunburst2.update_traces(
    hovertemplate="<b>%{label}</b><br>10위권 머문 날수: %{value}일<extra></extra>"
)

st.plotly_chart(fig_sunburst2, use_container_width=True)

st.subheader("💡 이 그래프로 알 수 있는 것")
st.write(
    "각 장르 내부에서 10위권 체류일수가 가장 높은 상위 10개 영화(1위~10위)의 체류일수와 장르별 비중을 복잡한 차트 없이 깔끔하게 한눈에 확인할 수 있습니다."
)

st.divider()
