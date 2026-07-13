import json
import time
from io import StringIO

import requests
import pandas as pd
import sqlalchemy as sa
import settings as s

SCHEMA = "oecd"
TABLE = "data"

DATAFLOWS = [
    "DSD_FUA_TRAN@DF_PT_ACCESS"
    ]

FIXED_DIMENSION_COLUMNS = [
    "REF_AREA",
    "UNIT_MEASURE",
    "MEASURE",
    "FREQ",
    "SECTOR",
    "SEX",
    "AGE",
    "ACTIVITY",
    "PRICE_BASE",
    "TRANSFORMATION",
    "STANDARD_REVENUE",
    "CTRY_SPECIFIC_REVENUE",
    "TRANSACTION",
    "ADJUSTMENT",
    "EDUCATION_LEV",
    "TABLE_IDENTIFIER",
    "INSTR_ASSET",
    "EXPENDITURE",
    "TERRITORIAL_LEVEL",
    "STATISTICAL_OPERATION",]

BASE_URL = "https://sdmx.oecd.org/public/rest/data"
REQUEST_TIMEOUT = 300
SQL_CHUNKSIZE = 5000
SLEEP_SECONDS = 1
engine = sa.create_engine(s.connection_string, fast_executemany=True)

def fetch_dataflow_metadata(dataflow_id):
    query = sa.text("""
        SELECT TOP 1 df.agency_id, df.dataflow_id, df.dataflow_name, ds.datastructure_id
        FROM oecd.dataflows df
        JOIN oecd.datastructures ds ON ds.agency_id = df.agency_id AND ds.dataflow_id = df.dataflow_id
        WHERE df.dataflow_id = :dataflow_id""")
    df = pd.read_sql(query, engine, params={"dataflow_id": dataflow_id})
    if df.empty: raise ValueError(f"Dataflow not found in metadata: {dataflow_id}")
    return df.iloc[0].to_dict()

def fetch_dimension_codelists(datastructure_id):
    query = sa.text("""
        SELECT dimension_id, codelist_agency_id, codelist_id
        FROM oecd.dimensions
        WHERE datastructure_id = :datastructure_id""")
    df = pd.read_sql(query, engine, params={"datastructure_id": datastructure_id})
    return {
        row["dimension_id"]: {"agency_id": row["codelist_agency_id"],"codelist_id": row["codelist_id"],}
        for _, row in df.iterrows()
        if pd.notna(row["dimension_id"])}

def fetch_dimension_codes_map(datastructure_id):
    query = sa.text("""
        SELECT d.dimension_id, dc.code, dc.code_name
        FROM oecd.dimensions d
        JOIN oecd.dimension_codes dc ON dc.agency_id = d.codelist_agency_id AND dc.codelist_id = d.codelist_id
        WHERE d.datastructure_id = :datastructure_id""")
    df = pd.read_sql(query, engine, params={"datastructure_id": datastructure_id})
    result = {}
    for _, row in df.iterrows():
        dimension_id = row["dimension_id"]
        code = row["code"]
        code_name = row["code_name"]
        if pd.isna(dimension_id) or pd.isna(code): continue
        result.setdefault(dimension_id, {})[str(code)] = code_name
    return result

def fetch_oecd_csv(agency_id, dataflow_id):
    url = f"{BASE_URL}/{agency_id},{dataflow_id}/all"
    params = {"format": "csvfilewithlabels"}
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    print("STATUS:", response.status_code)
    print("CONTENT-TYPE:", response.headers.get("Content-Type"))
    print("URL:", response.url)
    response.raise_for_status()
    return response.text

def safe_value(row, column):
    if column not in row.index: return None
    value = row.get(column)
    if pd.isna(value): return None
    return str(value)

def get_label(row, label_column):
    value = safe_value(row, label_column)
    return value

def get_code_name(dimension_codes_map, dimension_id, code):
    if code is None: return None
    return dimension_codes_map.get(dimension_id, {}).get(str(code))

