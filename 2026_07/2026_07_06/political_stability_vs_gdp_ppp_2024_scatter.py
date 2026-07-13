from pathlib import Path
import sys
import os
import pandas as pd
import sqlalchemy as sa
BASE_DIR = Path(__file__).resolve().parent
etl_path = (BASE_DIR.parent / "ETL").resolve()
sys.path.insert(0, str(etl_path))
import settings as s
module_path = (BASE_DIR.parent / "modules").resolve()
sys.path.insert(0, str(module_path))
from scatter_plot import create_scatter_chart

# ============================================================

"""
Wealthy countries tend to be more politically stable — but it's far from a rule.

Some countries achieve high incomes despite relatively low political stability, while others remain stable without becoming particularly wealthy.

Political stability vs GDP per capita (PPP), 2024.
"""


query = """
SELECT
 AA.[country_code]
,AA.[country_id]
,AA.[country_name]
,CASE
    WHEN AA.[country_code] IN (
        'DZA','AGO','BEN','BWA','BFA','BDI','CPV','CMR','CAF','TCD','COM','COG','COD','CIV','DJI','EGY',
        'GNQ','ERI','SWZ','ETH','GAB','GMB','GHA','GIN','GNB','KEN','LSO','LBR','LBY','MDG','MWI','MLI',
        'MRT','MUS','MAR','MOZ','NAM','NER','NGA','RWA','STP','SEN','SYC','SLE','SOM','ZAF','SSD','SDN',
        'TZA','TGO','TUN','UGA','ZMB','ZWE') THEN 'Africa'
    WHEN AA.[country_code] IN (
        'ALB','AND','AUT','BEL','BIH','BGR','BLR','CHE','CYP','CZE','DEU','DNK','ESP','EST','FIN','FRA',
        'GBR','GRC','HRV','HUN','IRL','ISL','ITA','LIE','LTU','LUX','LVA','MDA','MKD','MLT','MNE','NLD',
        'NOR','POL','PRT','ROU','RUS','SMR','SRB','SVK','SVN','SWE','UKR','MCO','XKX','IMN','GRL','GIB',
        'FRO','CHI') THEN 'Europe'
    WHEN AA.[country_code] IN (
        'AFG','ARE','ARM','AZE','BHR','BGD','BRN','BTN','CHN','GEO','HKG','IDN','IND','IRN','IRQ','ISR',
        'JOR','JPN','KAZ','KGZ','KHM','KOR','KWT','LAO','LBN','LKA','MAC','MDV','MMR','MNG','MYS','NPL',
        'OMN','PAK','PHL','QAT','SAU','SGP','SYR','THA','TJK','TKM','TLS','TUR','UZB','VNM','YEM','PSE',
        'NCL','PRK','MNP','GUM','ASM') THEN 'Asia'
    WHEN AA.[country_code] IN (
        'ARG','ATG','BHS','BLZ','BOL','BRA','BRB','CAN','CHL','COL','CRI','CUB','DMA','DOM','ECU','GRD',
        'GTM','GUY','HND','HTI','JAM','KNA','LCA','MEX','NIC','PAN','PER','PRY','SLV','SUR','TTO','URY',
        'USA','VCT','VEN','ABW','PRI','BMU','TCA','MAF','SXM','CYM','VGB','CUW','VIR') THEN 'Americas'
    WHEN AA.[country_code] IN (
        'AUS','FJI','FSM','KIR','MHL','NRU','NZL','PLW','PNG','SLB','TON','TUV','VUT','WSM','PYF') THEN 'Oceania'
    ELSE 'Other' END AS continent
,AA.[year]
,AA.[value] AS stability
,GDP.[year] AS gdp_year
,GDP.[value] AS gdp_ppp
FROM [World_Data_Atlas].[worldbank].[data] AS AA
LEFT JOIN worldbank.entities ENT ON AA.[country_id] = ENT.iso2_code AND AA.[country_code] = ENT.[wb_id]
OUTER APPLY (
    SELECT TOP 1 G.[year] ,G.[value]
    FROM [World_Data_Atlas].[worldbank].[data] AS G
    WHERE G.[indicator_code] = 'NY.GDP.PCAP.PP.KD' AND G.[country_code] = AA.[country_code] AND G.[country_id] = AA.[country_id] AND G.[year] IN (2024, 2023, 2022)         AND G.[value] IS NOT NULL
    ORDER BY G.[year] DESC) AS GDP
WHERE AA.[indicator_code] = 'GOV_WGI_PV.SC' AND AA.[year] = 2024 AND ENT.is_country = 1;
        """

FILE_NAME = "political_stability_vs_gdp_ppp_2024.png"
X_COL = "gdp_ppp"
Y_COL = "stability"
MAP_TITLE = "Political Stability and Wealth"
MAP_SUBTITLE = "Political stability score vs GDP per capita PPP, 2024"
X_LABEL = "GDP per capita, PPP (constant international $)"
Y_LABEL = "Political stability score (0–100)"
FOOTER_LEFT = "X: World Bank NY.GDP.PCAP.PP.KD | Y: WGI GOV_WGI_PV.SC"
FOOTER_RIGHT = "Source: World Bank WDI + WGI"
POINT_COLOR = "#B7FF00"
SHOW_LABELS = False
X_LOG = True
Y_LOG = False
POINT_SIZE = 66
COLOR_COL = "continent"
continent_color_map = {
    "Africa": "#F97316",
    "Europe": "#0000FF",
    "Asia": "#22C55E",
    "Americas": "#FF0000",
    "Oceania": "#FFFFFF"
}

# ============================================================

OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
create_scatter_chart(
    df=df,
    output_file=OUTPUT_FILE,
    x_col=X_COL,
    y_col=Y_COL,
    title=MAP_TITLE,
    subtitle=MAP_SUBTITLE,
    x_label=X_LABEL,
    y_label=Y_LABEL,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..","Logos","4.png",)),
    x_log=X_LOG,
    y_log=Y_LOG,
    color_col=COLOR_COL,
    show_labels=SHOW_LABELS,
    point_size=POINT_SIZE,
    legend_location = 'lower right',
    category_color_map=continent_color_map,
    point_color=POINT_COLOR)