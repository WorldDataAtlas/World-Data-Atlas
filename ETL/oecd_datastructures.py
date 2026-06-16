import requests
import pandas as pd
import sqlalchemy as sa
import xml.etree.ElementTree as ET
import settings as s

SCHEMA = "oecd"
TABLE = "datastructures"
URL = "https://sdmx.oecd.org/public/rest/v1/dataflow/all/all/latest"
HEADERS = {"Accept": "application/vnd.sdmx.structure+xml; charset=utf-8; version=2.1"}
engine = sa.create_engine(s.connection_string,fast_executemany=True)

def parse_datastructures(xml_text):
    root = ET.fromstring(xml_text)
    ns = {"str": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"}
    rows = []
    for dataflow in root.findall(".//str:Dataflow", ns):
        dataflow_agency_id = dataflow.attrib.get("agencyID")
        dataflow_id = dataflow.attrib.get("id")
        dataflow_version = dataflow.attrib.get("version")
        structure_ref = dataflow.find(".//str:Structure/*", ns)
        if structure_ref is not None:
            datastructure_agency_id = (structure_ref.attrib.get("agencyID") or dataflow_agency_id)
            datastructure_id = structure_ref.attrib.get("id")
            datastructure_version = structure_ref.attrib.get("version")
            source_method = "structure_ref"
        elif "@" in dataflow_id:
            datastructure_agency_id = dataflow_agency_id
            datastructure_id = dataflow_id.split("@")[0]
            datastructure_version = dataflow_version
            source_method = "parsed_from_dataflow_id"
        else:
            print(f"NO STRUCTURE FOUND | {dataflow_agency_id} | {dataflow_id}")
            continue
        rows.append({
            "agency_id": datastructure_agency_id,
            "dataflow_id": dataflow_id,
            "datastructure_id": datastructure_id,
            "datastructure_version": datastructure_version,
            "source_method": source_method})
    df = pd.DataFrame(rows)
    if not df.empty: df = df.drop_duplicates(subset=["agency_id","dataflow_id","datastructure_id","datastructure_version"]).reset_index(drop=True)
    return df

def fetch_datastructures():
    response = requests.get(URL,headers=HEADERS,timeout=120)
    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    response.raise_for_status()
    return parse_datastructures(response.text)

def delete_old_data():
    with engine.begin() as conn: conn.execute(sa.text(f"TRUNCATE TABLE {SCHEMA}.{TABLE}"))

def insert_data(df):
    if df.empty:
        print("Nothing to insert")
        return
    df.to_sql(name=TABLE,schema=SCHEMA,con=engine,if_exists="append",index=False,chunksize=1000)

def main():
    print("Downloading OECD datastructure references...")
    df = fetch_datastructures()
    print(f"Rows parsed: {len(df):,}")
    print(df["source_method"].value_counts())
    print(df.head(30).to_string(index=False))
    print("Deleting old data...")
    delete_old_data()
    print("Inserting data...")
    insert_data(df)
    print("DONE")
if __name__ == "__main__": main()

"""
CREATE TABLE oecd.datastructures (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    agency_id NVARCHAR(100),
    dataflow_id NVARCHAR(300),
    datastructure_id NVARCHAR(300),
    datastructure_version NVARCHAR(50),
    source_method NVARCHAR(100),
    [is_dimension_loaded] [bit] NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""