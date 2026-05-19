from pathlib import Path
from moviepy import ImageSequenceClip

BASE_DIR = Path(__file__).parent
input_folder = BASE_DIR / "world_fertility"
output_file = BASE_DIR / "fertility_x.mp4"

images = sorted(str(p) for p in input_folder.glob("*.png"))

print("Folder:", input_folder)
print("Frames found:", len(images))

clip = ImageSequenceClip(images, fps=10)

clip.write_videofile(
    str(output_file),
    codec="libx264",
    audio=False,
    preset="medium",
    bitrate="5000k",
    ffmpeg_params=["-vf", "scale=1920:-2", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
)

print("Done:", output_file)