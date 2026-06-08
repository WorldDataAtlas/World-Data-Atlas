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

query = """     SELECT  MED.[iso3_code] AS [country_id] ,
                        [name] as [country_name],
                        ROUND(MED.[value], 1) AS [median_age],
                        ROUND(FER.[value], 2) AS [fertility]
                FROM [World_Data_Atlas].[un].[data] as MED
                LEFT JOIN (     SELECT [wb_id],[iso2_code],[name],[is_country]
                                FROM [World_Data_Atlas].[worldbank].[entities]
                                WHERE [is_country] = 1) AS ENT ON ENT.[iso2_code] = MED.[iso2_code]
                LEFT JOIN (     SELECT  [iso3_code], [value]
                                FROM [World_Data_Atlas].[un].[data] as FER
                                WHERE [indicator_id] = 19 AND [variant_id] = 4 AND [year] = 2025) AS FER ON FER.[iso3_code] = MED.[iso3_code]
                WHERE ENT.[is_country] = 1 and MED.[indicator_id] = 67 AND MED.[variant_id] = 4 AND MED.[sex_id] = 3 and MED.[year] = 2025
        """

FILE_NAME = "median_age_vs_fertility_2025.png"
X_COL = "median_age"
Y_COL = "fertility"
MAP_TITLE = "Median Age vs Fertility"
MAP_SUBTITLE = "Countries, 2025"
X_LABEL = "Median age (years)"
Y_LABEL = "Fertility rate (births per woman)"
FOOTER_LEFT = "Each dot represents one country"
FOOTER_RIGHT = "Source: United Nations"
POINT_COLOR = "#D4FF00"
SHOW_LABELS = False
X_LOG = False
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
    show_labels=SHOW_LABELS,
    point_color=POINT_COLOR)