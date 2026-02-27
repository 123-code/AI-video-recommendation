"""Download more free stock videos from alternative Pexels URLs and Pixabay."""
import os
import subprocess
import requests

VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "videos")
existing = set(os.listdir(VIDEOS_DIR))
downloaded = 0

# Alternative Pexels URLs (SD format which is less likely to be blocked)
PEXELS_SD = [
    ("pexels_sunset_sd", "https://videos.pexels.com/video-files/857251/857251-sd_640_360_25fps.mp4"),
    ("pexels_rain_sd", "https://videos.pexels.com/video-files/2491284/2491284-sd_640_360_24fps.mp4"),
    ("pexels_neon_sd", "https://videos.pexels.com/video-files/3129957/3129957-sd_640_360_30fps.mp4"),
    ("pexels_waterfall_sd", "https://videos.pexels.com/video-files/1670898/1670898-sd_640_360_30fps.mp4"),
    ("pexels_fireworks_sd", "https://videos.pexels.com/video-files/2330784/2330784-sd_640_360_24fps.mp4"),
    ("pexels_flower_sd", "https://videos.pexels.com/video-files/2536662/2536662-sd_640_360_25fps.mp4"),
    ("pexels_waves_sd", "https://videos.pexels.com/video-files/1918465/1918465-sd_640_360_25fps.mp4"),
    ("pexels_autumn_sd", "https://videos.pexels.com/video-files/3040711/3040711-sd_640_360_24fps.mp4"),
    ("pexels_lightning_sd", "https://videos.pexels.com/video-files/2824289/2824289-sd_640_360_24fps.mp4"),
    ("pexels_underwater_sd", "https://videos.pexels.com/video-files/855282/855282-sd_640_360_25fps.mp4"),
    ("pexels_coffee_sd", "https://videos.pexels.com/video-files/2836486/2836486-sd_640_360_24fps.mp4"),
    ("pexels_mist_sd", "https://videos.pexels.com/video-files/4812203/4812203-sd_640_360_25fps.mp4"),
    ("pexels_jellyfish_sd", "https://videos.pexels.com/video-files/4065924/4065924-sd_640_360_25fps.mp4"),
    ("pexels_campfire_sd", "https://videos.pexels.com/video-files/857135/857135-sd_640_360_25fps.mp4"),
    ("pexels_palm_sd", "https://videos.pexels.com/video-files/854669/854669-sd_640_360_25fps.mp4"),
    ("pexels_snow_sd", "https://videos.pexels.com/video-files/856049/856049-sd_640_360_25fps.mp4"),
    ("pexels_galaxy_sd", "https://videos.pexels.com/video-files/1526909/1526909-sd_640_360_25fps.mp4"),
    ("pexels_butterfly_sd", "https://videos.pexels.com/video-files/2611510/2611510-sd_640_360_25fps.mp4"),
    ("pexels_dandelion_sd", "https://videos.pexels.com/video-files/3629519/3629519-sd_640_360_24fps.mp4"),
]

# Additional Pexels videos with known working IDs
PEXELS_EXTRA = [
    ("pexels_drone_mountains", "https://videos.pexels.com/video-files/2169880/2169880-hd_1920_1080_30fps.mp4"),
    ("pexels_northern_lights", "https://videos.pexels.com/video-files/3163534/3163534-hd_1920_1080_30fps.mp4"),
    ("pexels_beach_sunset", "https://videos.pexels.com/video-files/1409899/1409899-hd_1920_1080_25fps.mp4"),
    ("pexels_road_driving", "https://videos.pexels.com/video-files/3680112/3680112-hd_1920_1080_24fps.mp4"),
    ("pexels_cat_cute", "https://videos.pexels.com/video-files/855029/855029-hd_1920_1080_25fps.mp4"),
    ("pexels_rain_drops", "https://videos.pexels.com/video-files/2257010/2257010-hd_1920_1080_25fps.mp4"),
    ("pexels_timelapse_sky", "https://videos.pexels.com/video-files/1542080/1542080-hd_1920_1080_30fps.mp4"),
    ("pexels_bokeh_lights", "https://videos.pexels.com/video-files/852397/852397-hd_1920_1080_25fps.mp4"),
    ("pexels_river_forest", "https://videos.pexels.com/video-files/2491283/2491283-hd_1920_1080_24fps.mp4"),
    ("pexels_night_city", "https://videos.pexels.com/video-files/2795741/2795741-hd_1920_1080_25fps.mp4"),
    ("pexels_wave_crash", "https://videos.pexels.com/video-files/1093665/1093665-hd_1920_1080_30fps.mp4"),
    ("pexels_field_wind", "https://videos.pexels.com/video-files/2330782/2330782-hd_1920_1080_24fps.mp4"),
    ("pexels_smoke_art", "https://videos.pexels.com/video-files/1721294/1721294-hd_1920_1080_25fps.mp4"),
    ("pexels_cooking_flame", "https://videos.pexels.com/video-files/3048160/3048160-hd_1920_1080_25fps.mp4"),
    ("pexels_city_walk", "https://videos.pexels.com/video-files/2795175/2795175-hd_1920_1080_25fps.mp4"),
]

def download_and_trim(name, url, duration=6):
    fname = f"{name}.mp4"
    if fname in existing:
        return True
    tmp = os.path.join(VIDEOS_DIR, f"_tmp_{fname}")
    out = os.path.join(VIDEOS_DIR, fname)
    try:
        print(f"  {name}...", end=" ", flush=True)
        r = requests.get(url, timeout=20, stream=True)
        if r.status_code != 200:
            print(f"HTTP {r.status_code}")
            return False
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        subprocess.run([
            "ffmpeg", "-y", "-i", tmp, "-t", str(duration),
            "-vf", "scale=480:854:force_original_aspect_ratio=decrease,pad=480:854:(ow-iw)/2:(oh-ih)/2,setsar=1",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-an", "-movflags", "+faststart", out
        ], capture_output=True, timeout=30)
        os.remove(tmp)
        if os.path.exists(out) and os.path.getsize(out) > 10000:
            print("OK")
            return True
        print("too small")
        if os.path.exists(out): os.remove(out)
        return False
    except Exception as e:
        print(f"error: {e}")
        for p in [tmp, out]:
            if os.path.exists(p): os.remove(p)
        return False

print("=== Downloading SD versions ===")
for name, url in PEXELS_SD:
    if download_and_trim(name, url):
        downloaded += 1

print("\n=== Downloading extra HD videos ===")
for name, url in PEXELS_EXTRA:
    if download_and_trim(name, url):
        downloaded += 1

final_count = len([f for f in os.listdir(VIDEOS_DIR) if f.endswith(('.mp4', '.mov')) and f != 'demo.mov'])
print(f"\n=== Done! Total: {final_count} videos (downloaded {downloaded} more) ===")
