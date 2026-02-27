"""Download free stock videos from Pexels and generate supplementary content with ffmpeg."""
import os
import subprocess
import random
import math
import json
import sys
import requests
import time

VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

existing = set(os.listdir(VIDEOS_DIR))
downloaded = 0

# ---------------------------------------------------------------------------
# Part 1: Download free stock videos from Pexels (no API key needed for direct links)
# ---------------------------------------------------------------------------

PEXELS_DIRECT_URLS = [
    ("pexels_ocean_waves", "https://videos.pexels.com/video-files/1093662/1093662-hd_1920_1080_30fps.mp4"),
    ("pexels_sunset_beach", "https://videos.pexels.com/video-files/857251/857251-hd_1920_1080_25fps.mp4"),
    ("pexels_city_night", "https://videos.pexels.com/video-files/2795173/2795173-hd_1920_1080_25fps.mp4"),
    ("pexels_forest_fog", "https://videos.pexels.com/video-files/3571264/3571264-hd_1920_1080_30fps.mp4"),
    ("pexels_rain_window", "https://videos.pexels.com/video-files/2491284/2491284-hd_1920_1080_24fps.mp4"),
    ("pexels_clouds_sky", "https://videos.pexels.com/video-files/2516159/2516159-hd_1920_1080_24fps.mp4"),
    ("pexels_neon_lights", "https://videos.pexels.com/video-files/3129957/3129957-hd_1920_1080_30fps.mp4"),
    ("pexels_waterfall", "https://videos.pexels.com/video-files/1670898/1670898-hd_1920_1080_30fps.mp4"),
    ("pexels_highway_cars", "https://videos.pexels.com/video-files/2053100/2053100-hd_1920_1080_30fps.mp4"),
    ("pexels_fireworks", "https://videos.pexels.com/video-files/2330784/2330784-hd_1920_1080_24fps.mp4"),
    ("pexels_snow_mountain", "https://videos.pexels.com/video-files/3015510/3015510-hd_1920_1080_24fps.mp4"),
    ("pexels_flower_bloom", "https://videos.pexels.com/video-files/2536662/2536662-hd_1920_1080_25fps.mp4"),
    ("pexels_bird_flight", "https://videos.pexels.com/video-files/3214448/3214448-hd_1920_1080_25fps.mp4"),
    ("pexels_waves_aerial", "https://videos.pexels.com/video-files/1918465/1918465-hd_1920_1080_25fps.mp4"),
    ("pexels_starry_sky", "https://videos.pexels.com/video-files/1851190/1851190-hd_1920_1080_25fps.mp4"),
    ("pexels_autumn_leaves", "https://videos.pexels.com/video-files/3040711/3040711-hd_1920_1080_24fps.mp4"),
    ("pexels_city_aerial", "https://videos.pexels.com/video-files/1739010/1739010-hd_1920_1080_30fps.mp4"),
    ("pexels_lightning", "https://videos.pexels.com/video-files/2824289/2824289-hd_1920_1080_24fps.mp4"),
    ("pexels_underwater", "https://videos.pexels.com/video-files/855282/855282-hd_1920_1080_25fps.mp4"),
    ("pexels_coffee_pour", "https://videos.pexels.com/video-files/2836486/2836486-hd_1920_1080_24fps.mp4"),
    ("pexels_train_window", "https://videos.pexels.com/video-files/3048163/3048163-hd_1920_1080_25fps.mp4"),
    ("pexels_morning_mist", "https://videos.pexels.com/video-files/4812203/4812203-hd_1920_1080_25fps.mp4"),
    ("pexels_dandelion", "https://videos.pexels.com/video-files/3629519/3629519-hd_1920_1080_24fps.mp4"),
    ("pexels_jellyfish", "https://videos.pexels.com/video-files/4065924/4065924-hd_1920_1080_25fps.mp4"),
    ("pexels_campfire", "https://videos.pexels.com/video-files/857135/857135-hd_1920_1080_25fps.mp4"),
    ("pexels_palm_trees", "https://videos.pexels.com/video-files/854669/854669-hd_1920_1080_25fps.mp4"),
    ("pexels_snow_falling", "https://videos.pexels.com/video-files/856049/856049-hd_1920_1080_25fps.mp4"),
    ("pexels_traffic_blur", "https://videos.pexels.com/video-files/854671/854671-hd_1920_1080_25fps.mp4"),
    ("pexels_galaxy", "https://videos.pexels.com/video-files/1526909/1526909-hd_1920_1080_25fps.mp4"),
    ("pexels_butterfly", "https://videos.pexels.com/video-files/2611510/2611510-hd_1920_1080_25fps.mp4"),
]

