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

"""
Not all post-communist EU countries have converged at the same pace.

GDP per capita (PPP, constant 2021 international $) still varies considerably across the region.

Source: World Bank

#Economics #EU #DataViz #WorldDataAtlas
"""


query = """
SELECT  AA.[country_code],
        AA.[country_id],
        AA.[country_name],
        AA.[year],
        AA.[value]
FROM [World_Data_Atlas].[worldbank].[data] AS AA
LEFT JOIN worldbank.entities ENT ON AA.[country_id] = ENT.iso2_code AND AA.[country_code] = ENT.[wb_id]
WHERE AA.[indicator_code] = 'NY.GDP.PCAP.PP.KD'
        and AA.[country_name] in ('Croatia','Slovenia','Czechia','Bulgaria','Poland','Romania','Hungary','Slovak Republic','Estonia','Latvia','Lithuania')
        """

MAP_TITLE = "GDP per Capita in Post-Communist EU Countries"
MAP_SUBTITLE = "GDP per capita, PPP"
MAP_SOURCE = "Source: World Bank"
FILE_NAME = "gdp_ppp_post_communist_eu.png"
FOOTER_LEFT = "Indicator: GDP per capita, PPP (constant international $)"
FOOTER_RIGHT = "Source: World Bank"
SERIES_COL = "country_code"
Y_LABEL = "GDP per capita, PPP"
LEGEND_LOCATION = "upper left"

series_config = [
    {"source_value": "SVN", "label": "Slovenia", "color": "#1100FF"},
    {"source_value": "CZE", "label": "Czechia", "color": "#00FFE1"},
    {"source_value": "EST", "label": "Estonia", "color": "#0DFF00"},
    {"source_value": "LTU", "label": "Lithuania", "color": "#AFB55C"},
    {"source_value": "POL", "label": "Poland", "color": "#FFFFFF"},
    {"source_value": "LVA", "label": "Latvia", "color": "#FF0000"},
    {"source_value": "HRV", "label": "Croatia", "color": "#1E0A0A"},
    {"source_value": "HUN", "label": "Hungary", "color": "#FFA200"},
    {"source_value": "ROU", "label": "Romania", "color": "#693709"},
    {"source_value": "SVK", "label": "Slovakia", "color": "#DD00FF"},
    {"source_value": "BGR", "label": "Bulgaria", "color": "#A0A0A0"},
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