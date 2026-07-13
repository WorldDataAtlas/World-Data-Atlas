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
🌍 Fewer workers, more retirees.

The potential support ratio—the number of people aged 25–64 per person aged 65+—has been falling across every major region for decades.

Source: United Nations | #WorldDataAtlas

"""


query = """
    SELECT AA.[location_id]
        ,AA.[location_name]
        ,AA.[iso2_code]
        ,AA.[iso3_code]
        ,AA.[indicator_name]
        ,AA.[year]
        ,AA.[value]
        ,AA.[sex_name]
        ,AA.[age_id]
    FROM [World_Data_Atlas].[un].[data] AS AA
    LEFT JOIN [World_Data_Atlas].worldbank.entities ENT ON AA.[iso2_code] = ENT.iso2_code
    WHERE [indicator_id] = 85 and AA.[sex_id] = 3 and AA.[variant_id] = 4
            and AA.[age_id] = 1013 and AA.[iso3_code] in ('EUR','ASI','WLD','AFR','NAC','SAM')
    order by AA.[year]
        """

MAP_TITLE = "Potential Support Ratio by Region"
MAP_SUBTITLE = "Both sexes, age group 25–64 per person aged 65+, 1950–2050"
MAP_SOURCE = "United Nations World Population Prospects"
FILE_NAME = "potential_support_ratio_regions.png"
FOOTER_LEFT = "Medium variant projection"
FOOTER_RIGHT = "Source: United Nations"
SERIES_COL = "iso3_code"
Y_LABEL = "Working-age persons per person aged 65+"

LEGEND_LOCATION = "lower left"
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