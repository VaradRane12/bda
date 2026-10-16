"""
Step 3: Dashboard for the results produced by analysis.ipynb (Spark).

Run:  streamlit run app.py
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Wikipedia Trends", page_icon="📈", layout="wide")


@st.cache_data
def load():
    r = Path(__file__).parent / "results"   # works no matter which folder we run from
    return {
        "summary": json.load(open(r / "summary.json")),
        "top_pages": pd.read_csv(r / "top_pages.csv"),
        "hourly": pd.read_csv(r / "hourly_traffic.csv", parse_dates=["hour"]),
        "device": pd.read_csv(r / "device_split.csv"),
        "trending": pd.read_csv(r / "trending.csv", parse_dates=["peak_hour"]),
        "heatmap": pd.read_csv(r / "heatmap.csv"),
        "words": pd.read_csv(r / "top_words.csv"),
        "page_hourly": pd.read_csv(r / "page_hourly.csv", parse_dates=["hour"]),
    }


try:
    d = load()
except FileNotFoundError:
    st.error("No results found. Run `analysis.ipynb` first, it creates the `results/` folder.")
    st.stop()

s = d["summary"]


def short(n):
    for unit, size in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if n >= size:
            return f"{n / size:.1f}{unit}"
    return str(n)


# ---------------- Header ----------------
st.title("📈 What was the world curious about?")
st.caption(
    f"English Wikipedia pageviews · {s['first_hour'][:16]} → {s['last_hour'][:16]} UTC · "
    "processed with Apache Spark (PySpark)"
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Raw rows processed", short(s["raw_rows"]))
c2.metric("Raw data size", f"{s['raw_gb']} GB")
c3.metric("Hourly files", s["files"])
c4.metric("Unique pages", short(s["unique_pages"]))
c5.metric("Total views", short(s["total_views"]))

tabs = st.tabs(["🏆 Top pages", "🔥 Trending", "⏱️ Traffic over time", "🗺️ Heatmap",
                "🔎 Search a page", "🔤 Top words", "⚙️ How it works"])

# ---------------- Top pages ----------------
with tabs[0]:
    n = st.slider("How many pages?", 5, 25, 15)
    top = d["top_pages"].head(n)
    fig = px.bar(top.iloc[::-1], x="views", y="title", orientation="h", text_auto=".3s")
    fig.update_layout(height=30 * n + 100, yaxis_title=None, xaxis_title="Views")
    st.plotly_chart(fig, width="stretch")

# ---------------- Trending ----------------
with tabs[1]:
    st.markdown(
        "A page is **trending** when its busiest hour is far above its normal hour.  \n"
        "`spike score = peak hour views ÷ average hourly views`"
    )
    tr = d["trending"]
    st.dataframe(
        tr[["title", "spike_score", "peak_views", "avg_views", "peak_hour"]],
        width="stretch", hide_index=True,
        column_config={"spike_score": st.column_config.ProgressColumn(
            "spike score", format="%.1fx", min_value=0, max_value=float(tr.spike_score.max()))},
    )
    pick = st.selectbox("See the spike for:", tr.title)
    one = d["page_hourly"].query("title == @pick").sort_values("hour")
    fig = px.area(one, x="hour", y="views", title=f"{pick}: views per hour")
    st.plotly_chart(fig, width="stretch")

# ---------------- Traffic over time ----------------
with tabs[2]:
    hourly = d["hourly"]
    fig = px.area(hourly, x="hour", y="views", color="device",
                  title="Views per hour, desktop vs mobile (UTC)")
    st.plotly_chart(fig, width="stretch")

    left, right = st.columns(2)
    fig = px.pie(d["device"], names="device", values="views", hole=0.55, title="Device share")
    left.plotly_chart(fig, width="stretch")

    by_hod = hourly.assign(hour_of_day=hourly.hour.dt.hour).groupby("hour_of_day", as_index=False).views.mean()
    fig = px.bar(by_hod, x="hour_of_day", y="views", title="Average views by hour of day (UTC)")
    right.plotly_chart(fig, width="stretch")

# ---------------- Heatmap ----------------
with tabs[3]:
    hm = d["heatmap"].pivot(index="title", columns="hour_of_day", values="views").fillna(0)
    hm = hm.loc[hm.sum(axis=1).sort_values(ascending=False).index]
    fig = px.imshow(hm, aspect="auto", color_continuous_scale="YlOrRd",
                    labels=dict(x="Hour of day (UTC)", y="", color="views"),
                    title="When are the top pages read?")
    fig.update_layout(height=600)
    st.plotly_chart(fig, width="stretch")

# ---------------- Search ----------------
with tabs[4]:
    ph = d["page_hourly"]
    titles = ph.groupby("title").views.sum().sort_values(ascending=False).index.tolist()
    chosen = st.multiselect("Compare pages (top 300 + trending)", titles, default=titles[:3])
    if chosen:
        fig = px.line(ph[ph.title.isin(chosen)].sort_values("hour"), x="hour", y="views", color="title")
        st.plotly_chart(fig, width="stretch")

# ---------------- Words ----------------
with tabs[5]:
    st.markdown("Computed with **RDD MapReduce**: each word in a title gets that page's views, then `reduceByKey` adds them up.")
    w = d["words"].head(25)
    fig = px.treemap(w, path=["word"], values="views", color="views", color_continuous_scale="Blues")
    fig.update_layout(height=550, margin=dict(t=10, l=0, r=0, b=0))
    st.plotly_chart(fig, width="stretch")

# ---------------- How it works ----------------
with tabs[6]:
    st.graphviz_chart("""
    digraph {
        rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#eef3ff", fontname="Helvetica"];
        A [label="Wikimedia\\nhourly dumps (.gz)"];
        B [label="HDFS / local disk"];
        C [label="Spark: load +\\nclean + aggregate"];
        D [label="Parquet\\n(cleaned data)"];
        E [label="Spark SQL +\\nRDD MapReduce"];
        F [label="results/*.csv"];
        G [label="Streamlit\\ndashboard"];
        A -> B -> C -> D -> E -> F -> G;
    }
    """)
    st.markdown(f"""
| Step | Tool | What happens |
|---|---|---|
| Ingest | Python `requests` | {s['files']} hourly files downloaded ({s['raw_gb']} GB) |
| Storage | HDFS / local disk | Raw gzip files stored as-is |
| Processing | **Apache Spark** on {s['cores']} cores | {s['raw_rows']:,} rows counted in {s['load_seconds']} s |
| Cleaning | Spark DataFrames | Kept English Wikipedia, removed system pages → {s['clean_rows']:,} rows |
| Storage | **Parquet** | Columnar, compressed format for fast re-reads |
| Analysis | **Spark SQL** | Top pages, time-series, device split, spike detection |
| Analysis | **RDD MapReduce** | Word count weighted by views |
| Visualization | **Streamlit + Plotly** | This dashboard (time-series, heatmap, treemap) |
""")
