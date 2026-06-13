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


"""Life expectancy bar race. To be honest, I don't think this format works particularly well for this dataset, but here it is anyway. 😄"""



TOP_N = 14

FILE_NAME = "highest_life_expectancy_bar_race_1950_2035.mp4"
TITLE = "Countries with the Highest Life Expectancy"
SUBTITLE = "Top 10 countries by life expectancy at birth, 1950–2035"
FOOTER_LEFT = "Life expectancy at birth, both sexes"
FOOTER_RIGHT = "Source: UN World Population Prospects"
TIME_COL = "year"
CATEGORY_COL = "iso3_code"
VALUE_COL = "value"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"
X_LABEL = "Life expectancy at birth, years"
DECIMAL_PLACES = 2
AUDIO_FILE = BASE_DIR / "Audio" / "Audio.mp3"
FLAGS_DIR = BASE_DIR / "flags_png"

query = """
    SELECT
        CASE
            WHEN D.[location_name] = 'Russian Federation' THEN 'Russia'
            WHEN D.[location_name] = 'United Kingdom' THEN 'UK'
            WHEN D.[location_name] = 'United States of America' THEN 'USA'
            WHEN D.[location_name] = 'United Republic of Tanzania' THEN 'Tanzania'
            WHEN D.[location_name] = 'Iran (Islamic Republic of)' THEN 'Iran'
            WHEN D.[location_name] = 'Democratic Republic of the Congo' THEN 'Congo, Dem.Rep.'
            WHEN D.[location_name] = 'Northern Mariana Islands' THEN 'N. Mariana Is.'
            WHEN D.[location_name] = 'Central African Republic' THEN 'Central Afr. Rep.'
            WHEN D.[location_name] = 'British Virgin Islands' THEN 'British Virgin Is.'
            WHEN D.[location_name] = 'Bosnia and Herzegovina' THEN 'Bosnia & Herz.'
            WHEN D.[location_name] = 'Sao Tome and Principe' THEN 'Sao Tome & Prin.'
            WHEN D.[location_name] = 'Syrian Arab Republic' THEN 'Syria'
            WHEN D.[location_name] = 'United Arab Emirates' THEN 'UAE'
            WHEN D.[location_name] = 'Antigua and Barbuda' THEN 'Antigua & Barb.'
            WHEN D.[location_name] = 'Trinidad and Tobago' THEN 'Trinidad & Tob.'
            WHEN D.[location_name] = 'Dominican Republic' THEN 'Dom. Rep.'
            WHEN D.[location_name] = 'Equatorial Guinea' THEN 'Eq. Guinea'
            WHEN D.[location_name] = 'Brunei Darussalam' THEN 'Brunei'
            WHEN D.[location_name] = 'French Polynesia' THEN 'Fr. Polynesia'
            WHEN D.[location_name] = 'Marshall Islands' THEN 'Marshall Is.'
            WHEN D.[location_name] = 'Papua New Guinea' THEN 'Papua N. Guinea'
            WHEN D.[location_name] = 'North Macedonia' THEN 'N. Macedonia'
            WHEN D.[location_name] = 'Solomon Islands' THEN 'Solomon Is.'
            WHEN D.[location_name] = 'Cayman Islands' THEN 'Cayman Is.'
            WHEN D.[location_name] = 'American Samoa' THEN 'Am. Samoa'
            WHEN D.[location_name] = 'China, Hong Kong SAR' THEN 'Hong Kong'
        ELSE [location_name] 
        END AS [location_name]
        ,D.[iso2_code]
        ,D.[iso3_code]
        ,D.[year]
        ,D.[value]
    FROM [World_Data_Atlas].[un].[data] AS D
    LEFT JOIN ( SELECT is_country, [name], [iso2_code] FROM worldbank.entities) ENT ON (ENT.[name] = D.[location_name]) OR (D.[iso2_code] = ENT.[iso2_code])
    WHERE   D.[variant_id] = 4 AND 
            D.[sex_id] = 3 AND 
            D.[indicator_id] = 75 AND
            D.[age_id] = 223 AND
            ENT.is_country = 1
    ORDER BY D.[year] desc
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
    decimal_places=DECIMAL_PLACES,
    color_palette=COLOR_PALETTE,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png")),
    include_music=True,
    music_path=AUDIO_FILE,
    music_volume=0.25,
    loop_music=True,
    flag_col=FLAG_COL,
    show_flags=True,
    flags_dir=FLAGS_DIR
)