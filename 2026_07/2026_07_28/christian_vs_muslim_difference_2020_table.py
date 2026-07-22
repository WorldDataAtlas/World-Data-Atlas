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

TOP_N = 10
FILE_NAME = "christian_vs_muslim_difference_2020.png"
TITLE = "Christian vs Muslim Population"
SUBTITLE = "Top 10 and Bottom 10 countries by the difference between the Christian and Muslim shares of the population, 2020"
FOOTER_LEFT = "Difference in percentage points (Christians − Muslims)"
FOOTER_RIGHT = "Source: Pew Research Center"
LEFT_PANEL_TITLE = "Largest Christian Majority"
RIGHT_PANEL_TITLE = "Largest Muslim Majority"
LABEL_COL = "country"
FLAG_COL = "country_code"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "christian_minus_muslim_pp"

query = f"""
        SELECT
                EN.iso2_code AS country_code,
                AG.country,
                ROUND(AG.christians * 100.0 / AG.population, 2) AS christians_pct,
                ROUND(AG.muslims * 100.0 / AG.population, 2) AS muslims_pct,
                ROUND((AG.christians - AG.muslims) * 100.0 / AG.population, 2) AS christian_minus_muslim_pp
        FROM pew.global_religious_estimates AG
        LEFT JOIN worldbank.entities EN ON LOWER(LTRIM(RTRIM(EN.name))) = LOWER(LTRIM(RTRIM(AG.country))) AND EN.is_country = 1
        WHERE
                AG.level = 1
                AND AG.year = 2020
                AND AG.population > 0
                AND EN.iso2_code IS NOT NULL
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