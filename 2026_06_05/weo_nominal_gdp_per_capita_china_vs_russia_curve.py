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
        D.[year],
        D.[value],
        C.code_name AS series,
        D.country
    FROM imf.[data] D
    LEFT JOIN imf.api_dimension_codes C ON D.country = C.code_id AND C.codelist_id = 'CL_WEO_COUNTRY'
    WHERE D.dataflow_id = 'WEO'
    AND D.indicator = 'NGDPDPC'
    AND D.[value] IS NOT NULL
    AND D.country IN ('CHN', 'RUS')
    AND D.[year] BETWEEN 1992 AND 2031    
    """


"""In 1992, Russia's GDP per capita was far above China's.

By 2031, IMF projections suggest China will be ahead.

A remarkable reversal in less than four decades.

Source: IMF WEO

#Economics #China #DataViz #Russia
"""

MAP_TITLE = "China Is Catching Russia"
MAP_SUBTITLE = "Nominal GDP per Capita, 1992–2031 (IMF prediction included)"
MAP_SOURCE = "Source: IMF World Economic Outlook (WEO)"
FILE_NAME = "weo_nominal_gdp_per_capita_china_vs_russia_1992_2031.png"

FOOTER_LEFT = "Indicator: NGDPDPC (GDP per capita, current prices, U.S. dollars)"
FOOTER_RIGHT = "Data: IMF WEO"

SERIES_COL = "series"
Y_LABEL = "GDP per capita (current US$)"
LEGEND_LOCATION = "upper right"

series_config = [
    {
        "source_value": "China, People's Republic of",
        "label": "China",
        "color": "#EF4444"
    },
    {
        "source_value": "Russian Federation",
        "label": "Russian",
        "color": "#60A5FA"
    }]

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