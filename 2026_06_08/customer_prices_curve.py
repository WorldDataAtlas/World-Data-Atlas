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


"""The EU isn't one inflation story.

Since 1996, consumer prices have followed very different paths across Europe's five largest economies. Poland stands out.

Romania would be off the chart entirely: 4,924 (1996 = 100) by 2025.

Source: IMF HICP

#Economics #Inflation #EU #Europe #DataViz
"""

query = """
WITH base AS (
    SELECT country, [value] AS base_value
    FROM imf.[data]
    WHERE dataflow_id = 'CPI' AND index_type = 'HICP' AND coicop_1999 = '_T' AND type_of_transformation = 'IX'
      AND [frequency] = 'A' AND [year] = 1996 AND country IN ('DEU','FRA','ITA','ESP','POL'))

SELECT d.country, d.[year], 100.0 * d.[value] / b.base_value AS [value]
FROM imf.[data] d
JOIN base b ON d.country = b.country
WHERE d.dataflow_id = 'CPI' AND d.index_type = 'HICP' AND d.coicop_1999 = '_T' AND d.type_of_transformation = 'IX'
  AND d.[frequency] = 'A' AND d.country IN ('DEU','FRA','ITA','ESP','POL')
ORDER BY d.country, d.[year];
"""

MAP_TITLE = "Consumer Prices in Europe's Largest Economies"
MAP_SUBTITLE = "Germany, France, Italy, Spain and Poland (1996 = 100)"
MAP_SOURCE = "Source: IMF HICP"
FILE_NAME = "hicp_prices_largest_eu_economies_1996_base.png"
FOOTER_LEFT = "HICP all-items index, rebased to 1996 = 100"
FOOTER_RIGHT = "Source: IMF, author's calculations"
SERIES_COL = "country"
Y_LABEL = "Price level index (1996 = 100)"
LEGEND_LOCATION = "upper left"

series_config = [
    {"source_value": "DEU", "label": "Germany", "color": "#2563EB"},
    {"source_value": "FRA", "label": "France", "color": "#16A34A"},
    {"source_value": "ITA", "label": "Italy", "color": "#F59E0B"},
    {"source_value": "ESP", "label": "Spain", "color": "#A855F7"},
    {"source_value": "POL", "label": "Poland", "color": "#DC2626"},
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