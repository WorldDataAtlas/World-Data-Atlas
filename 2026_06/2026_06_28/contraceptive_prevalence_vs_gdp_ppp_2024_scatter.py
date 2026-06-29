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
      AA.[location_name]
      ,AA.[iso2_code]
      ,AA.[iso3_code]
        ,CASE
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
       END AS continent
      ,AA.[indicator_name]
      ,AA.[year]
      ,AA.[value]
      ,GDP.[value] AS GDP_PPP
      ,AA.category_id
      ,AA.category_name
FROM [World_Data_Atlas].[un].[data] as AA
LEFT JOIN worldbank.entities ENT ON AA.iso2_code = ENT.iso2_code AND AA.iso3_code = ENT.[wb_id]
LEFT JOIN ( SELECT [country_code], [country_id], [value]
            FROM [World_Data_Atlas].[worldbank].[data]
            WHERE [indicator_code] = 'NY.GDP.PCAP.PP.KD' AND [year] = 2024) AS GDP ON GDP.[country_code] = AA.iso3_code AND GDP.[country_id] = AA.iso2_code
WHERE   AA.indicator_id = 1 and 
        AA.[variant_id] = 4 and 
        AA.[age_id] = 31 and 
        AA.[year] = 2024 and 
        AA.category_id = 99 AND 
        ENT.is_country = 1 and
        GDP.[value] is not null
        """

FILE_NAME = "contraceptive_prevalence_vs_gdp_ppp_2024.png"

X_COL = "GDP_PPP"
Y_COL = "value"

MAP_TITLE = "Contraceptive Use vs GDP per Capita"
MAP_SUBTITLE = "Any method, women aged 15–49, 2024"

X_LABEL = "GDP per capita, PPP (constant 2021 international $)"
Y_LABEL = "Contraceptive prevalence, any method (%)"

FOOTER_LEFT = "Source: United Nations + World Bank"
FOOTER_RIGHT = "WorldDataAtlas.com"

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