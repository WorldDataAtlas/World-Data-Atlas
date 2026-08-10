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
💳 How has government debt evolved across different economies?

This chart compares central government debt as a share of GDP in the United States, Switzerland, Ukraine and Latin America & the Caribbean.

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
WHERE [indicator_code] = 'GC.DOD.TOTL.GD.ZS' AND [country_code] IN ('USA','CHE','LCN','UKR')
ORDER BY [year] DESC
        """

MAP_TITLE = "Central Government Debt"
MAP_SUBTITLE = "Central government debt as a share of GDP"
MAP_SOURCE = "World Bank"
FILE_NAME = "central_government_debt_gdp.png"
FOOTER_LEFT = "Central government debt (% of GDP)"
FOOTER_RIGHT = "Source: World Bank"
SERIES_COL = "country_code"
Y_LABEL = "Percent of GDP"
LEGEND_LOCATION = "upper left"

series_config = [   {"source_value": "USA", "label": "United States", "color": "#60A5FA"},
                    {"source_value": "CHE", "label": "Switzerland", "color": "#22C55E"},
                    {"source_value": "LCN", "label": "Latin America & Caribbean", "color": "#F59E0B"},
                    {"source_value": "UKR", "label": "Ukraine", "color": "#F472B6"}]

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