from pathlib import Path
import os
import requests
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import pandas as pd

FIG_WIDTH = 16
FIG_HEIGHT = 9
DPI = 300
FONT_FAMILY = "Segoe UI"
BACKGROUND_COLOR = "#010103"
CARD_COLOR = "#111827"
TEXT_COLOR = "#F8FAFC"
MUTED_COLOR = "#94A3B8"
GRID_COLOR = "#243041"
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
FLAG_X_OFFSET = 0.058
COUNTRY_X_OFFSET = 0.08
RANK_X_OFFSET_FROM_RIGHT = 0.08
CHANGE_X_OFFSET_FROM_RIGHT = 0.01
FOOTER_LEFT_X = 0.05
FOOTER_RIGHT_X = 0.94
FOOTER_Y = 0.03
LOGO_X = 1.05
LOGO_Y = 1.05
LOGO_ZOOM = 0.11
LOGO_ALPHA = 0.9
SHOW_FLAGS = True
FLAG_SIZE = "40x30"
FLAG_ZOOM = 0.45

def add_logo(fig, logo_path):
    if logo_path is None or not os.path.exists(logo_path): return
    logo = mpimg.imread(logo_path)
    imagebox = OffsetImage(logo, zoom=LOGO_ZOOM, alpha=LOGO_ALPHA)
    ab = AnnotationBbox(imagebox, (LOGO_X, LOGO_Y), xycoords="figure fraction", frameon=False)
    fig.add_artist(ab)

def get_flag_path(iso2, flags_dir):
    if not iso2 or len(str(iso2)) != 2: return None
    iso2 = str(iso2).lower()
    flags_dir = Path(flags_dir)
    flags_dir.mkdir(exist_ok=True)
    flag_path = flags_dir / f"{iso2}.png"
    if flag_path.exists(): return flag_path
    try:
        response = requests.get(f"https://flagcdn.com/{FLAG_SIZE}/{iso2}.png", timeout=10)
        if response.status_code == 200:
            flag_path.write_bytes(response.content)
            return flag_path
    except requests.RequestException: return None
    return None

def draw_panel(
    fig,
    data,
    x0,
    y0,
    width,
    height,
    title,
    color,
    top_n,
    label_col,
    flag_col,
    left_value_col,
    right_value_col,
    change_col,
    left_value_prefix="#",
    right_value_prefix="#",
    show_flags=True,
    flags_dir=None,):

    panel = FancyBboxPatch((x0, y0), width, height, boxstyle="round,pad=0.012,rounding_size=0.025", linewidth=1.2, edgecolor=GRID_COLOR, facecolor=CARD_COLOR, transform=fig.transFigure)
    fig.patches.append(panel)
    fig.text(x0 + 0.02, y0 + height - 0.065, title,fontsize=PANEL_TITLE_FONT_SIZE, weight="bold", color=color, ha="left")
    row_top = y0 + height - 0.12
    row_gap = (height - 0.1) / top_n
    for i, (_, row) in enumerate(data.iterrows(), start=1):
        y = row_top - (i - 1) * row_gap
        fig.text(x0 + ROW_NUMBER_X_OFFSET, y, f"{i:02d}", fontsize=ROW_NUMBER_FONT_SIZE, color=MUTED_COLOR, ha="left", va="center")
        if show_flags and flags_dir is not None and flag_col and flag_col in row.index:
            flag_path = get_flag_path(row[flag_col], flags_dir)
            if flag_path is not None:
                flag_img = mpimg.imread(flag_path)
                imagebox = OffsetImage(flag_img, zoom=FLAG_ZOOM)
                ab = AnnotationBbox(imagebox, (x0 + FLAG_X_OFFSET, y), xycoords=fig.transFigure, frameon=False, box_alignment=(0.5, 0.5))
                fig.add_artist(ab)
        if label_col and label_col in row.index:
            fig.text( x0 + COUNTRY_X_OFFSET, y, row[label_col], fontsize=COUNTRY_FONT_SIZE, weight="bold", color=TEXT_COLOR, ha="left", va="center")
        if left_value_col and right_value_col:
            if pd.notna(row[left_value_col]) and pd.notna(row[right_value_col]):
                fig.text( x0 + width - RANK_X_OFFSET_FROM_RIGHT, y, f"{left_value_prefix}{int(row[left_value_col])} → {right_value_prefix}{int(row[right_value_col])}", fontsize=RANK_FONT_SIZE, color=MUTED_COLOR, ha="right", va="center")
        if change_col and change_col in row.index:
            fig.text(x0 + width - CHANGE_X_OFFSET_FROM_RIGHT, y, f"{row[change_col]}", fontsize=CHANGE_FONT_SIZE, weight="bold", color=color, ha="right", va="center")

def create_double_table_chart(
    left_data,
    right_data,
    output_file,
    title,
    subtitle,
    footer_left,
    footer_right,
    left_panel_title,
    right_panel_title,
    label_col,
    flag_col,
    left_value_col,
    right_value_col,
    change_col,
    top_n=10,
    left_value_prefix="#",
    right_value_prefix="#",
    left_color = "#22C55E",
    right_color = "#EF4444", 
    logo_path=None,
    flags_dir=None,):

    plt.rcParams["font.family"] = FONT_FAMILY
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.axis("off")
    fig.text(HEADER_TITLE_X, HEADER_TITLE_Y, title, fontsize=TITLE_FONT_SIZE, weight="bold", color=TEXT_COLOR, ha="left")
    fig.text(HEADER_SUBTITLE_X, HEADER_SUBTITLE_Y, subtitle, fontsize=SUBTITLE_FONT_SIZE, color=MUTED_COLOR, ha="left")
    draw_panel(
        fig=fig,
        data=left_data,
        x0=LEFT_PANEL_X,
        y0=PANEL_Y,
        width=PANEL_WIDTH,
        height=PANEL_HEIGHT,
        title=left_panel_title,
        color=left_color,
        top_n=top_n,
        label_col=label_col,
        flag_col=flag_col,
        left_value_col=left_value_col,
        right_value_col=right_value_col,
        change_col=change_col,
        left_value_prefix=left_value_prefix,
        right_value_prefix=right_value_prefix,
        show_flags=SHOW_FLAGS,
        flags_dir=flags_dir)
    draw_panel(
        fig=fig,
        data=right_data,
        x0=RIGHT_PANEL_X,
        y0=PANEL_Y,
        width=PANEL_WIDTH,
        height=PANEL_HEIGHT,
        title=right_panel_title,
        color=right_color,
        top_n=top_n,
        label_col=label_col,
        flag_col=flag_col,
        left_value_col=left_value_col,
        right_value_col=right_value_col,
        change_col=change_col,
        left_value_prefix=left_value_prefix,
        right_value_prefix=right_value_prefix,
        show_flags=SHOW_FLAGS,
        flags_dir=flags_dir)
    fig.text(FOOTER_LEFT_X, FOOTER_Y, footer_left, fontsize=FOOTER_FONT_SIZE, color=MUTED_COLOR, ha="left")
    fig.text(FOOTER_RIGHT_X, FOOTER_Y, footer_right, fontsize=FOOTER_FONT_SIZE, color=MUTED_COLOR, ha="right")
    add_logo(fig, logo_path)
    output_file = Path(output_file)
    output_file.parent.mkdir(exist_ok=True)
    plt.savefig(output_file, dpi=DPI, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output_file}")