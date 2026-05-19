import pandas as pd
import requests
import json
import time
import sqlalchemy as sa
import settings as s

def to_json(value):
    if value is None: return None
    return json.dumps(value, ensure_ascii=False)

def fetch_country_data(country_name):
    url = f"https://restcountries.com/v3.1/name/{country_name}"
    response = requests.get(url=url, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data[0]

rows, new_rows = [], []

#Get list of all countries
url = "https://restcountries.com/v3.1/all?fields=name"
response = requests.get(url)
response.raise_for_status()
data = response.json()
for item in data:
    name_data = item["name"]
    native = []
    for lang_data in name_data.get("nativeName", {}).values():
        native.append(lang_data.get("common"))
        native.append(lang_data.get("official"))
    native = list(set(filter(None, native)))
    rows.append({"common_name": name_data.get("common"), "official_name": name_data.get("official"), "native_names": ", ".join(native) if native else None})
df = pd.DataFrame(rows)

#Get details to the all countries
for _, row in df.iterrows():
    country_name = row["common_name"]
    try:
        country = fetch_country_data(country_name)
        new_rows.append({
            **row.to_dict(),
            "cca2": country.get("cca2"),
            "cca3": country.get("cca3"),
            "ccn3": country.get("ccn3"),
            "cioc": country.get("cioc"),
            "independent": country.get("independent"),
            "status": country.get("status"),
            "un_member": country.get("unMember"),
            "region": country.get("region"),
            "subregion": country.get("subregion"),
            "continents": to_json(country.get("continents")),
            "landlocked": country.get("landlocked"),
            "area_km2": country.get("area"),
            "population": country.get("population"),
            "capital": to_json(country.get("capital")),
            "latlng": to_json(country.get("latlng")),
            "capital_info": to_json(country.get("capitalInfo")),
            "tld": to_json(country.get("tld")),
            "idd": to_json(country.get("idd")),
            "timezones": to_json(country.get("timezones")),
            "borders": to_json(country.get("borders")),
            "currencies": to_json(country.get("currencies")),
            "languages": to_json(country.get("languages")),
            "gini": to_json(country.get("gini")),
            "start_of_week": country.get("startOfWeek"),
        })
        time.sleep(0.1)
    except Exception as e:
        print(f"Error for {country_name}: {e}")
        new_rows.append({**row.to_dict(), "error": str(e)})
df_enriched = pd.DataFrame(new_rows)

engine = sa.create_engine(s.connection_string)
with engine.begin() as conn: conn.execute(sa.text("TRUNCATE TABLE restcountries.countries"))
df_enriched.to_sql(name="countries", schema="restcountries", con=engine, if_exists="append", index=False, chunksize=20, method="multi")


"""
CREATE TABLE restcountries.countries (
    id INT IDENTITY(1,1) PRIMARY KEY,
    cca2 NVARCHAR(10),
    cca3 NVARCHAR(10),
    ccn3 NVARCHAR(10),
    cioc NVARCHAR(10),
    common_name NVARCHAR(1500) NOT NULL,
    official_name NVARCHAR(1500),
    native_names NVARCHAR(MAX),
    independent BIT,
    [status] NVARCHAR(500),
    un_member BIT,
    region NVARCHAR(500),
    subregion NVARCHAR(500),
    continents NVARCHAR(MAX),
    landlocked BIT,
    area_km2 FLOAT,
    latlng NVARCHAR(MAX),
    borders NVARCHAR(MAX),
    [population] BIGINT,
    gini NVARCHAR(MAX),
    capital NVARCHAR(MAX),
    capital_info NVARCHAR(MAX),
    tld NVARCHAR(MAX),
    idd NVARCHAR(MAX),
    timezones NVARCHAR(MAX),
    currencies NVARCHAR(MAX),
    languages NVARCHAR(MAX),
    start_of_week NVARCHAR(500),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
"""