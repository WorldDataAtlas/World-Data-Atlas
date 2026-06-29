import pandas as pd
import sqlalchemy as sa
from pathlib import Path
import sys
import os
BASE_DIR = Path(__file__).resolve().parent
etl_path = (BASE_DIR.parent / "ETL").resolve()
sys.path.insert(0, str(etl_path))
import settings as s
module_path = (BASE_DIR.parent / "modules").resolve()
sys.path.insert(0, str(module_path))
from graph_double_table import create_double_table_chart

# ============================================================

"""Migration has reshaped populations over the past 25 years.

Some countries gained the equivalent of more than half their current population through net migration, while others experienced sustained net outflows.
Cumulative net migration as a share of population, 2000–2025."""


TOP_N = 15
FILE_NAME = "un_cumulative_net_migration_top_bottom_2000_2025.png"
TITLE = "Cumulative Net Migration Since 2000"
SUBTITLE = "Top and bottom countries by cumulative net migration as % of population, 2000–2025"
FOOTER_LEFT = "Net migration = immigrants − emigrants"
FOOTER_RIGHT = "Source: United Nations, World Population Prospects"
LEFT_PANEL_TITLE = "Highest net migration gain"
RIGHT_PANEL_TITLE = "Highest net migration loss"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "value"

query = f"""
WITH base AS (
    SELECT 
        CASE 
            WHEN D.[location_name] = 'Russian Federation' THEN 'Russia'
            WHEN D.[location_name] = 'United States of America' THEN 'USA'
            WHEN D.[location_name] = 'Democratic Republic of the Congo' THEN 'Congo'
            WHEN D.[location_name] = 'Iran (Islamic Republic of)' THEN 'Iran'
            WHEN D.[location_name] = 'United Kingdom' THEN 'UK'
            WHEN D.[location_name] = 'South Africa' THEN 'SA'
            WHEN D.[location_name] = 'Republic of Moldova' THEN 'Moldova'
            WHEN D.[location_name] = 'Kosovo (under UNSC res. 1244)' THEN 'Kosovo'
            WHEN D.[location_name] = 'Venezuela (Bolivarian Republic of)' THEN 'Venezuela'
            WHEN D.[location_name] = 'Central African Republic' THEN 'Cen. Af. Rep.'
            WHEN D.[location_name] = 'United Arab Emirates' THEN 'UEA'
            WHEN D.[location_name] = 'Bosnia and Herzegovina' THEN 'Bos, and Her.'
            ELSE D.[location_name]
        END AS [location_name],
        D.[iso2_code],
        D.[iso3_code],
        D.[year],
        CAST(D.[value] AS FLOAT) AS [net_migration],
        CAST(POP.[value] AS FLOAT) AS [population]
    FROM [World_Data_Atlas].[un].[data] AS D
    LEFT JOIN worldbank.entities ENT ON D.iso2_code = ENT.iso2_code AND D.iso3_code = ENT.[wb_id]
    LEFT JOIN [World_Data_Atlas].[un].[data] POP 
        ON POP.[iso2_code] = D.[iso2_code]
       AND POP.[iso3_code] = D.[iso3_code]
       AND POP.[year] = D.[year]
       AND POP.[sex_id] = 3
       AND POP.[variant_id] = 4
       AND POP.[indicator_id] = 49
    WHERE D.[indicator_id] = 65
      AND D.[variant_id] = 4
      AND D.[year] BETWEEN 2000 AND 2026
      AND ENT.[is_country] = 1),
calc AS (
    SELECT
        [location_name],
        [iso2_code],
        [iso3_code],
        [year],
        [net_migration],
        [population],
        SUM([net_migration]) OVER (
            PARTITION BY [iso3_code]
            ORDER BY [year]
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS [cumulative_net_migration]
    FROM base)
SELECT
    [location_name],
    [iso2_code],
    [iso3_code],
    [year],
    [net_migration] AS [net_migration_persons],
    [population] AS [population_persons],
    [cumulative_net_migration] AS [cumulative_net_migration_since_persons],
    ROUND([cumulative_net_migration] * 100.0 / NULLIF([population], 0), 4) AS [value]
FROM calc
where [year] = 2025 and [location_name] not in ('Andorra','Curaçao','Sint Maarten (Dutch part)','Nauru','Tuvalu','Tonga','Samoa','Marshall Islands','Micronesia (Fed. States of)','Fiji','Saint Vincent and the Grenadines','Guam','American Samoa','Northern Mariana Islands','United States Virgin Islands','Saint Martin (French part)','Puerto Rico','Turks and Caicos Islands', 'British Virgin Islands','Cayman Islands','China, Macao SAR','Monaco','San Marino','Gibraltar','Seychelles','Maldives')
ORDER BY ROUND([cumulative_net_migration] * 100.0 / NULLIF([population], 0), 4) desc,[location_name], [year];
        """

# ============================================================

engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
climbers = df.sort_values(CHANGE_COL,ascending=False).head(TOP_N)
fallers = df.sort_values(CHANGE_COL,ascending=True).head(TOP_N)
OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
FLAGS_DIR = BASE_DIR / "flags_png"
create_double_table_chart(
    left_data=climbers,
    right_data=fallers,
    output_file=OUTPUT_FILE,
    title=TITLE,
    subtitle=SUBTITLE,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    left_panel_title=LEFT_PANEL_TITLE,
    right_panel_title=RIGHT_PANEL_TITLE,
    label_col=LABEL_COL,
    flag_col=FLAG_COL,
    left_value_col=LEFT_VALUE_ID,
    right_value_col=RIGHT_VALUE_ID,
    change_col=CHANGE_COL,
    top_n=TOP_N,
    left_value_prefix="#",
    right_value_prefix="#",
    decimal_places=2,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
    flags_dir=FLAGS_DIR)