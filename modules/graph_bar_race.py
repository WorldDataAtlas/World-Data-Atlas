from pathlib import Path
import os
import requests
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.animation import FuncAnimation, FFMpegWriter
import imageio_ffmpeg
try:
    from moviepy import VideoFileClip, AudioFileClip, concatenate_audioclips
    from moviepy.audio.fx.AudioFadeOut import AudioFadeOut
except ImportError:
    VideoFileClip, AudioFileClip, concatenate_audioclips, AudioFadeOut = None, None, None, None
mpl.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()

FIG_WIDTH = 16
FIG_HEIGHT = 9
DPI = 200
FONT_FAMILY = "Segoe UI"
BACKGROUND_COLOR = "#010103"
CARD_COLOR = "#111827"
TEXT_COLOR = "#F8FAFC"
MUTED_COLOR = "#94A3B8"
GRID_COLOR = "#243041"
TITLE_FONT_SIZE = 30
SUBTITLE_FONT_SIZE = 17
AXIS_FONT_SIZE = 13
TICK_FONT_SIZE = 12
FOOTER_FONT_SIZE = 13
LABEL_FONT_SIZE = 15
VALUE_FONT_SIZE = 14
PERIOD_FONT_SIZE = 68
AXES_POSITION = [0.23, 0.16, 0.64, 0.66]
TITLE_X = 0.08
TITLE_Y = 0.93
SUBTITLE_X = 0.08
SUBTITLE_Y = 0.875
FOOTER_LEFT_X = 0.08
FOOTER_RIGHT_X = 0.88
FOOTER_Y = 0.055
LOGO_X = 0.9
LOGO_Y = 0.905
LOGO_ZOOM = 0.087
LOGO_ALPHA = 0.9
BAR_ALPHA = 0.90
BAR_HEIGHT = 0.78
DEFAULT_BAR_COLOR = "#60A5FA"
VALUE_PADDING = 0.015
X_AXIS_MARGIN = 0.16
PERIOD_X = 0.86
PERIOD_Y = 0.22
PERIOD_ALPHA = 0.36
SHOW_GRID = True
GRID_ALPHA = 0.35
FLAG_SIZE = "40x30"
FLAG_ZOOM = 0.45
FLAG_X = -0.17
LABEL_X = -0.135
DEFAULT_COLOR_PALETTE = ["#2563EB","#16A34A","#F59E0B","#DC2626","#A855F7","#06B6D4","#84CC16","#F97316","#EC4899","#14B8A6"]

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

def format_value(value, value_format=None, decimal_places=0):
    if callable(value_format): return value_format(value)
    if value_format is not None: return value_format.format(value)
    return f"{value:,.{decimal_places}f}"

def ease_in_out(progress): return progress * progress * (3 - 2 * progress)

def build_category_maps(category_config):
    label_map, color_map = {}, {}
    if category_config is None: return label_map, color_map
    for item in category_config:
        source_value = item.get("source_value")
        label = item.get("label", source_value)
        color = item.get("color")
        label_map[source_value] = label
        if color is not None: color_map[source_value] = color
    return label_map, color_map

def assign_category_colors(df, category_col, color_col, color_palette):
    df = df.copy()
    categories = sorted(df[category_col].dropna().unique())
    auto_color_map = {category: color_palette[i % len(color_palette)] for i, category in enumerate(categories)}
    df[color_col] = df[color_col].fillna(df[category_col].map(auto_color_map))
    return df

