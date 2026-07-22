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

"""
🌍 Potential support ratio (2025)

African countries top the ranking thanks to their young populations. The Gulf states stand out even more—not because of higher fertility alone, but because of their exceptionally large working-age migrant populations.

Source: United Nations
"""

TOP_N = 15
FILE_NAME = "potential_support_ratio_top_bottom_10_2025.png"
TITLE = "Potential Support Ratio"
SUBTITLE = "Top 10 and Bottom 15 Countries, 2025"
FOOTER_LEFT = "People aged 25–64 per person aged 65+ (both sexes)"
FOOTER_RIGHT = "Source: United Nations"
LEFT_PANEL_TITLE = "Highest"
RIGHT_PANEL_TITLE = "Lowest"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "value"

query = f"""
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
        WHERE [indicator_id] = 85 AND ENT.[IS_COUNTRY] = 1 and AA.[sex_id] = 3 and AA.[variant_id] = 4
                and AA.[age_id] = 1013 and AA.[year] = 2025
        ORDER BY AA.[value]
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