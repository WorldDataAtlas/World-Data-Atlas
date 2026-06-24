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

"""The pandemic triggered a visible jump in health spending across much of the world.

Yet large regional differences persist.

Current health expenditure (% of GDP).

Source: World Bank

#Healthcare #COVID19 #Economics #DataViz"""


query = """
    SELECT D.[country_code]
        ,D.[country_id]
        ,D.[country_name]
        ,D.[indicator_code]
        ,D.[indicator_name]
        ,D.[year]
        ,D.[value]
        ,ENT.is_country
    FROM [World_Data_Atlas].[worldbank].[data] as D
    LEFT JOIN worldbank.entities ENT ON D.[country_id] = ENT.iso2_code AND D.[country_code] = ENT.[wb_id]
    WHERE indicator_code = 'SH.XPD.CHEX.GD.ZS' AND ENT.is_country = 0 AND 
    D.[country_name] IN ('World','European Union','North America','South Asia','Sub-Saharan Africa','Africa Eastern and Southern')
    ORDER BY D.[year] DESC
        """

MAP_TITLE = "Health Spending as Share of GDP"
MAP_SUBTITLE = "Current health expenditure in selected regions"
MAP_SOURCE = "World Bank"
FILE_NAME = "health_expenditure_share_gdp_regions.png"
FOOTER_LEFT = "Source: World Bank"
FOOTER_RIGHT = "WorldDataAtlas.com"
SERIES_COL = "country_name"
Y_LABEL = "Current health expenditure (% of GDP)"
LEGEND_LOCATION = "upper right"

series_config = [
    {"source_value": "World", "label": "World", "color": "#60A5FA"},
    {"source_value": "North America", "label": "North America", "color": "#F472B6"},
    {"source_value": "South Asia", "label": "South Asia", "color": "#22C55E"},
    {"source_value": "Sub-Saharan Africa", "label": "Sub-Saharan Africa", "color": "#F59E0B"},
    {"source_value": "Africa Eastern and Southern", "label": "Eastern & Southern Africa", "color": "#A78BFA"},
    {"source_value": "European Union", "label": "European Union", "color": "#4000FF"}
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
    marker_size=15,
    y_label=Y_LABEL,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    legend_location= LEGEND_LOCATION,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
)