def download_and_trim(name, url, duration=6):
    fname = f"{name}.mp4"
    if fname in existing:
        return True
    tmp = os.path.join(VIDEOS_DIR, f"_tmp_{fname}")
    out = os.path.join(VIDEOS_DIR, fname)
    try:
        print(f"  Downloading {name}...", end=" ", flush=True)
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

print("=== Downloading Pexels stock videos ===")
for name, url in PEXELS_DIRECT_URLS:
    if download_and_trim(name, url):
        downloaded += 1

# ---------------------------------------------------------------------------
# Part 2: Generate diverse videos with ffmpeg
# ---------------------------------------------------------------------------

FFMPEG_RECIPES = [
    # Mandelbrot zooms at different locations
    ("gen_mandelbrot_zoom1", '-f lavfi -i "mandelbrot=s=480x854:maxiter=120:start_scale=2:end_scale=0.001:start_x=-0.7435:start_y=0.1314" -t 5 -pix_fmt yuv420p'),
    ("gen_mandelbrot_zoom2", '-f lavfi -i "mandelbrot=s=480x854:maxiter=200:start_scale=3:end_scale=0.01:start_x=-0.16:start_y=1.0405" -t 5 -pix_fmt yuv420p'),
    ("gen_mandelbrot_zoom3", '-f lavfi -i "mandelbrot=s=480x854:maxiter=150:start_scale=2:end_scale=0.005:start_x=-1.256:start_y=0.38" -t 6 -pix_fmt yuv420p'),
    ("gen_mandelbrot_deep", '-f lavfi -i "mandelbrot=s=480x854:maxiter=300:start_scale=1:end_scale=0.0001:start_x=-0.74529:start_y=0.11308" -t 7 -pix_fmt yuv420p'),

    # Cellular automata
    ("gen_life_pattern1", '-f lavfi -i "life=s=480x854:mold=10:r=30:ratio=0.5:death_color=0x000000FF:life_color=0xFF00FFFF:stitch=0" -t 5 -pix_fmt yuv420p'),
    ("gen_life_pattern2", '-f lavfi -i "life=s=480x854:mold=8:r=25:ratio=0.3:death_color=0x001030FF:life_color=0x00FF80FF:stitch=1" -t 5 -pix_fmt yuv420p'),
    ("gen_life_pattern3", '-f lavfi -i "life=s=480x854:mold=15:r=20:ratio=0.6:death_color=0x200010FF:life_color=0xFFAA00FF:stitch=0" -t 5 -pix_fmt yuv420p'),
    ("gen_cellauto1", '-f lavfi -i "cellauto=s=480x854:r=30:ratio=0.5:rule=30" -t 5 -pix_fmt yuv420p'),
    ("gen_cellauto2", '-f lavfi -i "cellauto=s=480x854:r=30:ratio=0.5:rule=110" -t 5 -pix_fmt yuv420p'),
    ("gen_cellauto3", '-f lavfi -i "cellauto=s=480x854:r=30:ratio=0.4:rule=90" -t 5 -pix_fmt yuv420p'),

    # Gradient animations
    ("gen_gradient_warm", '-f lavfi -i "gradients=s=480x854:c0=FF4500:c1=FFD700:c2=FF1493:c3=FF6347:speed=0.01:duration=5" -t 5 -pix_fmt yuv420p'),
    ("gen_gradient_cool", '-f lavfi -i "gradients=s=480x854:c0=0000FF:c1=00CED1:c2=7B68EE:c3=00FF7F:speed=0.01:duration=5" -t 5 -pix_fmt yuv420p'),
    ("gen_gradient_neon", '-f lavfi -i "gradients=s=480x854:c0=FF00FF:c1=00FFFF:c2=FFFF00:c3=FF00FF:speed=0.02:duration=5" -t 5 -pix_fmt yuv420p'),
    ("gen_gradient_sunset", '-f lavfi -i "gradients=s=480x854:c0=FF4500:c1=DC143C:c2=FF8C00:c3=8B0000:speed=0.008:duration=6" -t 6 -pix_fmt yuv420p'),
    ("gen_gradient_aurora", '-f lavfi -i "gradients=s=480x854:c0=00FF00:c1=0000FF:c2=FF00FF:c3=00FFFF:speed=0.015:duration=5" -t 5 -pix_fmt yuv420p'),
    ("gen_gradient_ocean", '-f lavfi -i "gradients=s=480x854:c0=006994:c1=0077B6:c2=00B4D8:c3=90E0EF:speed=0.01:duration=5" -t 5 -pix_fmt yuv420p'),

    # Noise / organic patterns
    ("gen_noise_rgb", '-f lavfi -i "nullsrc=s=480x854:r=30,geq=random(1)*255:random(2)*255:random(3)*255" -t 4 -pix_fmt yuv420p'),

    # Color source animations with effects
    ("gen_color_pulse_red", '-f lavfi -i "color=c=red:s=480x854:r=30,geq=r=128+127*sin(2*PI*T+X/50):g=50*sin(PI*T):b=50*cos(PI*T)" -t 5 -pix_fmt yuv420p'),
    ("gen_color_pulse_blue", '-f lavfi -i "color=c=blue:s=480x854:r=30,geq=r=50*sin(PI*T):g=50*cos(PI*T+Y/60):b=128+127*sin(2*PI*T+Y/40)" -t 5 -pix_fmt yuv420p'),
    ("gen_plasma_warm", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=r=128+127*sin(X/30+T*2):g=128+127*sin(Y/25+T*3):b=64+63*sin((X+Y)/40+T)" -t 6 -pix_fmt yuv420p'),
    ("gen_plasma_cool", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=r=64+63*sin(X/40+T):g=128+127*sin(Y/20+T*2):b=128+127*cos(X/30+Y/30+T*1.5)" -t 6 -pix_fmt yuv420p'),
    ("gen_plasma_electric", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=r=128+127*sin(X/20+T*3):g=255*abs(sin(T+X/50)):b=128+127*cos(Y/15+T*2)" -t 5 -pix_fmt yuv420p'),
    ("gen_wave_interference", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=lum=128+127*sin(sqrt((X-240)*(X-240)+(Y-427)*(Y-427))/10-T*5)" -t 6 -pix_fmt yuv420p'),

    # Sierpinski
    ("gen_sierpinski1", '-f lavfi -i "sierpinski=s=480x854:r=30:type=carpet" -t 5 -pix_fmt yuv420p'),
    ("gen_sierpinski2", '-f lavfi -i "sierpinski=s=480x854:r=30:type=triangle" -t 5 -pix_fmt yuv420p'),

    # Test patterns (retro/aesthetic)
    ("gen_testsrc_smpte", '-f lavfi -i "testsrc2=s=480x854:r=30,hue=h=t*30" -t 5 -pix_fmt yuv420p'),
    ("gen_testsrc_bars", '-f lavfi -i "smptebars=s=480x854:r=30,hue=h=t*60:s=sin(t)*0.5+1.5" -t 5 -pix_fmt yuv420p'),

    # Lissajous curves
    ("gen_lissajous1", '-f lavfi -i "nullsrc=s=480x854:r=30,geq=lum=255*lt(abs(X-240-200*sin(2*PI*T+0.5))+abs(Y-427-350*sin(3*PI*T)),30)" -t 6 -pix_fmt yuv420p'),

    # Radial gradient animations
    ("gen_radial_pulse", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=r=255*exp(-((X-240)*(X-240)+(Y-427)*(Y-427))/(10000+5000*sin(T*3))):g=200*exp(-((X-240)*(X-240)+(Y-427)*(Y-427))/(15000+7000*cos(T*2))):b=255*exp(-((X-240)*(X-240)+(Y-427)*(Y-427))/(8000+4000*sin(T*4)))" -t 6 -pix_fmt yuv420p'),

    # More organic color animations
    ("gen_moiré_pattern", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=lum=128+127*sin(X*X/500+Y*Y/500+T*5)" -t 5 -pix_fmt yuv420p'),
    ("gen_tunnel_effect", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=lum=128+127*sin(sqrt((X-240)*(X-240)+(Y-427)*(Y-427))/5+atan2(Y-427\\,X-240)*3-T*8)" -t 6 -pix_fmt yuv420p'),
    ("gen_spiral_rgb", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=r=128+127*sin(sqrt((X-240)*(X-240)+(Y-427)*(Y-427))/8+atan2(Y-427\\,X-240)*2-T*5):g=128+127*sin(sqrt((X-240)*(X-240)+(Y-427)*(Y-427))/8+atan2(Y-427\\,X-240)*2-T*5+2):b=128+127*sin(sqrt((X-240)*(X-240)+(Y-427)*(Y-427))/8+atan2(Y-427\\,X-240)*2-T*5+4)" -t 6 -pix_fmt yuv420p'),
    ("gen_checkerboard_warp", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=lum=255*mod(floor(X/(20+10*sin(T))+T*2)+floor(Y/(20+10*cos(T))),2)" -t 5 -pix_fmt yuv420p'),

    # Fire / lava
    ("gen_fire_glow", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=r=clip(255*(1-Y/854.0)+80*random(1)\\,0\\,255):g=clip(180*(1-Y/854.0)*abs(sin(T*2+X/30))+30*random(1)\\,0\\,255):b=clip(30*(1-Y/600.0)\\,0\\,255)" -t 5 -pix_fmt yuv420p'),

    # Matrix rain effect
    ("gen_matrix_rain", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=r=0:g=clip(255*lt(random(1)\\,0.02)*255+80*lt(random(1)\\,0.05)\\,0\\,255):b=0" -t 5 -pix_fmt yuv420p'),

    # Psychedelic color cycling
    ("gen_psychedelic1", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=r=128+127*sin(X/15+T*4):g=128+127*sin(Y/15+T*3+2.094):b=128+127*sin((X+Y)/20+T*5+4.189)" -t 5 -pix_fmt yuv420p'),
    ("gen_psychedelic2", '-f lavfi -i "color=c=black:s=480x854:r=30,geq=r=128+127*cos(sqrt(X*X+Y*Y)/20-T*6):g=128+127*cos(sqrt(X*X+Y*Y)/20-T*6+2.094):b=128+127*cos(sqrt(X*X+Y*Y)/20-T*6+4.189)" -t 5 -pix_fmt yuv420p'),
]

print(f"\n=== Generating {len(FFMPEG_RECIPES)} videos with ffmpeg ===")
for name, recipe in FFMPEG_RECIPES:
    fname = f"{name}.mp4"
    out = os.path.join(VIDEOS_DIR, fname)
    if fname in existing:
        print(f"  {name}: exists, skip")
        downloaded += 1
        continue
    try:
        cmd = f'ffmpeg -y {recipe} -c:v libx264 -preset ultrafast -crf 26 -an -movflags +faststart "{out}"'
        print(f"  Generating {name}...", end=" ", flush=True)
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
        if os.path.exists(out) and os.path.getsize(out) > 5000:
            print("OK")
            downloaded += 1
        else:
            print(f"failed (rc={r.returncode})")
            if os.path.exists(out): os.remove(out)
    except Exception as e:
        print(f"error: {e}")
        if os.path.exists(out): os.remove(out)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

final_count = len([f for f in os.listdir(VIDEOS_DIR) if f.endswith(('.mp4', '.mov')) and f != 'demo.mov'])
print(f"\n=== Done! Total videos: {final_count} (added {downloaded} new) ===")
