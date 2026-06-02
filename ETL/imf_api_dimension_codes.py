


import requests
import pandas as pd
import sqlalchemy as sa
import settings as s
import json

BASE_URL = "https://api.imf.org/external/sdmx/2.1"
URL = f"{BASE_URL}/codelist/all/all/latest"
SCHEMA = "imf"
TABLE = "api_dimension_codes"
HEADERS = {"Accept": "application/vnd.sdmx.structure+json;version=1.0.0"}
REQUEST_TIMEOUT = 300

def fetch_json(url):
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print("First 500 chars:")
    print(response.text[:500])
    response.raise_for_status()
    return response.json()

def get_localized_text(value):
    if isinstance(value, dict): return value.get("en") or next(iter(value.values()), None)
    return value

def to_json(value):
    if value in [None, "", [], {}]: return None
    return json.dumps(value, ensure_ascii=False)
payload = fetch_json(URL)
codelists = (payload.get("data", {}).get("codelists", []))
rows = []
for codelist in codelists:
    codelist_agency_id = codelist.get("agencyID")
    codelist_id = codelist.get("id")
    codelist_version = codelist.get("version")
    codes = codelist.get("codes", [])
    for code in codes:
        rows.append({
            "codelist_agency_id": codelist_agency_id,
            "codelist_id": codelist_id,
            "codelist_version": codelist_version,
            "code_id": code.get("id"),
            "code_name": get_localized_text(code.get("name")),
            "description": get_localized_text(code.get("description")),
            "names_json": to_json(code.get("names")),
            "descriptions_json": to_json(code.get("descriptions")),
            "links_json": to_json(code.get("links"))})
df = pd.DataFrame(rows)
df = (df[df["code_id"].notna()].drop_duplicates(subset=["codelist_agency_id","codelist_id","codelist_version","code_id"]).reset_index(drop=True))
print("Codelists:", df["codelist_id"].nunique())
print("Rows:", len(df))
engine = sa.create_engine(s.connection_string, fast_executemany=True)
with engine.begin() as conn: conn.execute(sa.text(f"TRUNCATE TABLE {SCHEMA}.{TABLE}"))
df.to_sql(name=TABLE, schema=SCHEMA, con=engine, if_exists="append", index=False, chunksize=5000)
print(f"Inserted rows: {len(df)}")
print("DONE")


"""
CREATE TABLE imf.api_dimension_codes (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    codelist_agency_id NVARCHAR(100),
    codelist_id NVARCHAR(300),
    codelist_version NVARCHAR(100),
    code_id NVARCHAR(500),
    code_name NVARCHAR(MAX),
    [description] NVARCHAR(MAX),
    names_json NVARCHAR(MAX),
    descriptions_json NVARCHAR(MAX),
    links_json NVARCHAR(MAX),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""