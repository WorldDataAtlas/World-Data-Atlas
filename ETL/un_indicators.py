import requests
import pandas as pd
import sqlalchemy as sa
import settings as s

BASE_URL = "https://population.un.org/dataportalapi/api/v1"
ENDPOINT = "indicators"

def fetch_all_pages(endpoint):
    url = f"{BASE_URL}/{endpoint}?format=json"
    rows = []
    while url:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        payload = response.json()
        rows.extend(payload.get("data", []))
        url = payload.get("nextPage")
    return rows

def safe_get(row, *keys):
    for key in keys:
        value = row.get(key)
        if value not in [None, ""]: return value
    return None

indicators_raw = fetch_all_pages(ENDPOINT)
df_raw = pd.DataFrame(indicators_raw)
rows = []
for item in indicators_raw:
    rows.append({
        "indicator_id": safe_get(item, "id", "indicatorId"),
        "indicator_name": safe_get(item, "name", "indicator", "indicatorName"),
        "short_name": safe_get(item, "shortName", "short_name"),
        "description": safe_get(item, "description", "definition"),
        "topic_id": safe_get(item, "topicId"),
        "topic_name": safe_get(item, "topicName", "topic"),})

df_indicators = pd.DataFrame(rows)
df_indicators["indicator_id"] = pd.to_numeric(df_indicators["indicator_id"], errors="coerce").astype("Int64")
df_indicators["topic_id"] = pd.to_numeric(df_indicators["topic_id"], errors="coerce").astype("Int64")
df_indicators = (df_indicators[df_indicators["indicator_id"].notna()]
    .drop_duplicates(subset=["indicator_id"])
    .reset_index(drop=True))

engine = sa.create_engine(s.connection_string, fast_executemany=True)
with engine.begin() as conn: conn.execute(sa.text("TRUNCATE TABLE un.indicators"))
df_indicators.to_sql(name="indicators", schema="un", con=engine, if_exists="append", index=False, chunksize=500)

"""
CREATE TABLE un.indicators (
    indicator_id INT PRIMARY KEY,
    indicator_name NVARCHAR(MAX),
    short_name NVARCHAR(MAX),
    description NVARCHAR(MAX),
    topic_id INT NULL,
    topic_name NVARCHAR(255),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""