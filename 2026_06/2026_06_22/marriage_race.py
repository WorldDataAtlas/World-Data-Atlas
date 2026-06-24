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

"""Marriage rates have changed significantly across the world over the past decades.

Some countries have seen sharp declines, while others have remained relatively stable.

Share of women aged 15–49 who are married or in union.

Source: United Nations"""


TOP_N = 12
FILE_NAME = "currently_married_percent_race.mp4"
TITLE = "Currently Married Women"
SUBTITLE = "Share of women aged 15–49 who are married or in union"
FOOTER_LEFT = "Source: United Nations"
FOOTER_RIGHT = "WorldDataAtlas.com"
TIME_COL = "year"
CATEGORY_COL = "iso3_code"
VALUE_COL = "value"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"
X_LABEL = "% of women aged 15–49"
AUDIO_FILE = BASE_DIR / "Audio" / "Audio.mp3"
FLAGS_DIR = BASE_DIR / "flags_png"

query = """
    SELECT 
            CASE
                WHEN D.location_name = 'Venezuela (Bolivarian Republic of)' THEN 'Venezuela'
                WHEN D.location_name = 'Iran (Islamic Republic of)' THEN 'Iran'
                WHEN D.location_name = 'Russian Federation' THEN 'Russia'
                WHEN D.location_name = 'United Arab Emirates' THEN 'UAE'
                WHEN D.location_name = 'United States of America' THEN 'USA'
                WHEN D.location_name = 'Bolivia (Plurinational State of)' THEN 'Bolivia'
                WHEN D.location_name = 'Micronesia (Fed. States of)' THEN 'Micronesia'
                WHEN D.location_name = 'Solomon Islands' THEN 'Solomon Isls'
                WHEN D.location_name = 'United Republic of Tanzania' THEN 'Tanzania'
                WHEN D.location_name = 'Lao People''s Democratic Republic' THEN 'Laos'
                WHEN D.location_name = 'Republic of Moldova' THEN 'Moldova'
                WHEN D.location_name = 'Dem. People''s Rep. of Korea' THEN 'North Korea'
                WHEN D.location_name = 'Northern Mariana Islands' THEN 'North Korea'
                ELSE D.location_name
            END AS location_name
        ,D.[iso2_code]
        ,D.[iso3_code]
        ,D.[indicator_id]
        ,D.[indicator_name]
        ,D.[year]
        ,D.[value]
    FROM [World_Data_Atlas].[un].[data] as D
    LEFT JOIN worldbank.entities ENT ON D.iso2_code = ENT.iso2_code AND D.iso3_code = ENT.[wb_id]
    WHERE indicator_id = 42 and [variant_id] = 4 and ENT.is_country = 1 and D.[iso2_code] not in ('MP')
    ORDER BY D.[value]
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