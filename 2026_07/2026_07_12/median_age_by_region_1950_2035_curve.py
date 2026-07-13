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

"""
🌍 The world's population is getting older.

Median age has risen across every major region over the past decades, with Europe remaining the oldest and Africa the youngest.

Source: United Nations | #WorldDataAtlas
"""



query = """
    SELECT
         AA.[location_id]
        ,AA.[location_name]
        ,AA.[iso2_code]
        ,AA.[iso3_code]
        ,AA.[year]
        ,AA.[value]
    FROM [World_Data_Atlas].[un].[data] AS AA
    LEFT JOIN worldbank.entities AS ENT
        ON AA.[iso2_code] = ENT.[iso2_code]
    WHERE AA.[indicator_id] = 67
        AND (ENT.[is_country] = 0 OR ENT.[is_country] IS NULL)
        AND AA.[variant_id] = 4
        AND AA.[iso3_code] IN ('EUR', 'ASI', 'WLD', 'AFR', 'NAC', 'SAM')
    ORDER BY AA.[year]
"""

MAP_TITLE = "Median Age by Region"
MAP_SUBTITLE = "World and major regions, 1950–2035"
MAP_SOURCE = "Source: United Nations, World Population Prospects"
FILE_NAME = "median_age_by_region_1950_2035.png"
FOOTER_LEFT = "Medium variant"
FOOTER_RIGHT = "WorldDataAtlas"
SERIES_COL = "iso3_code"
Y_LABEL = "Median age (years)"
LEGEND_LOCATION = "upper left"

series_config = [
    {"source_value": "WLD","label": "World","color": "#F8FAFC"},
    {"source_value": "AFR","label": "Africa","color": "#22C55E"},
    {"source_value": "ASI", "label": "Asia", "color": "#F59E0B" },
    {"source_value": "EUR", "label": "Europe", "color": "#60A5FA" },
    {"source_value": "NAC", "label": "North America", "color": "#F472B6"},
    {"source_value": "SAM", "label": "South America", "color": "#A78BFA"}]

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
    marker_size=1,
    y_label=Y_LABEL,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    legend_location= LEGEND_LOCATION,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
)