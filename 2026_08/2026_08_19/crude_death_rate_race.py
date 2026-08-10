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

"""
⚰️ Which countries have the highest crude death rates—and how has the ranking changed over time?

Watch the Top 10 countries by crude death rate from 1950 to 2030, including UN projections.

Source: United Nations | #WorldDataAtlas
"""

TOP_N = 10
FILE_NAME = "crude_death_rate_race.mp4"
TITLE = "Crude Death Rate"
SUBTITLE = "Top 10 countries by deaths per 1,000 people, 1950–2030"
FOOTER_LEFT = "Both sexes | Medium variant projection"
FOOTER_RIGHT = "Source: United Nations World Population Prospects"
TIME_COL = "year"
CATEGORY_COL = "iso3_code"
VALUE_COL = "value"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"
X_LABEL = "Deaths per 1,000 population"
AUDIO_FILE = BASE_DIR / "Audio" / "Audio.mp3"
FLAGS_DIR = BASE_DIR / "flags_png"

query = """
SELECT aa.[location_id]
      , CASE 
            WHEN aa.[location_name] = 'Bosnia and Herzegovina' THEN 'Bosn. and Herz.'
            WHEN aa.[location_name] = 'Republic of Moldova' THEN 'Moldova'
            WHEN aa.[location_name] = 'State of Palestine' THEN 'Palestine'
            WHEN aa.[location_name] = 'Iran (Islamic Republic of)' THEN 'Iran'
            WHEN aa.[location_name] = 'China, Hong Kong SAR' THEN 'Hong Kong'
            WHEN aa.[location_name] = 'China, Macao SAR' THEN 'Macao'
            WHEN aa.[location_name] = 'Dem. People''s Rep. of Korea' THEN 'North Korea'
            WHEN aa.[location_name] = 'Republic of Korea' THEN 'South Korea'
            WHEN aa.[location_name] = 'Central African Republic' THEN 'CAR'
            WHEN aa.[location_name] = 'Democratic Republic of the Congo' THEN 'DR Congo'
            WHEN aa.[location_name] = 'Bolivia (Plurinational State of)' THEN 'Bolivia'
            WHEN aa.[location_name] = 'Venezuela (Bolivarian Republic of)' THEN 'Venezuela'
            WHEN aa.[location_name] = 'Lao People''s Democratic Republic' THEN 'Laos'
            WHEN aa.[location_name] = 'Russian federation' THEN 'Russia'
            WHEN aa.[location_name] = 'United Arab Emirates' THEN 'UAE'
            WHEN aa.[location_name] = 'Syrian Arab Republic' THEN 'Syria'
        ELSE aa.[location_name]
        END AS [location_name]
      ,aa.[iso2_code]
      ,aa.[iso3_code]
      ,aa.[year]
      ,aa.[value]
FROM [World_Data_Atlas].[un].[data] as aa
LEFT JOIN worldbank.entities AS ENT ON AA.iso2_code = ENT.iso2_code
where aa.[year] < 2031 and aa.[indicator_id] = 59 and aa.[variant_id] = 4 and ENT.is_country = 1 and aa.[sex_id] = 3 and aa.[iso2_code] not in ('PW','ST','VC','TC','MP','SX','AS','VG','XK','VI')

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
    seconds_per_period=1.3,
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