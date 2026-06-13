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

"""One of the most important trends of the last 75 years:

Humanity moved from villages to cities.

World urbanization:
1950 → 29%
2025 → 58%
2035 → 61% (UN projection)

#Urbanization #Demography #DataViz #Economics"""


query = """
    SELECT *
    FROM (
        SELECT
            D.location_name,
            D.iso2_code,
            D.iso3_code,
            D.[year],
            ENT.is_country,
            MAX(CASE WHEN D.category_name = 'Rural' THEN D.[value] END) AS rural_pop,
            MAX(CASE WHEN D.category_name = 'Urban' THEN D.[value] END) AS urban_pop,
            MAX(CASE WHEN D.category_name = 'Total' THEN D.[value] END) AS total_pop,
            100.0 * MAX(CASE WHEN D.category_name = 'Urban' THEN D.[value] END) / NULLIF(MAX(CASE WHEN D.category_name = 'Total' THEN D.[value] END), 0) AS [value]
        FROM [World_Data_Atlas].[un].[data] AS D
        LEFT JOIN worldbank.entities ENT ON D.iso2_code = ENT.iso2_code AND D.iso3_code = ENT.[wb_id]
        WHERE D.indicator_id = 91 AND D.variant_id = 4 AND D.sex_id = 3
        AND D.iso2_code NOT IN ('FO','AS','CW','PR','TC','MP','GU','VI','BH','BM','KY','GI','HK','MO','KW','MC','NR','MF','SG','SX')
        GROUP BY D.location_name, D.iso2_code, D.iso3_code, D.[year], ENT.is_country
    ) AS AA
    WHERE AA.[value] IS NOT NULL AND iso2_code IN ('EP','AA','AJ','A9','XU','1W')
        """

MAP_TITLE = "Urbanization Around the World"
MAP_SUBTITLE = "Share of population living in urban areas by region"
MAP_SOURCE = "Source: UN World Population Prospects"
FILE_NAME = "urban_population_share_by_region.png"
FOOTER_LEFT = "Indicator: Urban population (% of total population)"
FOOTER_RIGHT = "Source: UN World Population Prospects"
SERIES_COL = "iso2_code"
Y_LABEL = "Urban population (%)"
LEGEND_LOCATION = "upper left"
series_config = [
    {"source_value": "1W", "label": "World",         "color": "#F8FAFC"},
    {"source_value": "A9", "label": "Africa",        "color": "#F97316"},
    {"source_value": "AA", "label": "Asia",          "color": "#22C55E"},
    {"source_value": "XU", "label": "North America", "color": "#60A5FA"},
    {"source_value": "AJ", "label": "South America", "color": "#F472B6"},
    {"source_value": "EP", "label": "Europe",        "color": "#A78BFA"},
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
    marker_size=0,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    legend_location= LEGEND_LOCATION,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
)