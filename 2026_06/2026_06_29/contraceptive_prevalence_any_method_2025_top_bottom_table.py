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

"""Contraceptive use varies dramatically across the world.

In some countries, fewer than one in five women use contraception, while in others the figure exceeds 80%.

Top and bottom countries by the share of women aged 15–49 currently using any method of contraception, 2025.

Source: United Nations

#Demography #Healthcare #DataViz"""


TOP_N = 10
FILE_NAME = "contraceptive_prevalence_any_method_2025_top_bottom.png"
TITLE = "Contraceptive Use, 2025"
SUBTITLE = "Top and bottom countries by the share of women aged 15–49 currently using any method of contraception"
FOOTER_LEFT = "Source: United Nations"
FOOTER_RIGHT = "WorldDataAtlas.com"
LEFT_PANEL_TITLE = "Highest prevalence"
RIGHT_PANEL_TITLE = "Lowest prevalence"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "value"

query = f"""
        SELECT
                AA.[location_name]
                ,AA.[iso3_code]
                ,AA.[iso2_code]
                ,AA.[indicator_name]
                ,AA.[year]
                ,AA.[value]
                ,AA.category_id
                ,AA.category_name
        FROM [World_Data_Atlas].[un].[data] as AA
        LEFT JOIN worldbank.entities ENT ON AA.iso2_code = ENT.iso2_code AND AA.iso3_code = ENT.[wb_id]
        WHERE   AA.indicator_id = 1 and 
                AA.[variant_id] = 4 and 
                AA.[age_id] = 31 and 
                AA.[year] = 2025 and 
                AA.category_id = 99 AND 
                ENT.is_country = 1
        ORDER BY AA.[value]
        """

# ============================================================

engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
top = df.sort_values(CHANGE_COL,ascending=True).head(TOP_N)
bottom = df.sort_values(CHANGE_COL,ascending=False).head(TOP_N)
OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
FLAGS_DIR = BASE_DIR / "flags_png"
create_double_table_chart(
    left_data=bottom,
    right_data=top,
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
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
    flags_dir=FLAGS_DIR)