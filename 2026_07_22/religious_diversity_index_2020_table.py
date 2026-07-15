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
🌍 Which countries are the most religiously diverse?

This ranking uses the Simpson Diversity Index to measure how evenly different religious groups are represented in each country.

Source: Pew Research Center | #WorldDataAtlas
"""



TOP_N = 10
FILE_NAME = "religious_diversity_index_2020.png"
TITLE = "Religious Diversity Index"
SUBTITLE = "Top 10 and Bottom 10 countries by religious diversity, 2020"
FOOTER_LEFT = "Simpson Diversity Index (0–100)"
FOOTER_RIGHT = "Source: Pew Research Center"
LEFT_PANEL_TITLE = "Most Diverse"
RIGHT_PANEL_TITLE = "Least Diverse"
LABEL_COL = "country"
FLAG_COL = "country_code"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "religious_diversity_index"

query = f"""
WITH religion_shares AS (
SELECT
    EN.iso2_code AS country_code,
    country,
    [population],
    christians * 1.0 / NULLIF([population], 0) AS christian_share,
    muslims * 1.0 / NULLIF([population], 0) AS muslim_share,
    religiously_unaffiliated * 1.0/ NULLIF([population], 0) AS unaffiliated_share,
    buddhists * 1.0 / NULLIF([population], 0) AS buddhist_share,
    hindus * 1.0 / NULLIF([population], 0) AS hindu_share,
    jews * 1.0 / NULLIF([population], 0) AS jewish_share,
    other_religions * 1.0 / NULLIF([population], 0) AS other_share
FROM [World_Data_Atlas].[pew].[global_religious_estimates] AS AG
LEFT JOIN [World_Data_Atlas].[worldbank].[entities] AS EN ON LTRIM(RTRIM(LOWER(EN.[name]))) = LTRIM(RTRIM(LOWER(AG.country))) AND EN.is_country = 1
WHERE [level] = 1 AND [year] = 2020 AND [population] > 0)

SELECT
    country_code,
    country,
    ROUND(
        (1 - POWER(christian_share, 2) - POWER(muslim_share, 2) - POWER(unaffiliated_share, 2)
            - POWER(buddhist_share, 2) - POWER(hindu_share, 2) - POWER(jewish_share, 2) - POWER(other_share, 2)) * 100,
        2) AS religious_diversity_index,
    ROUND(christian_share * 100, 2) AS christians_pct,
    ROUND(muslim_share * 100, 2) AS muslims_pct,
    ROUND(unaffiliated_share * 100, 2) AS unaffiliated_pct,
    ROUND(buddhist_share * 100, 2) AS buddhists_pct,
    ROUND(hindu_share * 100, 2) AS hindus_pct,
    ROUND(jewish_share * 100, 2) AS jews_pct,
    ROUND(other_share * 100, 2) AS other_religions_pct
FROM religion_shares
ORDER BY religious_diversity_index DESC;
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