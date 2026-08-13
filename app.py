import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="종로구 전자도서관 소장목록 분석", layout="wide")

st.markdown(
    """
    <style>
    html, body, [class*="css"] { font-size: 14px; }
    h1 { font-size: 1.6rem !important; }
    h2 { font-size: 1.3rem !important; }
    h3 { font-size: 1.1rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem !important; }
    [data-testid="stCaptionContainer"] { font-size: 0.8rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

CSV_PATH = "서울특별시 종로구_전자도서관소장목록_20250701.csv"

# 구마다 분류 체계(용어, 세분화 수준)가 달라 유사 항목을 하나의 대분류로 통합한다.
BUCKET_MAP = {
    "문학": "문학/소설", "소설": "문학/소설", "장르문학": "문학/소설",
    "무협": "문학/소설", "판타지": "문학/소설", "로맨스": "문학/소설",
    "시/에세이": "에세이", "에세이": "에세이",
    "인문": "인문/사회", "인문/사회": "인문/사회", "인문/역사": "인문/사회",
    "인문/사회/역사": "인문/사회", "정치/사회": "인문/사회",
    "경제경영": "경제/경영", "경제/경영": "경제/경영", "마케팅/세일즈": "경제/경영",
    "투자/재테크": "경제/경영", "취업/창업": "경제/경영",
    "자기관리": "자기계발", "자기계발": "자기계발", "성공학/처세술": "자기계발", "삶의자세": "자기계발",
    "가정과생활": "가정/생활/건강", "가정/생활/요리": "가정/생활/건강",
    "건강/생활": "가정/생활/건강", "건강/의학": "가정/생활/건강", "실용": "가정/생활/건강",
    "어린이/청소년": "아동/청소년", "청소년": "아동/청소년", "어린이": "아동/청소년",
    "동화": "아동/청소년", "아동": "아동/청소년", "유아/초등": "아동/청소년",
    "유아": "아동/청소년", "유아/어린이": "아동/청소년", "스마트동화": "아동/청소년",
    "해외원서": "외국어/해외원서", "국어와외국어": "외국어/해외원서", "국어/외국어": "외국어/해외원서",
    "외국도서": "외국어/해외원서", "외국어": "외국어/해외원서", "언어": "외국어/해외원서", "영어": "외국어/해외원서",
    "자연과과학": "과학/기술", "과학/공학": "과학/기술", "자연/과학": "과학/기술",
    "기술/공학": "과학/기술", "IT/프로그래밍": "과학/기술", "컴퓨터와인터넷": "과학/기술", "컴퓨터/IT": "과학/기술",
    "예술/대중문화": "예술/대중문화", "뮤직": "예술/대중문화", "인터뷰 오디오북": "예술/대중문화", "북채널": "예술/대중문화",
    "만화": "만화", "단행본만화": "만화", "웹툰": "만화", "만화/잡지": "만화",
    "역사/문화": "역사/문화/여행", "역사/문화/지리": "역사/문화/여행", "여행/취미": "역사/문화/여행",
    "여행": "역사/문화/여행", "취미/실용/스포츠": "역사/문화/여행",
    "종교": "종교",
    "수험서/자격증": "수험서/자격증", "교재/수험서": "수험서/자격증",
    "대학교재": "수험서/자격증", "교양/일반": "수험서/자격증",
    "미분류": "기타",
}


def normalize_category(raw):
    if pd.isna(raw):
        return "기타"
    key = str(raw).replace("／", "/").strip()
    return BUCKET_MAP.get(key, "기타")


@st.cache_data
def load_data(path):
    df = pd.read_csv(path, encoding="cp949")
    df["데이터기준일"] = pd.to_datetime(df["데이터기준일"], errors="coerce")
    return df


@st.cache_data
def load_all_districts():
    frames = []

    df = pd.read_csv("서울특별시 종로구_전자도서관소장목록_20250701.csv", encoding="cp949")
    frames.append(pd.DataFrame({
        "자치구": "종로구",
        "서명": df["서명"],
        "저자": df["저자"],
        "출판사": df["출판사"],
        "카테고리_원본": df["대분류"],
        "보유수량": df["보유 권수"],
        "데이터기준일": df["데이터기준일"],
    }))

    df = pd.read_csv("data_unused/서울특별시 동대문구_공공도서관 전자책 보유 현황_20230310.csv", encoding="cp949")
    frames.append(pd.DataFrame({
        "자치구": "동대문구",
        "서명": df["도서명"],
        "저자": df["저자"],
        "출판사": df["출판사"],
        "카테고리_원본": df["카테고리"],
        "보유수량": pd.NA,
        "데이터기준일": df["데이터기준일"],
    }))

    df = pd.read_csv("data_unused/서울특별시 동작구_구립도서관 전자도서 보유 목록_20260413.csv", encoding="cp949")
    frames.append(pd.DataFrame({
        "자치구": "동작구",
        "서명": df["제목"],
        "저자": df["저자"],
        "출판사": df["출판사"],
        "카테고리_원본": df["카테고리"].str.split(">").str[0].str.strip(),
        "보유수량": df["수량"],
        "데이터기준일": df["입고일자"],
    }))

    df = pd.read_csv("data_unused/서울특별시 서초구_전자도서관 도서정보_20260605.csv", encoding="cp949")
    frames.append(pd.DataFrame({
        "자치구": "서초구",
        "서명": df["도서명"],
        "저자": df["저자명"],
        "출판사": df["출판사"],
        "카테고리_원본": df["카테고리"],
        "보유수량": pd.NA,
        "데이터기준일": df["데이터기준일"],
    }))

    df = pd.read_csv("data_unused/서울특별시 영등포구_전자책 목록_20250822.csv", encoding="cp949")
    frames.append(pd.DataFrame({
        "자치구": "영등포구",
        "서명": df["제목"],
        "저자": df["저자"],
        "출판사": df["출판사"],
        "카테고리_원본": df["대분류"],
        "보유수량": df["보유 종수"],
        "데이터기준일": df["데이터 기준일자"],
    }))

    combined = pd.concat(frames, ignore_index=True)
    combined["카테고리"] = combined["카테고리_원본"].apply(normalize_category)
    combined["보유수량"] = pd.to_numeric(combined["보유수량"], errors="coerce")
    return combined


def render_jongno_dashboard():
    df = load_data(CSV_PATH)

    st.title("📚 서울특별시 종로구 전자도서관 소장목록 분석")
    st.caption(f"데이터 기준일: {df['데이터기준일'].max().date()} · 총 {len(df):,}건")

    # --- 사이드바 필터 ---
    st.sidebar.header("필터")

    gubun_options = sorted(df["구분"].unique())
    gubun_sel = st.sidebar.multiselect("구분", gubun_options, default=gubun_options)

    daebunryu_options = sorted(df["대분류"].unique())
    daebunryu_sel = st.sidebar.multiselect("대분류", daebunryu_options, default=daebunryu_options)

    keyword = st.sidebar.text_input("서명 검색어")
    author_keyword = st.sidebar.text_input("저자 검색어")
    publisher_keyword = st.sidebar.text_input("출판사 검색어")

    filtered = df[df["구분"].isin(gubun_sel) & df["대분류"].isin(daebunryu_sel)]
    if keyword:
        filtered = filtered[filtered["서명"].str.contains(keyword, case=False, na=False)]
    if author_keyword:
        filtered = filtered[filtered["저자"].str.contains(author_keyword, case=False, na=False)]
    if publisher_keyword:
        filtered = filtered[filtered["출판사"].str.contains(publisher_keyword, case=False, na=False)]

    # --- 요약 지표 ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("자료 건수", f"{len(filtered):,}")
    col2.metric("보유 권수 합계", f"{filtered['보유 권수'].sum():,}")
    col3.metric("출판사 수", f"{filtered['출판사'].nunique():,}")
    col4.metric("저자 수", f"{filtered['저자'].nunique():,}")

    st.divider()

    top_n = st.slider("상위 노출 개수", min_value=5, max_value=30, value=15, step=5)

    # --- 대분류 분포 / 출판사 / 저자 Top N (한 줄 배치) ---
    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("대분류별 자료 건수")
        cat_count = filtered["대분류"].value_counts().reset_index()
        cat_count.columns = ["대분류", "건수"]
        donut = (
            alt.Chart(cat_count)
            .mark_arc(innerRadius=60)
            .encode(theta="건수:Q", color="대분류:N", tooltip=["대분류", "건수"])
        )
        st.altair_chart(donut, width='stretch')

    with c2:
        st.subheader(f"출판사 보유 건수 상위 {top_n}")
        pub_top = filtered["출판사"].value_counts().head(top_n).reset_index()
        pub_top.columns = ["출판사", "건수"]
        chart = (
            alt.Chart(pub_top)
            .mark_bar()
            .encode(x="건수:Q", y=alt.Y("출판사:N", sort="-x"), tooltip=["출판사", "건수"])
        )
        st.altair_chart(chart, width='stretch')

    with c3:
        st.subheader(f"저자 보유 건수 상위 {top_n}")
        author_top = filtered["저자"].value_counts().head(top_n).reset_index()
        author_top.columns = ["저자", "건수"]
        chart = (
            alt.Chart(author_top)
            .mark_bar()
            .encode(x="건수:Q", y=alt.Y("저자:N", sort="-x"), tooltip=["저자", "건수"])
        )
        st.altair_chart(chart, width='stretch')

    st.divider()

    # --- 출판사 × 대분류 히트맵 ---
    st.subheader(f"출판사(보유 건수 상위 {top_n}) × 대분류 히트맵")
    top_publishers = filtered["출판사"].value_counts().head(top_n).index.tolist()
    heat_df = filtered[filtered["출판사"].isin(top_publishers)]
    heat_count = heat_df.groupby(["출판사", "대분류"]).size().reset_index(name="건수")
    heatmap = (
        alt.Chart(heat_count)
        .mark_rect()
        .encode(
            x=alt.X("대분류:N", title="대분류"),
            y=alt.Y("출판사:N", sort=top_publishers, title="출판사"),
            color=alt.Color("건수:Q", title="건수", scale=alt.Scale(scheme="blues")),
            tooltip=["출판사", "대분류", "건수"],
        )
    )
    st.altair_chart(heatmap, width='stretch')

    st.divider()

    # --- 보유 권수 분포 ---
    st.subheader("보유 권수 분포 (100권 이하)")
    hist_df = filtered[filtered["보유 권수"] <= 100]
    hist = (
        alt.Chart(hist_df)
        .mark_bar()
        .encode(
            x=alt.X("보유 권수:Q", bin=alt.Bin(maxbins=30), title="보유 권수"),
            y=alt.Y("count()", title="건수"),
            tooltip=[alt.Tooltip("count()", title="건수")],
        )
    )
    st.altair_chart(hist, width='stretch')

    with st.expander("보유 권수 상위 자료 보기 (e러닝 등 대량 보유 포함)"):
        st.dataframe(
            filtered.sort_values("보유 권수", ascending=False).head(20),
            width='stretch',
        )

    st.divider()

    # --- 대분류별 평균 보유 권수 ---
    st.subheader("대분류별 평균 보유 권수")
    cat_avg = filtered.groupby("대분류")["보유 권수"].mean().reset_index()
    cat_avg.columns = ["대분류", "평균 보유 권수"]
    avg_chart = (
        alt.Chart(cat_avg)
        .mark_bar()
        .encode(
            x=alt.X("평균 보유 권수:Q", title="평균 보유 권수"),
            y=alt.Y("대분류:N", sort="-x", title="대분류"),
            tooltip=["대분류", alt.Tooltip("평균 보유 권수:Q", format=".2f")],
        )
    )
    st.altair_chart(avg_chart, width='stretch')
    st.caption("일부 대분류는 e러닝 등 대량 보유 자료(수천~1만 권 단위)의 영향으로 평균이 실제 체감보다 크게 나올 수 있습니다.")

    st.divider()

    # --- 데이터 테이블 ---
    st.subheader("전체 데이터")
    st.dataframe(filtered, width='stretch', height=400)

    csv_download = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "필터링된 데이터 CSV 다운로드",
        data=csv_download,
        file_name="종로구_전자도서관_필터결과.csv",
        mime="text/csv",
    )


def render_district_comparison():
    data = load_all_districts()

    st.title("🏙️ 자치구별 전자도서관 소장 비교")
    st.caption(
        "종로구·동대문구·동작구·서초구·영등포구 5개 자치구의 전자도서관(전자책) 소장 데이터를 비교합니다. "
        "각 구는 데이터 기준일이 다르고(2023~2026년), 원본 분류 체계도 서로 달라 유사 항목을 하나의 대분류로 통합했습니다. "
        "따라서 절대적인 순위보다는 상대적인 경향 파악용으로 참고해 주세요."
    )

    district_options = sorted(data["자치구"].unique())
    district_sel = st.multiselect("자치구 선택", district_options, default=district_options)
    filtered = data[data["자치구"].isin(district_sel)]

    st.divider()

    st.subheader("자치구별 총 자료 건수 / 출판사 수 / 저자 수")
    summary = (
        filtered.groupby("자치구")
        .agg(자료건수=("서명", "count"), 출판사수=("출판사", "nunique"), 저자수=("저자", "nunique"))
        .reset_index()
    )

    if len(summary):
        cols = st.columns(len(summary))
        for col, row in zip(cols, summary.itertuples()):
            with col:
                st.metric(row.자치구, f"{row.자료건수:,}건")
                st.caption(f"출판사 {row.출판사수:,}곳 · 저자 {row.저자수:,}명")

        bar = (
            alt.Chart(summary)
            .mark_bar()
            .encode(
                x=alt.X("자치구:N", sort="-y", title="자치구"),
                y=alt.Y("자료건수:Q", title="자료 건수"),
                color=alt.Color("자치구:N", legend=None),
                tooltip=["자치구", "자료건수", "출판사수", "저자수"],
            )
        )
        st.altair_chart(bar, width="stretch")
    else:
        st.info("자치구를 하나 이상 선택해 주세요.")

    st.divider()

    st.subheader("자치구별 대분류 비중 (통합 분류 기준)")
    cat_share = (
        filtered.groupby(["자치구", "카테고리"])
        .size()
        .reset_index(name="건수")
    )

    if len(cat_share):
        stacked = (
            alt.Chart(cat_share)
            .mark_bar()
            .encode(
                x=alt.X("건수:Q", stack="normalize", axis=alt.Axis(format="%"), title="비중"),
                y=alt.Y("자치구:N", title=None),
                color=alt.Color("카테고리:N", legend=alt.Legend(title="대분류")),
                tooltip=["자치구", "카테고리", "건수"],
            )
        )
        st.altair_chart(stacked, width="stretch")

    st.divider()

    st.subheader("자치구별 평균 보유 수량")
    st.caption("동대문구·서초구 원본 데이터에는 권/수량 정보가 없어 이 비교에서는 제외됩니다.")
    qty = (
        filtered.dropna(subset=["보유수량"])
        .groupby("자치구")["보유수량"]
        .mean()
        .reset_index(name="평균보유수량")
    )
    if len(qty):
        qty_chart = (
            alt.Chart(qty)
            .mark_bar()
            .encode(
                x=alt.X("자치구:N", sort="-y", title="자치구"),
                y=alt.Y("평균보유수량:Q", title="평균 보유 수량"),
                color=alt.Color("자치구:N", legend=None),
                tooltip=["자치구", alt.Tooltip("평균보유수량:Q", format=".2f")],
            )
        )
        st.altair_chart(qty_chart, width="stretch")
    else:
        st.info("선택된 자치구 중 보유 수량 정보가 있는 구가 없습니다.")


tab1, tab2 = st.tabs(["📚 종로구 상세 분석", "🏙️ 자치구 비교"])

with tab1:
    render_jongno_dashboard()

with tab2:
    render_district_comparison()
