import requests
import pandas as pd
import sqlalchemy as sa
import settings as s
import json
import re
import xml.etree.ElementTree as ET

BASE_URL = "https://api.imf.org/external/sdmx/2.1"

DATAFLOW_ID = "WEO"
FILTERS = {"INDICATOR": "GS_ED"}

START_PERIOD = "1900"
END_PERIOD = "2035"

SCHEMA = "imf"
TABLE = "data"
REQUEST_TIMEOUT = 300
HEADERS = {}

def parse_structure_urn(urn):
    match = re.search(r"DataStructure=([^:]+):([^(]+)\(([^)]+)\)", urn or "")
    if not match: return None
    return {"agency_id": match.group(1), "structure_id": match.group(2), "version": match.group(3)}

def get_dataflow(engine):
    sql = """
    SELECT *
    FROM imf.api_dataflows
    WHERE dataflow_id = :dataflow_id
    """
    df = pd.read_sql(sa.text(sql), engine, params={"dataflow_id": DATAFLOW_ID})
    if df.empty: raise Exception(f"Dataflow not found: {DATAFLOW_ID}")
    return df.iloc[0].to_dict()

def get_dimensions(engine, structure):
    sql = """
    SELECT *
    FROM imf.api_datastructures
    WHERE structure_id = :structure_id AND agency_id = :agency_id AND version = :version ORDER BY dimension_position
    """
    return pd.read_sql(sa.text(sql), engine, params={"structure_id": structure["structure_id"], "agency_id": structure["agency_id"], "version": structure["version"]})

def build_key(dimensions_df):
    parts = []
    for _, row in dimensions_df.iterrows():
        if row["dimension_type"] == "TimeDimension": continue
        dimension_id = row["dimension_id"]
        parts.append(FILTERS.get(dimension_id, ""))
    return ".".join(parts)

def build_url(flow, key):
    return (
        f"{BASE_URL}/data/"
        f"{flow['dataflow_agency_id']},{flow['dataflow_id']},{flow['dataflow_version']}/"
        f"{key}"
        f"?startPeriod={START_PERIOD}&endPeriod={END_PERIOD}")

def fetch_xml(url):
    print("URL:", url)
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print("First 500 chars:")
    print(response.text[:500])
    response.raise_for_status()
    if not response.text.strip().startswith("<?xml"): raise Exception("Response is not XML.")
    return response.text

def strip_namespace(tag):
    if "}" in tag: return tag.split("}", 1)[1]
    return tag

def parse_year(time_period):
    try: return int(str(time_period)[:4])
    except Exception: return None

def parse_float(value_raw):
    try: return float(value_raw) if value_raw not in [None, ""] else None
    except Exception: return None

def parse_sdmx_xml(xml_text, flow, dimensions_df, source_url):
    root = ET.fromstring(xml_text)
    dimension_ids = [row["dimension_id"] for _, row in dimensions_df.iterrows() if row["dimension_type"] != "TimeDimension"]
    series_count, obs_count, rows = 0, 0, []
    for elem in root.iter():
        if strip_namespace(elem.tag) != "Series": continue
        series_count += 1
        series_attrs = dict(elem.attrib)
        dim_values = {dim: series_attrs.get(dim) for dim in dimension_ids if dim in series_attrs}
        for obs in list(elem):
            if strip_namespace(obs.tag) != "Obs": continue
            obs_count += 1
            obs_attrs = dict(obs.attrib)
            time_period = obs_attrs.get("TIME_PERIOD") or obs_attrs.get("TIME")
            value = parse_float(obs_attrs.get("OBS_VALUE"))
            row = {
                "dataflow_id": flow["dataflow_id"],
                "dataflow_agency_id": flow["dataflow_agency_id"],
                "dataflow_version": flow["dataflow_version"],
                "series_key": ".".join([dim_values.get(dim, "") or "" for dim in dimension_ids]),
                "time_period": time_period,
                "year": parse_year(time_period),
                "value": value,
                "attributes_json": json.dumps(obs_attrs, ensure_ascii=False)}
            for dim_id, dim_value in dim_values.items(): row[dim_id.lower()] = dim_value
            rows.append(row)
    print("Series found:", series_count)
    print("Observations found:", obs_count)
    return pd.DataFrame(rows)

