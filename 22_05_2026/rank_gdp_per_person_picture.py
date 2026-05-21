import pandas as pd
import sqlalchemy as sa
import sys
import os
etl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ETL"))
sys.path.insert(0, etl_path)
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modules"))
sys.path.insert(0, module_path)
import settings as s
from graphic_map import create_world_map

engine = sa.create_engine(s.connection_string, fast_executemany=True)

query = """ WITH ranked_data AS (
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
                WHERE [is_country] = 1) AS ENT
                ON ENT.[name] = D.[country_name]
            WHERE D.[indicator_code] = 'NY.GDP.PCAP.CD' AND ENT.[is_country] = 1 AND D.[year] IN (1990, 2024) AND D.[value] IS NOT NULL),
            pivoted AS (
            SELECT
                [country_code],
                [country_id],
                [country_name],
                MAX(CASE WHEN [year] = 1990 THEN gdp_per_capita END) AS gdp_1990,
                MAX(CASE WHEN [year] = 2024 THEN gdp_per_capita END) AS gdp_2024,
                MAX(CASE WHEN [year] = 1990 THEN gdp_rank END) AS rank_1990,
                MAX(CASE WHEN [year] = 2024 THEN gdp_rank END) AS rank_2024
            FROM ranked_data
            GROUP BY [country_code], [country_id], [country_name])
            SELECT 
                [country_code],
                [country_name],
                [country_id],
                (rank_1990 - rank_2024) AS [value]
            FROM pivoted
            WHERE rank_1990 IS NOT NULL AND rank_2024 IS NOT NULL"""

df = pd.read_sql(query, engine)
highlight_countries = (df.dropna(subset=["country_code", "value"]).set_index("country_code")["value"].to_dict())
create_world_map(
    highlight_countries=highlight_countries,
    map_title="Biggest GDP per Capita Ranking Changes ",
    map_subtitle='1990 - 2024',
    source_text="Source: World Bank",
    watermark_text="World Data Atlas",
    iso_column="ADM0_A3",
    value_column="value",
    fig_width=16,
    fig_height=9,
    dpi=450,
    save_image=True,
    output_file="22_05_2026\\results\\rank_gdp_per_person_1990_2024.png",
    output_bbox="tight",
    output_face_color=True,
    tight_layout=True,
    show_axis=False,
    map_x_limits=None,
    map_y_limits=None,
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
    color_scale_low="#F63B3B",
    color_scale_high="#37FF00",       
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
    legend_min_value=-80,
    legend_max_value=110,
    legend_ticks = None,
    legend_tick_labels = None,
    fill_missing_value=0,
    show_plot=False,
    logo_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Logos", "5.png")),
    logo_x=0.92,
    logo_y=0.08,
    logo_zoom=0.08,
    logo_alpha=0.9,
    world_url="https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip")