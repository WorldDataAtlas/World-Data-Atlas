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
    le.country_name,
    le.country_code,
    CASE
        WHEN le.country_code IN (
            'DZA','AGO','BEN','BWA','BFA','BDI','CPV','CMR','CAF','TCD','COM','COG','COD','CIV','DJI','EGY',
            'GNQ','ERI','SWZ','ETH','GAB','GMB','GHA','GIN','GNB','KEN','LSO','LBR','LBY','MDG','MWI','MLI',
            'MRT','MUS','MAR','MOZ','NAM','NER','NGA','RWA','STP','SEN','SYC','SLE','SOM','ZAF','SSD','SDN',
            'TZA','TGO','TUN','UGA','ZMB','ZWE') THEN 'Africa'
        WHEN le.country_code IN (
            'ALB','AND','AUT','BEL','BIH','BGR','BLR','CHE','CYP','CZE','DEU','DNK','ESP','EST','FIN','FRA',
            'GBR','GRC','HRV','HUN','IRL','ISL','ITA','LIE','LTU','LUX','LVA','MDA','MKD','MLT','MNE','NLD',
            'NOR','POL','PRT','ROU','RUS','SMR','SRB','SVK','SVN','SWE','UKR','MCO','XKX','IMN','GRL','GIB',
            'FRO','CHI') THEN 'Europe'
        WHEN le.country_code IN (
            'AFG','ARE','ARM','AZE','BHR','BGD','BRN','BTN','CHN','GEO','HKG','IDN','IND','IRN','IRQ','ISR',
            'JOR','JPN','KAZ','KGZ','KHM','KOR','KWT','LAO','LBN','LKA','MAC','MDV','MMR','MNG','MYS','NPL',
            'OMN','PAK','PHL','QAT','SAU','SGP','SYR','THA','TJK','TKM','TLS','TUR','UZB','VNM','YEM','PSE',
            'NCL','PRK','MNP','GUM','ASM') THEN 'Asia'
        WHEN le.country_code IN (
            'ARG','ATG','BHS','BLZ','BOL','BRA','BRB','CAN','CHL','COL','CRI','CUB','DMA','DOM','ECU','GRD',
            'GTM','GUY','HND','HTI','JAM','KNA','LCA','MEX','NIC','PAN','PER','PRY','SLV','SUR','TTO','URY',
            'USA','VCT','VEN','ABW','PRI','BMU','TCA','MAF','SXM','CYM','VGB','CUW','VIR') THEN 'Americas'
        WHEN le.country_code IN ('AUS','FJI','FSM','KIR','MHL','NRU','NZL','PLW','PNG','SLB','TON','TUV','VUT','WSM','PYF') THEN 'Oceania'
        ELSE 'Other'
    END AS continent,
    le.[value] AS life_expectancy,
    fr.[value] AS fertility_rate,
    le.country_code AS [label]
FROM worldbank.[data] le
LEFT JOIN (SELECT is_country, [name] FROM [World_Data_Atlas].[worldbank].[entities]) AS ENT ON ENT.[name] = le.[country_name]
INNER JOIN worldbank.[data] fr ON le.country_code = fr.country_code AND le.[year] = fr.[year]
WHERE le.indicator_code = 'SP.DYN.LE00.IN' 
AND fr.indicator_code = 'SP.DYN.TFRT.IN'
AND le.[year] = 2024
AND ENT.is_country = 1
AND le.[value] IS NOT NULL
AND fr.[value] IS NOT NULL
"""

"""The countries where people live the longest are often the least likely to replace their populations.

Modernity seems remarkably good at extending life — and remarkably bad at producing more of it.

Source: World Bank

#Demography #Population #DataViz"""


FILE_NAME = "life_expectancy_vs_fertility_by_continent_2024"

X_COL = "life_expectancy"
Y_COL = "fertility_rate"

MAP_TITLE = "Life Expectancy and Fertility - Longer Lives, Fewer Children"
MAP_SUBTITLE = "Countries by life expectancy, fertility rate and continent, 2024"

X_LABEL = "Life expectancy at birth (years)"
Y_LABEL = "Fertility rate (births per woman)"

FOOTER_LEFT = "Indicators: SP.DYN.LE00.IN vs SP.DYN.TFRT.IN"
FOOTER_RIGHT = "Source: World Bank"

POINT_COLOR = "#000000"
POINT_SIZE = 66
SHOW_LABELS = False

X_LOG = False
Y_LOG = False

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
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..","Logos","4.png")),
    x_log=X_LOG,
    y_log=Y_LOG,
    show_labels=SHOW_LABELS,
    point_color=POINT_COLOR,
    color_col="continent",
    point_size=POINT_SIZE,
    category_color_map=continent_color_map,
    show_color_legend=True,)