def delete_existing_rows(engine, flow):
    sql = """
    DELETE FROM imf.data
    WHERE dataflow_id = :dataflow_id
      AND dataflow_agency_id = :dataflow_agency_id
      AND dataflow_version = :dataflow_version
      AND [year] BETWEEN :start_year AND :end_year
      AND indicator = :indicator
    """
    params = {
        "dataflow_id": flow["dataflow_id"],
        "dataflow_agency_id": flow["dataflow_agency_id"],
        "dataflow_version": flow["dataflow_version"],
        "start_year": int(START_PERIOD[:4]),
        "end_year": int(END_PERIOD[:4]),
        "indicator": FILTERS["INDICATOR"]}

    with engine.begin() as conn: result = conn.execute(sa.text(sql), params)
    print(f"Deleted existing rows: {result.rowcount}")

def main():
    engine = sa.create_engine(s.connection_string, fast_executemany=True)
    flow = get_dataflow(engine)
    structure = parse_structure_urn(flow["structure_urn"])
    if not structure: raise Exception("Could not parse structure_urn.")
    dimensions_df = get_dimensions(engine, structure)
    print("Dimensions:")
    print(dimensions_df[["dimension_id", "dimension_position", "dimension_type"]].to_string(index=False))
    key = build_key(dimensions_df)
    print("Key:", key)
    url = build_url(flow, key)
    xml_text = fetch_xml(url)
    df = parse_sdmx_xml(xml_text, flow, dimensions_df, url)
    print("Rows parsed:", len(df))
    print(df.head(5))
    if df.empty:
        print("No data rows found.")
        return
    delete_existing_rows(engine, flow)
    df.to_sql(name=TABLE, schema=SCHEMA, con=engine, if_exists="append", index=False, chunksize=5000)
    print("DONE")
    print(f"Inserted rows: {len(df)}")

if __name__ == "__main__": main()

