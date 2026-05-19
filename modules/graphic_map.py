import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize


def create_world_map(
    highlight_countries,
    map_title="Developing a map look",
    map_subtitle="Dummy test",
    source_text="Source: worldbank.org",
    watermark_text="World Data Atlas",
    iso_column="ADM0_A3",
    value_column="value",
    fig_width=16,
    fig_height=8.5,
    dpi=300,
    save_image=False,
    output_file="world_map_custom.png",
    output_bbox="tight",
    output_face_color=True,
    tight_layout=True,
    show_axis=False,
    map_x_limits=None,
    map_y_limits=None,
    map_aspect="equal",
    font_family="Segoe UI Variable",
    title_font_size=20,
    title_font_weight="bold",
    title_pad=10,
    subtitle_font_size=10,
    subtitle_font_weight="normal",
    source_font_size=7,
    source_font_weight="normal",
    watermark_font_size=32,
    watermark_font_weight="bold",
    watermark_alpha=0.012,
    title_color="#F8FAFC",
    subtitle_color="#94A3B8",
    source_color="#64748B",
    watermark_color="#FFFFFF",
    subtitle_x=0.5,
    subtitle_y=0.995,
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
    color_background="#0B0F14",
    color_sea="#0B0F14",
    color_no_data="#1B222B",
    color_border="#2D3744",
    color_scale_low="#4F8FE8",
    color_scale_high="#F2A51A",
    highlight_border_color="#F3F4F6",
    country_border_width=0.10,
    highlight_border_width=0.22,
    no_data_alpha=1.0,
    highlight_alpha=1.0,
    remove_antarctica=True,
    antarctica_names=None,
    show_ocean_background=True,
    show_legend=True,
    legend_title="Value",
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
    legend_min_value=None,
    legend_max_value=None,
    legend_ticks=None,
    legend_tick_labels=None,
    fill_missing_value=0,
    show_plot=True,
    world_url="https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"):

    if antarctica_names is None: antarctica_names = ["Antarctica"]

    plt.rcParams["font.family"] = font_family

    world = gpd.read_file(world_url)
    world = world.to_crs("+proj=robin")

    if remove_antarctica: world = world[~world["ADMIN"].isin(antarctica_names)]

    df = pd.DataFrame([{iso_column: iso, value_column: value} for iso, value in highlight_countries.items()])
    merged = world.merge(df, on=iso_column, how="left")
    merged[value_column] = merged[value_column].fillna(fill_missing_value)
    mentioned = merged[merged[iso_column].isin(highlight_countries.keys())]
    not_mentioned = merged[~merged[iso_column].isin(highlight_countries.keys())]
    custom_cmap = LinearSegmentedColormap.from_list("custom_scale",[color_scale_low, color_scale_high])
    if legend_min_value is None: legend_min = merged[value_column].min()
    else: legend_min = legend_min_value
    if legend_max_value is None: legend_max = merged[value_column].max()
    else: legend_max = legend_max_value
    norm = Normalize(vmin=legend_min, vmax=legend_max)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    fig.patch.set_facecolor(color_background)
    if show_ocean_background: ax.set_facecolor(color_sea)
    if map_aspect is not None: ax.set_aspect(map_aspect)
    not_mentioned.plot(ax=ax, color=color_no_data, edgecolor=color_border, linewidth=country_border_width, alpha=no_data_alpha)
    mentioned.plot(
        ax=ax,
        column=value_column,
        cmap=custom_cmap,
        norm=norm,
        edgecolor=highlight_border_color,
        linewidth=highlight_border_width,
        alpha=highlight_alpha,
        legend=False)

    if show_legend:
        sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=norm)
        sm._A = []
        cbar = fig.colorbar(sm, ax=ax, fraction=legend_fraction, pad=legend_pad, shrink=legend_shrink, aspect=legend_aspect)
        cbar.set_label(legend_title, color=legend_title_color, fontsize=legend_title_font_size)
        cbar.ax.tick_params(labelsize=legend_tick_font_size, colors=legend_tick_color)
        cbar.outline.set_edgecolor(legend_border_color)
        cbar.outline.set_linewidth(legend_border_width)
        if legend_ticks is not None: cbar.set_ticks(legend_ticks)
        if legend_tick_labels is not None: cbar.set_ticklabels(legend_tick_labels)

    ax.set_title(map_title, fontsize=title_font_size, color=title_color, weight=title_font_weight, pad=title_pad)

    if map_subtitle:
        ax.text(
            subtitle_x,
            subtitle_y,
            map_subtitle,
            transform=ax.transAxes,
            ha=subtitle_ha,
            va=subtitle_va,
            fontsize=subtitle_font_size,
            color=subtitle_color,
            weight=subtitle_font_weight)

    if source_text:
        ax.text(
            source_x,
            source_y,
            source_text,
            transform=ax.transAxes,
            ha=source_ha,
            va=source_va,
            fontsize=source_font_size,
            color=source_color,
            weight=source_font_weight)

    if watermark_text:
        ax.text(
            watermark_x,
            watermark_y,
            watermark_text,
            transform=ax.transAxes,
            ha=watermark_ha,
            va=watermark_va,
            fontsize=watermark_font_size,
            color=watermark_color,
            weight=watermark_font_weight,
            alpha=watermark_alpha,
            rotation=watermark_rotation)

    if map_x_limits is not None: ax.set_xlim(map_x_limits)
    if map_y_limits is not None: ax.set_ylim(map_y_limits)
    if not show_axis: ax.axis("off")
    if tight_layout: plt.tight_layout()
    if save_image:
        save_facecolor = fig.get_facecolor() if output_face_color else None
        plt.savefig(output_file, dpi=dpi, bbox_inches=output_bbox, facecolor=save_facecolor)
    if show_plot: plt.show()
    else: plt.close(fig)

