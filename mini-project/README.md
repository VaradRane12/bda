# Wikipedia Pageview Trend Analytics using Apache Spark

> *"We analyzed 470 million Wikipedia page visits to find what the world was curious about, and when."*

BDA Lab Mini Project (BIT27PE10): Design and implement a Big Data Analytics application.

## Tech stack (from the syllabus)

| Syllabus topic | Used for |
|---|---|
| **Apache Spark (PySpark)** | Loading, cleaning and analyzing ~470M rows in parallel |
| **Spark SQL** | Top pages, time-series, device split, trending/spike detection |
| **RDDs + MapReduce** | Word count weighted by views (`flatMap` → `reduceByKey`) |
| **HDFS** | Stores the raw files; Spark reads them from `hdfs://localhost:9000/wiki/raw` (`hdfs_upload.sh`) |
| **Parquet** | Columnar storage for the cleaned data |
| **Python visualization** | Time-series, heatmap, treemap with Streamlit + Plotly |

## Dataset

[Wikimedia hourly pageview dumps](https://dumps.wikimedia.org/other/pageviews/). One gzip file per hour, ~60 MB and ~6.5 million rows each.

```
en Virat_Kohli 2453 0
│  │           │    └ unused
│  │           └ views in that hour
│  └ page title
└ project (en = English desktop, en.m = English mobile)
```

The default is **3 days = 72 files ≈ 4.2 GB ≈ 470 million rows**.

## How to run

```bash
# 1. setup (Python 3.11 + Java 17)
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-spark.txt

# 2. download data (~4.2 GB, ~7 minutes from the mirror)
python download_data.py                         # or: --start 2026-09-25 --days 7

# 3. put the data in HDFS (needs Hadoop running: start-dfs.sh)
./hdfs_upload.sh
#    the notebook reads hdfs://localhost:9000/wiki/raw/*.gz
#    (to read local files instead, change DATA_PATH in the notebook to data/raw/*.gz)

# 4. run the Spark analysis: open and "Run All"
jupyter notebook analysis.ipynb

# 5. open the dashboard
streamlit run app.py
```

## Deploy the dashboard (Streamlit Community Cloud)

On [share.streamlit.io](https://share.streamlit.io) → **Create app** → repo `VaradRane12/bda`, branch `mini-project`,
main file `mini-project/app.py`. It only installs `requirements.txt` (Streamlit, Pandas, Plotly). Spark isn't needed,
because the dashboard reads the precomputed `results/` folder.

## Project structure

```
download_data.py   Step 1: download hourly files from Wikimedia
hdfs_upload.sh     Step 1b: copy raw data into HDFS
analysis.ipynb     Step 2: all Spark processing (load → clean → Parquet → SQL + RDD → results/)
app.py             Step 3: Streamlit dashboard reading results/
requirements.txt        dashboard dependencies (used by Streamlit Cloud)
requirements-spark.txt  everything, incl. PySpark + Jupyter
results/           Small CSV/JSON outputs from Spark (what the dashboard shows)
data/raw/          Downloaded .gz files before upload to HDFS (not committed)
data/clean/        Cleaned Parquet data      (not committed)
```

## Analyses

1. **Top pages**: most viewed English Wikipedia articles
2. **Trending / spike detection**: `peak hour views ÷ average hourly views`, which finds news events automatically
3. **Time-series**: views per hour, desktop vs mobile
4. **Heatmap**: what hour of the day each top page is read
5. **MapReduce word count**: most popular words across everything people read

## 5 Vs of this dataset

- **Volume**: ~470M rows for 3 days; a full month is ~4 billion
- **Velocity**: a new file every hour, 24×7
- **Variety**: 300+ languages and projects, desktop and mobile, system pages mixed in
- **Veracity**: noisy (special pages, bots, junk titles), so it needs cleaning
- **Value**: shows real-world events through what people read
