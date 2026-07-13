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
🌍 Top 10 vs Bottom 10 countries by life expectancy at birth (2024).

A child born today can expect to live decades longer depending on where they are born.

Source: World Bank
"""


TOP_N = 10
FILE_NAME = "life_expectancy_top_bottom_10_2024.png"
TITLE = "Life Expectancy at Birth"
SUBTITLE = "Top 10 and Bottom 10 Countries, 2024"
FOOTER_LEFT = "Years"
FOOTER_RIGHT = "Source: World Bank | WorldDataAtlas"
LEFT_PANEL_TITLE = "Highest"
RIGHT_PANEL_TITLE = "Lowest"
LABEL_COL = "country_name"
FLAG_COL = "country_id"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "value"

query = f"""
    SELECT
         AA.[id]
        ,AA.[country_code]
        ,AA.[country_id]
        ,AA.[country_name]
        ,AA.[indicator_name]
        ,AA.[year]
        ,AA.[value]
    FROM [World_Data_Atlas].[worldbank].[data] AS AA
    LEFT JOIN worldbank.entities ENT
        ON AA.[country_id] = ENT.iso2_code
    WHERE AA.[indicator_code] = 'SP.DYN.LE00.IN'
        AND AA.[year] = 2024
        AND ENT.is_country = 1
        AND AA.[value] IS NOT NULL
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