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

"""Qatar has only ~40 women per 100 men.

Latvia has ~116.

The difference isn't biology—it's migration.

Source: UN Population Data

#Demography #Population #DataViz
"""

TOP_N = 10
FILE_NAME = "women_per_man_top_bottom_2025.png"
TITLE = "Gender Imbalance by Country"
SUBTITLE = "Women per man, 2025"
FOOTER_LEFT = "Indicator: UN total population by sex"
FOOTER_RIGHT = "Source: UN Population Data"
LEFT_PANEL_TITLE = "Most women per man"
RIGHT_PANEL_TITLE = "Fewest women per man"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"
LEFT_VALUE_ID = None
RIGHT_VALUE_ID = None
CHANGE_COL = "women_per_man"

query = f"""
        WITH pop AS (
                SELECT
                        D.location_name,
                        D.iso2_code,
                        D.sex_id,
                        D.[value]
                FROM un.[data] D
                LEFT JOIN ( SELECT is_country, [name] FROM worldbank.entities) ENT ON ENT.[name] = D.[location_name]
                WHERE D.indicator_id = 49 AND D.[year] = 2025 AND D.variant_id = 4 AND ENT.is_country = 1 AND D.sex_id IN (1,2))
        SELECT
                location_name,
                iso2_code,
                MAX(CASE WHEN sex_id = 2 THEN [value] END) AS females,
                MAX(CASE WHEN sex_id = 1 THEN [value] END) AS males,
                CAST(MAX(CASE WHEN sex_id = 2 THEN [value] END) / NULLIF(MAX(CASE WHEN sex_id = 1 THEN [value] END),0) AS DECIMAL(10,4)) AS women_per_man
        FROM pop
        GROUP BY location_name, iso2_code
        HAVING MAX(CASE WHEN sex_id = 1 THEN [value] END) IS NOT NULL AND MAX(CASE WHEN sex_id = 2 THEN [value] END) IS NOT NULL
        ORDER BY women_per_man DESC;
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