def prepare_bar_race_data(df,time_col,category_col,value_col,category_config=None,fill_missing_value=0,flag_col=None,color_palette=None):
    plot_df = df.copy()
    plot_df = plot_df.replace([np.inf, -np.inf], np.nan)
    plot_df = plot_df.dropna(subset=[time_col, category_col, value_col])
    plot_df[time_col] = plot_df[time_col].astype(int)
    plot_df[value_col] = plot_df[value_col].astype(float)
    plot_df[category_col] = plot_df[category_col].astype(str)
    label_map, color_map = build_category_maps(category_config)
    plot_df["display_label"] = plot_df[category_col].map(label_map)
    plot_df["display_label"] = plot_df["display_label"].fillna(plot_df[category_col].astype(str))
    plot_df["color"] = plot_df[category_col].map(color_map)
    if color_palette is None: color_palette = DEFAULT_COLOR_PALETTE
    plot_df = assign_category_colors(df=plot_df, category_col=category_col, color_col="color", color_palette=color_palette)
    if flag_col is not None and flag_col in plot_df.columns: plot_df["flag_code"] = plot_df[flag_col]
    else: plot_df["flag_code"] = None
    plot_df = (plot_df.sort_values([time_col, category_col]).groupby([time_col, category_col], as_index=False).agg({value_col: "mean","display_label": "first","color": "first","flag_code": "first"}))
    times = sorted(plot_df[time_col].unique())
    categories = sorted(plot_df[category_col].unique())
    index = pd.MultiIndex.from_product([times, categories], names=[time_col, category_col])
    complete_df = (plot_df.set_index([time_col, category_col]).reindex(index).reset_index())
    complete_df[value_col] = complete_df[value_col].fillna(fill_missing_value)
    complete_df["display_label"] = (complete_df.groupby(category_col)["display_label"].ffill())
    complete_df["display_label"] = (complete_df.groupby(category_col)["display_label"].bfill())
    complete_df["display_label"] = complete_df["display_label"].fillna(complete_df[category_col].astype(str))
    complete_df["color"] = complete_df.groupby(category_col)["color"].ffill()
    complete_df["color"] = complete_df.groupby(category_col)["color"].bfill()
    complete_df["flag_code"] = complete_df.groupby(category_col)["flag_code"].ffill()
    complete_df["flag_code"] = complete_df.groupby(category_col)["flag_code"].bfill()
    return complete_df, times

def add_rank_positions(period_df, category_col, value_col, top_n):
    ranked = period_df.copy()
    ranked = ranked.sort_values(value_col, ascending=False).reset_index(drop=True)
    ranked["rank_index"] = ranked.index
    ranked["target_y"] = top_n - 1 - ranked["rank_index"]
    ranked.loc[ranked["rank_index"] >= top_n, "target_y"] = -1.2
    return ranked.set_index(category_col)

def interpolate_animation_data(df,time_col,category_col,value_col,top_n=10,frames_per_period=30,smooth_rank_animation=True,rank_easing=True):
    frames = []
    times = sorted(df[time_col].unique())
    for i in range(len(times) - 1):
        current_time = times[i]
        next_time = times[i + 1]
        current_period = df[df[time_col] == current_time]
        next_period = df[df[time_col] == next_time]
        current_df = add_rank_positions(current_period, category_col, value_col, top_n)
        next_df = add_rank_positions(next_period, category_col, value_col, top_n)
        categories = current_df.index.union(next_df.index)
        current_df = current_df.reindex(categories)
        next_df = next_df.reindex(categories)
        for frame_step in range(frames_per_period):
            progress = frame_step / frames_per_period
            eased_progress = ease_in_out(progress) if rank_easing else progress
            frame_df = current_df.copy()
            frame_df[value_col] = (current_df[value_col].fillna(0) * (1 - progress)+ next_df[value_col].fillna(0) * progress)
            frame_df["display_label"] = current_df["display_label"].combine_first(next_df["display_label"])
            frame_df["color"] = current_df["color"].combine_first(next_df["color"])
            frame_df["flag_code"] = current_df["flag_code"].combine_first(next_df["flag_code"])
            if smooth_rank_animation:
                frame_df["animated_y"] = (current_df["target_y"].fillna(-1.2) * (1 - eased_progress) + next_df["target_y"].fillna(-1.2) * eased_progress)
            else: frame_df["animated_y"] = frame_df[value_col].rank(method="first", ascending=True) - 1
            frame_df["animation_period"] = current_time
            frame_df["animation_progress"] = progress
            frame_df["animation_time_label"] = str(current_time)
            frame_df = frame_df.reset_index()
            frame_df = frame_df[(frame_df["animated_y"] > -1.05) & (frame_df["animated_y"] < top_n - 0.05)]
            frames.append(frame_df)
    last_df = add_rank_positions(df[df[time_col] == times[-1]], category_col, value_col, top_n).reset_index()
    last_df = last_df[last_df["rank_index"] < top_n]
    last_df["animated_y"] = last_df["target_y"]
    last_df["animation_period"] = times[-1]
    last_df["animation_progress"] = 1
    last_df["animation_time_label"] = str(times[-1])
    frames.append(last_df)
    return frames

