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
🏥 How much of their economy do different regions devote to healthcare?

This chart compares health expenditure as a share of GDP across the European Union, the Arab World, Latin America & Caribbean, China and India.

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
WHERE [indicator_code] = 'SH.XPD.CHEX.GD.ZS' and [country_id] IN ('EU', '1A', 'XJ','CN','IN')
ORDER BY [year] DESC
        """

MAP_TITLE = "Current Health Expenditure"
MAP_SUBTITLE = "Share of GDP spent on healthcare"
MAP_SOURCE = "World Bank"
FILE_NAME = "health_expenditure_share_gdp_regions.png"
FOOTER_LEFT = "Current health expenditure (% of GDP)"
FOOTER_RIGHT = "Source: World Bank"
SERIES_COL = "country_id"
Y_LABEL = "Percent of GDP"
LEGEND_LOCATION = "upper left"

series_config = [   {"source_value": "EU", "label": "European Union", "color": "#60A5FA"},
                    {"source_value": "1A", "label": "Arab World", "color": "#F59E0B"},
                    {"source_value": "XJ", "label": "Latin America & Caribbean", "color": "#F472B6"},
                    {"source_value": "CN", "label": "China", "color": "#EF4444"},
                    {"source_value": "IN", "label": "India", "color": "#22C55E"}]

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