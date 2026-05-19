import requests
import pandas as pd
import sqlalchemy as sa
import settings as s

query = """
SELECT ?languageLabel ?iso6391
       (SAMPLE(?iso6393_value) AS ?iso6393)
       (MAX(?speakers_value) AS ?speakers)
WHERE {
  ?language wdt:P218 ?iso6391.
  OPTIONAL { ?language wdt:P220 ?iso6393_value. }
  OPTIONAL { ?language wdt:P1098 ?speakers_value. }
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en".
  }
}
GROUP BY ?language ?languageLabel ?iso6391
"""

url = "https://query.wikidata.org/sparql"
headers = {"Accept": "application/sparql-results+json", "User-Agent": "WorldDataAtlas/1.0 (" + s.mail + ")"}
response = requests.get(url, params={"query": query}, headers=headers, timeout=60)
response.raise_for_status()
data = response.json()["results"]["bindings"]
rows = []

for item in data:
    rows.append({
        "language_name": item.get("languageLabel", {}).get("value"),
        "iso639_1": item.get("iso6391", {}).get("value"),
        "iso639_3": item.get("iso6393", {}).get("value"),
        "speakers": item.get("speakers", {}).get("value"),
    })
df = pd.DataFrame(rows)

df = df[~((df["language_name"] == "Latin") & (df["iso639_1"] == "la") & (df["iso639_3"] == "lat"))]
engine = sa.create_engine(s.connection_string, fast_executemany=True)
with engine.begin() as conn: conn.execute(sa.text("TRUNCATE TABLE wiki.languages"))
df.to_sql(name="languages", schema="wiki", con=engine, if_exists="append", index=False, chunksize=25)

"""
CREATE TABLE wiki.languages (
    id INT IDENTITY(1,1) PRIMARY KEY,
    language_name NVARCHAR(MAX) NOT NULL,
    iso639_1 NVARCHAR(200),
    iso639_3 NVARCHAR(200),
    speakers BIGINT,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
"""