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

"""Health spending varies enormously across countries.

In 2023, some economies devoted less than 3% of GDP to healthcare, while others spent more than 15%.

Top and bottom countries by current health expenditure as a share of GDP.

Source: World Bank

#Healthcare #Economics"""

TOP_N = 10
FILE_NAME = "health_expenditure_share_gdp_2023_top_bottom.png"
TITLE = "Health Expenditure, 2023"
SUBTITLE = "Top and bottom countries by current health expenditure as a share of GDP"
FOOTER_LEFT = "Source: World Bank"
FOOTER_RIGHT = "WorldDataAtlas.com"
LEFT_PANEL_TITLE = "Lowest spending"
RIGHT_PANEL_TITLE = "Highest spending"
LABEL_COL = "country_name"
FLAG_COL = "country_id"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "value"

query = """
        SELECT
                CASE
                        WHEN D.[country_name] = 'Syrian Arab Republic' THEN 'Syria'
                        WHEN D.[country_name] = 'Lao PDR' THEN 'Laos'
                        WHEN D.[country_name] = 'Brunei Darussalam' THEN 'Brunei'
                        ELSE D.[country_name]
                END AS [country_name]
                ,D.[country_code]
                ,D.[country_id]
                ,D.[year]
                ,D.[value]
        FROM [World_Data_Atlas].[worldbank].[data] as D
        LEFT JOIN worldbank.entities ENT ON D.[country_id] = ENT.iso2_code AND D.[country_code] = ENT.[wb_id]
        WHERE indicator_code = 'SH.XPD.CHEX.GD.ZS' AND ENT.is_country = 1 AND D.[year] = 2023
        ORDER BY D.[value] DESC
        """

# ============================================================

engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
fallers = df.sort_values(CHANGE_COL,ascending=False).head(TOP_N)
climbers = df.sort_values(CHANGE_COL,ascending=True).head(TOP_N)
OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
FLAGS_DIR = BASE_DIR / "flags_png"
create_double_table_chart(
    left_data=fallers ,
    right_data=climbers,
    output_file=OUTPUT_FILE,
    title=TITLE,
    subtitle=SUBTITLE,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    left_panel_title=RIGHT_PANEL_TITLE,
    right_panel_title=LEFT_PANEL_TITLE ,
    label_col=LABEL_COL,
    flag_col=FLAG_COL,
    left_value_col=RIGHT_VALUE_ID ,
    right_value_col=LEFT_VALUE_ID,
    change_col=CHANGE_COL,
    top_n=TOP_N,
    decimal_places=2,
    left_value_prefix="#",
    right_value_prefix="#",
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
    flags_dir=FLAGS_DIR)