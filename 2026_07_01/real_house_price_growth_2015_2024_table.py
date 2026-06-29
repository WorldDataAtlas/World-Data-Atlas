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

"""House prices don't tell the whole story.

After adjusting for inflation, real house price growth since 2015 varies widely across selected OECD and partner economies—from nearly doubling to outright declines.

Sources: OECD + World Bank

#Housing #RealEstate #Inflation #Economics"""


TOP_N = 15
FILE_NAME = "real_house_price_growth_2015_2024.png"
TITLE = "Real House Price Growth Since 2015"
SUBTITLE = "Top and bottom countries by residential property price growth after adjusting for inflation"
FOOTER_LEFT = "Sources: OECD + World Bank"
FOOTER_RIGHT = "WorldDataAtlas.com"
LEFT_PANEL_TITLE = "Lowest growth"
RIGHT_PANEL_TITLE = "Highest growth"
LABEL_COL = "wb_country_name"
FLAG_COL = "iso2_code"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "real_house_price_growth"

query = f"""
WITH house_prices AS (
    SELECT
        d.ref_area_name,
        TRY_CAST(d.time_period AS int) AS time_period,
        d.obs_value AS house_price_index,
        d.REF_AREA AS iso3_code
    FROM oecd.data d
    WHERE d.dataflow_name = 'National and regional house price indices'
      AND d.indicator_name = 'House price index'
      AND d.unit_name = 'Index'
      AND d.transformation_name = 'Not applicable'
      AND d.FREQ = 'A'
      AND d.ADJUSTMENT = 'N'
      AND JSON_VALUE(d.dimensions_json, '$."BASE_PER"') = '2015.0'
      AND TRY_CAST(d.time_period AS int) = 2024
      AND JSON_VALUE(d.dimensions_json, '$."VINTAGE"') = '_T'
      AND JSON_VALUE(d.dimensions_json, '$."DWELLINGS"') = '_T'
      AND JSON_VALUE(d.dimensions_json, '$."REF_AREA_TYPE"') = 'COU'
      AND d.ref_area_name NOT IN ('Euro area (20 countries)','EU-27','Ireland excluding Dublin')
),
inflation AS (
    SELECT
        D.country_name,
        D.country_id AS iso2_code,
        D.country_code AS iso3_code,
        (EXP(SUM(LOG(1 + D.value / 100.0))) - 1) * 100 AS cumulative_inflation
    FROM World_Data_Atlas.worldbank.data AS D
    WHERE D.indicator_code = 'FP.CPI.TOTL.ZG'
      AND D.year BETWEEN 2015 AND 2024
      AND D.country_code IN ('FIN','ITA','CHN','FRA','BRA','SWE','JPN','BEL','DNK','GBR','DEU','IND','NOR','ROU','ESP','ISR','LUX','AUT',
                             'NZL','SVK','IRL','NLD','HRV','LVA','SVN','CHL','MEX','POL','EST','BGR','CZE','PRT','LTU','ISL','HUN','TUR')
      AND D.[value] IS NOT NULL
    GROUP BY D.country_name, D.country_id, D.country_code
    HAVING COUNT(DISTINCT D.[year]) = 10)

SELECT
    inf.country_name AS wb_country_name,
    inf.iso2_code,
    hp.iso3_code,
    ROUND(hp.house_price_index,2) AS house_price_index,
    ROUND(hp.house_price_index - 100,2) AS nominal_house_price_growth,
    ROUND(inf.cumulative_inflation,2) AS cumulative_inflation,
    ROUND((((hp.house_price_index / 100.0) / (1 + inf.cumulative_inflation / 100.0)) - 1) * 100,2) AS real_house_price_growth
FROM house_prices hp
INNER JOIN inflation inf ON hp.iso3_code = inf.iso3_code
ORDER BY real_house_price_growth DESC;
        """

# ============================================================

engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
climbers = df.sort_values(CHANGE_COL,ascending=True).head(TOP_N)
fallers = df.sort_values(CHANGE_COL,ascending=False).head(TOP_N)
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