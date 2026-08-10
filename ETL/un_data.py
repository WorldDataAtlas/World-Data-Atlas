import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pandas as pd
import sqlalchemy as sa
import settings as s

INDICATOR_IDS = [59]

START_YEAR = 1900
END_YEAR = 2050

BASE_URL = "https://population.un.org/dataportalapi/api/v1"
TOKEN = s.un_token
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
SCHEMA = "un"
TABLE = "data"
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
BATCH_LOCATION_SIZE = 50
MAX_WORKERS = 5
SQL_CHUNKSIZE = 20000
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
        response = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = session.get(url, timeout=REQUEST_TIMEOUT)
                if response.status_code == 404:
                    print(f"404 skip: {url}")
                    return rows
                if response.status_code == 401: raise Exception("Unauthorized - invalid or expired UN token")
                if response.status_code in [429, 500, 502, 503, 504]:
                    wait = attempt
                    print(f"{response.status_code} retry {attempt}/{MAX_RETRIES}, waiting {wait}s")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                break
            except requests.exceptions.Timeout:
                wait = attempt
                print(f"TIMEOUT retry {attempt}/{MAX_RETRIES}, waiting {wait}s")
                time.sleep(wait)
            except requests.exceptions.RequestException as e:
                wait = attempt
                print(f"REQUEST ERROR retry {attempt}/{MAX_RETRIES}: {e}")
                time.sleep(wait)
        else:
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
    url = (f"{BASE_URL}/data/indicators/{indicator_id}/locations/{location_id}/start/{START_YEAR}/end/{END_YEAR}/?format=json")
    return fetch_all_pages(url)

def fetch_one_location(indicator_id, location):
    location_id = location["id"]
    location_name = location.get("name")
    rows = fetch_indicator_location_data(indicator_id=indicator_id, location_id=location_id)
    return {"indicator_id": indicator_id, "location_id": location_id, "location_name": location_name, "rows": rows}

def normalize_indicator_rows(raw_rows):
    if not raw_rows: return pd.DataFrame()
    rows = []
    for item in raw_rows:
        rows.append({
            "location_id": safe_get(item, "locationId"),
            "location_name": safe_get(item, "location", "locationName", "locationLabel"),
            "iso2_code": safe_get(item, "iso2", "iso2Code"),
            "iso3_code": safe_get(item, "iso3", "iso3Code"),
            "indicator_id": safe_get(item, "indicatorId"),
            "indicator_name": safe_get(item, "indicator", "indicatorName", "indicatorLabel"),
            "year": safe_get(item, "timeLabel", "year", "time"),
            "value": safe_get(item, "value"),
            "variant_id": safe_get(item, "variantId"),
            "variant_name": safe_get(item, "variant", "variantName", "variantLabel"),
            "sex_id": safe_get(item, "sexId"),
            "sex_name": safe_get(item, "sex", "sexLabel","sexName"),
            "age_id": safe_get(item, "ageId"),
            "age_name": safe_get(item, "ageLabel", "age", "ageName"),
            "category_id": safe_get(item, "categoryId"),
            "category_name": safe_get(item, "category", "categoryLabel", "categoryName")})
    df = pd.DataFrame(rows)
    int_cols = ["location_id", "indicator_id", "year", "variant_id", "sex_id", "age_id", "category_id"]
    for col in int_cols: df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["indicator_id"].notna() & df["year"].notna() & df["value"].notna()].reset_index(drop=True)
    return df

def insert_batch(df, engine):
    if df.empty: return 0
    df.to_sql(name=TABLE, schema=SCHEMA, con=engine, if_exists="append", index=False, chunksize=SQL_CHUNKSIZE)
    return len(df)

def chunk_list(values, chunk_size):
    for i in range(0, len(values), chunk_size): yield values[i:i + chunk_size]

def delete_old_data(engine):
    with engine.begin() as conn:
        for indicator_id in INDICATOR_IDS:
            conn.execute(
                sa.text(f"DELETE FROM {SCHEMA}.{TABLE} WHERE indicator_id = :indicator_id"), {"indicator_id": indicator_id})

def main():
    start_time = datetime.now()
    engine = sa.create_engine(s.connection_string, fast_executemany=True)
    locations_raw = fetch_locations()
    locations_selected = [item for item in locations_raw if item.get("id") is not None and item.get("iso3") is not None]
    print(f"Locations selected: {len(locations_selected)}")
    delete_old_data(engine)
    print("Old data deleted.")
    total_inserted, errors = 0, []
    for indicator_id in INDICATOR_IDS:
        print(f"\n=== Indicator {indicator_id} ===")
        for batch_number, location_batch in enumerate(
            chunk_list(locations_selected, BATCH_LOCATION_SIZE),
            start=1):
            print(f"\nBatch {batch_number} | locations: {len(location_batch)}")
            batch_raw_rows = []
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(fetch_one_location, indicator_id, location) for location in location_batch]
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        print(f'{result["location_id"]} | {result["location_name"]} | rows: {len(result["rows"])}')
                        batch_raw_rows.extend(result["rows"])
                    except Exception as e:
                        error = {"indicator_id": indicator_id, "error": str(e)}
                        errors.append(error)
                        print(f"ERROR: {error}")
            df_batch = normalize_indicator_rows(batch_raw_rows)
            inserted = insert_batch(df_batch, engine)
            total_inserted += inserted
            print(f"Inserted batch rows: {inserted}")
            print(f"Total inserted: {total_inserted}")
    elapsed = datetime.now() - start_time
    print("\nDONE")
    print(f"Total inserted: {total_inserted}")
    print(f"Errors: {len(errors)}")
    print(f"Elapsed: {elapsed}")
    if errors:
        print("\nERROR SAMPLE:")
        for error in errors[:20]: print(error)
if __name__ == "__main__": main()

"""
CREATE TABLE [un].[data](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[location_id] [int] NULL,
	[location_name] [nvarchar](max) NULL,
	[iso2_code] [nvarchar](20) NULL,
	[iso3_code] [nvarchar](30) NULL,
	[indicator_id] [int] NOT NULL,
	[indicator_name] [nvarchar](max) NULL,
	[year] [int] NOT NULL,
	[value] [float] NULL,
	[variant_id] [int] NULL,
	[variant_name] [nvarchar](max) NULL,
	[sex_id] [int] NULL,
	[sex_name] [nvarchar](max) NULL,
	[age_id] [int] NULL,
	[age_name] [nvarchar](max) NULL,
	[category_id] [int] NULL,
	[category_name] [nvarchar](max) NULL,
	[created_at] [datetime2](7) NOT NULL
)
"""