def normalize_oecd_csv(csv_text, metadata, dimension_codes_map):
    dataflow_id = metadata["dataflow_id"]
    dataflow_name = metadata["dataflow_name"]
    datastructure_id = metadata["datastructure_id"]
    df_raw = pd.read_csv(StringIO(csv_text))
    print("Raw rows:", len(df_raw))
    print("Raw columns:")
    print(df_raw.columns.tolist())
    technical_columns = {"STRUCTURE","STRUCTURE_ID","STRUCTURE_NAME","ACTION","TIME_PERIOD","Time period","OBS_VALUE","Observation value"}
    fixed_set = set(FIXED_DIMENSION_COLUMNS)
    rows = []
    for _, row in df_raw.iterrows():
        obs_value = pd.to_numeric(row.get("OBS_VALUE"), errors="coerce")
        time_period = safe_value(row, "TIME_PERIOD")
        if time_period is None or pd.isna(obs_value): continue
        output = {
            "dataflow_id": dataflow_id,
            "dataflow_name": dataflow_name,
            "datastructure_id": datastructure_id,
            "structure_id": safe_value(row, "STRUCTURE_ID"),
            "structure_name": safe_value(row, "STRUCTURE_NAME"),
            "time_period": time_period,
            "obs_value": obs_value,}
        for col in FIXED_DIMENSION_COLUMNS: output[col] = safe_value(row, col)
        output["indicator_code"] = output.get("MEASURE")
        output["indicator_name"] = (get_label(row, "Measure") or get_code_name(dimension_codes_map, "MEASURE", output.get("MEASURE")))
        output["unit_code"] = output.get("UNIT_MEASURE")
        output["unit_name"] = (get_label(row, "Unit of measure") or get_code_name(dimension_codes_map, "UNIT_MEASURE", output.get("UNIT_MEASURE")))
        output["ref_area_name"] = (get_label(row, "Reference area") or get_code_name(dimension_codes_map, "REF_AREA", output.get("REF_AREA")))
        output["freq_name"] = (get_label(row, "Frequency of observation") or get_code_name(dimension_codes_map, "FREQ", output.get("FREQ")))
        output["sex_name"] = (get_label(row, "Sex") or get_code_name(dimension_codes_map, "SEX", output.get("SEX")))
        output["age_name"] = (get_label(row, "Age") or get_code_name(dimension_codes_map, "AGE", output.get("AGE")))
        output["sector_name"] = (get_label(row, "Institutional sector") or get_label(row, "Sector") or get_code_name(dimension_codes_map, "SECTOR", output.get("SECTOR")))
        output["activity_name"] = (get_label(row, "Economic activity") or get_label(row, "Activity") or get_code_name(dimension_codes_map, "ACTIVITY", output.get("ACTIVITY")))
        output["price_base_name"] = (get_label(row, "Price base") or get_code_name(dimension_codes_map, "PRICE_BASE", output.get("PRICE_BASE")))
        output["transformation_name"] = (get_label(row, "Transformation") or get_code_name(dimension_codes_map, "TRANSFORMATION", output.get("TRANSFORMATION")))
        extra_dimensions = {}
        for col in df_raw.columns:
            if col in technical_columns: continue
            if col in fixed_set: continue
            if not (col.isupper() or "_" in col): continue
            value = safe_value(row, col)
            if value is not None: extra_dimensions[col] = value
        attributes = {}
        for col in df_raw.columns:
            if col in technical_columns: continue
            if col in fixed_set: continue
            if col in extra_dimensions: continue
            value = safe_value(row, col)
            if value is not None: attributes[col] = value
        output["dimensions_json"] = (json.dumps(extra_dimensions, ensure_ascii=False) if extra_dimensions else None)
        output["attributes_json"] = (json.dumps(attributes, ensure_ascii=False) if attributes else None)
        rows.append(output)
    df = pd.DataFrame(rows)
    return df

def delete_old_data(dataflow_id):
    with engine.begin() as conn: conn.execute(sa.text(f"""DELETE FROM {SCHEMA}.{TABLE} WHERE dataflow_id = :dataflow_id"""),{"dataflow_id": dataflow_id})

def insert_data(df):
    if df.empty:
        print("Nothing to insert")
        return 0
    df.to_sql(name=TABLE,schema=SCHEMA,con=engine,if_exists="append",index=False,chunksize=SQL_CHUNKSIZE)
    return len(df)

