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
💰 Which South American countries have seen the biggest gains in living standards?

Watch the Top 10 South American countries by GDP per capita (PPP) from 1990 to 2024.

Source: World Bank | #WorldDataAtlas
"""

TOP_N = 10
FILE_NAME = "south_america_gdp_per_capita_ppp_race.mp4"
TITLE = "GDP per Capita (PPP)"
SUBTITLE = "Top 10 South American countries, International dollars (current PPP), 1990–2024"
FOOTER_LEFT = "Purchasing Power Parity (PPP), current international $"
FOOTER_RIGHT = "Source: World Bank"
TIME_COL = "year"
CATEGORY_COL = "country_code"
VALUE_COL = "value"
LABEL_COL = "country_name"
FLAG_COL = "country_id"
X_LABEL = "International $ (PPP)"
AUDIO_FILE = BASE_DIR / "Audio" / "Audio.mp3"
FLAGS_DIR = BASE_DIR / "flags_png"

query = """
SELECT [country_code]
      ,[country_id]
      ,CASE 
        WHEN [country_name] = 'Bolivia (Plurinational State of)' THEN 'Bolivia'
        WHEN [country_name] = 'Venezuela (Bolivarian Republic of)' THEN 'Venezuela'
        WHEN [country_name] = 'Central African Republic' THEN 'CAF'
     ELSE [country_name] END AS [country_name]
      ,[year]
      ,[value]
FROM [World_Data_Atlas].[worldbank].[data]
WHERE [indicator_code] = 'NY.GDP.PCAP.PP.CD' AND [country_code] IN ('ARG','BOL','BRA','CHL','COL','ECU','GUY','PRY','PER','SUR','URY','VEN')
ORDER BY [year] DESC
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
    decimal_places=0,
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