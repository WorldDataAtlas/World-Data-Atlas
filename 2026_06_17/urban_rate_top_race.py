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
from graph_bar_race import create_bar_race

# ============================================================

"""From villages to cities.

Top 10 most urbanized countries, 1950–2035 (UN projections).

One of the most important demographic transformations in modern history.

#Urbanization #Demography #DataViz #WorldDataAtlas"""


TOP_N = 10

FILE_NAME = "urbanization_rate_bar_race.mp4"
TITLE = "Most Urbanized Countries Over Time"
SUBTITLE = "Top 10 countries by urban population share"
FOOTER_LEFT = "Urban population as % of total population"
FOOTER_RIGHT = "Source: UN World Population Prospects"
TIME_COL = "year"
CATEGORY_COL = "iso3_code"
VALUE_COL = "value"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"
X_LABEL = "Urban population (%)"
AUDIO_FILE = BASE_DIR / "Audio" / "Audio.mp3"
FLAGS_DIR = BASE_DIR / "flags_png"

query = """
    SELECT *
    FROM (
        SELECT
            CASE
                WHEN D.location_name = 'Venezuela (Bolivarian Republic of)' THEN 'Venezuela'
                WHEN D.location_name = 'Iran (Islamic Republic of)' THEN 'Iran'
                WHEN D.location_name = 'Russian Federation' THEN 'Russia'
                WHEN D.location_name = 'United Arab Emirates' THEN 'UAE'
                WHEN D.location_name = 'United States of America' THEN 'USA'
                WHEN D.location_name = 'Bolivia (Plurinational State of)' THEN 'Bolivia'
                WHEN D.location_name = 'Bolivia (Plurinational State of)' THEN 'Bolivia'
                WHEN D.location_name = 'Micronesia (Fed. States of)' THEN 'Micronesia'
                WHEN D.location_name = 'Solomon Islands' THEN 'Solomon Isls'
                WHEN D.location_name = 'United Republic of Tanzania' THEN 'Tanzania'
                WHEN D.location_name = 'Lao People''s Democratic Republic' THEN 'Laos'
                WHEN D.location_name = 'Republic of Moldova' THEN 'Moldova'
                ELSE D.location_name
            END AS location_name,
            D.iso2_code,
            D.iso3_code,
            D.[year],
            ENT.is_country,
            MAX(CASE WHEN D.category_name = 'Rural' THEN D.[value] END) AS rural_pop,
            MAX(CASE WHEN D.category_name = 'Urban' THEN D.[value] END) AS urban_pop,
            MAX(CASE WHEN D.category_name = 'Total' THEN D.[value] END) AS total_pop,
            100.0 * MAX(CASE WHEN D.category_name = 'Urban' THEN D.[value] END) / NULLIF(MAX(CASE WHEN D.category_name = 'Total' THEN D.[value] END), 0) AS value
        FROM [World_Data_Atlas].[un].[data] AS D
        LEFT JOIN worldbank.entities ENT ON D.iso2_code = ENT.iso2_code AND D.iso3_code = ENT.[wb_id]
        WHERE D.indicator_id = 91 AND D.variant_id = 4 AND D.sex_id = 3
        AND D.iso2_code NOT IN ('ST','IM','GL','FO','AS','CW','PR','TC','MP','GU','VI','BH','BM','KY','GI','HK','MO','KW','MC','NR','MF','SG','SX')
        GROUP BY D.location_name, D.iso2_code, D.iso3_code, D.[year], ENT.is_country
    ) AS AA
    WHERE AA.is_country = 1 AND AA.[value] IS NOT NULL
    """

# ============================================================

COLOR_PALETTE = ["#2563EB","#16A34A","#F59E0B","#DC2626","#A855F7","#06B6D4","#84CC16","#F97316","#EC4899","#14B8A6"]
engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)
df["year"] = df["year"].astype(int)
df["value"] = df["value"].astype(float)
df = df.dropna(subset=[TIME_COL, CATEGORY_COL, VALUE_COL, LABEL_COL, FLAG_COL])
df[FLAG_COL] = df[FLAG_COL].astype(str).str.lower()
df[CATEGORY_COL] = df[CATEGORY_COL].astype(str)
df[LABEL_COL] = df[LABEL_COL].astype(str)
df = df[(df[FLAG_COL].str.len() == 2) & (df[CATEGORY_COL].str.len() == 3)]
category_config = (
    df[[CATEGORY_COL, LABEL_COL]]
    .drop_duplicates()
    .assign(color=lambda x: x[CATEGORY_COL].map(s.COUNTRY_COLORS))
    .rename(columns={CATEGORY_COL: "source_value", LABEL_COL: "label"})
    .to_dict("records"))
OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
create_bar_race(
    df=df,
    output_file=OUTPUT_FILE,
    time_col=TIME_COL,
    category_col=CATEGORY_COL,
    value_col=VALUE_COL,
    title=TITLE,
    subtitle=SUBTITLE,
    x_label=X_LABEL,
    footer_left=FOOTER_LEFT,
    footer_right=FOOTER_RIGHT,
    category_config=category_config,
    top_n=TOP_N,
    fps=30,
    seconds_per_period=0.8,
    value_format=None,
    decimal_places=2,
    color_palette=COLOR_PALETTE,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
    include_music=True,
    music_path=AUDIO_FILE,
    music_volume=0.25,
    loop_music=True,
    flag_col=FLAG_COL,
    show_flags=True,
    flags_dir=FLAGS_DIR,
)