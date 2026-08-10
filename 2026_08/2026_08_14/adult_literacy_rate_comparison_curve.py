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
📚 How has adult literacy changed over time?

This chart compares adult literacy rates in the Arab World, China, India and the world average.

Source: World Bank | #WorldDataAtlas
"""



query = """
SELECT [country_code]
      ,[country_id]
      ,CASE 
        WHEN [country_name] = 'Bolivia (Plurinational State of)' THEN 'Bolivia'
        WHEN [country_name] = 'Venezuela (Bolivarian Republic of)' THEN 'Venezuela'
        WHEN [country_name] = 'Central African Republic' THEN 'CAF'
     ELSE [country_name] END AS [country_name]
      ,[year]
      ,[value]
FROM [World_Data_Atlas].[worldbank].[data]
WHERE [indicator_code] = 'SE.ADT.LITR.ZS' and [country_id] in ('1A','IN','1W','CN')
ORDER BY [country_id] DESC
        """

MAP_TITLE = "Adult Literacy Rate"
MAP_SUBTITLE = "Arab World, World, India and China"
MAP_SOURCE = "World Bank"
FILE_NAME = "adult_literacy_rate_comparison.png"
FOOTER_LEFT = "Share of people aged 15+ who can read and write with understanding"
FOOTER_RIGHT = "Source: World Bank"
SERIES_COL = "country_id"
Y_LABEL = "Literacy rate (%)"
LEGEND_LOCATION = "lower right"

series_config = [   {"source_value": "1A", "label": "Arab World", "color": "#F59E0B"},
                    {"source_value": "1W", "label": "World", "color": "#F8FAFC"},
                    {"source_value": "IN", "label": "India", "color": "#22C55E"},
                    {"source_value": "CN", "label": "China", "color": "#60A5FA"}]

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