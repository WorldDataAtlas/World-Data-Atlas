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
Unemployment rates vary widely across the world.

In 2024, some economies are operating close to full employment, while others continue to struggle with persistent labor market challenges.

Lowest and highest unemployment rates according to the IMF World Economic Outlook.

Source: IMF WEO

#Economics #Unemployment #LaborMarket #DataViz
"""



TOP_N = 10
FILE_NAME = ".png"

TOP_N = 10
FILE_NAME = "unemployment_rate_2024_top_bottom.png"

TITLE = "Unemployment Rate, 2024"
SUBTITLE = "Top and bottom countries by unemployment rate"
FOOTER_LEFT = "Source: IMF World Economic Outlook (WEO)"
FOOTER_RIGHT = "WorldDataAtlas"
LEFT_PANEL_TITLE = "Lowest unemployment"
RIGHT_PANEL_TITLE = "Highest unemployment"
LABEL_COL = "COUNTRY_NAME"
FLAG_COL = "COUNTRY_ID"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "value"

query = f"""
        SELECT  A.[COUNTRY],
                A.[COUNTRY_ID],
                CASE 
                WHEN A.[COUNTRY_NAME] = 'Macao Special Administrative Region, People''s Republic of China' THEN 'Macao'
                WHEN A.[COUNTRY_NAME] = 'Andorra, Principality of' THEN 'Andorra'
                WHEN A.[COUNTRY_NAME] = 'North Macedonia, Republic of' THEN 'North Macedonia'
                WHEN A.[COUNTRY_NAME] = 'Armenia, Republic of' THEN 'Armenia'
                ELSE A.[COUNTRY_NAME]
                END AS [COUNTRY_NAME],
                A.[year],
                A.[value]
        FROM (
        SELECT
                E.iso2_code AS [COUNTRY_ID],
                d.[country] AS [COUNTRY],
                [COUNTRY_codes].code_name AS [COUNTRY_NAME],
                d.[year],
                CAST(ROUND(d.[value], 2) AS DECIMAL(10,2)) AS [value]
        FROM imf.data d
        LEFT JOIN worldbank.entities E ON d.[country] = E.wb_id
        LEFT JOIN imf.api_dataflows f ON f.dataflow_id = d.dataflow_id
        LEFT JOIN imf.indicator_names i ON i.code_id = d.indicator
        LEFT JOIN imf.api_dimension_codes [COUNTRY_codes] ON [COUNTRY_codes].code_id = d.[country] AND [COUNTRY_codes].codelist_id = 'CL_WEO_COUNTRY'
        WHERE d.dataflow_id = 'WEO' AND d.indicator = 'LUR' and d.[year] = 2024 and d.[frequency] = 'A') AS A
        GROUP BY A.[COUNTRY], A.[COUNTRY_NAME], A.[year], A.[value], A.[COUNTRY_ID]
        ORDER BY [value]
        """

# ============================================================

engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
lowest = df.sort_values(CHANGE_COL, ascending=True).head(TOP_N)
highest = df.sort_values(CHANGE_COL, ascending=False).head(TOP_N)
OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
FLAGS_DIR = BASE_DIR / "flags_png"
create_double_table_chart(
    left_data=lowest,
    right_data=highest,
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