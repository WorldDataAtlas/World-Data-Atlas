from pathlib import Path
import sys
import pandas as pd
import sqlalchemy as sa
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
BASE_DIR = Path(__file__).resolve().parent
etl_path = (BASE_DIR.parent / "ETL").resolve()
sys.path.insert(0, str(etl_path))
import settings as s
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import requests
import os

query = """
    WITH ranked_data AS (
        SELECT
            D.[country_code],
            D.[country_id],
            D.[country_name],
            D.[year],
            CAST(D.[value] AS FLOAT) AS gdp_per_capita,
            RANK() OVER (PARTITION BY D.[year] ORDER BY D.[value] DESC) AS gdp_rank
        FROM [World_Data_Atlas].[worldbank].[data] AS D
        LEFT JOIN (
            SELECT
                [wb_id],
                [iso2_code],
                [name],
                [is_country]
            FROM [World_Data_Atlas].[worldbank].[entities]
            WHERE [is_country] = 1) AS ENT ON ENT.[name] = D.[country_name]
        WHERE D.[indicator_code] = 'NY.GDP.PCAP.CD' AND ENT.[is_country] = 1 AND D.[year] IN (1990, 2024) AND D.[value] IS NOT NULL),
    pivoted AS (    SELECT
                        [country_code],
                        [country_id],
                        [country_name],
                        MAX(CASE WHEN [year] = 1990 THEN gdp_rank END) AS rank_1990,
                        MAX(CASE WHEN [year] = 2024 THEN gdp_rank END) AS rank_2024
                    FROM ranked_data
                    GROUP BY [country_code], [country_id], [country_name]),
    rank_changes AS (    SELECT
                            [country_code],
                            [country_id],
                            [country_name],
                            rank_1990,
                            rank_2024,
                            rank_1990 - rank_2024 AS rank_change
                        FROM pivoted
                        WHERE rank_1990 IS NOT NULL AND rank_2024 IS NOT NULL)

    SELECT *
    FROM (  SELECT TOP (10) *
            FROM rank_changes
            ORDER BY rank_change DESC) AS climbers
    UNION ALL
    SELECT *
    FROM (  SELECT TOP (10) *
            FROM rank_changes
            ORDER BY rank_change ASC) AS fallers;"""

START_YEAR = 1990
END_YEAR = 2024
TOP_N = 10

FLAGS_DIR = BASE_DIR / "flags_png"
FLAGS_DIR.mkdir(exist_ok=True)

FLAG_SIZE = "40x30"
FLAG_ZOOM = 0.42
FLAG_X_OFFSET = 0.075
COUNTRY_X_OFFSET = 0.105

LOGO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "4.png"))
LOGO_X = 1.01
LOGO_Y = 1.01
LOGO_ZOOM = 0.11
LOGO_ALPHA = 0.9

FLAG_ZOOM = 0.45
FLAG_X_OFFSET = 0.058
COUNTRY_X_OFFSET = 0.105

OUTPUT_FILENAME = f"gdp_rank_change_{START_YEAR}_{END_YEAR}.png"

TITLE = "How the Global Wealth Rankings Changed"
SUBTITLE = f"GDP per capita ranking, {START_YEAR} → {END_YEAR}"
FOOTER_LEFT = "Metric: GDP per capita, current US$ · Ranking among countries with available World Bank data"
FOOTER_RIGHT = "Source: World Bank"

LEFT_PANEL_TITLE = "Biggest Climbers"
RIGHT_PANEL_TITLE = "Biggest Fallers"

SHOW_FLAGS = True

FIG_WIDTH = 16
FIG_HEIGHT = 9
DPI = 300

FONT_FAMILY = "Segoe UI"

BACKGROUND_COLOR = "#010103"
CARD_COLOR = "#111827"
TEXT_COLOR = "#F8FAFC"
MUTED_COLOR = "#94A3B8"
GRID_COLOR = "#243041"
CLIMBER_COLOR = "#22C55E"
FALLER_COLOR = "#EF4444"

TITLE_FONT_SIZE = 30
SUBTITLE_FONT_SIZE = 17
PANEL_TITLE_FONT_SIZE = 20
ROW_NUMBER_FONT_SIZE = 14
COUNTRY_FONT_SIZE = 18
RANK_FONT_SIZE = 15
CHANGE_FONT_SIZE = 16
FOOTER_FONT_SIZE = 14

HEADER_TITLE_X = 0.05
HEADER_TITLE_Y = 1.02
HEADER_SUBTITLE_X = 0.05
HEADER_SUBTITLE_Y = 0.94

LEFT_PANEL_X = 0.06
RIGHT_PANEL_X = 0.52
PANEL_Y = 0.13
PANEL_WIDTH = 0.42
PANEL_HEIGHT = 0.75

ROW_NUMBER_X_OFFSET = 0.02
COUNTRY_X_OFFSET = 0.075
RANK_X_OFFSET_FROM_RIGHT = 0.08
CHANGE_X_OFFSET_FROM_RIGHT = 0.01

FOOTER_LEFT_X = 0.05
FOOTER_RIGHT_X = 0.94
FOOTER_Y = 0.03

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / OUTPUT_FILENAME

