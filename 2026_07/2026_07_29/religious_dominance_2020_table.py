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
🌍 Which countries are the most religiously homogeneous—and which are the most diverse?

Share of the population belonging to the country’s largest religious or unaffiliated group.

Source: Pew Research Center | #WorldDataAtlas
"""


TOP_N = 10
FILE_NAME = "religious_dominance_2020.png"
TITLE = "Religious Dominance"
SUBTITLE = "Top 10 and Bottom 10 countries by the share of the largest religious or unaffiliated group, 2020"
FOOTER_LEFT = "Share of population represented by the largest group (%)"
FOOTER_RIGHT = "Source: Pew Research Center"
LEFT_PANEL_TITLE = "Most Dominated"
RIGHT_PANEL_TITLE = "Most Diverse"
LABEL_COL = "country"
FLAG_COL = "country_code"
LEFT_VALUE_ID = "largest_group"
RIGHT_VALUE_ID = None
CHANGE_COL = "largest_group_pct"

query = f"""
        SELECT
                EN.iso2_code AS country_code,
                AG.country,
                ROUND(
                        (
                        SELECT MAX(v)
                        FROM (VALUES (AG.christians),(AG.muslims),(AG.hindus),(AG.buddhists),(AG.jews),(AG.other_religions),(AG.religiously_unaffiliated)
                        ) t(v)) * 100.0 / AG.population,2) AS largest_group_pct,
                CASE
                        WHEN AG.christians = (
                        SELECT MAX(v)
                        FROM (VALUES
                                (AG.christians),(AG.muslims),(AG.hindus),
                                (AG.buddhists),(AG.jews),
                                (AG.other_religions),(AG.religiously_unaffiliated)
                        ) t(v)
                        ) THEN 'Christianity'
                        WHEN AG.muslims = (
                        SELECT MAX(v)
                        FROM (VALUES
                                (AG.christians),(AG.muslims),(AG.hindus),
                                (AG.buddhists),(AG.jews),
                                (AG.other_religions),(AG.religiously_unaffiliated)
                        ) t(v)
                        ) THEN 'Islam'
                        WHEN AG.hindus = (
                        SELECT MAX(v)
                        FROM (VALUES
                                (AG.christians),(AG.muslims),(AG.hindus),
                                (AG.buddhists),(AG.jews),
                                (AG.other_religions),(AG.religiously_unaffiliated)
                        ) t(v)
                        ) THEN 'Hinduism'
                        WHEN AG.buddhists = (
                        SELECT MAX(v)
                        FROM (VALUES
                                (AG.christians),(AG.muslims),(AG.hindus),
                                (AG.buddhists),(AG.jews),
                                (AG.other_religions),(AG.religiously_unaffiliated)
                        ) t(v)
                        ) THEN 'Buddhism'
                        WHEN AG.jews = (
                        SELECT MAX(v)
                        FROM (VALUES
                                (AG.christians),(AG.muslims),(AG.hindus),
                                (AG.buddhists),(AG.jews),
                                (AG.other_religions),(AG.religiously_unaffiliated)
                        ) t(v)
                        ) THEN 'Judaism'
                        WHEN AG.other_religions = (
                        SELECT MAX(v)
                        FROM (VALUES
                                (AG.christians),(AG.muslims),(AG.hindus),
                                (AG.buddhists),(AG.jews),
                                (AG.other_religions),(AG.religiously_unaffiliated)
                        ) t(v)
                        ) THEN 'Other religions'
                        ELSE 'Religiously unaffiliated'
                END AS largest_group
        FROM pew.global_religious_estimates AG
        LEFT JOIN worldbank.entities EN ON LOWER(LTRIM(RTRIM(EN.name))) = LOWER(LTRIM(RTRIM(AG.country)))
        WHERE AG.level = 1 AND AG.year = 2020 AND EN.is_country = 1;
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