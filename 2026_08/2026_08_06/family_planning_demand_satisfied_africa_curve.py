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
👶 How has access to family planning changed across Africa?

This chart compares the share of family planning demand satisfied by any contraceptive method for all women, married women, and unmarried women in Africa.

Source: United Nations | #WorldDataAtlas
"""

query = """
    SELECT
        AA.[location_id]
        ,AA.[location_name]
        ,AA.[iso2_code]
        ,AA.[iso3_code]
        ,AA.category_id
        ,AA.category_name
        ,AA.[year]
        ,AA.[value]
    FROM [World_Data_Atlas].[un].[data] AS AA
    WHERE AA.[indicator_id] = 7 AND AA.[variant_id] = 4 AND AA.[iso2_code] = 'A9'
    ORDER BY AA.[year]
        """

MAP_TITLE = "Demand for Family Planning Satisfied"
MAP_SUBTITLE = "Africa, by relationship status, 1970–2030"
MAP_SOURCE = "United Nations"
FILE_NAME = "family_planning_demand_satisfied_africa.png"
FOOTER_LEFT = "Share of demand satisfied by any contraceptive method"
FOOTER_RIGHT = "Source: United Nations"
SERIES_COL = "category_id"
Y_LABEL = "Percent"
LEGEND_LOCATION = "lower right"

series_config = [   {"source_value": 99, "label": "All women", "color": "#60A5FA"},
                    {"source_value": 100, "label": "Married or in a union", "color": "#F472B6"},
                    {"source_value": 101, "label": "Unmarried women", "color": "#22C55E"}]

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