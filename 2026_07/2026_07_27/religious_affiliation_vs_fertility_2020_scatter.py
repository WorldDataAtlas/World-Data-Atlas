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
🌍 Does religion correlate with fertility?

This chart compares the share of people affiliated with a religion against the fertility rate across countries in 2020.

Sources: Pew Research Center & United Nations | #WorldDataAtlas
"""

query = """
    SELECT
        EN.wb_id AS country_code,
        P.country,
        ROUND((P.christians + P.muslims + P.buddhists + P.hindus + P.jews + P.other_religions) * 100.0 / NULLIF(P.population,0),2) AS believers_pct,
        U.value AS fertility_rate,
        CASE
            WHEN U.iso3_code IN (
                'DZA','AGO','BEN','BWA','BFA','BDI','CPV','CMR','CAF','TCD','COM','COG','COD','CIV','DJI','EGY',
                'GNQ','ERI','SWZ','ETH','GAB','GMB','GHA','GIN','GNB','KEN','LSO','LBR','LBY','MDG','MWI','MLI',
                'MRT','MUS','MAR','MOZ','NAM','NER','NGA','RWA','STP','SEN','SYC','SLE','SOM','ZAF','SSD','SDN',
                'TZA','TGO','TUN','UGA','ZMB','ZWE') THEN 'Africa'
            WHEN U.iso3_code IN (
                'ALB','AND','AUT','BEL','BIH','BGR','BLR','CHE','CYP','CZE','DEU','DNK','ESP','EST','FIN','FRA',
                'GBR','GRC','HRV','HUN','IRL','ISL','ITA','LIE','LTU','LUX','LVA','MDA','MKD','MLT','MNE','NLD',
                'NOR','POL','PRT','ROU','RUS','SMR','SRB','SVK','SVN','SWE','UKR','MCO','XKX','IMN','GRL','GIB',
                'FRO','CHI') THEN 'Europe'
            WHEN U.iso3_code IN (
                'AFG','ARE','ARM','AZE','BHR','BGD','BRN','BTN','CHN','GEO','HKG','IDN','IND','IRN','IRQ','ISR',
                'JOR','JPN','KAZ','KGZ','KHM','KOR','KWT','LAO','LBN','LKA','MAC','MDV','MMR','MNG','MYS','NPL',
                'OMN','PAK','PHL','QAT','SAU','SGP','SYR','THA','TJK','TKM','TLS','TUR','UZB','VNM','YEM','PSE',
                'NCL','PRK','MNP','GUM','ASM') THEN 'Asia'
            WHEN U.iso3_code IN (
                'ARG','ATG','BHS','BLZ','BOL','BRA','BRB','CAN','CHL','COL','CRI','CUB','DMA','DOM','ECU','GRD',
                'GTM','GUY','HND','HTI','JAM','KNA','LCA','MEX','NIC','PAN','PER','PRY','SLV','SUR','TTO','URY',
                'USA','VCT','VEN','ABW','PRI','BMU','TCA','MAF','SXM','CYM','VGB','CUW','VIR') THEN 'Americas'
            WHEN U.iso3_code IN (
                'AUS','FJI','FSM','KIR','MHL','NRU','NZL','PLW','PNG','SLB','TON','TUV','VUT','WSM','PYF') THEN 'Oceania'
            ELSE 'Other' END AS continent
    FROM [World_Data_Atlas].[pew].[global_religious_estimates] AS P
    LEFT JOIN [World_Data_Atlas].[worldbank].[entities] AS EN
        ON LTRIM(RTRIM(LOWER(EN.name))) = LTRIM(RTRIM(LOWER(P.country))) AND EN.is_country = 1
    INNER JOIN [World_Data_Atlas].[un].[data] AS U ON U.iso2_code = EN.iso2_code AND U.indicator_id = 19 AND U.year = 2020 AND U.variant_id = 4
    WHERE P.level = 1 AND P.year = 2020 AND P.population > 0 AND EN.wb_id IS NOT NULL
    ORDER BY believers_pct DESC;
        """

query = """
    SELECT
        EN.wb_id AS country_code,
        P.country,
        ROUND((P.christians + P.muslims + P.buddhists + P.hindus + P.jews + P.other_religions) * 100.0 / NULLIF(P.population,0),2) AS believers_pct,
        U.value AS fertility_rate,
        CASE
            WHEN U.iso3_code IN (
                'DZA','AGO','BEN','BWA','BFA','BDI','CPV','CMR','CAF','TCD','COM','COG','COD','CIV','DJI','EGY',
                'GNQ','ERI','SWZ','ETH','GAB','GMB','GHA','GIN','GNB','KEN','LSO','LBR','LBY','MDG','MWI','MLI',
                'MRT','MUS','MAR','MOZ','NAM','NER','NGA','RWA','STP','SEN','SYC','SLE','SOM','ZAF','SSD','SDN',
                'TZA','TGO','TUN','UGA','ZMB','ZWE') THEN 'Africa'
            WHEN U.iso3_code IN (
                'ALB','AND','AUT','BEL','BIH','BGR','BLR','CHE','CYP','CZE','DEU','DNK','ESP','EST','FIN','FRA',
                'GBR','GRC','HRV','HUN','IRL','ISL','ITA','LIE','LTU','LUX','LVA','MDA','MKD','MLT','MNE','NLD',
                'NOR','POL','PRT','ROU','RUS','SMR','SRB','SVK','SVN','SWE','UKR','MCO','XKX','IMN','GRL','GIB',
                'FRO','CHI') THEN 'Europe'
            WHEN U.iso3_code IN (
                'AFG','ARE','ARM','AZE','BHR','BGD','BRN','BTN','CHN','GEO','HKG','IDN','IND','IRN','IRQ','ISR',
                'JOR','JPN','KAZ','KGZ','KHM','KOR','KWT','LAO','LBN','LKA','MAC','MDV','MMR','MNG','MYS','NPL',
                'OMN','PAK','PHL','QAT','SAU','SGP','SYR','THA','TJK','TKM','TLS','TUR','UZB','VNM','YEM','PSE',
                'NCL','PRK','MNP','GUM','ASM') THEN 'Asia'
            WHEN U.iso3_code IN (
                'ARG','ATG','BHS','BLZ','BOL','BRA','BRB','CAN','CHL','COL','CRI','CUB','DMA','DOM','ECU','GRD',
                'GTM','GUY','HND','HTI','JAM','KNA','LCA','MEX','NIC','PAN','PER','PRY','SLV','SUR','TTO','URY',
                'USA','VCT','VEN','ABW','PRI','BMU','TCA','MAF','SXM','CYM','VGB','CUW','VIR') THEN 'Americas'
            WHEN U.iso3_code IN (
                'AUS','FJI','FSM','KIR','MHL','NRU','NZL','PLW','PNG','SLB','TON','TUV','VUT','WSM','PYF') THEN 'Oceania'
            ELSE 'Other' END AS continent
    FROM [World_Data_Atlas].[pew].[global_religious_estimates] AS P
    LEFT JOIN [World_Data_Atlas].[worldbank].[entities] AS EN
        ON LTRIM(RTRIM(LOWER(EN.name))) = LTRIM(RTRIM(LOWER(P.country))) AND EN.is_country = 1
    INNER JOIN [World_Data_Atlas].[un].[data] AS U ON U.iso2_code = EN.iso2_code AND U.indicator_id = 19 AND U.year = 2020 AND U.variant_id = 4
    WHERE P.level = 1 AND P.year = 2020 AND P.population > 0 AND EN.wb_id IS NOT NULL
    ORDER BY believers_pct DESC;
        """

FILE_NAME = "religious_affiliation_vs_fertility_2020.png"
X_COL = "believers_pct"
Y_COL = "fertility_rate"
MAP_TITLE = "Religious Affiliation and Fertility"
MAP_SUBTITLE = "Countries, 2020"
X_LABEL = "Religiously affiliated population (%)"
Y_LABEL = "Fertility rate (children per woman)"
FOOTER_LEFT = "Religiously affiliated = Christians + Muslims + Hindus + Buddhists + Jews + Other religions"
FOOTER_RIGHT = "Sources: Pew Research Center, United Nations"
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
    legend_location = 'upper left',
    category_color_map=continent_color_map,
    point_color=POINT_COLOR)