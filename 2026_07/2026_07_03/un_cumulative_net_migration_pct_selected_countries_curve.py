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
from graph_curve import create_multi_line_chart

# ============================================================

"""Migration has reshaped many countries over the past three decades.

This chart shows cumulative net migration since 1995 as a share of each country's current population.

Source: United Nations, World Population Prospects.

#Migration #Demography #Population #DataViz"""


query = """
WITH base AS (
    SELECT 
        CASE 
            WHEN D.[location_name] = 'Russian Federation' THEN 'Russia'
            WHEN D.[location_name] = 'United States of America' THEN 'USA'
            WHEN D.[location_name] = 'Democratic Republic of the Congo' THEN 'Congo'
            WHEN D.[location_name] = 'Iran (Islamic Republic of)' THEN 'Iran'
            WHEN D.[location_name] = 'United Kingdom' THEN 'UK'
            WHEN D.[location_name] = 'South Africa' THEN 'SA'
            ELSE D.[location_name]
        END AS [location_name],
        D.[iso2_code],
        D.[iso3_code],
        D.[year],
        CAST(D.[value] AS FLOAT) AS [net_migration],
        CAST(POP.[value] AS FLOAT) AS [population]
    FROM [World_Data_Atlas].[un].[data] AS D
    LEFT JOIN worldbank.entities ENT 
        ON D.iso2_code = ENT.iso2_code 
       AND D.iso3_code = ENT.[wb_id]
    LEFT JOIN [World_Data_Atlas].[un].[data] POP 
        ON POP.[iso2_code] = D.[iso2_code]
       AND POP.[iso3_code] = D.[iso3_code]
       AND POP.[year] = D.[year]
       AND POP.[sex_id] = 3
       AND POP.[variant_id] = 4
       AND POP.[indicator_id] = 49
    WHERE D.[indicator_id] = 65
      AND D.[variant_id] = 4
      AND D.[year] BETWEEN 1995 AND 2025
      AND ENT.[is_country] = 1
      AND D.[location_name] IN (
            'Germany',
            'France',
            'Sweden',
            'United States of America'
      )
),
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
    [cumulative_net_migration] AS [cumulative_net_migration_since_1995_persons],
    ROUND(
        [cumulative_net_migration] * 100.0 / NULLIF([population], 0),
        4
    ) AS [value]

FROM calc
ORDER BY [location_name], [year];
        """

MAP_TITLE = "Cumulative Net Migration Since 1995"
MAP_SUBTITLE = "Selected countries, 1995–2025"
MAP_SOURCE = "Source: United Nations, World Population Prospects"
FILE_NAME = "un_cumulative_net_migration_pct_selected_countries.png"
FOOTER_LEFT = "Cumulative net migration since 1995 as % of current population"
FOOTER_RIGHT = "WorldDataAtlas.com"
SERIES_COL = "location_name"
Y_LABEL = "Cumulative net migration (% of population)"
LEGEND_LOCATION = "upper left"

series_config = [
    {"source_value": "Germany", "label": "Germany", "color": "#F59E0B"},
    {"source_value": "France",  "label": "France",  "color": "#2563EB"},
    {"source_value": "Sweden",  "label": "Sweden",  "color": "#22C55E"},
    {"source_value": "USA",     "label": "USA",     "color": "#60A5FA"},
]

# ============================================================

OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
df["year"] = df["year"].astype(int)
df["value"] = df["value"].astype(float)
create_multi_line_chart(
    df=df,
    output_file=OUTPUT_FILE,
    x_col="year",
    y_col="value",
    series_col=SERIES_COL,
    series_config=series_config,
    title=MAP_TITLE,
    subtitle=MAP_SUBTITLE,
    marker_size=15,
    y_label=Y_LABEL,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    legend_location= LEGEND_LOCATION,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
)