import requests
import pandas as pd
import sqlalchemy as sa
import settings as s
import json
import re

BASE_URL = "https://api.imf.org/external/sdmx/2.1"
URL = f"{BASE_URL}/dataflow/all/all/latest"
SCHEMA = "imf"
TABLE = "api_dataflows"
HEADERS = {"Accept": "application/vnd.sdmx.structure+json;version=1.0.0"}
REQUEST_TIMEOUT = 120

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

def parse_dataflow_urn(urn):
    if not urn: return None
    match = re.search(r"Dataflow=([^:]+):([^(]+)\(([^)]+)\)", urn)
    if not match: return None
    return {"dataflow_agency_id": match.group(1), "dataflow_id": match.group(2), "dataflow_version": match.group(3)}

def get_dataflow_urn(links):
    if not isinstance(links, list): return None
    for link in links:
        urn = link.get("urn")
        if urn and "Dataflow=" in urn: return urn
    return None

payload = fetch_json(URL)
dataflows = (payload.get("data", {}).get("dataflows", []))
rows = []
for item in dataflows:
    links = item.get("links", [])
    dataflow_urn = get_dataflow_urn(links)
    parsed_urn = parse_dataflow_urn(dataflow_urn) or {}
    rows.append({
        "dataflow_id": item.get("id"),
        "dataflow_name": get_localized_text(item.get("name")),
        "description": get_localized_text(item.get("description")),
        "dataflow_agency_id": parsed_urn.get("dataflow_agency_id"),
        "dataflow_version": parsed_urn.get("dataflow_version"),
        "dataflow_urn": dataflow_urn,
        "structure_urn": item.get("structure"),
        "agency_id": item.get("agencyID"),
        "version": item.get("version"),
        "annotations_json": to_json(item.get("annotations")),
        "links_json": to_json(item.get("links")),
        "names_json": to_json(item.get("names")),})

df = pd.DataFrame(rows)
df = (df[df["dataflow_id"].notna()].drop_duplicates(subset=["dataflow_id"]).reset_index(drop=True))
print("Rows found:", len(df))
engine = sa.create_engine(s.connection_string, fast_executemany=True)
with engine.begin() as conn: conn.execute(sa.text(f"TRUNCATE TABLE {SCHEMA}.{TABLE}"))
df.to_sql(name=TABLE, schema=SCHEMA, con=engine, if_exists="append", index=False, chunksize=1000)
print()
print(f"Inserted rows: {len(df)}")
print("DONE")

"""
CREATE TABLE imf.api_dataflows (
    dataflow_id NVARCHAR(100) PRIMARY KEY,
    dataflow_name NVARCHAR(MAX),
    [description] NVARCHAR(MAX),
    dataflow_agency_id NVARCHAR(100),
    dataflow_version NVARCHAR(50),
    dataflow_urn NVARCHAR(MAX),
    structure_urn NVARCHAR(MAX) NULL,
    agency_id NVARCHAR(100),
    [version] NVARCHAR(50),
    annotations_json NVARCHAR(MAX),
    links_json NVARCHAR(MAX),
    names_json NVARCHAR(MAX),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""