"""
CREATE TABLE imf.[data] (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    dataflow_id NVARCHAR(100) NOT NULL,
    dataflow_agency_id NVARCHAR(100) NULL,
    dataflow_version NVARCHAR(50) NULL,
    series_key NVARCHAR(MAX) NULL,
    accounting_entry NVARCHAR(300) NULL,
    accounts NVARCHAR(300) NULL,
    activity NVARCHAR(300) NULL,
    adjustment NVARCHAR(300) NULL,
    age NVARCHAR(300) NULL,
    age_group NVARCHAR(300) NULL,
    aggregation_type NVARCHAR(300) NULL,
    answer_id NVARCHAR(300) NULL,
    bop_accounting_entry NVARCHAR(300) NULL,
    c_resid NVARCHAR(300) NULL,
    coicop NVARCHAR(300) NULL,
    coicop_1999 NVARCHAR(300) NULL,
    composite_breakdown NVARCHAR(300) NULL,
    contact_id NVARCHAR(300) NULL,
    contact_type NVARCHAR(300) NULL,
    counterpart_area NVARCHAR(300) NULL,
    counterpart_country NVARCHAR(300) NULL,
    counterpart_sector NVARCHAR(300) NULL,
    country NVARCHAR(300) NULL,
    cpa2_1 NVARCHAR(300) NULL,
    currency NVARCHAR(300) NULL,
    currency_type NVARCHAR(300) NULL,
    cust_breakdown NVARCHAR(300) NULL,
    data_transformation NVARCHAR(300) NULL,
    disability_status NVARCHAR(300) NULL,
    dv_type NVARCHAR(300) NULL,
    education_lev NVARCHAR(300) NULL,
    emission_type NVARCHAR(300) NULL,
    energy_product NVARCHAR(300) NULL,
    energy_source NVARCHAR(300) NULL,
    entry_id NVARCHAR(300) NULL,
    expenditure NVARCHAR(300) NULL,
    ffs NVARCHAR(300) NULL,
    food_security_environment NVARCHAR(300) NULL,
    freq NVARCHAR(300) NULL,
    frequency NVARCHAR(300) NULL,
    fsi_icre NVARCHAR(300) NULL,
    fxr_currency NVARCHAR(300) NULL,
    gas_type NVARCHAR(300) NULL,
    gender NVARCHAR(300) NULL,
    geo NVARCHAR(300) NULL,
    geographic_marine_zones_and_climatic_classifications NVARCHAR(300) NULL,
    gfs_grp NVARCHAR(300) NULL,
    gs_li_ds NVARCHAR(300) NULL,
    gs_li_ea NVARCHAR(300) NULL,
    gs_li_ed NVARCHAR(300) NULL,
    gs_li_occ NVARCHAR(300) NULL,
    gs_ms NVARCHAR(300) NULL,
    implementing_jurisdiction NVARCHAR(300) NULL,
    income_wealth_quantile NVARCHAR(300) NULL,
    index_type NVARCHAR(300) NULL,
    indic_bt NVARCHAR(300) NULL,
    indic_em NVARCHAR(300) NULL,
    indicator NVARCHAR(300) NULL,
    indicator_type NVARCHAR(300) NULL,
    industry NVARCHAR(300) NULL,
    initial_assessment NVARCHAR(300) NULL,
    instr_asset NVARCHAR(300) NULL,
    issuance_date NVARCHAR(300) NULL,
    issuer NVARCHAR(300) NULL,
    jurisdiction NVARCHAR(300) NULL,
    legal_spouse_presence NVARCHAR(300) NULL,
    level_of_government_implementation NVARCHAR(300) NULL,
    levels_of_policy_intervention NVARCHAR(300) NULL,
    mfs_srvy NVARCHAR(300) NULL,
    motive NVARCHAR(300) NULL,
    na_item NVARCHAR(300) NULL,
    nace_r2 NVARCHAR(300) NULL,
    nsdp_cat NVARCHAR(300) NULL,
    number_of_children NVARCHAR(300) NULL,
    occupation NVARCHAR(300) NULL,
    policy_type NVARCHAR(300) NULL,
    price_type NVARCHAR(300) NULL,
    prices NVARCHAR(300) NULL,
    principal_employment_earnings NVARCHAR(300) NULL,
    [product] NVARCHAR(300) NULL,
    production_index NVARCHAR(300) NULL,
    question NVARCHAR(300) NULL,
    reason NVARCHAR(300) NULL,
    ref_area NVARCHAR(300) NULL,
    ref_sector NVARCHAR(300) NULL,
    reporting_type NVARCHAR(300) NULL,
    rpb NVARCHAR(300) NULL,
    s_adj NVARCHAR(300) NULL,
    s_adjustment NVARCHAR(300) NULL,
    scenario NVARCHAR(300) NULL,
    sector NVARCHAR(300) NULL,
    segment NVARCHAR(300) NULL,
    series NVARCHAR(300) NULL,
    sex NVARCHAR(300) NULL,
    spouse_employment_earnings NVARCHAR(300) NULL,
    statinfo NVARCHAR(300) NULL,
    [status] NVARCHAR(300) NULL,
    sto NVARCHAR(300) NULL,
    sub_type NVARCHAR(300) NULL,
    subject_code NVARCHAR(300) NULL,
    subject_id NVARCHAR(300) NULL,
    survey_id NVARCHAR(300) NULL,
    transformation NVARCHAR(300) NULL,
    type_of_transformation NVARCHAR(300) NULL,
    unit NVARCHAR(300) NULL,
    unit_measure NVARCHAR(300) NULL,
    urbanisation NVARCHAR(300) NULL,
    vintage NVARCHAR(300) NULL,
    wgt_type NVARCHAR(300) NULL,
    time_period NVARCHAR(50) NOT NULL,
    [year] INT NULL,
    [value] FLOAT NULL,
    attributes_json NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);

CREATE INDEX IX_imf_data_flow ON imf.data(dataflow_id);
CREATE INDEX IX_imf_data_country ON imf.data(country);
CREATE INDEX IX_imf_data_ref_area ON imf.data(ref_area);
CREATE INDEX IX_imf_data_indicator ON imf.data(indicator);
CREATE INDEX IX_imf_data_year ON imf.data([year]);
CREATE INDEX IX_imf_data_flow_year ON imf.data(dataflow_id, [year]);

"""