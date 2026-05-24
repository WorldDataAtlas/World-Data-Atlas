from pathlib import Path
from moviepy import ImageSequenceClip, AudioFileClip, concatenate_videoclips
from moviepy.audio.fx.AudioLoop import AudioLoop
from moviepy.audio.fx.AudioFadeOut import AudioFadeOut

BASE_DIR = Path(__file__).parent

input_folder = BASE_DIR / "results"
output = BASE_DIR / "fertility_x.mp4"
audio_file = BASE_DIR / "audio" / "audio.mp3"

FPS = 6
END_HOLD_SECONDS = 5
AUDIO_FADEOUT_SECONDS = 5

images = sorted(str(p) for p in input_folder.glob("*.png"))
if not images: raise ValueError("No PNG frames found.")
main_clip = ImageSequenceClip(images, fps=FPS)
last_frame_clip = ImageSequenceClip([images[-1]] * int(FPS * END_HOLD_SECONDS), fps=FPS)
clip = concatenate_videoclips([main_clip, last_frame_clip])

if audio_file.exists():
    audio = AudioFileClip(str(audio_file))
    if audio.duration < clip.duration: audio = audio.with_effects([AudioLoop(duration=clip.duration)])
    else: audio = audio.subclipped(0, clip.duration)
    audio = audio.with_effects([AudioFadeOut(AUDIO_FADEOUT_SECONDS)])
    clip = clip.with_audio(audio)
    print("Audio added:", audio_file)
else: print("No audio file found, exporting without sound.")
clip.write_videofile(
    str(output),
    codec="libx264",
    audio_codec="aac",
    preset="medium",
    bitrate="5000k",
    ffmpeg_params=["-vf", "scale=1920:-2", "-pix_fmt", "yuv420p", "-movflags", "+faststart"],)
print("Done:", output)