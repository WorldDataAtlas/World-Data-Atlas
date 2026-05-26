from pathlib import Path
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from adjustText import adjust_text

DEFAULT_STYLE = {
    "fig_width": 16,
    "fig_height": 9,
    "dpi": 300,
    "font_family": "Segoe UI",
    "background_color": "#010103",
    "card_color": "#111827",
    "text_color": "#F8FAFC",
    "muted_color": "#94A3B8",
    "grid_color": "#243041",
    "title_font_size": 30,
    "subtitle_font_size": 17,
    "axis_font_size": 13,
    "tick_font_size": 12,
    "footer_font_size": 13,
    "label_font_size": 9,
    "point_alpha": 0.72,
    "point_size": 55,
    "point_edge_color": "#F8FAFC",
    "point_edge_width": 0.35,
    "axes_position": [0.08, 0.16, 0.80, 0.66],
    "title_x": 0.08,
    "title_y": 0.93,
    "subtitle_x": 0.08,
    "subtitle_y": 0.875,
    "footer_left_x": 0.08,
    "footer_right_x": 0.88,
    "footer_y": 0.055,
    "logo_x": 0.799,
    "logo_y": 0.86,
    "logo_zoom": 0.07,
    "logo_alpha": 0.9,}

def add_logo(fig, logo_path, x, y, zoom, alpha):
    if logo_path is None or not os.path.exists(logo_path): return
    logo = mpimg.imread(logo_path)
    imagebox = OffsetImage(logo, zoom=zoom, alpha=alpha)
    ab = AnnotationBbox(imagebox, (x, y), xycoords="figure fraction", frameon=False)
    fig.add_artist(ab)

def style_axis(ax, style):
    ax.set_facecolor(style["card_color"])
    for spine in ax.spines.values():
        spine.set_color(style["grid_color"])
        spine.set_linewidth(1.2)
    ax.tick_params(axis="x", colors=style["muted_color"], labelsize=style["tick_font_size"])
    ax.tick_params(axis="y", colors=style["muted_color"], labelsize=style["tick_font_size"])
    ax.grid(True, axis="both", color=style["grid_color"], linewidth=0.8, alpha=0.45)

def create_scatter_chart(
    df,
    output_file,
    x_col,
    y_col,
    title,
    subtitle,
    x_label,
    y_label,
    footer_left,
    footer_right,
    logo_path=None,
    style_overrides=None,
    x_log=True,
    y_log=True,
    x_min=None,
    x_max=None,
    y_min=None,
    y_max=None,
    x_ticks=7,
    y_ticks=7,
    point_color="#60A5FA",
    label_offset_x=1.06,
    label_offset_y=1.04,
    show_labels=True,):

    style = DEFAULT_STYLE.copy()
    if style_overrides: style.update(style_overrides)
    plt.rcParams["font.family"] = style["font_family"]
    plot_df = df.copy()
    plot_df = plot_df.replace([np.inf, -np.inf], np.nan)
    plot_df = plot_df.dropna(subset=[x_col, y_col])
    if x_log: plot_df = plot_df[plot_df[x_col] > 0]
    if y_log: plot_df = plot_df[plot_df[y_col] > 0]
    fig = plt.figure(figsize=(style["fig_width"], style["fig_height"]), dpi=style["dpi"])
    fig.patch.set_facecolor(style["background_color"])
    ax = fig.add_axes(style["axes_position"])
    style_axis(ax, style)
    if x_log: ax.set_xscale("log")
    if y_log: ax.set_yscale("log")
    ax.scatter(plot_df[x_col], plot_df[y_col], s=style["point_size"], color=point_color, alpha=style["point_alpha"], edgecolors=style["point_edge_color"], linewidths=style["point_edge_width"])
    if x_min is not None or x_max is not None: ax.set_xlim(x_min, x_max)
    if y_min is not None or y_max is not None: ax.set_ylim(y_min, y_max)
    ax.set_xlabel(x_label, color=style["muted_color"], fontsize=style["axis_font_size"])
    ax.set_ylabel(y_label, color=style["muted_color"], fontsize=style["axis_font_size"])
    if x_log: ax.xaxis.set_major_locator(mticker.LogLocator(numticks=x_ticks))
    else: ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=x_ticks))
    if y_log: ax.yaxis.set_major_locator(mticker.LogLocator(numticks=y_ticks))
    else: ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=y_ticks))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:,.0f}"))
    if show_labels and "label" in plot_df.columns:
        texts = []
        for _, row in plot_df.iterrows():
            label_x = row[x_col] * label_offset_x if x_log else row[x_col]
            label_y = row[y_col] * label_offset_y if y_log else row[y_col]
            text_obj = ax.text(label_x,label_y,str(row["label"]),fontsize=style["label_font_size"],color=style["text_color"],ha="left",va="bottom")
            texts.append(text_obj)
        adjust_text(texts,ax=ax,arrowprops=dict(arrowstyle="-",color=style["muted_color"],lw=0.5,alpha=0.45,))
    fig.text(style["title_x"], style["title_y"], title, fontsize=style["title_font_size"], weight="bold", color=style["text_color"], ha="left")
    fig.text(style["subtitle_x"], style["subtitle_y"], subtitle, fontsize=style["subtitle_font_size"], color=style["muted_color"], ha="left")
    fig.text(style["footer_left_x"], style["footer_y"], footer_left, fontsize=style["footer_font_size"], color=style["muted_color"], ha="left")
    fig.text(style["footer_right_x"], style["footer_y"], footer_right, fontsize=style["footer_font_size"], color=style["muted_color"], ha="right")
    add_logo(fig=fig, logo_path=logo_path, x=style["logo_x"], y=style["logo_y"], zoom=style["logo_zoom"], alpha=style["logo_alpha"])
    output_file = Path(output_file)
    output_file.parent.mkdir(exist_ok=True)
    plt.savefig(output_file, dpi=style["dpi"], facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output_file}")