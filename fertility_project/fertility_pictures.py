import pandas as pd
import sqlalchemy as sa
import ETL.settings as s
from modules.graphic_map import create_world_map


engine = sa.create_engine(s.connection_string, fast_executemany=True)

for year in range(1960, 2025):
    print(year)    
    query = """ SELECT 
        D.[country_code],
        D.[country_id],
        D.[value]
    FROM [World_Data_Atlas].[worldbank].[data] AS D
    LEFT JOIN (
        SELECT [wb_id],[iso2_code],[name],[is_country]
        FROM [World_Data_Atlas].[worldbank].[entities]
        WHERE [is_country] = 1
    ) AS ENT ON ENT.[name] = D.[country_name]
    WHERE D.[indicator_code] = 'SP.DYN.TFRT.IN' AND D.[year] = """ + str(year) + """ AND ENT.[is_country] = 1
    """
    df = pd.read_sql(query, engine)
    highlight_countries = (df.dropna(subset=["country_code", "value"]).set_index("country_code")["value"].to_dict())
    create_world_map(
        highlight_countries=highlight_countries,
        map_title="Fertility rate",
        map_subtitle=str(year),
        source_text="Source: World Bank",
        watermark_text="World Data Atlas",
        iso_column="ADM0_A3",
        value_column="value",
        fig_width=16,
        fig_height=8.5,
        dpi=450,
        save_image=True,
        output_file="world_fertility/world_fertility_" + str(year) + ".png",
        output_bbox="tight",
        output_face_color=True,
        tight_layout=True,
        show_axis=False,
        map_x_limits=None,
        map_y_limits=None,
        map_aspect="equal",
        font_family="Segoe UI Variable",
        title_font_size=16,
        title_font_weight="normal",
        title_pad=10,
        subtitle_font_size=14,
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
        subtitle_y=0.965,
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
        color_background="#0B1220",
        color_sea="#0B1220",
        color_no_data="#1E293B",
        color_border="#334155",
        color_scale_low="#3B82F6",
        color_scale_high="#FF0000",       
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
        legend_min_value=0,
        legend_max_value=9,
        legend_ticks=None,
        legend_tick_labels=None,
        fill_missing_value=0,
        show_plot=False,
        world_url="https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
    )