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

"""Urbanization is not just about wealth.

Countries with similar GDP per capita often have very different shares of people living in cities.

GDP per capita (PPP) vs urban population share, 2024.

#Urbanization #Economics #DataViz #WorldDataAtlas"""


query = """
        SELECT  
                CASE
                WHEN AA.[iso3_code] IN (
                        'DZA','AGO','BEN','BWA','BFA','BDI','CPV','CMR','CAF','TCD','COM','COG','COD','CIV','DJI','EGY',
                        'GNQ','ERI','SWZ','ETH','GAB','GMB','GHA','GIN','GNB','KEN','LSO','LBR','LBY','MDG','MWI','MLI',
                        'MRT','MUS','MAR','MOZ','NAM','NER','NGA','RWA','STP','SEN','SYC','SLE','SOM','ZAF','SSD','SDN',
                        'TZA','TGO','TUN','UGA','ZMB','ZWE') THEN 'Africa'
                WHEN AA.[iso3_code] IN (
                        'ALB','AND','AUT','BEL','BIH','BGR','BLR','CHE','CYP','CZE','DEU','DNK','ESP','EST','FIN','FRA',
                        'GBR','GRC','HRV','HUN','IRL','ISL','ITA','LIE','LTU','LUX','LVA','MDA','MKD','MLT','MNE','NLD',
                        'NOR','POL','PRT','ROU','RUS','SMR','SRB','SVK','SVN','SWE','UKR','MCO','XKX','IMN','GRL','GIB',
                        'FRO','CHI') THEN 'Europe'
                WHEN AA.[iso3_code] IN (
                        'AFG','ARE','ARM','AZE','BHR','BGD','BRN','BTN','CHN','GEO','HKG','IDN','IND','IRN','IRQ','ISR',
                        'JOR','JPN','KAZ','KGZ','KHM','KOR','KWT','LAO','LBN','LKA','MAC','MDV','MMR','MNG','MYS','NPL',
                        'OMN','PAK','PHL','QAT','SAU','SGP','SYR','THA','TJK','TKM','TLS','TUR','UZB','VNM','YEM','PSE',
                        'NCL','PRK','MNP','GUM','ASM') THEN 'Asia'
                WHEN AA.[iso3_code] IN (
                        'ARG','ATG','BHS','BLZ','BOL','BRA','BRB','CAN','CHL','COL','CRI','CUB','DMA','DOM','ECU','GRD',
                        'GTM','GUY','HND','HTI','JAM','KNA','LCA','MEX','NIC','PAN','PER','PRY','SLV','SUR','TTO','URY',
                        'USA','VCT','VEN','ABW','PRI','BMU','TCA','MAF','SXM','CYM','VGB','CUW','VIR') THEN 'Americas'
                WHEN AA.[iso3_code] IN ('AUS','FJI','FSM','KIR','MHL','NRU','NZL','PLW','PNG','SLB','TON','TUV','VUT','WSM','PYF') THEN 'Oceania'
                ELSE 'Other'
                END AS continent,
                AA.location_name,
                AA.iso2_code,
                AA.iso3_code,
                AA.[year],
                AA.is_country,
                AA.[value] AS urban_rate,
                GDP.[value] AS GDP_PPP
        FROM (
        SELECT
                D.location_name,
                D.iso2_code,
                D.iso3_code,
                D.[year],
                ENT.is_country,
                100.0 * MAX(CASE WHEN D.category_name = 'Urban' THEN D.[value] END) / NULLIF(MAX(CASE WHEN D.category_name = 'Total' THEN D.[value] END), 0) AS [value]
        FROM [World_Data_Atlas].[un].[data] AS D
        LEFT JOIN worldbank.entities ENT ON D.iso2_code = ENT.iso2_code AND D.iso3_code = ENT.[wb_id]
        WHERE D.indicator_id = 91 AND D.variant_id = 4 AND D.sex_id = 3 AND ENT.is_country = 1 AND D.[value] IS NOT NULL and D.[year] = 2024
        AND D.iso2_code NOT IN ('ST','IM','GL','FO','AS','CW','PR','TC','MP','GU','VI','BH','BM','KY','GI','HK','MO','KW','MC','NR','MF','SG','SX')
        GROUP BY D.location_name, D.iso2_code, D.iso3_code, D.[year], ENT.is_country
        ) AS AA
        LEFT JOIN ( SELECT [country_code], [country_id], [value]
                FROM [World_Data_Atlas].[worldbank].[data]
                WHERE [indicator_code] = 'NY.GDP.PCAP.PP.KD' AND [year] = 2024) AS GDP ON GDP.[country_code] = AA.iso3_code AND GDP.[country_id] = AA.iso2_code
        WHERE GDP.[value] IS NOT NULL
        """

FILE_NAME = "gdp_ppp_per_capita_vs_urbanization_2024.png"

X_COL = "GDP_PPP"
Y_COL = "urban_rate"

MAP_TITLE = "Urbanization and Wealth"
MAP_SUBTITLE = "GDP per capita PPP vs urban population share, 2024"
X_LABEL = "GDP per capita, PPP (constant international $)"
Y_LABEL = "Urban population (% of total)"
FOOTER_LEFT = "X: World Bank NY.GDP.PCAP.PP.KD | Y: UN urban population share"
FOOTER_RIGHT = "Sources: World Bank, UN WPP"
POINT_COLOR = "#B7FF00"
SHOW_LABELS = False
X_LOG = True
Y_LOG = False
POINT_COLOR = "#000000"
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