def add_logo(fig):
    logo = mpimg.imread(LOGO_PATH)
    imagebox = OffsetImage(logo, zoom=LOGO_ZOOM, alpha=LOGO_ALPHA)
    ab = AnnotationBbox(imagebox, (LOGO_X, LOGO_Y), xycoords="figure fraction", frameon=False)
    fig.add_artist(ab)

def get_flag_path(iso2):
    if not iso2 or len(str(iso2)) != 2: return None
    iso2 = str(iso2).lower()
    flag_path = FLAGS_DIR / f"{iso2}.png"
    if flag_path.exists(): return flag_path
    try:
        response = requests.get(f"https://flagcdn.com/{FLAG_SIZE}/{iso2}.png", timeout=10)
        if response.status_code == 200:
            flag_path.write_bytes(response.content)
            return flag_path
    except requests.RequestException: return None
    return None

engine = sa.create_engine(s.connection_string)
df = pd.read_sql(query, engine)

climbers = df[df["rank_change"] > 0].sort_values("rank_change", ascending=False)
fallers = df[df["rank_change"] < 0].sort_values("rank_change", ascending=True)
plt.rcParams["font.family"] = FONT_FAMILY
fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
fig.patch.set_facecolor(BACKGROUND_COLOR)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor(BACKGROUND_COLOR)
ax.axis("off")

fig.text(HEADER_TITLE_X,HEADER_TITLE_Y,TITLE,fontsize=TITLE_FONT_SIZE,weight="bold",color=TEXT_COLOR,ha="left")
fig.text(HEADER_SUBTITLE_X,HEADER_SUBTITLE_Y,SUBTITLE,fontsize=SUBTITLE_FONT_SIZE,color=MUTED_COLOR,ha="left")

def draw_panel(data, x0, y0, width, height, title, color, direction_symbol):
    panel = FancyBboxPatch((x0, y0),width,height,boxstyle="round,pad=0.012,rounding_size=0.025",linewidth=1.2,edgecolor=GRID_COLOR,facecolor=CARD_COLOR,transform=fig.transFigure)
    fig.patches.append(panel)
    fig.text(x0 + 0.02, y0 + height - 0.065, title, fontsize=PANEL_TITLE_FONT_SIZE, weight="bold", color=color, ha="left")
    row_top = y0 + height - 0.12
    row_gap = (height - 0.1) / TOP_N
    for i, (_, row) in enumerate(data.iterrows(), start=1):
        y = row_top - (i - 1) * row_gap
        country_label = row["country_name"]
        flag_path = get_flag_path(row["country_id"])
        rank_1990 = int(row["rank_1990"])
        rank_2024 = int(row["rank_2024"])
        change = int(row["rank_change"])
        fig.text(x0 + ROW_NUMBER_X_OFFSET,y,f"{i:02d}",fontsize=ROW_NUMBER_FONT_SIZE,color=MUTED_COLOR,ha="left",va="center")
        if SHOW_FLAGS and flag_path is not None:
            flag_img = mpimg.imread(flag_path)
            imagebox = OffsetImage(flag_img, zoom=FLAG_ZOOM)
            ab = AnnotationBbox(imagebox,(x0 + FLAG_X_OFFSET, y),xycoords=fig.transFigure,frameon=False,box_alignment=(0.5, 0.5))
            fig.add_artist(ab)
        fig.text(x0 + COUNTRY_X_OFFSET,y,country_label,fontsize=COUNTRY_FONT_SIZE,weight="bold",color=TEXT_COLOR,ha="left",va="center")
        fig.text(x0 + width - RANK_X_OFFSET_FROM_RIGHT,y,f"#{rank_1990} → #{rank_2024}",fontsize=RANK_FONT_SIZE,color=MUTED_COLOR,ha="right",va="center")
        fig.text(x0 + width - CHANGE_X_OFFSET_FROM_RIGHT,y,f"{direction_symbol}{abs(change)}",fontsize=CHANGE_FONT_SIZE,weight="bold",color=color,ha="right",va="center")

draw_panel(data=climbers,x0=LEFT_PANEL_X,y0=PANEL_Y,width=PANEL_WIDTH,height=PANEL_HEIGHT,title=LEFT_PANEL_TITLE,color=CLIMBER_COLOR,direction_symbol="+")
draw_panel(data=fallers,x0=RIGHT_PANEL_X,y0=PANEL_Y,width=PANEL_WIDTH,height=PANEL_HEIGHT,title=RIGHT_PANEL_TITLE,color=FALLER_COLOR,direction_symbol="-")
fig.text(FOOTER_LEFT_X,FOOTER_Y,FOOTER_LEFT,fontsize=FOOTER_FONT_SIZE,color=MUTED_COLOR,ha="left")
fig.text(FOOTER_RIGHT_X,FOOTER_Y,FOOTER_RIGHT,fontsize=FOOTER_FONT_SIZE,color=MUTED_COLOR,ha="right")
add_logo(fig)
plt.savefig(OUTPUT_FILE,dpi=DPI,facecolor=fig.get_facecolor(),bbox_inches="tight")
plt.close(fig)
print(f"Saved: {OUTPUT_FILE}")