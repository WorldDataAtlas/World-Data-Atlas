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

"""The first $20,000 of GDP per person seems far more valuable than the next $100,000.

Once countries reach a certain level of prosperity, additional wealth has surprisingly little impact on life expectancy."""

query = """
        SELECT
        D.[location_name],
        CASE
                WHEN D.[iso3_code] IN (
                'DZA','AGO','BEN','BWA','BFA','BDI','CPV','CMR','CAF','TCD','COM','COG','COD','CIV','DJI','EGY',
                'GNQ','ERI','SWZ','ETH','GAB','GMB','GHA','GIN','GNB','KEN','LSO','LBR','LBY','MDG','MWI','MLI',
                'MRT','MUS','MAR','MOZ','NAM','NER','NGA','RWA','STP','SEN','SYC','SLE','SOM','ZAF','SSD','SDN',
                'TZA','TGO','TUN','UGA','ZMB','ZWE') THEN 'Africa'
                WHEN D.[iso3_code] IN (
                'ALB','AND','AUT','BEL','BIH','BGR','BLR','CHE','CYP','CZE','DEU','DNK','ESP','EST','FIN','FRA',
                'GBR','GRC','HRV','HUN','IRL','ISL','ITA','LIE','LTU','LUX','LVA','MDA','MKD','MLT','MNE','NLD',
                'NOR','POL','PRT','ROU','RUS','SMR','SRB','SVK','SVN','SWE','UKR','MCO','XKX','IMN','GRL','GIB',
                'FRO','CHI') THEN 'Europe'
                WHEN D.[iso3_code] IN (
                'AFG','ARE','ARM','AZE','BHR','BGD','BRN','BTN','CHN','GEO','HKG','IDN','IND','IRN','IRQ','ISR',
                'JOR','JPN','KAZ','KGZ','KHM','KOR','KWT','LAO','LBN','LKA','MAC','MDV','MMR','MNG','MYS','NPL',
                'OMN','PAK','PHL','QAT','SAU','SGP','SYR','THA','TJK','TKM','TLS','TUR','UZB','VNM','YEM','PSE',
                'NCL','PRK','MNP','GUM','ASM') THEN 'Asia'
                WHEN D.[iso3_code] IN (
                'ARG','ATG','BHS','BLZ','BOL','BRA','BRB','CAN','CHL','COL','CRI','CUB','DMA','DOM','ECU','GRD',
                'GTM','GUY','HND','HTI','JAM','KNA','LCA','MEX','NIC','PAN','PER','PRY','SLV','SUR','TTO','URY',
                'USA','VCT','VEN','ABW','PRI','BMU','TCA','MAF','SXM','CYM','VGB','CUW','VIR') THEN 'Americas'
                WHEN D.[iso3_code] IN ('AUS','FJI','FSM','KIR','MHL','NRU','NZL','PLW','PNG','SLB','TON','TUV','VUT','WSM','PYF') THEN 'Oceania'
                ELSE 'Other'
        END AS continent
        ,D.[iso2_code]
        ,D.[iso3_code]
        ,D.[year]
        ,D.[value] AS [LIFE_EXPACTANCY]
        ,GDP_PPP.[value] AS [GDP_PPP]
        FROM [World_Data_Atlas].[un].[data] AS D
        LEFT JOIN ( SELECT is_country, [name], [iso2_code] FROM worldbank.entities) ENT ON (ENT.[name] = D.[location_name]) OR (D.[iso2_code] = ENT.[iso2_code])
        LEFT JOIN (
        SELECT D.[country_code]
                ,D.[country_id]
                ,D.[country_name]
                ,D.[year]
                ,D.[value]
        FROM [World_Data_Atlas].[worldbank].[data] AS D
        LEFT JOIN ( SELECT is_country, [name], [iso2_code] FROM worldbank.entities) ENT ON (D.[country_id] = ENT.[iso2_code])
        WHERE   D.[year] = 2023 AND
                D.[indicator_code] = 'NY.GDP.PCAP.PP.CD' AND
                ENT.is_country = 1) AS GDP_PPP ON GDP_PPP.[country_id] = D.[iso2_code]
        WHERE   D.[variant_id] = 4 AND 
                D.[sex_id] = 3 AND 
                D.[indicator_id] = 75 AND
                D.[age_id] = 223 AND
                D.[year] = 2023 AND
                ENT.is_country = 1 AND
                GDP_PPP.[value] IS NOT NULL
        """

FILE_NAME = "life_expectancy_vs_gdp_per_person_ppp_2025.png"
X_COL = "GDP_PPP"
Y_COL = "LIFE_EXPACTANCY"
MAP_TITLE = "Life Expectancy vs GDP per Person"
MAP_SUBTITLE = "All countries, 2023"
X_LABEL = "GDP per person, PPP"
Y_LABEL = "Life expectancy at birth, years"
FOOTER_LEFT = "GDP per person in PPP terms; life expectancy at birth, both sexes"
FOOTER_RIGHT = "Source: UN World and World Bank"
SHOW_LABELS = True
X_LOG = False
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