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
🌍 Where do the most people have no religious affiliation?

This ranking shows the countries with the highest and lowest shares of people identifying with no religion in 2020.

Source: Pew Research Center | #WorldDataAtlas
"""


TOP_N = 10
FILE_NAME = ".png"

TOP_N = 10
FILE_NAME = "religiously_unaffiliated_share_2020.png"
TITLE = "Religiously Unaffiliated Population"
SUBTITLE = "Top 10 and Bottom 10 countries by share of the population with no religious affiliation, 2020"
FOOTER_LEFT = "Share of total population (%)"
FOOTER_RIGHT = "Source: Pew Research Center"
LEFT_PANEL_TITLE = "Highest Share"
RIGHT_PANEL_TITLE = "Lowest Share"
LABEL_COL = "country"
FLAG_COL = "country_code"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "unaffiliated_pct"

query = f"""
WITH unaffiliated AS (
    SELECT
        EN.iso2_code AS country_code,
        AG.country,
        AG.population,
        AG.religiously_unaffiliated,
        ROUND(AG.religiously_unaffiliated * 100.0 / NULLIF(AG.population, 0), 2) AS unaffiliated_pct
    FROM [World_Data_Atlas].[pew].[global_religious_estimates] AS AG
    LEFT JOIN [World_Data_Atlas].[worldbank].[entities] AS EN ON LTRIM(RTRIM(LOWER(EN.name))) = LTRIM(RTRIM(LOWER(AG.country))) AND EN.is_country = 1
    WHERE AG.level = 1 AND AG.year = 2020 AND AG.population > 0)

SELECT
    country_code,
    country,
    population,
    religiously_unaffiliated,
    unaffiliated_pct
FROM unaffiliated
ORDER BY unaffiliated_pct DESC;
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