import requests
import pandas as pd
import sqlalchemy as sa
import xml.etree.ElementTree as ET
import settings as s

SCHEMA = "oecd"
TABLE = "dataflows"

URL = "https://sdmx.oecd.org/public/rest/v1/dataflow/all/all/latest"
HEADERS = {"Accept": "application/vnd.sdmx.structure+xml; charset=utf-8; version=2.1"}
engine = sa.create_engine(s.connection_string, fast_executemany=True)

def parse_dataflows(xml_text):
    root = ET.fromstring(xml_text)
    ns = {"str": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure", "com": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",}
    rows = []
    for dataflow in root.findall(".//str:Dataflow", ns):
        agency_id = dataflow.attrib.get("agencyID")
        dataflow_id = dataflow.attrib.get("id")
        dataflow_version = dataflow.attrib.get("version")
        dataflow_name = None
        for name_element in dataflow.findall("com:Name", ns):
            lang = name_element.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
            if lang == "en":
                dataflow_name = name_element.text
                break
            if dataflow_name is None: dataflow_name = name_element.text
        description_list = []
        for description_element in dataflow.findall("com:Description", ns):
            if description_element.text: description_list.append(description_element.text)
        description = " | ".join(description_list)
        rows.append({"agency_id": agency_id,"dataflow_id": dataflow_id,"dataflow_version": dataflow_version,"dataflow_name": dataflow_name,"description": description})
    return pd.DataFrame(rows)

def fetch_dataflows():
    response = requests.get(URL, headers=HEADERS, timeout=120)
    response.raise_for_status()
    return parse_dataflows(response.text)

def delete_old_data():
    with engine.begin() as conn: conn.execute(sa.text(f"""TRUNCATE TABLE {SCHEMA}.{TABLE}"""))

def insert_data(df):
    if df.empty:
        print("Nothing to insert")
        return
    df.to_sql(name=TABLE, schema=SCHEMA, con=engine, if_exists="append", index=False, chunksize=1000)

def main():
    print("Downloading OECD dataflows...")
    df = fetch_dataflows()
    print(f"Rows downloaded: {len(df):,}")
    print("Deleting old data...")
    delete_old_data()
    print("Inserting...")
    insert_data(df)
    print("Done")
    print(df.head())

if __name__ == "__main__": main()

"""
CREATE TABLE oecd.dataflows (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    agency_id NVARCHAR(100) NOT NULL,
    dataflow_id NVARCHAR(300) NOT NULL,
    dataflow_version NVARCHAR(50) NOT NULL,
    dataflow_name NVARCHAR(1000) NOT NULL,
    description NVARCHAR(MAX) NULL,
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
);
"""