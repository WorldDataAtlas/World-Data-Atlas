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
The economic convergence of post-communist Europe is one of the biggest success stories of the past three decades.

While the gap with the rest of the EU remains, it has narrowed substantially since 1990.

Population-weighted GDP per capita (PPP), constant 2021 international $
"""


query = """
SELECT
    GDP.[year],
    CASE
        WHEN GDP.country_code IN ('BGR','HRV','CZE','EST','HUN','LVA','LTU','POL','ROU','SVK','SVN')
        THEN 'Post-communist EU'
        ELSE 'Other EU'
    END AS eu_group,
    SUM(GDP.[value] * POP.[value]) / SUM(POP.[value]) AS [value],
    SUM(POP.[value]) AS [population]
FROM worldbank.data GDP
INNER JOIN worldbank.data POP
    ON GDP.country_code = POP.country_code
   AND GDP.country_id = POP.country_id
   AND GDP.[year] = POP.[year]
   AND POP.indicator_code = 'SP.POP.TOTL'
WHERE GDP.indicator_code = 'NY.GDP.PCAP.PP.KD'
  AND GDP.country_code IN ('BGR','HRV','CZE','EST','HUN','LVA','LTU','POL','ROU','SVK','SVN',
        'AUT','BEL','CYP','DNK','FIN','FRA','DEU','GRC','IRL','ITA','LUX','MLT','NLD','PRT','ESP','SWE')
GROUP BY
    GDP.[year],
    CASE
        WHEN GDP.country_code IN ('BGR','HRV','CZE','EST','HUN','LVA','LTU','POL','ROU','SVK','SVN')
        THEN 'Post-communist EU'
        ELSE 'Other EU'
    END
ORDER BY GDP.[year], eu_group;
        """

MAP_TITLE = "Two Europes, One Long Catch-Up"
MAP_SUBTITLE = "Population-weighted GDP per capita, PPP, 1990–2024"
MAP_SOURCE = "Source: World Bank"
FILE_NAME = "post_communist_eu_vs_other_eu_gdp_ppp_weighted.png"
FOOTER_LEFT = "GDP per capita, PPP (constant 2021 international $), weighted by population"
FOOTER_RIGHT = "Source: World Bank"
SERIES_COL = "eu_group"
Y_LABEL = "GDP per capita, PPP"
LEGEND_LOCATION = "upper left"

series_config = [{"source_value": "Post-communist EU", "label": "Post-communist EU", "color": "#F472B6"},
                 {"source_value": "Other EU", "label": "Other EU", "color": "#60A5FA"}]

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