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

query = """
SELECT
    A.country_code,
    A.country_name,
    MAX(CASE WHEN A.year = 1995 THEN A.value END) AS life_1995,
    MAX(CASE WHEN A.year = 2024 THEN A.value END) AS life_2024,
    (MAX(CASE WHEN A.year = 2024 THEN A.value END) - MAX(CASE WHEN A.year = 1995 THEN A.value END)) AS life_change,
    MAX(CASE WHEN B.year = 1995 THEN B.value END) AS gdp_1995,
    MAX(CASE WHEN B.year = 2024 THEN B.value END) AS gdp_2024,
    ((MAX(CASE WHEN B.year = 2024 THEN B.value END) - MAX(CASE WHEN B.year = 1995 THEN B.value END))
        / MAX(CASE WHEN B.year = 1995 THEN B.value END)) * 100 AS gdp_change_pct
,CASE
    WHEN A.[country_code] IN (
        'DZA','AGO','BEN','BWA','BFA','BDI','CPV','CMR','CAF','TCD','COM','COG','COD','CIV','DJI','EGY',
        'GNQ','ERI','SWZ','ETH','GAB','GMB','GHA','GIN','GNB','KEN','LSO','LBR','LBY','MDG','MWI','MLI',
        'MRT','MUS','MAR','MOZ','NAM','NER','NGA','RWA','STP','SEN','SYC','SLE','SOM','ZAF','SSD','SDN',
        'TZA','TGO','TUN','UGA','ZMB','ZWE') THEN 'Africa'
    WHEN A.[country_code] IN (
        'ALB','AND','AUT','BEL','BIH','BGR','BLR','CHE','CYP','CZE','DEU','DNK','ESP','EST','FIN','FRA',
        'GBR','GRC','HRV','HUN','IRL','ISL','ITA','LIE','LTU','LUX','LVA','MDA','MKD','MLT','MNE','NLD',
        'NOR','POL','PRT','ROU','RUS','SMR','SRB','SVK','SVN','SWE','UKR','MCO','XKX','IMN','GRL','GIB',
        'FRO','CHI') THEN 'Europe'
    WHEN A.[country_code] IN (
        'AFG','ARE','ARM','AZE','BHR','BGD','BRN','BTN','CHN','GEO','HKG','IDN','IND','IRN','IRQ','ISR',
        'JOR','JPN','KAZ','KGZ','KHM','KOR','KWT','LAO','LBN','LKA','MAC','MDV','MMR','MNG','MYS','NPL',
        'OMN','PAK','PHL','QAT','SAU','SGP','SYR','THA','TJK','TKM','TLS','TUR','UZB','VNM','YEM','PSE',
        'NCL','PRK','MNP','GUM','ASM') THEN 'Asia'
    WHEN A.[country_code] IN (
        'ARG','ATG','BHS','BLZ','BOL','BRA','BRB','CAN','CHL','COL','CRI','CUB','DMA','DOM','ECU','GRD',
        'GTM','GUY','HND','HTI','JAM','KNA','LCA','MEX','NIC','PAN','PER','PRY','SLV','SUR','TTO','URY',
        'USA','VCT','VEN','ABW','PRI','BMU','TCA','MAF','SXM','CYM','VGB','CUW','VIR') THEN 'Americas'
    WHEN A.[country_code] IN (
        'AUS','FJI','FSM','KIR','MHL','NRU','NZL','PLW','PNG','SLB','TON','TUV','VUT','WSM','PYF') THEN 'Oceania'
    ELSE 'Other' END AS continent
FROM worldbank.data A
JOIN worldbank.data B ON A.country_id = B.country_id
JOIN worldbank.entities E ON A.country_id = E.iso2_code
WHERE A.indicator_code='SP.DYN.LE00.IN' AND B.indicator_code='NY.GDP.PCAP.PP.KD' AND A.year IN (1995,2024) AND B.year IN (1995,2024) AND E.is_country=1
GROUP BY A.country_code, A.country_name
HAVING
MAX(CASE WHEN A.year=1995 THEN A.value END) IS NOT NULL
AND
MAX(CASE WHEN A.year=2024 THEN A.value END) IS NOT NULL
AND
MAX(CASE WHEN B.year=1995 THEN B.value END) IS NOT NULL
AND
MAX(CASE WHEN B.year=2024 THEN B.value END) IS NOT NULL
        """

FILE_NAME = "gdp_growth_vs_life_expectancy_change_1995_2024.png"

X_COL = "gdp_change_pct"
Y_COL = "life_change"

MAP_TITLE = "Economic Growth and Life Expectancy"
MAP_SUBTITLE = "Change in real GDP per capita and life expectancy, 1995–2024"

X_LABEL = "Real GDP per capita growth (%)"
Y_LABEL = "Life expectancy change (years)"

FOOTER_LEFT = "GDP per capita: constant 2021 international dollars, PPP"
FOOTER_RIGHT = "Source: World Bank | WorldDataAtlas"

POINT_COLOR = "#B7FF00"
SHOW_LABELS = False

X_LOG = False
Y_LOG = False

POINT_SIZE = 66
COLOR_COL = "continent"
continent_color_map = {
    "Africa": "#F97316",
    "Europe": "#0000FF",
    "Asia": "#22C55E",
    "Americas": "#FF0000",
    "Oceania": "#FFFFFF"}

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