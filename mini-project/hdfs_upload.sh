#!/bin/bash
# Optional: store the raw data in HDFS (Hadoop Distributed File System).
# Needs Hadoop running:  start-dfs.sh
# Then in analysis.ipynb set DATA_PATH = "hdfs://localhost:9000/wiki/raw/*.gz"

hdfs dfs -mkdir -p /wiki/raw
hdfs dfs -put -f data/raw/*.gz /wiki/raw/

echo "Files in HDFS:"
hdfs dfs -ls -h /wiki/raw | head -10
echo "Total size:"
hdfs dfs -du -s -h /wiki/raw
