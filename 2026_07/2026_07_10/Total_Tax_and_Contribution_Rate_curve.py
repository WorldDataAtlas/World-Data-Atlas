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
         AA.[id]
        ,AA.[country_code]
        ,AA.[country_id]
        ,AA.[country_name]
        ,AA.[indicator_name]
        ,AA.[year]
        ,AA.[value]
    FROM [World_Data_Atlas].[worldbank].[data] AS AA
    LEFT JOIN worldbank.entities AS ENT
        ON AA.[country_id] = ENT.[iso2_code]
        AND AA.[country_code] = ENT.[wb_id]
    WHERE AA.[indicator_code] = 'PAY.TAX.TOT.TAX.RT.ZS'
        AND ENT.[name] = AA.[country_name]
        AND ENT.[is_country] = 1
        AND AA.[country_name] IN (
            'United States',
            'France',
            'Germany',
            'United Kingdom',
            'China'
        )
    ORDER BY AA.[year], AA.[country_name]
"""

MAP_TITLE = "Total Tax and Contribution Rate"
MAP_SUBTITLE = "Selected countries, 2005–2019"
MAP_SOURCE = "Source: World Bank, Doing Business"
FILE_NAME = "total_tax_and_contribution_rate_selected_countries.png"

FOOTER_LEFT = "Total taxes and mandatory contributions paid by a standardized company"
FOOTER_RIGHT = "WorldDataAtlas"

SERIES_COL = "country_name"
Y_LABEL = "% of commercial profit"
LEGEND_LOCATION = "lower left"

series_config = [
    {
        "source_value": "United States",
        "label": "United States",
        "color": "#60A5FA"
    },
    {
        "source_value": "France",
        "label": "France",
        "color": "#F472B6"
    },
    {
        "source_value": "Germany",
        "label": "Germany",
        "color": "#22C55E"
    },
    {
        "source_value": "United Kingdom",
        "label": "United Kingdom",
        "color": "#F59E0B"
    },
    {
        "source_value": "China",
        "label": "China",
        "color": "#A78BFA"
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
    marker_size=15,
    y_label=Y_LABEL,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    legend_location= LEGEND_LOCATION,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
)