def draw_bar_race_frame(ax,frame_df,value_col,top_n,value_format,decimal_places,x_label,default_bar_color,show_values=True,show_rank_numbers=False,show_flags=True,flags_dir=None):
    ax.clear()
    ax.set_facecolor(CARD_COLOR)
    frame_df = frame_df.copy()
    frame_df = frame_df.sort_values("animated_y", ascending=True)
    values = frame_df[value_col].astype(float).tolist()
    y_positions = frame_df["animated_y"].astype(float).tolist()
    colors = frame_df["color"].fillna(default_bar_color).tolist()
    max_value = max(values) if values else 1
    ax.set_xlim(0, max_value * (1 + X_AXIS_MARGIN))
    ax.set_ylim(-0.5, top_n - 0.5)
    ax.barh(y_positions, values, color=colors, alpha=BAR_ALPHA, height=BAR_HEIGHT)
    ax.set_yticks([])
    ax.set_yticklabels([])
    for _, row in frame_df.iterrows():
        y = float(row["animated_y"])
        label = str(row["display_label"])
        if show_rank_numbers:
            rank = top_n - int(round(y))
            label = f"{rank}. {label}"
        if show_flags and flags_dir is not None and pd.notna(row.get("flag_code")):
            flag_path = get_flag_path(row["flag_code"], flags_dir)
            if flag_path is not None:
                flag_img = mpimg.imread(flag_path)
                imagebox = OffsetImage(flag_img, zoom=FLAG_ZOOM)
                ab = AnnotationBbox(imagebox, (FLAG_X, y), xycoords=("axes fraction", "data"), frameon=False, box_alignment=(0.5, 0.5))
                ax.add_artist(ab)
        ax.text(LABEL_X,y,label,transform=ax.get_yaxis_transform(),fontsize=LABEL_FONT_SIZE,weight="bold",color=TEXT_COLOR,ha="left",va="center")
    if show_values:
        for _, row in frame_df.iterrows():
            value = float(row[value_col])
            y = float(row["animated_y"])
            ax.text(value + max_value * VALUE_PADDING,y,format_value(value, value_format, decimal_places),va="center",ha="left",color=TEXT_COLOR,fontsize=VALUE_FONT_SIZE,weight="bold")
    ax.text(PERIOD_X,PERIOD_Y,frame_df["animation_time_label"].iloc[0],transform=ax.transAxes,color=TEXT_COLOR,fontsize=PERIOD_FONT_SIZE,weight="bold",alpha=PERIOD_ALPHA,ha="right",va="center")
    ax.set_xlabel(x_label, color=MUTED_COLOR, fontsize=AXIS_FONT_SIZE)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.tick_params(axis="x", colors=MUTED_COLOR, labelsize=TICK_FONT_SIZE)
    ax.tick_params(axis="y", length=0)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)
        spine.set_linewidth(1.1)
    ax.spines["left"].set_visible(False)
    if SHOW_GRID: ax.grid(True, axis="x", color=GRID_COLOR, linewidth=0.8, alpha=GRID_ALPHA)
    else: ax.grid(False)

def add_audio_to_video(video_path,audio_path,output_path,audio_volume=0.35,loop_audio=True,audio_fadeout_seconds=3):
    if audio_path is None: return video_path
    if (VideoFileClip is None or AudioFileClip is None or concatenate_audioclips is None):
        raise ImportError("moviepy is required for adding audio. Install it with: pip install moviepy")
    video = VideoFileClip(str(video_path))
    audio = AudioFileClip(str(audio_path))
    if loop_audio and audio.duration < video.duration:
        repeat_count = int(np.ceil(video.duration / audio.duration))
        audio = concatenate_audioclips([audio] * repeat_count)
        audio = audio.subclipped(0, video.duration)
    else: audio = audio.subclipped(0, min(audio.duration, video.duration))
    audio = audio.with_volume_scaled(audio_volume)
    if (AudioFadeOut is not None and audio_fadeout_seconds and audio_fadeout_seconds > 0):
        audio = audio.with_effects([AudioFadeOut(audio_fadeout_seconds)])
    final_video = video.with_audio(audio)
    final_video.write_videofile(str(output_path), codec="libx264", audio_codec="aac")
    video.close()
    audio.close()
    final_video.close()
    return output_path

