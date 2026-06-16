import time
import requests
import pandas as pd
import sqlalchemy as sa
import xml.etree.ElementTree as ET
import settings as s

SCHEMA = "oecd"
SOURCE_TABLE = "dimensions"
TARGET_TABLE = "dimension_codes"
BASE_URL = "https://sdmx.oecd.org/public/rest/v1/codelist"
HEADERS = {"Accept": "application/vnd.sdmx.structure+xml; charset=utf-8; version=2.1"}
REQUEST_TIMEOUT = 150
MAX_RETRIES = 5
SLEEP_SECONDS = 0.1
SQL_CHUNKSIZE = 5000

engine = sa.create_engine(s.connection_string,fast_executemany=True)

def fetch_codelists_from_sql():
    query = f"""
        SELECT DISTINCT codelist_agency_id AS agency_id, codelist_id, codelist_version
        FROM {SCHEMA}.{SOURCE_TABLE}
        WHERE codelist_id IS NOT NULL AND codelist_agency_id IS NOT NULL
        ORDER BY codelist_agency_id, codelist_id, codelist_version"""
    return pd.read_sql(query, engine)

def fetch_codelist_xml(agency_id, codelist_id):
    url = f"{BASE_URL}/{agency_id}/{codelist_id}/latest"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url,headers=HEADERS,timeout=REQUEST_TIMEOUT)
            if response.status_code in [429, 500, 502, 503, 504]:
                wait = attempt
                print(f"{response.status_code} retry {attempt}/{MAX_RETRIES} | {agency_id} | {codelist_id} | waiting {wait}s")
                time.sleep(wait)
                continue
            if response.status_code == 404:
                print(f"404 skip | {agency_id} | {codelist_id}")
                return None
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            wait = attempt
            print(f"REQUEST ERROR retry {attempt}/{MAX_RETRIES} | {agency_id} | {codelist_id} | {e}")
            time.sleep(wait)
    print(f"FAILED | {agency_id} | {codelist_id}")
    return None

def get_english_name(element, ns):
    name = None
    for name_el in element.findall("com:Name", ns):
        lang = name_el.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
        if lang == "en": return name_el.text
        if name is None: name = name_el.text
    return name

def get_parent_code(code_element, ns):
    parent_ref = code_element.find(".//str:Parent/*", ns)
    if parent_ref is not None: return parent_ref.attrib.get("id")
    return None

def parse_codelist(xml_text, fallback_agency_id, fallback_codelist_id):
    if not xml_text: return pd.DataFrame()
    root = ET.fromstring(xml_text)
    ns = {"str": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure","com": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"}
    codelist = root.find(".//str:Codelist", ns)
    if codelist is None: return pd.DataFrame()
    agency_id = codelist.attrib.get("agencyID") or fallback_agency_id
    codelist_id = codelist.attrib.get("id") or fallback_codelist_id
    codelist_version = codelist.attrib.get("version")
    rows = []
    for code in codelist.findall("str:Code", ns):
        code_id = code.attrib.get("id")
        code_name = get_english_name(code, ns)
        parent_code = get_parent_code(code, ns)
        rows.append({
            "agency_id": agency_id,
            "codelist_id": codelist_id,
            "codelist_version": codelist_version,
            "code": code_id,
            "code_name": code_name,
            "parent_code": parent_code})
    df = pd.DataFrame(rows)
    return df

def delete_old_data():
    with engine.begin() as conn: conn.execute(sa.text(f"TRUNCATE TABLE {SCHEMA}.{TARGET_TABLE}"))

def insert_batch(df):
    if df.empty: return 0
    df.to_sql(name=TARGET_TABLE,schema=SCHEMA,con=engine,if_exists="append",index=False,chunksize=SQL_CHUNKSIZE)
    return len(df)

def main():
    codelists = fetch_codelists_from_sql()
    print(f"Codelists to process: {len(codelists):,}")
    delete_old_data()
    print("Old dimension codes deleted.")
    total_inserted, errors = 0, []
    for i, row in codelists.iterrows():
        agency_id = row["agency_id"]
        codelist_id = row["codelist_id"]
        print(f"{i + 1}/{len(codelists)} | {agency_id} | {codelist_id}")
        try:
            xml_text = fetch_codelist_xml(agency_id=agency_id,codelist_id=codelist_id)
            if xml_text is None: continue
            df_codes = parse_codelist(xml_text=xml_text,fallback_agency_id=agency_id,fallback_codelist_id=codelist_id)
            if df_codes.empty:
                print("No codes parsed.")
                continue
            df_codes = df_codes.drop_duplicates(subset=["agency_id","codelist_id","codelist_version","code"]).reset_index(drop=True)
            inserted = insert_batch(df_codes)
            total_inserted += inserted
            time.sleep(SLEEP_SECONDS)
        except Exception as e:
            error = {"agency_id": agency_id,"codelist_id": codelist_id,"error": str(e)}
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
CREATE TABLE oecd.dimension_codes (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    agency_id NVARCHAR(100) NOT NULL,
    codelist_id NVARCHAR(300) NOT NULL,
    codelist_version NVARCHAR(50) NULL,
    code NVARCHAR(300) NOT NULL,
    code_name NVARCHAR(2000) NULL,
    parent_code NVARCHAR(300) NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""