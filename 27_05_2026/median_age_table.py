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
FILE_NAME = "median_age_table.png"
TITLE = "Countries with the Highest and Lowest Median Ages"
SUBTITLE = "2025"
FOOTER_LEFT = "Metric: Median age of population"
FOOTER_RIGHT = "Source: United Nations"
LEFT_PANEL_TITLE = "Youngest Populations"
RIGHT_PANEL_TITLE = "Oldest Populations"
LABEL_COL = "country_name"
FLAG_COL = "country_id"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "median_age"
LEFT_COLOR = "#22C55E"
RIGHT_COLOR = "#FF0000"
LEFT_DIRECTION_SYMBOL = ''
RIGHT_DIRECTION_SYMBOL = ''

query = f"""
        SELECT  D.[iso3_code] AS [country_id] ,
                [name] as [country_name],
                ROUND(D.[value], 1) AS [median_age]
        FROM [World_Data_Atlas].[un].[data] as D
        LEFT JOIN (     SELECT [wb_id],[iso2_code],[name],[is_country]
                        FROM [World_Data_Atlas].[worldbank].[entities]
                        WHERE [is_country] = 1) AS ENT ON ENT.[iso2_code] = D.[iso2_code]
        WHERE ENT.[is_country] = 1 and [indicator_id] = 67 AND D.[variant_id] = 4 AND [sex_id] = 3 and D.[year] = 2025
        """

engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
olders = df.sort_values("median_age", ascending=False).head(TOP_N)
youngsters = df.sort_values("median_age", ascending=True).head(TOP_N)

# ============================================================

OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
FLAGS_DIR = BASE_DIR / "flags_png"
create_double_table_chart(
    left_data=youngsters,
    right_data=olders,
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
    left_color = LEFT_COLOR,
    right_color = RIGHT_COLOR,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
    flags_dir=FLAGS_DIR)