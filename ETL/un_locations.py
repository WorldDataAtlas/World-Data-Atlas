import requests
import pandas as pd
import sqlalchemy as sa
import settings as s

BASE_URL = "https://population.un.org/dataportalapi/api/v1"
ENDPOINT = "locations"

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

locations_raw = fetch_all_pages(ENDPOINT)
df_raw = pd.DataFrame(locations_raw)
rows = []

for item in locations_raw:
    rows.append({
        "location_id": item.get("id"),
        "location_name": item.get("name"),
        "iso2_code": item.get("iso2"),
        "iso3_code": item.get("iso3"),
        "longitude": item.get("longitude"),
        "latitude": item.get("latitude"),})

df_locations = pd.DataFrame(rows)
df_locations["location_id"] = pd.to_numeric(df_locations["location_id"],errors="coerce").astype("Int64")
df_locations["longitude"] = pd.to_numeric(df_locations["longitude"],errors="coerce")
df_locations["latitude"] = pd.to_numeric(df_locations["latitude"],errors="coerce")
df_locations = (df_locations[df_locations["location_id"].notna()].drop_duplicates(subset=["location_id"]).reset_index(drop=True))

engine = sa.create_engine(s.connection_string, fast_executemany=True)
with engine.begin() as conn: conn.execute(sa.text("TRUNCATE TABLE un.locations"))
df_locations.to_sql(name="locations", schema="un", con=engine, if_exists="append", index=False, chunksize=500)

"""
CREATE TABLE un.locations (
    location_id INT PRIMARY KEY,
    location_name NVARCHAR(MAX),
    iso2_code NVARCHAR(2),
    iso3_code NVARCHAR(3),
    longitude FLOAT NULL,
    latitude FLOAT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""