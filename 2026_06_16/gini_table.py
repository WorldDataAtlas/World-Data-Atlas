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
FILE_NAME = "gini_table.png"

TITLE = "Income Inequality Around the World"
SUBTITLE = "Latest available Gini index"
FOOTER_LEFT = "Lower values = more equal income distribution"
FOOTER_RIGHT = "Source: World Bank"
LEFT_PANEL_TITLE = "Most Equal"
RIGHT_PANEL_TITLE = "Most Unequal"
LABEL_COL = "country_name_year"
FLAG_COL = "country_id"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "value"

"""The gap between rich and poor varies dramatically around the world.

Interestingly, being wealthy doesn't guarantee low inequality.

Latest available Gini index by country.

Source: World Bank

#Economics #Gini #Inequality #DataViz"""



query = f"""
        WITH latest_gini AS (
        SELECT
                D.country_code,
                D.country_id,
                D.country_name,
                D.[year],
                D.[value],
                ROW_NUMBER() OVER (PARTITION BY D.country_code ORDER BY D.[year] DESC) AS rn
        FROM worldbank.data D
        INNER JOIN worldbank.entities E ON D.country_id = E.iso2_code
        WHERE D.indicator_code = 'SI.POV.GINI' AND D.[value] IS NOT NULL AND E.is_country = 1)
        SELECT
                country_code,
                country_id,
                CONCAT(country_name, ' (', CAST([year] AS varchar(4)), ')') AS country_name_year,
                [year],
                [value]
        FROM latest_gini
        WHERE rn = 1
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
    #left_direction_symbol="+",
    #right_direction_symbol="-",
    left_value_prefix="#",
    right_value_prefix="#",
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
    flags_dir=FLAGS_DIR)