def create_bar_race(
    df,
    output_file,
    time_col,
    category_col,
    value_col,
    title,
    subtitle,
    x_label,
    footer_left,
    footer_right,
    category_config=None,
    logo_path=None,
    top_n=10,
    fps=30,
    seconds_per_period=1.0,
    value_format=None,
    decimal_places=0,
    fill_missing_value=0,
    default_bar_color=DEFAULT_BAR_COLOR,
    color_palette=None,
    show_values=True,
    show_rank_numbers=False,
    include_music=False,
    music_path=None,
    music_volume=0.35,
    loop_music=True,
    flag_col=None,
    show_flags=True,
    end_hold_seconds=3,
    audio_fadeout_seconds=3,
    flags_dir=None,
    smooth_rank_animation=True,
    rank_easing=True):

    plt.rcParams["font.family"] = FONT_FAMILY
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    frames_per_period = max(1, int(fps * seconds_per_period))
    prepared_df, _ = prepare_bar_race_data(df=df,time_col=time_col,category_col=category_col,value_col=value_col,category_config=category_config,fill_missing_value=fill_missing_value,flag_col=flag_col,color_palette=color_palette)
    frames = interpolate_animation_data(df=prepared_df,time_col=time_col,category_col=category_col,value_col=value_col,top_n=top_n,frames_per_period=frames_per_period,smooth_rank_animation=smooth_rank_animation,rank_easing=rank_easing)
    if end_hold_seconds > 0:
        hold_frame_count = int(fps * end_hold_seconds)
        frames.extend([frames[-1].copy() for _ in range(hold_frame_count)])
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax = fig.add_axes(AXES_POSITION)
    fig.text(TITLE_X, TITLE_Y, title, fontsize=TITLE_FONT_SIZE, weight="bold", color=TEXT_COLOR, ha="left")
    fig.text(SUBTITLE_X, SUBTITLE_Y, subtitle, fontsize=SUBTITLE_FONT_SIZE, color=MUTED_COLOR, ha="left")
    fig.text(FOOTER_LEFT_X, FOOTER_Y, footer_left, fontsize=FOOTER_FONT_SIZE, color=MUTED_COLOR, ha="left")
    fig.text(FOOTER_RIGHT_X, FOOTER_Y, footer_right, fontsize=FOOTER_FONT_SIZE, color=MUTED_COLOR, ha="right")
    add_logo(fig, logo_path)
    def update(frame_index):
        draw_bar_race_frame(ax=ax,frame_df=frames[frame_index],value_col=value_col,top_n=top_n,value_format=value_format,decimal_places=decimal_places,x_label=x_label,default_bar_color=default_bar_color,show_values=show_values,show_rank_numbers=show_rank_numbers,show_flags=show_flags,flags_dir=flags_dir)
    animation = FuncAnimation(fig, update, frames=len(frames), interval=1000 / fps, repeat=False)
    temporary_video_file = output_file
    if include_music and music_path is not None: temporary_video_file = output_file.with_name(output_file.stem + "_silent_temp.mp4")
    writer = FFMpegWriter(fps=fps, codec="libx264", bitrate=5000, metadata={"artist": "author"})
    animation.save(temporary_video_file, writer=writer, dpi=DPI, savefig_kwargs={"facecolor": fig.get_facecolor(), "bbox_inches": "tight"})
    plt.close(fig)
    if include_music and music_path is not None:
        add_audio_to_video(video_path=temporary_video_file,audio_path=music_path,output_path=output_file,audio_volume=music_volume,loop_audio=loop_music,audio_fadeout_seconds=audio_fadeout_seconds)
        try: os.remove(temporary_video_file)
        except OSError: pass
    print(f"Saved: {output_file}")