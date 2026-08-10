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
⚰️ Which countries have the highest and lowest crude death rates today?

This ranking compares the number of deaths per 1,000 people across countries in 2025. Remember that crude death rates are strongly influenced by a country's age structure, not just the quality of healthcare.

Source: United Nations | #WorldDataAtlas
"""

TOP_N = 10
FILE_NAME = "crude_death_rate_2025.png"
TITLE = "Crude Death Rate"
SUBTITLE = "Highest and lowest crude death rates by country, 2025"
FOOTER_LEFT = "Deaths per 1,000 population | Both sexes"
FOOTER_RIGHT = "Source: United Nations"
LEFT_PANEL_TITLE = "Lowest"
RIGHT_PANEL_TITLE = "Highest"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "value"

query = f"""
SELECT aa.[location_id]
      , CASE 
            WHEN aa.[location_name] = 'Bosnia and Herzegovina' THEN 'Bosn. and Herz.'
            WHEN aa.[location_name] = 'Republic of Moldova' THEN 'Moldova'
            WHEN aa.[location_name] = 'State of Palestine' THEN 'Palestine'
            WHEN aa.[location_name] = 'Iran (Islamic Republic of)' THEN 'Iran'
            WHEN aa.[location_name] = 'China, Hong Kong SAR' THEN 'Hong Kong'
            WHEN aa.[location_name] = 'China, Macao SAR' THEN 'Macao'
            WHEN aa.[location_name] = 'Dem. People''s Rep. of Korea' THEN 'North Korea'
            WHEN aa.[location_name] = 'Republic of Korea' THEN 'South Korea'
            WHEN aa.[location_name] = 'Central African Republic' THEN 'CAR'
            WHEN aa.[location_name] = 'Democratic Republic of the Congo' THEN 'DR Congo'
            WHEN aa.[location_name] = 'Bolivia (Plurinational State of)' THEN 'Bolivia'
            WHEN aa.[location_name] = 'Venezuela (Bolivarian Republic of)' THEN 'Venezuela'
            WHEN aa.[location_name] = 'Lao People''s Democratic Republic' THEN 'Laos'
            WHEN aa.[location_name] = 'Russian federation' THEN 'Russia'
            WHEN aa.[location_name] = 'United Arab Emirates' THEN 'UAE'
            WHEN aa.[location_name] = 'Syrian Arab Republic' THEN 'Syria'
        ELSE aa.[location_name]
        END AS [location_name]
      ,aa.[iso2_code]
      ,aa.[iso3_code]
      ,aa.[year]
      ,aa.[value]
FROM [World_Data_Atlas].[un].[data] as aa
LEFT JOIN worldbank.entities AS ENT ON AA.iso2_code = ENT.iso2_code
where aa.[indicator_id] = 59 and aa.[variant_id] = 4 and ENT.is_country = 1 and aa.[sex_id] = 3 and aa.[year] = 2025 and aa.[iso2_code] not in ('ST','VC','TC','MP','SX','AS','VG','XK','VI')
      
      """

# ============================================================

engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
fallers = df.sort_values(CHANGE_COL,ascending=False).head(TOP_N)
climbers= df.sort_values(CHANGE_COL,ascending=True).head(TOP_N)
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