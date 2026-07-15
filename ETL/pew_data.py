import os
import pandas as pd
import sqlalchemy as sa
import settings as s

CSV_FILENAME = "Religious Composition 2010-2020 (unrounded counts).csv"
DB_SCHEMA = "pew"
DB_TABLE = "global_religious_estimates"

def clean_value(val):
    if pd.isna(val): return None
    val_str = str(val).strip()
    if "<" in val_str: return 9999
    if ',' in val_str:
        test_val = val_str.replace(',', '')
        if test_val.isdigit(): return int(test_val)
    return val

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file_path = os.path.join(script_dir, CSV_FILENAME)
    engine = sa.create_engine(s.connection_string, fast_executemany=True)
    print(f"Loading from: {input_file_path}...")
    df = pd.read_csv(input_file_path)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    for col in df.columns: df[col] = df[col].apply(clean_value)
    df.columns = df.columns.str.lower()
    if 'countrycode' in df.columns: df = df.rename(columns={'countrycode': 'country_code'})
    print(f"Deleting {DB_SCHEMA}.{DB_TABLE}...")
    try:
        with engine.begin() as conn: conn.execute(sa.text(f"TRUNCATE TABLE {DB_SCHEMA}.{DB_TABLE}"))
        print(f"Writing to {DB_SCHEMA}.{DB_TABLE}...")
        df.to_sql(
            name=DB_TABLE,
            schema=DB_SCHEMA,
            con=engine,
            if_exists="append",
            index=False,
            chunksize=500)
        print(f"Imported {len(df)} rows")
    except Exception as e: print(f"Error: {e}")
    print("Normalizing country names...")
    with engine.begin() as conn:
        conn.execute(sa.text(f"""
            DELETE FROM {DB_SCHEMA}.{DB_TABLE}
            WHERE country IN (
                'French Guiana',
                'Martinique',
                'Taiwan',
                'Guadeloupe',
                'Western Sahara',
                'Mayotte',
                'Reunion'
            );

            UPDATE {DB_SCHEMA}.{DB_TABLE}
            SET country = CASE country
                WHEN 'South Korea' THEN 'Korea, Rep.'
                WHEN 'Cape Verde' THEN 'Cabo Verde'
                WHEN 'Vietnam' THEN 'Viet Nam'
                WHEN 'Czech Republic' THEN 'Czechia'
                WHEN 'Hong Kong' THEN 'Hong Kong SAR, China'
                WHEN 'Turkey' THEN 'Turkiye'
                WHEN 'U.S. Virgin Islands' THEN 'Virgin Islands (U.S.)'
                WHEN 'Venezuela' THEN 'Venezuela, RB'
                WHEN 'Slovakia' THEN 'Slovak Republic'
                WHEN 'Puerto Rico' THEN 'Puerto Rico (US)'
                WHEN 'Laos' THEN 'Lao PDR'
                WHEN 'Somalia' THEN 'Somalia, Fed. Rep.'
                WHEN 'Syria' THEN 'Syrian Arab Republic'
                WHEN 'North Korea' THEN 'Korea, Dem. People''s Rep.'
                WHEN 'Palestinian territories' THEN 'West Bank and Gaza'
                WHEN 'Federated States of Micronesia' THEN 'Micronesia, Fed. Sts.'
                WHEN 'Egypt' THEN 'Egypt, Arab Rep.'
                WHEN 'Iran' THEN 'Iran, Islamic Rep.'
                WHEN 'Yemen' THEN 'Yemen, Rep.'
                WHEN 'Bosnia-Herzegovina' THEN 'Bosnia and Herzegovina'
                WHEN 'Gambia' THEN 'Gambia, The'
                WHEN 'Republic of the Congo' THEN 'Congo, Rep.'
                WHEN 'Bahamas' THEN 'Bahamas, The'
                WHEN 'Macao' THEN 'Macao SAR, China'
                WHEN 'Democratic Republic of the Congo' THEN 'Congo, Dem. Rep.'
                WHEN 'Kyrgyzstan' THEN 'Kyrgyz Republic'
                WHEN 'Ivory Coast' THEN 'Cote d''Ivoire'
                WHEN 'Brunei' THEN 'Brunei Darussalam'
                WHEN 'Russia' THEN 'Russian Federation'
                ELSE country
            END
            WHERE country IN (
                'South Korea',
                'Cape Verde',
                'Vietnam',
                'Czech Republic',
                'Hong Kong',
                'Turkey',
                'U.S. Virgin Islands',
                'Venezuela',
                'Slovakia',
                'Puerto Rico',
                'Laos',
                'Somalia',
                'Syria',
                'North Korea',
                'Palestinian territories',
                'Federated States of Micronesia',
                'Egypt',
                'Iran',
                'Yemen',
                'Bosnia-Herzegovina',
                'Gambia',
                'Republic of the Congo',
                'Bahamas',
                'Macao',
                'Democratic Republic of the Congo',
                'Kyrgyzstan',
                'Ivory Coast',
                'Brunei',
                'Russia'
            );"""))
    print("Country names normalized.")
if __name__ == '__main__': main()

"""
DROP TABLE IF EXISTS pew.global_religious_estimates;
CREATE TABLE pew.global_religious_estimates (
    id INT IDENTITY(1,1) PRIMARY KEY,
    region NVARCHAR(255) NULL,
    country NVARCHAR(255) NULL,
    year INT NULL,
    population BIGINT NULL,
    christians BIGINT NULL,
    muslims BIGINT NULL,
    religiously_unaffiliated BIGINT NULL,
    buddhists BIGINT NULL,
    hindus BIGINT NULL,
    jews BIGINT NULL,
    other_religions BIGINT NULL,
    level INT NULL,
    country_code INT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
"""