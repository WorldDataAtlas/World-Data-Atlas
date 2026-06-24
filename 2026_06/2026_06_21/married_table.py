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
Where are women most likely to be married?

Top and bottom countries by the share of women aged 15–49 who are currently married or in union, 2025.

Source: United Nations

#Demography #DataViz
"""


TOP_N = 10
FILE_NAME = "currently_married_percent_2025_top_bottom.png"
TITLE = "Currently Married Women, 2025"
SUBTITLE = "Top and bottom countries by share of women aged 15–49 who are married or in union"
FOOTER_LEFT = "Source: UN Population Division"
FOOTER_RIGHT = "WorldDataAtlas.com"
LEFT_PANEL_TITLE = "Highest share"
RIGHT_PANEL_TITLE = "Lowest share"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"

LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None

CHANGE_COL = "value"

query = f"""
        SELECT 
                CASE
                WHEN D.location_name = 'Venezuela (Bolivarian Republic of)' THEN 'Venezuela'
                WHEN D.location_name = 'Iran (Islamic Republic of)' THEN 'Iran'
                WHEN D.location_name = 'Russian Federation' THEN 'Russia'
                WHEN D.location_name = 'United Arab Emirates' THEN 'UAE'
                WHEN D.location_name = 'United States of America' THEN 'USA'
                WHEN D.location_name = 'Bolivia (Plurinational State of)' THEN 'Bolivia'
                WHEN D.location_name = 'Micronesia (Fed. States of)' THEN 'Micronesia'
                WHEN D.location_name = 'Solomon Islands' THEN 'Solomon Isls'
                WHEN D.location_name = 'United Republic of Tanzania' THEN 'Tanzania'
                WHEN D.location_name = 'Lao People''s Democratic Republic' THEN 'Laos'
                WHEN D.location_name = 'Republic of Moldova' THEN 'Moldova'
                WHEN D.location_name = 'Dem. People''s Rep. of Korea' THEN 'North Korea'
                WHEN D.location_name = 'Northern Mariana Islands' THEN 'North Korea'
                ELSE D.location_name
                END AS location_name
        ,D.[iso2_code]
        ,D.[iso3_code]
        ,D.[indicator_id]
        ,D.[indicator_name]
        ,D.[year]
        ,D.[value]
        FROM [World_Data_Atlas].[un].[data] as D
        LEFT JOIN worldbank.entities ENT ON D.iso2_code = ENT.iso2_code AND D.iso3_code = ENT.[wb_id]
        WHERE indicator_id = 42 and [variant_id] = 4 and ENT.is_country = 1 and D.[year] = 2025 and D.[iso2_code] not in ('MP')
        ORDER BY D.[value]

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