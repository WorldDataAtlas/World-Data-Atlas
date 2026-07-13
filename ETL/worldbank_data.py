import requests
import pandas as pd
import sqlalchemy as sa
import settings as s

INDICATOR = ""
INDICATORS = ["PAY.TAX.TOT.TAX.RT.ZS"]

SCHEMA = "worldbank"
TABLE = "data"
engine = sa.create_engine(s.connection_string, fast_executemany=True)

def fetch_worldbank_indicator(indicator_code):
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}"
    params = {"format": "json", "per_page": 20000}
    response = requests.get(url, params=params, timeout=120)
    response.raise_for_status()
    json_data = response.json()
    if len(json_data) < 2 or json_data[1] is None: return pd.DataFrame()
    rows = []
    for item in json_data[1]:
        rows.append({
            "country_code": item.get("countryiso3code"),
            "country_id": item.get("country", {}).get("id"),
            "country_name": item.get("country", {}).get("value"),
            "indicator_code": item.get("indicator", {}).get("id"),
            "indicator_name": item.get("indicator", {}).get("value"),
            "year": item.get("date"),
            "value": item.get("value"),
            "unit": item.get("unit"),
            "obs_status": item.get("obs_status"),
            "decimal_places": item.get("decimal"),})
    return pd.DataFrame(rows)

for INDICATOR in INDICATORS:
    print(INDICATOR)
    df = fetch_worldbank_indicator(INDICATOR)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["decimal_places"] = pd.to_numeric(df["decimal_places"], errors="coerce").astype("Int64")
    df = df[df["country_code"].notna()]
    df = df[df["country_code"] != ""]
    df = df[df["year"].notna()]
    df = df[df["value"].notna()]
    df = df.reset_index(drop=True)
    
    print(len(df))
    with engine.begin() as conn:
        conn.execute(
            sa.text(f"""
                DELETE FROM {SCHEMA}.{TABLE}
                WHERE indicator_code = :indicator_code
            """),{"indicator_code": INDICATOR})
    df.to_sql(name=TABLE, schema=SCHEMA, con=engine, if_exists="append", index=False, chunksize=500)

"""
CREATE TABLE worldbank.data (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    country_code NVARCHAR(3) NOT NULL,
    country_id NVARCHAR(3),
    country_name NVARCHAR(255),
    indicator_code NVARCHAR(100) NOT NULL,
    indicator_name NVARCHAR(500),
    [year] INT NOT NULL,
    [value] FLOAT NULL,
    unit NVARCHAR(100),
    obs_status NVARCHAR(50),
    decimal_places INT,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""