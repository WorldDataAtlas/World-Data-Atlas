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
🌍 Has rising secularization always been accompanied by lower fertility?

Between 2010 and 2020, countries followed very different paths—there is no clear global relationship between changes in secularization and fertility.

Sources: Pew Research Center & United Nations | #WorldDataAtlas
"""

query = """
WITH religion AS (
    SELECT
        EN.wb_id AS country_code,
        EN.iso2_code,
        P.country,
        MAX(
            CASE
                WHEN P.year = 2010 THEN
                    COALESCE(NULLIF(P.religiously_unaffiliated, 9999), 0)
                    * 100.0 / NULLIF(P.population, 0) END) AS unaffiliated_pct_2010,
        MAX(CASE WHEN P.year = 2020 THEN COALESCE(NULLIF(P.religiously_unaffiliated, 9999), 0) * 100.0 / NULLIF(P.population, 0) END) AS unaffiliated_pct_2020,
        MAX(CASE WHEN P.year = 2020 THEN P.population END) AS population_2020
    FROM pew.global_religious_estimates AS P
    INNER JOIN worldbank.entities AS EN ON LOWER(LTRIM(RTRIM(EN.name))) = LOWER(LTRIM(RTRIM(P.country))) AND EN.is_country = 1
    WHERE P.level = 1 AND P.year IN (2010, 2020)
    GROUP BY EN.wb_id, EN.iso2_code, P.country),

fertility AS (
    SELECT
        U.iso3_code,
        U.iso2_code,
        MAX(CASE WHEN U.year = 2010 THEN U.value END) AS fertility_2010,
        MAX(CASE WHEN U.year = 2020 THEN U.value END) AS fertility_2020
    FROM un.data AS U
    WHERE U.indicator_id = 19 AND U.variant_id = 4 AND U.year IN (2010, 2020)
    GROUP BY U.iso2_code, U.iso3_code)

SELECT
    R.country_code,
    R.country,
    ROUND(R.unaffiliated_pct_2010, 2) AS unaffiliated_pct_2010,
    ROUND(R.unaffiliated_pct_2020, 2) AS unaffiliated_pct_2020,
    ROUND(R.unaffiliated_pct_2020 - R.unaffiliated_pct_2010, 2) AS unaffiliated_change_pp,
    ROUND(F.fertility_2010, 2) AS fertility_2010,
    ROUND(F.fertility_2020, 2) AS fertility_2020,
    ROUND(F.fertility_2020 - F.fertility_2010, 2) AS fertility_change,
    R.population_2020,
    CASE
        WHEN F.iso3_code IN (
            'DZA','AGO','BEN','BWA','BFA','BDI','CPV','CMR','CAF','TCD','COM','COG','COD','CIV','DJI','EGY',
            'GNQ','ERI','SWZ','ETH','GAB','GMB','GHA','GIN','GNB','KEN','LSO','LBR','LBY','MDG','MWI','MLI',
            'MRT','MUS','MAR','MOZ','NAM','NER','NGA','RWA','STP','SEN','SYC','SLE','SOM','ZAF','SSD','SDN',
            'TZA','TGO','TUN','UGA','ZMB','ZWE') THEN 'Africa'
        WHEN F.iso3_code IN (
            'ALB','AND','AUT','BEL','BIH','BGR','BLR','CHE','CYP','CZE','DEU','DNK','ESP','EST','FIN','FRA',
            'GBR','GRC','HRV','HUN','IRL','ISL','ITA','LIE','LTU','LUX','LVA','MDA','MKD','MLT','MNE','NLD',
            'NOR','POL','PRT','ROU','RUS','SMR','SRB','SVK','SVN','SWE','UKR','MCO','XKX','IMN','GRL','GIB',
            'FRO','CHI') THEN 'Europe'
        WHEN F.iso3_code IN (
            'AFG','ARE','ARM','AZE','BHR','BGD','BRN','BTN','CHN','GEO','HKG','IDN','IND','IRN','IRQ','ISR',
            'JOR','JPN','KAZ','KGZ','KHM','KOR','KWT','LAO','LBN','LKA','MAC','MDV','MMR','MNG','MYS','NPL',
            'OMN','PAK','PHL','QAT','SAU','SGP','SYR','THA','TJK','TKM','TLS','TUR','UZB','VNM','YEM','PSE',
            'NCL','PRK','MNP','GUM','ASM') THEN 'Asia'
        WHEN F.iso3_code IN (
            'ARG','ATG','BHS','BLZ','BOL','BRA','BRB','CAN','CHL','COL','CRI','CUB','DMA','DOM','ECU','GRD',
            'GTM','GUY','HND','HTI','JAM','KNA','LCA','MEX','NIC','PAN','PER','PRY','SLV','SUR','TTO','URY',
            'USA','VCT','VEN','ABW','PRI','BMU','TCA','MAF','SXM','CYM','VGB','CUW','VIR') THEN 'Americas'
        WHEN F.iso3_code IN (
            'AUS','FJI','FSM','KIR','MHL','NRU','NZL','PLW','PNG','SLB','TON','TUV','VUT','WSM','PYF') THEN 'Oceania'
        ELSE 'Other' END AS continent
FROM religion AS R
INNER JOIN fertility AS F ON F.iso2_code = R.iso2_code
WHERE
    R.unaffiliated_pct_2010 IS NOT NULL
    AND R.unaffiliated_pct_2020 IS NOT NULL
    AND F.fertility_2010 IS NOT NULL
    AND F.fertility_2020 IS NOT NULL
ORDER BY unaffiliated_change_pp DESC;
        """

FILE_NAME = "secularization_vs_fertility_change_2010_2020.png"
X_COL = "unaffiliated_change_pp"
Y_COL = "fertility_change"
MAP_TITLE = "Secularization and Fertility Change"
MAP_SUBTITLE = "Change in religiously unaffiliated population share vs change in fertility rate, 2010–2020"
X_LABEL = "Change in religiously unaffiliated share (percentage points)"
Y_LABEL = "Change in fertility rate (children per woman)"
FOOTER_LEFT = "Bubble size: population in 2020"
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
    legend_location = 'lower right',
    category_color_map=continent_color_map,
    point_color=POINT_COLOR)