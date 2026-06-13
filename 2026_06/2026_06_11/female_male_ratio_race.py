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

TOP_N = 10

FILE_NAME = "women_per_1000_men_bar_race.mp4"
TITLE = "Countries with the Highest Female-to-Male Ratio"
SUBTITLE = "Number of women per 1,000 men over time"
FOOTER_LEFT = "Women per 1,000 men"
FOOTER_RIGHT = "Source: UN World Population Prospects"
TIME_COL = "year"
CATEGORY_COL = "iso3_code"
VALUE_COL = "value"
LABEL_COL = "location_name"
FLAG_COL = "iso2_code"
X_LABEL = "Women per 1,000 men"
AUDIO_FILE = BASE_DIR / "Audio" / "Audio.mp3"
FLAGS_DIR = BASE_DIR / "flags_png"


"""Not every demographic chart is exciting 😅

Still, I found it interesting enough to animate.

This race shows the countries with the highest number of women per 1,000 men over time. Some of the names at the top may surprise you.

Data: UN World Population Prospects

#DataViz #Demographics #Population #Statistics #DataScience"""

query = """
            WITH pop AS (
                    SELECT
                            D.location_name,
                            D.iso2_code,
                            D.iso3_code,
                            D.sex_id,
                            D.[year],
                            D.[value]
                    FROM un.[data] D
                    LEFT JOIN ( SELECT is_country, [name] FROM worldbank.entities) ENT ON ENT.[name] = D.[location_name]
                    WHERE D.indicator_id = 49 AND D.variant_id = 4 AND ENT.is_country = 1 AND D.sex_id IN (1,2) 
                        AND D.iso2_code NOT IN ('TC','SX'))
            SELECT
                    CASE
                        WHEN [location_name] = 'Russian Federation' THEN 'Russia'
                        WHEN [location_name] = 'United Kingdom' THEN 'UK'
                        WHEN [location_name] = 'United States of America' THEN 'USA'
                        WHEN [location_name] = 'United Republic of Tanzania' THEN 'Tanzania'
                        WHEN [location_name] = 'Iran (Islamic Republic of)' THEN 'Iran'
                        WHEN [location_name] = 'Democratic Republic of the Congo' THEN 'Congo, Dem.Rep.'
                        WHEN [location_name] = 'Northern Mariana Islands' THEN 'N. Mariana Is.'
                        WHEN [location_name] = 'Central African Republic' THEN 'Central Afr. Rep.'
                        WHEN [location_name] = 'British Virgin Islands' THEN 'British Virgin Is.'
                        WHEN [location_name] = 'Bosnia and Herzegovina' THEN 'Bosnia & Herz.'
                        WHEN [location_name] = 'Sao Tome and Principe' THEN 'Sao Tome & Prin.'
                        WHEN [location_name] = 'Syrian Arab Republic' THEN 'Syria'
                        WHEN [location_name] = 'United Arab Emirates' THEN 'UAE'
                        WHEN [location_name] = 'Antigua and Barbuda' THEN 'Antigua & Barb.'
                        WHEN [location_name] = 'Trinidad and Tobago' THEN 'Trinidad & Tob.'
                        WHEN [location_name] = 'Dominican Republic' THEN 'Dom. Rep.'
                        WHEN [location_name] = 'Equatorial Guinea' THEN 'Eq. Guinea'
                        WHEN [location_name] = 'Brunei Darussalam' THEN 'Brunei'
                        WHEN [location_name] = 'French Polynesia' THEN 'Fr. Polynesia'
                        WHEN [location_name] = 'Marshall Islands' THEN 'Marshall Is.'
                        WHEN [location_name] = 'Papua New Guinea' THEN 'Papua N. Guinea'
                        WHEN [location_name] = 'North Macedonia' THEN 'N. Macedonia'
                        WHEN [location_name] = 'Solomon Islands' THEN 'Solomon Is.'
                        WHEN [location_name] = 'Cayman Islands' THEN 'Cayman Is.'
                        WHEN [location_name] = 'American Samoa' THEN 'Am. Samoa'
                    ELSE [location_name] 
                    END AS [location_name],
                    [year],
                    iso2_code,
                    iso3_code,
                    MAX(CASE WHEN sex_id = 2 THEN [value] END) AS females,
                    MAX(CASE WHEN sex_id = 1 THEN [value] END) AS males,
                    ROUND((MAX(CASE WHEN sex_id = 2 THEN [value] END) *1000 / NULLIF(MAX(CASE WHEN sex_id = 1 THEN [value] END),0) ),0,0) AS value
            FROM pop
            GROUP BY location_name, iso2_code, iso3_code, [year]
            HAVING MAX(CASE WHEN sex_id = 1 THEN [value] END) IS NOT NULL AND MAX(CASE WHEN sex_id = 2 THEN [value] END) IS NOT NULL
            ORDER BY len([location_name]) desc, value DESC;
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
    flags_dir=FLAGS_DIR)