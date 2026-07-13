from pathlib import Path
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

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
    "legend_font_size": 13,
    "footer_font_size": 13,
    "line_width": 3.2,
    "marker_alpha": 0.85,
    "axes_position": [0.08, 0.16, 0.80, 0.66],
    "title_x": 0.08,
    "title_y": 0.93,
    "subtitle_x": 0.08,
    "subtitle_y": 0.875,
    "footer_left_x": 0.08,
    "footer_right_x": 0.88,
    "footer_y": 0.055,
    "logo_x": 0.80,
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
    ax.tick_params(axis="x",colors=style["muted_color"],labelsize=style["tick_font_size"])
    ax.tick_params(axis="y",colors=style["muted_color"],labelsize=style["tick_font_size"])
    ax.grid(True,axis="y",color=style["grid_color"],linewidth=0.9,alpha=0.55)
    ax.grid(True,axis="x",color=style["grid_color"],linewidth=0.5,alpha=0.18)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:.0f}"))

def create_multi_line_chart(
    df,
    output_file,
    x_col,
    y_col,
    series_col,
    series_config,
    title,
    subtitle,
    y_label,
    footer_left,
    footer_right,
    logo_path=None,
    style_overrides=None,
    x_padding_right=1,
    y_min=None,
    y_max=None,
    x_ticks=8,
    y_ticks=7,
    show_markers=True,
    show_legend=True,
    marker_size=15,
    legend_location= "upper right"):

    style = DEFAULT_STYLE.copy()
    if style_overrides: style.update(style_overrides)
    plt.rcParams["font.family"] = style["font_family"]
    fig = plt.figure(figsize=(style["fig_width"], style["fig_height"]),dpi=style["dpi"])
    fig.patch.set_facecolor(style["background_color"])
    ax = fig.add_axes(style["axes_position"])
    style_axis(ax, style)
    for item in series_config:
        source_value = item["source_value"]
        label = item.get("label", source_value)
        color = item["color"]
        subset = df[df[series_col] == source_value].sort_values(x_col)
        if subset.empty: continue
        ax.plot(subset[x_col],subset[y_col],color=color,linewidth=item.get("line_width", style["line_width"]),label=label,solid_capstyle="round")
        if show_markers:
            ax.scatter(subset[x_col], subset[y_col], color=color, s=marker_size, alpha=item.get("marker_alpha", style["marker_alpha"]), zorder=5)
    start_year = int(df[x_col].min())
    end_year = int(df[x_col].max())
    ax.set_xlim(start_year, end_year + x_padding_right)
    if y_min is None: y_min = df[y_col].min() * 1.12 if df[y_col].min() < 0 else 0
    if y_max is None: y_max = df[y_col].max() * 1.12   
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel("")
    ax.set_ylabel(y_label, color=style["muted_color"], fontsize=style["axis_font_size"])
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True, nbins=x_ticks))
    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=y_ticks))
    if show_legend:
        legend = ax.legend(loc=legend_location, frameon=False, fontsize=style["legend_font_size"], labelcolor=style["text_color"])
        for text in legend.get_texts(): text.set_color(style["text_color"])
    fig.text(style["title_x"], style["title_y"], title, fontsize=style["title_font_size"], weight="bold", color=style["text_color"], ha="left")
    fig.text(style["subtitle_x"], style["subtitle_y"], subtitle, fontsize=style["subtitle_font_size"], color=style["muted_color"], ha="left")
    fig.text(style["footer_left_x"], style["footer_y"], footer_left, fontsize=style["footer_font_size"], color=style["muted_color"], ha="left")
    fig.text(style["footer_right_x"], style["footer_y"], footer_right, fontsize=style["footer_font_size"], color=style["muted_color"], ha="right")
    add_logo(fig=fig, logo_path=logo_path, x=style["logo_x"], y=style["logo_y"], zoom=style["logo_zoom"], alpha=style["logo_alpha"])
    output_file = Path(output_file)
    output_file.parent.mkdir(exist_ok=True)
    plt.savefig(output_file,dpi=style["dpi"],facecolor=fig.get_facecolor(),bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output_file}")