def process_dataflow(dataflow_id):
    print("\n" + "=" * 90)
    print(f"Processing dataflow: {dataflow_id}")
    print("=" * 90)
    metadata = fetch_dataflow_metadata(dataflow_id)
    print(f"Agency: {metadata['agency_id']} | Dataflow: {metadata['dataflow_id']} | DSD: {metadata['datastructure_id']}")
    dimension_codes_map = fetch_dimension_codes_map(datastructure_id=metadata["datastructure_id"])
    csv_text = fetch_oecd_csv(agency_id=metadata["agency_id"],dataflow_id=metadata["dataflow_id"])
    df = normalize_oecd_csv(csv_text=csv_text,metadata=metadata,dimension_codes_map=dimension_codes_map)
    print(f"Rows normalized: {len(df):,}")
    print(df.head().to_string(index=False))
    print("Deleting old data for this dataflow...")
    delete_old_data(dataflow_id)
    print("Inserting...")
    inserted = insert_data(df)
    print(f"Inserted: {inserted:,}")
    return inserted

def main():
    total_inserted, errors = 0, []
    for dataflow_id in DATAFLOWS:
        try:
            inserted = process_dataflow(dataflow_id)
            total_inserted += inserted
            time.sleep(SLEEP_SECONDS)
        except Exception as e:
            error = {"dataflow_id": dataflow_id, "error": str(e)}
            errors.append(error)
            print("ERROR:", error)
    print("\nDONE")
    print(f"Total inserted: {total_inserted:,}")
    print(f"Errors: {len(errors)}")
    if errors:
        print("\nERROR SAMPLE:")
        for error in errors[:20]: print(error)
if __name__ == "__main__": main()



"""
CREATE TABLE oecd.[data] (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    dataflow_id NVARCHAR(300) NOT NULL,
    dataflow_name NVARCHAR(1000) NULL,
    datastructure_id NVARCHAR(500) NULL,
    structure_id NVARCHAR(500) NULL,
    structure_name NVARCHAR(1000) NULL,
    time_period NVARCHAR(50) NOT NULL,
    obs_value FLOAT NULL,
    REF_AREA NVARCHAR(500) NULL,
    UNIT_MEASURE NVARCHAR(500) NULL,
    MEASURE NVARCHAR(500) NULL,
    FREQ NVARCHAR(500) NULL,
    SECTOR NVARCHAR(500) NULL,
    SEX NVARCHAR(500) NULL,
    AGE NVARCHAR(500) NULL,
    ACTIVITY NVARCHAR(500) NULL,
    PRICE_BASE NVARCHAR(500) NULL,
    TRANSFORMATION NVARCHAR(500) NULL,
    STANDARD_REVENUE NVARCHAR(500) NULL,
    CTRY_SPECIFIC_REVENUE NVARCHAR(500) NULL,
    [TRANSACTION] NVARCHAR(500) NULL,
    ADJUSTMENT NVARCHAR(500) NULL,
    EDUCATION_LEV NVARCHAR(500) NULL,
    TABLE_IDENTIFIER NVARCHAR(500) NULL,
    INSTR_ASSET NVARCHAR(500) NULL,
    EXPENDITURE NVARCHAR(500) NULL,
    TERRITORIAL_LEVEL NVARCHAR(500) NULL,
    STATISTICAL_OPERATION NVARCHAR(500) NULL,
    indicator_code NVARCHAR(500) NULL,
    indicator_name NVARCHAR(2000) NULL,
    unit_code NVARCHAR(500) NULL,
    unit_name NVARCHAR(2000) NULL,
    ref_area_name NVARCHAR(2000) NULL,
    freq_name NVARCHAR(1000) NULL,
    sex_name NVARCHAR(1000) NULL,
    age_name NVARCHAR(1000) NULL,
    sector_name NVARCHAR(2000) NULL,
    activity_name NVARCHAR(2000) NULL,
    price_base_name NVARCHAR(1000) NULL,
    transformation_name NVARCHAR(1000) NULL,
    dimensions_json NVARCHAR(MAX) NULL,
    attributes_json NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);


CREATE INDEX ix_oecd_data_dataflow_time
ON oecd.data (dataflow_id, time_period);

CREATE INDEX ix_oecd_data_measure
ON oecd.data (MEASURE, UNIT_MEASURE, REF_AREA, time_period);

CREATE INDEX ix_oecd_data_ref_area
ON oecd.data (REF_AREA, time_period);
"""