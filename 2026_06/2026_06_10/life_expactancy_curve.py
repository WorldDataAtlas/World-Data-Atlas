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

"""Life expectancy has risen dramatically across the world over the past 75 years.

But what caught my attention are the sudden dips visible in several regions.

Do you know what caused these sharp declines around the early 1960s, mid-1990s, and 2020?

Data: UN World Population Prospects

#DataViz #Demographics #LifeExpectancy #Statistics #Population
"""

query = """
    SELECT
        D.[location_name]
        ,D.[iso2_code]
        ,D.[year]
        ,D.[value]
        ,[indicator_name]
    FROM [World_Data_Atlas].[un].[data] AS D
    WHERE   D.[variant_id] = 4 AND 
            D.[sex_id] = 3 AND 
            D.[indicator_id] = 75 AND
            D.[age_id] = 223 AND 
            D.[iso2_code] IN ('1W','A9','EP','RD','DR','XU')
    ORDER BY D.[value] desc
        """

MAP_TITLE = "Life Expectancy Around the World"
MAP_SUBTITLE = "World and major regions, 1950–2035"
MAP_SOURCE = "Source: UN World Population Prospects"
FILE_NAME = "life_expectancy_world_regions_1950_2035.png"
FOOTER_LEFT = "Life expectancy at birth, both sexes"
FOOTER_RIGHT = "Source: UN World Population Prospects"
SERIES_COL = "iso2_code"
Y_LABEL = "Life expectancy at birth, years"
LEGEND_LOCATION = "lower right"

series_config = [
    {"source_value": "1W", "label": "World", "color": "#FFFFFF"},
    {"source_value": "A9", "label": "Africa", "color": "#F472B6"},
    {"source_value": "EP", "label": "Europe", "color": "#22C55E"},
    {"source_value": "RD", "label": "Developed regions", "color": "#0B17F5"},
    {"source_value": "DR", "label": "Developing regions", "color": "#F50B0B"},
    {"source_value": "XU", "label": "Northern America", "color": "#F2FF00"},   
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