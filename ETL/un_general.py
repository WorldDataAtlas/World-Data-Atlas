import requests
import pandas as pd
import sqlalchemy as sa
import time
import settings as s

INDICATOR_IDS = [54]

START_YEAR = 1900
END_YEAR = 2035

BASE_URL = "https://population.un.org/dataportalapi/api/v1"
TOKEN = s.un_token
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
SCHEMA, TABLE = "un", "data"
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
BATCH_LOCATION_SIZE = 25
SQL_CHUNKSIZE = 5000

session = requests.Session()
session.headers.update(HEADERS)

def safe_get(row, *keys):
    for key in keys:
        value = row.get(key)
        if value not in [None, ""]: return value
    return None

def fetch_all_pages(url):
    rows = []
    while url:
        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = session.get(url, timeout=REQUEST_TIMEOUT)
                if response.status_code == 404:
                    print(f"404 skip: {url}")
                    return rows
                if response.status_code in [429, 500, 502, 503, 504]:
                    wait = attempt * 3
                    print(f"{response.status_code} retry {attempt}/{MAX_RETRIES}, waiting {wait}s")
                    time.sleep(wait)
                    continue
                if response.status_code == 401: raise Exception("Unauthorized - invalid or expired UN token")
                response.raise_for_status()
                success = True
                break
            except requests.exceptions.Timeout:
                wait = attempt * 3
                print(f"TIMEOUT retry {attempt}/{MAX_RETRIES}, waiting {wait}s")
                time.sleep(wait)
            except requests.exceptions.RequestException as e:
                wait = attempt * 3
                print(f"REQUEST ERROR retry {attempt}/{MAX_RETRIES}: {e}")
                time.sleep(wait)
        if not success:
            print(f"FAILED URL, skipping: {url}")
            return rows
        payload = response.json()
        rows.extend(payload.get("data", []))
        url = payload.get("nextPage")
    return rows

def fetch_locations():
    url = f"{BASE_URL}/locations?format=json"
    return fetch_all_pages(url)

def fetch_indicator_location_data(indicator_id, location_id):
    url = (
        f"{BASE_URL}/data/indicators/{indicator_id}"
        f"/locations/{location_id}"
        f"/start/{START_YEAR}"
        f"/end/{END_YEAR}/"
        f"?format=json")
    return fetch_all_pages(url)

def normalize_indicator_rows(raw_rows):
    rows = []
    for item in raw_rows:
        rows.append({
            "location_id": safe_get(item, "locationId"),
            "location_name": safe_get(item, "location", "locationName"),
            "iso2_code": safe_get(item, "iso2", "iso2Code"),
            "iso3_code": safe_get(item, "iso3", "iso3Code"),
            "indicator_id": safe_get(item, "indicatorId"),
            "indicator_name": safe_get(item, "indicator", "indicatorName"),
            "year": safe_get(item, "timeLabel", "year", "time"),
            "value": safe_get(item, "value"),
            "variant_id": safe_get(item, "variantId"),
            "variant_name": safe_get(item, "variant", "variantName"),
            "sex_id": safe_get(item, "sexId"),
            "sex_name": safe_get(item, "sex", "sexName"),
            "age_id": safe_get(item, "ageId"),
            "age_name": safe_get(item, "age", "ageName"),
            "category_id": safe_get(item, "categoryId"),
            "category_name": safe_get(item, "category", "categoryName"),})
    df = pd.DataFrame(rows)
    if df.empty: return df
    int_cols = ["location_id", "indicator_id", "year", "variant_id", "sex_id", "age_id", "category_id",]
    for col in int_cols: df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["indicator_id"].notna()& df["year"].notna()& df["value"].notna()].reset_index(drop=True)
    return df

def insert_batch(df, engine):
    if df.empty: return 0
    df.to_sql(name=TABLE, schema=SCHEMA, con=engine, if_exists="append", index=False, chunksize=SQL_CHUNKSIZE)
    return len(df)

def chunk_list(values, chunk_size):
    for i in range(0, len(values), chunk_size): yield values[i:i + chunk_size]

engine = sa.create_engine(s.connection_string, fast_executemany=True)
locations_raw = fetch_locations()
locations_selected = [
    item for item in locations_raw
    if item.get("id") is not None
    and item.get("iso3") is not None]

print(f"Locations selected: {len(locations_selected)}")

with engine.begin() as conn:
    for indicator_id in INDICATOR_IDS:
        conn.execute(sa.text(f"DELETE FROM {SCHEMA}.{TABLE} WHERE indicator_id = :indicator_id"), {"indicator_id": indicator_id})
print("Old data deleted.")

total_inserted,errors  = 0, []

for indicator_id in INDICATOR_IDS:
    print(f"\n=== Indicator {indicator_id} ===")
    for batch_number, location_batch in enumerate(
        chunk_list(locations_selected, BATCH_LOCATION_SIZE),
        start=1):
        print(f"\nBatch {batch_number} | locations: {len(location_batch)}")
        batch_raw_rows = []
        for loc in location_batch:
            location_id = loc["id"]
            location_name = loc.get("name")
            try:
                raw_rows = fetch_indicator_location_data(indicator_id=indicator_id, location_id=location_id)
                print(f"{location_id} | {location_name} | rows: {len(raw_rows)}")
                batch_raw_rows.extend(raw_rows)
            except Exception as e:
                error = {"indicator_id": indicator_id, "location_id": location_id, "location_name": location_name, "error": str(e)}
                errors.append(error)
                print(f"ERROR: {error}")
        df_batch = normalize_indicator_rows(batch_raw_rows)
        inserted = insert_batch(df_batch, engine)
        total_inserted += inserted

        print(f"Inserted batch rows: {inserted}")
        print(f"Total inserted: {total_inserted}")

print("\nDONE")
print(f"Total inserted: {total_inserted}")
print(f"Errors: {len(errors)}")

if errors:
    print("\nERROR SAMPLE:")
    for error in errors[:20]: print(error)

"""
CREATE TABLE un.data (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    location_id INT NULL,
    location_name NVARCHAR(MAX),
    iso2_code NVARCHAR(20),
    iso3_code NVARCHAR(30),
    indicator_id INT NOT NULL,
    indicator_name NVARCHAR(MAX),
    [year] INT NOT NULL,
    [value] FLOAT NULL,
    variant_id INT NULL,
    variant_name NVARCHAR(MAX),
    sex_id INT NULL,
    sex_name NVARCHAR(MAX),
    age_id INT NULL,
    age_name NVARCHAR(MAX),
    category_id INT NULL,
    category_name NVARCHAR(MAX),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""