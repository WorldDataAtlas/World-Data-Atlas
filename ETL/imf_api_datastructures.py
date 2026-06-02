import requests
import pandas as pd
import sqlalchemy as sa
import settings as s

BASE_URL = "https://api.imf.org/external/sdmx/2.1"
URL = f"{BASE_URL}/datastructure/all/all/latest"
SCHEMA = "imf"
TABLE = "api_datastructures"
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

payload = fetch_json(URL)
data_structures = (payload.get("data", {}).get("dataStructures", []))
rows = []
for structure in data_structures:
    structure_id = structure.get("id")
    structure_name = structure.get("name")
    agency_id = structure.get("agencyID")
    version = structure.get("version")
    components = structure.get("dataStructureComponents", {})
    dimension_list = components.get("dimensionList", {})
    dimensions = dimension_list.get("dimensions", [])
    time_dimensions = dimension_list.get("timeDimensions", [])
    for dimension in dimensions:
        local_representation = dimension.get("localRepresentation", {})
        enumeration_urn = None
        if isinstance(local_representation, dict): enumeration_urn = local_representation.get("enumeration")
        rows.append({
            "structure_id": structure_id,
            "structure_name": structure_name,
            "agency_id": agency_id,
            "version": version,
            "dimension_id": dimension.get("id"),
            "dimension_position": dimension.get("position"),
            "dimension_type": dimension.get("type"),
            "enumeration_urn": enumeration_urn,
            "concept_identity": dimension.get("conceptIdentity")})
    for dimension in time_dimensions:
        local_representation = dimension.get("localRepresentation", {})
        enumeration_urn = None
        if isinstance(local_representation, dict): enumeration_urn = local_representation.get("enumeration")
        rows.append({
            "structure_id": structure_id,
            "structure_name": structure_name,
            "agency_id": agency_id,
            "version": version,
            "dimension_id": dimension.get("id"),
            "dimension_position": dimension.get("position"),
            "dimension_type": dimension.get("type"),
            "enumeration_urn": enumeration_urn,
            "concept_identity": dimension.get("conceptIdentity")})
df = pd.DataFrame(rows)
df = (df.drop_duplicates(subset=["structure_id", "version", "dimension_id"]).reset_index(drop=True))
print("Structures:", df["structure_id"].nunique())
print("Rows:", len(df))
engine = sa.create_engine(s.connection_string, fast_executemany=True)
with engine.begin() as conn: conn.execute(sa.text(f"TRUNCATE TABLE {SCHEMA}.{TABLE}"))
df.to_sql(name=TABLE, schema=SCHEMA, con=engine, if_exists="append", index=False, chunksize=5000)
print(f"Inserted rows: {len(df)}")
print("DONE")

"""
CREATE TABLE imf.api_datastructures (
    structure_id NVARCHAR(200),
    structure_name NVARCHAR(MAX),
    agency_id NVARCHAR(100),
    [version] NVARCHAR(50),
    dimension_id NVARCHAR(200),
    dimension_position INT,
    dimension_type NVARCHAR(50),
    enumeration_urn NVARCHAR(MAX) NULL,
    concept_identity NVARCHAR(MAX),
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""