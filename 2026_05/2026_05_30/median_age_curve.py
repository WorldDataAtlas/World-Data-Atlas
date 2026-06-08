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

query = """ 
SELECT [year], CAST([value] AS FLOAT) AS value, 'World' AS series
FROM [World_Data_Atlas].[un].[data]
WHERE [indicator_id] = 67 AND [variant_id] = 4 AND [sex_id] = 3 AND [location_name] = 'World' AND [value] IS NOT NULL
"""

MAP_TITLE = "Global Median Age"
MAP_SUBTITLE = "World, 1950–2035"
MAP_SOURCE = "Source: United Nations"
FILE_NAME = "median_age_curve.png"
FOOTER_LEFT = "Metric: Median age of the total population"
FOOTER_RIGHT = "Source: United Nations"
SERIES_COL = "series"
Y_LABEL = "Median age (years)"

series_config = [{"source_value": "World", "label": "World", "color": "#1EFF00"}]

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
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
)