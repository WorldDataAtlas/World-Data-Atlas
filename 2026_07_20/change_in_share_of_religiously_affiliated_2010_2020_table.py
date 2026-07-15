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
🌍 The share of people affiliated with a religion changed markedly in some countries between 2010 and 2020. Where did it rise the most—and where did it decline the fastest?

Source: Pew Research Center | #WorldDataAtlas
"""


TOP_N = 10
FILE_NAME = "change_in_share_of_religiously_affiliated_2010_2020.png"
TITLE = "Change in Religious Affiliation"
SUBTITLE = "Top 10 increases and declines in the share of religiously affiliated people, 2010–2020"
FOOTER_LEFT = "Change in percentage points"
FOOTER_RIGHT = "Source: Pew Research Center | WorldDataAtlas"
LEFT_PANEL_TITLE = "Largest Increase"
RIGHT_PANEL_TITLE = "Largest Decline"
LABEL_COL = "country"
FLAG_COL = "iso2_code"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "believers_change_pp"

query = f"""
WITH country_data AS (
    SELECT
        country,
        [year],
        [population],
        christians + muslims + buddhists + hindus + jews + other_religions AS believers
    FROM [World_Data_Atlas].[pew].[global_religious_estimates]
    WHERE [level] = 1 AND [year] IN (2010, 2020)),
aggregated AS (
    SELECT
        CD.country,
        MAX(CASE WHEN CD.[year] = 2010 THEN CD.population END) AS population_2010,
        MAX(CASE WHEN CD.[year] = 2020 THEN CD.population END) AS population_2020,
        MAX(CASE WHEN CD.[year] = 2010 THEN CD.believers END) AS believers_2010,
        MAX(CASE WHEN CD.[year] = 2020 THEN CD.believers END) AS believers_2020
    FROM country_data AS CD
    GROUP BY CD.country)
SELECT
    EN.wb_id,
    EN.iso2_code,
    AG.country,
    AG.population_2010,
    AG.population_2020,
    AG.believers_2010,
    AG.believers_2020,
    AG.believers_2010 * 100.0 / NULLIF(AG.population_2010, 0) AS believers_pct_2010,
    AG.believers_2020 * 100.0 / NULLIF(AG.population_2020, 0) AS believers_pct_2020,
    (AG.believers_2020 * 100.0 / NULLIF(AG.population_2020, 0) - AG.believers_2010 * 100.0 / NULLIF(AG.population_2010, 0)) AS believers_change_pp
FROM aggregated AS AG
LEFT JOIN [World_Data_Atlas].[worldbank].[entities] AS EN ON LTRIM(RTRIM(LOWER(EN.[name]))) = LTRIM(RTRIM(LOWER(AG.country))) AND EN.is_country = 1
WHERE AG.population_2010 IS NOT NULL AND AG.population_2020 IS NOT NULL
ORDER BY believers_change_pp ASC;
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