from pathlib import Path
import sys
import os
import pandas as pd
import sqlalchemy as sa
BASE_DIR = Path(__file__).resolve().parent
etl_path = (BASE_DIR.parent / "ETL").resolve()
sys.path.insert(0, str(etl_path))
import settings as s
module_path = (BASE_DIR.parent / "modules").resolve()
sys.path.insert(0, str(module_path))
from scatter_plot import create_scatter_chart

# ============================================================

query = """
SELECT D.[country_name],D.[year],D.[value] AS [GDP_PPP_pc],FER.[FERTILITY]
FROM [World_Data_Atlas].[worldbank].[data] AS D
LEFT JOIN ( SELECT [wb_id],[iso2_code],[name],[is_country]
            FROM [World_Data_Atlas].[worldbank].[entities]
            WHERE [is_country] = 1) AS ENT ON ENT.[name] = D.[country_name]
LEFT JOIN ( SELECT [country_code],[value] AS [FERTILITY], [year]
            FROM [World_Data_Atlas].[worldbank].[data]
            WHERE [indicator_code] = 'SP.DYN.TFRT.IN') AS FER ON FER.[country_code] = D.[country_code] AND D.[year] = FER.[year]
WHERE D.[indicator_code] = 'NY.GDP.PCAP.PP.KD' AND ENT.[name] IS NOT NULL AND FER.[FERTILITY] IS NOT NULL"""

FILE_NAME = "fertility_vs_gdp_ppp_pc_all_years_log"
X_COL = "GDP_PPP_pc"
Y_COL = "FERTILITY"
MAP_TITLE = "Fertility and Prosperity"
MAP_SUBTITLE = "Country-year observations since 1995"
X_LABEL = "GDP per capita, PPP (constant 2021 international $)"
Y_LABEL = "Fertility rate (births per woman)"
FOOTER_LEFT = "Metric: GDP per capita, PPP (constant 2021 international $) vs. fertility rate (births per woman) · Each point represents a country in a given year"
FOOTER_RIGHT = "Source: World Bank"
POINT_COLOR = "#00FF08"
SHOW_LABELS = True
COLOR_COL = "year"
POINT_EDGE_WIDTH = 0.05
POINT_SIZE = 7
X_LOG = True
Y_LOG = False

# ============================================================

OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
create_scatter_chart(
    df=df,
    output_file=OUTPUT_FILE,
    x_col=X_COL,
    y_col=Y_COL,
    title=MAP_TITLE,
    subtitle=MAP_SUBTITLE,
    x_label=X_LABEL,
    y_label=Y_LABEL,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..","Logos","4.png",)),
    x_log=X_LOG,
    y_log=Y_LOG,
    color_col=COLOR_COL,
    show_labels=SHOW_LABELS,
    point_edge_width=POINT_EDGE_WIDTH,
    point_size=POINT_SIZE,
    point_color=POINT_COLOR)