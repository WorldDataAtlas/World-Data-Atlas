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

TOP_N = 10
FILE_NAME = "gdp_rank_change_1990_2024.png"

TITLE="How the Global Wealth Rankings Changed"
SUBTITLE=f"GDP per capita ranking, 1990 → 2024"
FOOTER_LEFT="Metric: GDP per capita, current US$ · Ranking among countries with available World Bank data"
FOOTER_RIGHT="Source: World Bank"
LEFT_PANEL_TITLE="Biggest Climbers"
RIGHT_PANEL_TITLE="Biggest Fallers"
LABEL_COL="country_name"
FLAG_COL="country_id"
LEFT_VALUE_ID="rank_1990"
RIGHT_VALUE_ID="rank_2024"
CHANGE_COL="rank_change"

query = """
    WITH ranked_data AS (
        SELECT
            D.[country_code],
            D.[country_id],
            D.[country_name],
            D.[year],
            CAST(D.[value] AS FLOAT) AS gdp_per_capita,
            RANK() OVER (PARTITION BY D.[year] ORDER BY D.[value] DESC) AS gdp_rank
        FROM [World_Data_Atlas].[worldbank].[data] AS D
        LEFT JOIN (
            SELECT
                [wb_id],
                [iso2_code],
                [name],
                [is_country]
            FROM [World_Data_Atlas].[worldbank].[entities]
            WHERE [is_country] = 1) AS ENT ON ENT.[name] = D.[country_name]
        WHERE D.[indicator_code] = 'NY.GDP.PCAP.CD' AND ENT.[is_country] = 1 AND D.[year] IN (1990, 2024) AND D.[value] IS NOT NULL),
    pivoted AS (    SELECT
                        [country_code],
                        [country_id],
                        [country_name],
                        MAX(CASE WHEN [year] = 1990 THEN gdp_rank END) AS rank_1990,
                        MAX(CASE WHEN [year] = 2024 THEN gdp_rank END) AS rank_2024
                    FROM ranked_data
                    GROUP BY [country_code], [country_id], [country_name]),
    rank_changes AS (    SELECT
                            [country_code],
                            [country_id],
                            [country_name],
                            rank_1990,
                            rank_2024,
                            rank_1990 - rank_2024 AS rank_change
                        FROM pivoted
                        WHERE rank_1990 IS NOT NULL AND rank_2024 IS NOT NULL)

    SELECT *
    FROM (  SELECT TOP (10) *
            FROM rank_changes
            ORDER BY rank_change DESC) AS climbers
    UNION ALL
    SELECT *
    FROM (  SELECT TOP (10) *
            FROM rank_changes
            ORDER BY rank_change ASC) AS fallers;"""

engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
climbers = df[df["rank_change"] > 0].sort_values("rank_change",ascending=False)
fallers = df[df["rank_change"] < 0].sort_values("rank_change",ascending=True)

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
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
    flags_dir=FLAGS_DIR)