"""

ISO_COLUMN
    Name of the country ISO code column inside the shapefile dataset.
    Usually: "ISO_A3"

VALUE_COLUMN
    Name of the numeric value column used in the temporary pandas dataframe.
    Usually: "value"

WORLD_URL
    URL to the Natural Earth world shapefile dataset.
    Contains:
        country borders
        country names
        geometry polygons

FIG_WIDTH
    Width of the final figure in inches.
    Higher value: wider image

FIG_HEIGHT
    Height of the final figure in inches.
    Higher value: taller image

DPI
    Dots per inch (image resolution).
    Typical values:
        100 = fast preview
        200 = good quality
        300+ = publication quality

SAVE_IMAGE
    If True: saves the image to disk
    If False: only displays it

OUTPUT_FILE
    Output filename for saved image.
    Example: "world_map.png"

OUTPUT_BBOX
    Bounding box mode when saving.
    Usually: "tight"
    Effect: removes extra whitespace around image

OUTPUT_FACE_COLOR
    If True: preserves configured background color when exporting
    If False: exported background may become transparent/default

TIGHT_LAYOUT
    Automatically optimizes spacing between plot elements.
    Recommended: True

SHOW_AXIS
    Show matplotlib axes.
    For maps usually: False

MAP_ASPECT
    Controls aspect ratio of map.
    Options:
        "equal" = realistic proportions
        "auto" = matplotlib decides
        None = no explicit control
    Recommended: "equal"

MAP_X_LIMITS
    Horizontal crop limits.
    Example: (-180, 180)
    If None: automatic

MAP_Y_LIMITS
    Vertical crop limits.
    Example: (-60, 85)
    If None: automatic

FONT_FAMILY
    Global font family used for all text.
    Examples: "DejaVu Sans", "Arial", "Calibri"

TITLE_FONT_SIZE
    Main title font size.

TITLE_FONT_WEIGHT
    Main title thickness.
    Examples:"normal", "bold", "light"

TITLE_PAD
    Vertical spacing between title and plot.

SUBTITLE_FONT_SIZE
    Subtitle font size.

SUBTITLE_FONT_WEIGHT
    Subtitle thickness.

SOURCE_FONT_SIZE
    Source text font size.

SOURCE_FONT_WEIGHT
    Source text thickness.

WATERMARK_FONT_SIZE
    Watermark font size.

WATERMARK_FONT_WEIGHT
    Watermark font thickness.

WATERMARK_ALPHA
    Watermark transparency.
    Range:
        0.0 = invisible
        1.0 = fully opaque
    Recommended:
        0.01 to 0.08

TITLE_COLOR
    Main title color.

SUBTITLE_COLOR
    Subtitle color.

SOURCE_COLOR
    Source text color.

WATERMARK_COLOR
    Watermark text color.

SUBTITLE_X
SUBTITLE_Y
    Subtitle position in axes coordinates.
    Examples:
        0.5 = centered horizontally
        1.0+ = above map

SUBTITLE_HA
    Subtitle horizontal alignment.
    Options: "left", "center", "right"

SUBTITLE_VA
    Subtitle vertical alignment.
    Options: "top", "center", "bottom"

SOURCE_X
SOURCE_Y
    Source text position.

SOURCE_HA
SOURCE_VA
    Source text alignment.

WATERMARK_X
WATERMARK_Y
    Watermark position.
    Example: 0.5, 0.5 = centered

WATERMARK_HA
WATERMARK_VA
    Watermark alignment.

WATERMARK_ROTATION
    Watermark rotation angle in degrees.

COLOR_BACKGROUND
    Whole image background color.

COLOR_SEA
    Ocean / map background color.

COLOR_NO_DATA
    Color used for countries not present in HIGHLIGHT_COUNTRIES.

COLOR_BORDER
    Border color for non-highlighted countries.

COLOR_SCALE_LOW
    Low end of gradient scale.

COLOR_SCALE_HIGH
    High end of gradient scale.

HIGHLIGHT_BORDER_COLOR
    Border color for highlighted countries.

COUNTRY_BORDER_WIDTH
    Border thickness for normal countries.

HIGHLIGHT_BORDER_WIDTH
    Border thickness for highlighted countries.

NO_DATA_ALPHA
    Transparency for countries without data.
    Range: 0.0 to 1.0

HIGHLIGHT_ALPHA
    Transparency for highlighted countries.
    Range: 0.0 to 1.0

REMOVE_ANTARCTICA
    If True: removes Antarctica from map.
    Useful for cleaner composition.

ANTARCTICA_NAMES
    List of country names treated as Antarctica.

SHOW_OCEAN_BACKGROUND
    If True: applies ocean background color.

SHOW_LEGEND
    If True: shows color scale legend.

LEGEND_TITLE
    Legend title text.

LEGEND_TITLE_FONT_SIZE
    Legend title font size.

LEGEND_TITLE_COLOR
    Legend title color.

LEGEND_TICK_FONT_SIZE
    Legend tick label size.

LEGEND_TICK_COLOR
    Legend tick label color.

LEGEND_BORDER_COLOR
    Legend outline color.

LEGEND_BORDER_WIDTH
    Legend outline thickness.

LEGEND_FRACTION
    Legend width relative to figure.
    Smaller: thinner legend

LEGEND_PAD
    Space between map and legend.

LEGEND_SHRINK
    Legend height scaling.
    Smaller: shorter legend

LEGEND_ASPECT
    Legend height-to-width ratio.
    Higher: taller and narrower legend

LEGEND_MIN_VALUE
LEGEND_MAX_VALUE
    Manual color scale boundaries.
    If None: automatically calculated from data

LEGEND_TICKS
    Custom tick positions.
    Example: [0, 0.5, 1]

LEGEND_TICK_LABELS
    Custom labels for legend ticks.
    Example: ["Low", "Medium", "High"]

FILL_MISSING_VALUE
    Value assigned to countries with no matching metric.
    Usually: 0

PLOT_ONLY_MENTIONED_WITH_SCALE
    Logical toggle intended for controlling whether only explicitly
    mentioned countries use the gradient scale.
    Currently optional unless explicitly implemented.

"""