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
from graph_curve import create_multi_line_chart

# ============================================================

"""The demographic trauma of the post-Soviet transition is clearly visible in the 1990s. Since then, the Baltic states have pulled ahead, while Russia, Ukraine, the Caucasus, and Central Asia have followed markedly different paths."""


query = """
    SELECT
        CASE
            WHEN D.[location_name] = 'Russian Federation' THEN 'Russia'
            WHEN D.[location_name] = 'Republic of Moldova' THEN 'Moldova'
        ELSE [location_name] 
        END AS [location_name]
        ,D.[iso2_code]
        ,D.[iso3_code]
        ,D.[year]
        ,D.[value]
    FROM [World_Data_Atlas].[un].[data] AS D
    WHERE   D.[variant_id] = 4 AND 
            D.[sex_id] = 3 AND 
            D.[indicator_id] = 75 AND
            D.[age_id] = 223 AND
            D.[year] < 2027 AND D.[year] > 1964 AND
            D.[iso3_code] IN ('ARM','AZE','BLR','EST','GEO','KAZ','KGZ','LVA','LTU','MDA','RUS','TJK','TKM','UKR','UZB')
    ORDER BY D.[year] desc
        """
MAP_TITLE = 'Life expectancy in some of post-Soviet states'
MAP_SUBTITLE = '1965–2026, both sexes'
MAP_SOURCE = 'Source: United Nations World Population Prospects'
FILE_NAME = 'post_soviet_life_expectancy.png'
FOOTER_LEFT = 'Life expectancy at birth (years)'
FOOTER_RIGHT = 'UN medium variant'
Y_LABEL = 'Life expectancy (years)'
LEGEND_LOCATION = "lower right"
SERIES_COL = 'iso3_code'
series_config = [
    {"source_value": "RUS", "label": "Russia",      "color": "#2563EB"},
    {"source_value": "UKR", "label": "Ukraine",     "color": "#FACC15"},
    {"source_value": "EST", "label": "Estonia",     "color": "#06B6D4"},
    {"source_value": "AZE", "label": "Azerbaijan",  "color": "#14B8A6"},
    {"source_value": "GEO", "label": "Georgia",     "color": "#EF4444"},
    {"source_value": "TKM", "label": "Turkmenistan","color": "#15803D"},
]



# ============================================================

OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
df["year"] = df["year"].astype(int)
df["value"] = df["value"].astype(float)
create_multi_line_chart(
    df=df,
    output_file=OUTPUT_FILE,
    x_col="year",
    y_col="value",
    series_col=SERIES_COL,
    series_config=series_config,
    title=MAP_TITLE,
    subtitle=MAP_SUBTITLE,
    y_label=Y_LABEL,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    legend_location= LEGEND_LOCATION,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
)