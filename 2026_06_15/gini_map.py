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
from graph_map import create_world_map

# ============================================================

query = """
        WITH latest_gini AS (
        SELECT
                D.country_code,
                D.country_id,
                D.country_name,
                D.[year],
                D.[value],
                ROW_NUMBER() OVER (PARTITION BY D.country_code ORDER BY D.[year] DESC) AS rn
        FROM worldbank.data D
        INNER JOIN worldbank.entities E ON D.country_id = E.iso2_code
        WHERE D.indicator_code = 'SI.POV.GINI' AND D.[value] IS NOT NULL AND E.is_country = 1)
        SELECT
                country_code,
                country_id,
                country_name,
                [year],
                [value]
        FROM latest_gini
        WHERE rn = 1
        """


"""Not all countries are equally unequal.

The latest available Gini data show huge differences in income distribution across the world.

While some countries remain relatively egalitarian, others exhibit levels of inequality several times higher.

Source: World Bank"""


MAP_TITLE = "Income Inequality Around the World"
MAP_SUBTITLE = "Latest available Gini index by country"
MAP_SOURCE = "Source: World Bank"
FILE_NAME = "world_gini_latest_available.png"
LEGEND_MIN = 20
LEGEND_MAX = 65
COLOR_SCALE_LOW = "#22C55E"
COLOR_SCALE_HIGH = "#EF4444"


CONTINENT = None
MAP_X_LIMITS = (-1800000, 4000000)      #Europe
MAP_Y_LIMITS = (3200000, 8200000)       #Europe
MAP_X_LIMITS = None
MAP_Y_LIMITS = None
WORLD_URL="https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
WORLD_URL="https://naturalearth.s3.amazonaws.com/50m_cultural/ne_50m_admin_0_countries.zip"

# ============================================================

OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME
engine = sa.create_engine(s.connection_string, fast_executemany=True)
df = pd.read_sql(query, engine)
highlight_countries = (df.dropna(subset=["country_code", "value"]).set_index("country_code")["value"].to_dict())
create_world_map(
highlight_countries=highlight_countries,
map_title=MAP_TITLE,
map_subtitle=MAP_SUBTITLE,
source_text="Source:" + MAP_SOURCE,
watermark_text="World Data Atlas",
iso_column="ADM0_A3",
value_column="value",
fig_width=16,
fig_height=9,
dpi=300,
save_image=True,
output_file=OUTPUT_FILE,
output_bbox="tight",
output_face_color=True,
tight_layout=True,
show_axis=False,
map_x_limits=MAP_X_LIMITS,
map_y_limits=MAP_Y_LIMITS,
map_aspect="equal",
font_family="Segoe UI Variable",
title_font_size=20,
title_font_weight="normal",
title_pad=10,
subtitle_font_size=18,
subtitle_font_weight="normal",
source_font_size=10,
source_font_weight="normal",
watermark_font_size=32,
watermark_font_weight="bold",
watermark_alpha=0.020,
title_color="#F8FAFC",
subtitle_color="#94A3B8",
source_color="#64748B",
watermark_color="#FFFFFF",
subtitle_x=0.5,
subtitle_y=0.955,
subtitle_ha="center",
subtitle_va="bottom",
source_x=0.03,
source_y=0.08,
source_ha="left",
source_va="bottom",
watermark_x=0.5,
watermark_y=0.42,
watermark_ha="center",
watermark_va="center",
watermark_rotation=0,
color_background="#010103",
color_sea="#0B1220",
color_no_data="#1E293B",
color_border="#334155",
color_scale_low=COLOR_SCALE_LOW,
color_scale_high=COLOR_SCALE_HIGH,
highlight_border_color="#F3F4F6",
country_border_width=0.08,
highlight_border_width=0.12,
no_data_alpha=1.0,
highlight_alpha=1.0,
remove_antarctica=True,
antarctica_names=None,
show_ocean_background=False,
show_legend=True,
legend_title=None,
legend_title_font_size=8,
legend_title_color="#94A3B8",
legend_tick_font_size=8,
legend_tick_color="#94A3B8",
legend_border_color="#414854",
legend_border_width=0.8,
legend_fraction=0.014,
legend_pad=0.012,
legend_shrink=0.58,
legend_aspect=24,
legend_min_value=LEGEND_MIN,
legend_max_value=LEGEND_MAX,
legend_ticks = None,
legend_tick_labels = None,
fill_missing_value=0,
show_plot=False,
logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "5.png")),
logo_x=0.92,
logo_y=0.08,
logo_zoom=0.08,
logo_alpha=0.9,
continent_only = CONTINENT,
world_url=WORLD_URL)