import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="종로구 전자도서관 소장목록 분석", layout="wide")

CSV_PATH = "서울특별시 종로구_전자도서관소장목록_20250701.csv"


@st.cache_data
def load_data(path):
    df = pd.read_csv(path, encoding="cp949")
    df["데이터기준일"] = pd.to_datetime(df["데이터기준일"], errors="coerce")
    return df


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

# --- 대분류 분포 ---
st.subheader("대분류별 자료 건수")
cat_count = filtered["대분류"].value_counts().reset_index()
cat_count.columns = ["대분류", "건수"]
donut = (
    alt.Chart(cat_count)
    .mark_arc(innerRadius=80)
    .encode(theta="건수:Q", color="대분류:N", tooltip=["대분류", "건수"])
)
st.altair_chart(donut, width='stretch')

st.divider()

# --- 출판사 / 저자 Top N ---
c3, c4 = st.columns(2)
top_n = st.slider("Top N", min_value=5, max_value=30, value=15, step=5)

with c3:
    st.subheader(f"출판사 보유 건수 Top {top_n}")
    pub_top = filtered["출판사"].value_counts().head(top_n).reset_index()
    pub_top.columns = ["출판사", "건수"]
    chart = (
        alt.Chart(pub_top)
        .mark_bar()
        .encode(x="건수:Q", y=alt.Y("출판사:N", sort="-x"), tooltip=["출판사", "건수"])
    )
    st.altair_chart(chart, width='stretch')

with c4:
    st.subheader(f"저자 보유 건수 Top {top_n}")
    author_top = filtered["저자"].value_counts().head(top_n).reset_index()
    author_top.columns = ["저자", "건수"]
    chart = (
        alt.Chart(author_top)
        .mark_bar()
        .encode(x="건수:Q", y=alt.Y("저자:N", sort="-x"), tooltip=["저자", "건수"])
    )
    st.altair_chart(chart, width='stretch')

st.divider()

# --- 보유 권수 분포 ---
st.subheader("보유 권수 분포 (100권 이하)")
hist_df = filtered[filtered["보유 권수"] <= 100]
hist = (
    alt.Chart(hist_df)
    .mark_bar()
    .encode(
        x=alt.X("보유 권수:Q", bin=alt.Bin(maxbins=30)),
        y="count()",
        tooltip=["count()"],
    )
)
st.altair_chart(hist, width='stretch')

with st.expander("보유 권수 상위 자료 보기 (e러닝 등 대량 보유 포함)"):
    st.dataframe(
        filtered.sort_values("보유 권수", ascending=False).head(20),
        width='stretch',
    )

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
