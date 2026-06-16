import time
import requests
import pandas as pd
import sqlalchemy as sa
import xml.etree.ElementTree as ET
import settings as s

SCHEMA = "oecd"
SOURCE_TABLE = "datastructures"
TARGET_TABLE = "dimensions"
BASE_URL = "https://sdmx.oecd.org/public/rest/v1/datastructure"
HEADERS = {"Accept": "application/vnd.sdmx.structure+xml; charset=utf-8; version=2.1"}
REQUEST_TIMEOUT = 120
MAX_RETRIES = 5
SLEEP_SECONDS = 0.15
SQL_CHUNKSIZE = 1000
engine = sa.create_engine(s.connection_string, fast_executemany=True)

def fetch_datastructures_from_sql():
    query = f"""
        SELECT DISTINCT agency_id, datastructure_id
        FROM {SCHEMA}.{SOURCE_TABLE}
        WHERE agency_id IS NOT NULL AND datastructure_id IS NOT NULL
        ORDER BY agency_id, datastructure_id"""
    return pd.read_sql(query, engine)

def fetch_datastructure_xml(agency_id, datastructure_id):
    url = f"{BASE_URL}/{agency_id}/{datastructure_id}/latest"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url,headers=HEADERS,timeout=REQUEST_TIMEOUT)
            if response.status_code in [429, 500, 502, 503, 504]:
                wait = attempt * 2
                print(f"{response.status_code} retry {attempt}/{MAX_RETRIES} | {agency_id} | {datastructure_id} | waiting {wait}s")
                time.sleep(wait)
                continue
            if response.status_code == 404:
                print(f"404 skip | {agency_id} | {datastructure_id}")
                return None
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            wait = attempt * 2
            print(f"REQUEST ERROR retry {attempt}/{MAX_RETRIES} | {agency_id} | {datastructure_id} | {e}")
            time.sleep(wait)
    print(f"FAILED | {agency_id} | {datastructure_id}")
    return None

def parse_dimensions(xml_text, agency_id, datastructure_id):
    if not xml_text: return pd.DataFrame()
    root = ET.fromstring(xml_text)
    ns = {"str": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure","com": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"}
    data_structure = root.find(".//str:DataStructure", ns)
    if data_structure is None: return pd.DataFrame()
    datastructure_version = data_structure.attrib.get("version")
    rows = []
    dimensions = data_structure.findall(".//str:DimensionList/str:Dimension",ns)
    for dimension in dimensions:
        dimension_id = dimension.attrib.get("id")
        dimension_position = dimension.attrib.get("position")
        concept_ref = dimension.find(".//str:ConceptIdentity/*", ns)
        codelist_ref = dimension.find(".//str:LocalRepresentation/str:Enumeration/*",ns)
        row = {
            "agency_id": agency_id,
            "datastructure_id": datastructure_id,
            "datastructure_version": datastructure_version,
            "dimension_position": dimension_position,
            "dimension_id": dimension_id,
            "concept_id": None,
            "concept_scheme_id": None,
            "concept_scheme_version": None,
            "concept_agency_id": None,
            "codelist_id": None,
            "codelist_version": None,
            "codelist_agency_id": None,}
        if concept_ref is not None:
            row["concept_id"] = concept_ref.attrib.get("id")
            row["concept_scheme_id"] = concept_ref.attrib.get("maintainableParentID")
            row["concept_scheme_version"] = concept_ref.attrib.get("maintainableParentVersion")
            row["concept_agency_id"] = concept_ref.attrib.get("agencyID")
        if codelist_ref is not None:
            row["codelist_id"] = codelist_ref.attrib.get("id")
            row["codelist_version"] = codelist_ref.attrib.get("version")
            row["codelist_agency_id"] = codelist_ref.attrib.get("agencyID")
        rows.append(row)
    df = pd.DataFrame(rows)
    if not df.empty: df["dimension_position"] = pd.to_numeric(df["dimension_position"],errors="coerce").astype("Int64")
    return df

def delete_old_data():
    with engine.begin() as conn: conn.execute(sa.text(f"TRUNCATE TABLE {SCHEMA}.{TARGET_TABLE}"))

def insert_batch(df):
    if df.empty: return 0
    df.to_sql(name=TARGET_TABLE,schema=SCHEMA,con=engine,if_exists="append",index=False,chunksize=SQL_CHUNKSIZE)
    return len(df)

def main():
    datastructures = fetch_datastructures_from_sql()
    print(f"Datastructures to process: {len(datastructures):,}")
    delete_old_data()
    print("Old dimensions deleted.")
    total_inserted = 0
    errors = []
    for i, row in datastructures.iterrows():
        agency_id = row["agency_id"]
        datastructure_id = row["datastructure_id"]
        print(f"{i + 1}/{len(datastructures)} | {agency_id} | {datastructure_id}")
        try:
            xml_text = fetch_datastructure_xml(agency_id=agency_id,datastructure_id=datastructure_id)
            if xml_text is None: continue
            df_dimensions = parse_dimensions(xml_text=xml_text,agency_id=agency_id,datastructure_id=datastructure_id)
            if df_dimensions.empty:
                print("No dimensions parsed.")
                continue
            inserted = insert_batch(df_dimensions)
            total_inserted += inserted
            time.sleep(SLEEP_SECONDS)
        except Exception as e:
            error = {"agency_id": agency_id,"datastructure_id": datastructure_id,"error": str(e)}
            errors.append(error)
            print(f"ERROR: {error}")
    print("\nDONE")
    print(f"Total inserted: {total_inserted:,}")
    print(f"Errors: {len(errors)}")
    if errors:
        print("\nERROR SAMPLE:")
        for error in errors[:20]: print(error)
if __name__ == "__main__": main()

"""
CREATE TABLE oecd.dimensions (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    agency_id NVARCHAR(100) NOT NULL,
    datastructure_id NVARCHAR(300) NOT NULL,
    datastructure_version NVARCHAR(50) NULL,
    dimension_position INT NULL,
    dimension_id NVARCHAR(200) NOT NULL,
    concept_id NVARCHAR(200) NULL,
    concept_scheme_id NVARCHAR(300) NULL,
    concept_scheme_version NVARCHAR(50) NULL,
    concept_agency_id NVARCHAR(100) NULL,
    codelist_id NVARCHAR(300) NULL,
    codelist_version NVARCHAR(50) NULL,
    codelist_agency_id NVARCHAR(100) NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""