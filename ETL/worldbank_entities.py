import requests
import pandas as pd
import sqlalchemy as sa
import settings as s

url = "https://api.worldbank.org/v2/country"
params = {"format": "json", "per_page": 1000}
response = requests.get(url, params=params, timeout=60)
response.raise_for_status()
data = response.json()[1]
rows = []

for item in data:
    region = item.get("region", {})
    admin_region = item.get("adminregion", {})
    income_level = item.get("incomeLevel", {})
    lending_type = item.get("lendingType", {})
    region_id = region.get("id")
    region_name = region.get("value")
    is_aggregate = region_name == "Aggregates"

    rows.append({
        "wb_id": item.get("id"),
        "iso2_code": item.get("iso2Code"),
        "name": item.get("name"),
        "region_id": region_id,
        "region_name": region_name,
        "admin_region_id": admin_region.get("id"),
        "admin_region_name": admin_region.get("value"),
        "income_level_id": income_level.get("id"),
        "income_level_name": income_level.get("value"),
        "lending_type_id": lending_type.get("id"),
        "lending_type_name": lending_type.get("value"),
        "capital_city": item.get("capitalCity"),
        "longitude": item.get("longitude"),
        "latitude": item.get("latitude"),
        "is_country": not is_aggregate,
        "is_region_or_aggregate": is_aggregate})

df_entities = pd.DataFrame(rows)
df_entities["longitude"] = pd.to_numeric(df_entities["longitude"], errors="coerce")
df_entities["latitude"] = pd.to_numeric(df_entities["latitude"], errors="coerce")
df_regions = (df_entities[["region_id", "region_name"]].dropna().drop_duplicates().sort_values("region_id").reset_index(drop=True))

engine = sa.create_engine(s.connection_string, fast_executemany=True)

with engine.begin() as conn:
    conn.execute(sa.text("TRUNCATE TABLE worldbank.entities"))
    conn.execute(sa.text("TRUNCATE TABLE worldbank.regions"))

df_entities.to_sql(name="entities", schema="worldbank", con=engine, if_exists="append", index=False, chunksize=500)
df_regions.to_sql(name="regions", schema="worldbank", con=engine, if_exists="append", index=False, chunksize=500)

"""
CREATE TABLE [worldbank].[entities](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[wb_id] [nvarchar](3) NOT NULL,
	[iso2_code] [nvarchar](2) NULL,
	[name] [nvarchar](255) NOT NULL,
	[region_id] [nvarchar](10) NULL,
	[region_name] [nvarchar](255) NULL,
	[admin_region_id] [nvarchar](10) NULL,
	[admin_region_name] [nvarchar](255) NULL,
	[income_level_id] [nvarchar](10) NULL,
	[income_level_name] [nvarchar](255) NULL,
	[lending_type_id] [nvarchar](10) NULL,
	[lending_type_name] [nvarchar](255) NULL,
	[capital_city] [nvarchar](255) NULL,
	[longitude] [float] NULL,
	[latitude] [float] NULL,
	[is_country] [bit] NOT NULL,
	[is_region_or_aggregate] [bit] NOT NULL,
	[created_at] [datetime2](7) NOT NULL)
 
CREATE TABLE [worldbank].[regions](
	[region_id] [nvarchar](10) NOT NULL,
	[region_name] [nvarchar](255) NOT NULL)
"""