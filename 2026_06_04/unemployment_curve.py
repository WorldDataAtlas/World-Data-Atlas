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
    SELECT
        D.[year] as year, 
        D.[value] as value,
        C.code_name AS series
    FROM imf.[data] AS D
    LEFT JOIN imf.api_dimension_codes C ON D.country = C.code_id AND C.codelist_id = 'CL_ER_COUNTRY_PUB'
    WHERE D.dataflow_id = 'WEO' AND D.indicator = 'LUR' AND [value] IS NOT NULL AND C.code_name in ('G7','Euro Area (EA)','United States') AND D.[year]<2026
    ORDER BY D.[year]
        """

MAP_TITLE = "Unemployment Rate"
MAP_SUBTITLE = "G7, Euro Area and United States, 1980–2025"
MAP_SOURCE = "Source: IMF World Economic Outlook (WEO)"
FILE_NAME = "weo_unemployment_g7_euro_area_usa.png"
FOOTER_LEFT = "Indicator: LUR (Unemployment rate, % of labor force)"
FOOTER_RIGHT = "Data: IMF WEO"
SERIES_COL = "series"
Y_LABEL = "Unemployment rate (%)"

series_config = [
    {
        "source_value": "G7",
        "label": "G7",
        "color": "#60A5FA"
    },
    {
        "source_value": "Euro Area (EA)",
        "label": "Euro Area",
        "color": "#F472B6"
    },
    {
        "source_value": "United States",
        "label": "United States",
        "color": "#22C55E"
    }
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
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
)