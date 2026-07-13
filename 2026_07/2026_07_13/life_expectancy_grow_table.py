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
🌍 Life expectancy has risen almost everywhere—but not equally.

Here are the countries with the largest and smallest improvements since 1995.

Source: World Bank
"""



TOP_N = 10
FILE_NAME = "life_expectancy_change_1995_2024.png"

TITLE = "Life Expectancy Change"
SUBTITLE = "Top 10 and Bottom 10 Countries, 1995–2024"
FOOTER_LEFT = "Change in years"
FOOTER_RIGHT = "Source: World Bank | WorldDataAtlas"
LEFT_PANEL_TITLE = "Largest Increase"
RIGHT_PANEL_TITLE = "Smallest Increase"
LABEL_COL = "country_name"
FLAG_COL = "country_id"
LEFT_VALUE_ID = "value_1995"
RIGHT_VALUE_ID = "value_2024"
CHANGE_COL = "difference"

query = f"""
SELECT
    AA.country_code,
    AA.country_id,
    case
        when AA.country_name = 'St. Vincent and the Grenadines' then 'St. Vincent & Grenadines'
        else AA.country_name
    end as country_name,
    MAX(CASE WHEN AA.[year] = 1995 THEN AA.[value] END) AS value_1995,
    MAX(CASE WHEN AA.[year] = 2024 THEN AA.[value] END) AS value_2024,
    MAX(CASE WHEN AA.[year] = 2024 THEN AA.[value] END) - MAX(CASE WHEN AA.[year] = 1995 THEN AA.[value] END) AS difference
FROM [World_Data_Atlas].[worldbank].[data] AS AA
LEFT JOIN worldbank.entities AS ENT ON AA.country_id = ENT.iso2_code
WHERE AA.indicator_code = 'SP.DYN.LE00.IN' AND ENT.is_country = 1 AND AA.[year] IN (1995, 2024)
GROUP BY AA.country_code, AA.country_id, AA.country_name
HAVING MAX(CASE WHEN AA.[year] = 1995 THEN AA.[value] END) IS NOT NULL AND MAX(CASE WHEN AA.[year] = 2024 THEN AA.[value] END) IS NOT NULL
ORDER BY [difference] DESC;
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
    left_value_prefix="",
    right_value_prefix="",
    decimal_places=2,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
    flags_dir=FLAGS_DIR)