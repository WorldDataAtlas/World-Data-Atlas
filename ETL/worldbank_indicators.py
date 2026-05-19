import requests
import pandas as pd
import sqlalchemy as sa
import json
import settings as s

def to_json(value):
    if value is None: return None
    return json.dumps(value, ensure_ascii=False)

def fetch_all_worldbank_indicators():
    base_url = "https://api.worldbank.org/v2/indicator"
    first_params = {"format": "json", "per_page": 1000, "page": 1}
    first_response = requests.get(base_url, params=first_params, timeout=60)
    first_response.raise_for_status()
    first_json = first_response.json()
    metadata = first_json[0]
    total_pages = metadata["pages"]
    print(f"Total pages: {total_pages}")
    print(f"Total indicators: {metadata['total']}")
    all_rows = []
    for page in range(1, total_pages + 1):
        params = {"format": "json", "per_page": 1000, "page": page}
        response = requests.get(base_url, params=params, timeout=60)
        response.raise_for_status()
        json_data = response.json()
        data = json_data[1]
        print(f"Downloading page {page}/{total_pages}... rows: {len(data)}")
        for item in data:
            source = item.get("source", {})
            topics = item.get("topics", [])
            topic_ids = [t.get("id") for t in topics if t.get("id")]
            topic_names = [t.get("value") for t in topics if t.get("value")]
            all_rows.append({
                "indicator_code": item.get("id"),
                "indicator_name": item.get("name"),
                "source_id": source.get("id"),
                "source_name": source.get("value"),
                "source_note": item.get("sourceNote"),
                "source_organization": item.get("sourceOrganization"),
                "topics_json": to_json(topics),
                "topic_ids": ", ".join(topic_ids) if topic_ids else None,
                "topic_names": ", ".join(topic_names) if topic_names else None})
    return pd.DataFrame(all_rows)

df_indicators = fetch_all_worldbank_indicators()
engine = sa.create_engine(s.connection_string, fast_executemany=True)
with engine.begin() as conn: conn.execute(sa.text("TRUNCATE TABLE worldbank.indicators"))
df_indicators.to_sql(name="indicators", schema="worldbank", con=engine, if_exists="append", index=False, chunksize=500)

"""
CREATE TABLE worldbank.indicators (
    indicator_code NVARCHAR(MAX),
    indicator_name NVARCHAR(MAX),
    source_id NVARCHAR(MAX),
    source_name NVARCHAR(MAX),
    source_note NVARCHAR(MAX),
    source_organization NVARCHAR(MAX),
    topics NVARCHAR(MAX),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""