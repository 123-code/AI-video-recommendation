import torch
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
from diffusers.utils import export_to_video
import numpy as np
from IPython.display import HTML
import PIL.Image
import imageio  # Import imageio

# Load the pipeline (keeping your existing setup)
pipe = DiffusionPipeline.from_pretrained("damo-vilab/text-to-video-ms-1.7b", torch_dtype=torch.float16, variant="fp16")
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_model_cpu_offload()
pipe.enable_vae_slicing()


for x in range(len(prompts)):
    
# Generate video frames
    prompt = prompts[x]
    video_duration_seconds = 3
    num_frames = video_duration_seconds * 10

# Generate frames
    video_frames = pipe(
        prompt,
        negative_prompt="low quality",
        num_inference_steps=25,
        num_frames=num_frames
    ).frames

# --- DEBUGGING ---
    print(f"Type of video_frames: {type(video_frames)}")

    if isinstance(video_frames, list):
        print(f"Length of video_frames (list): {len(video_frames)}")
        if len(video_frames) > 0:
            print(f"Type of first element in list: {type(video_frames[0])}")
            if isinstance(video_frames[0], np.ndarray):
                 print(f"Shape of first element in list (NumPy array): {video_frames[0].shape}")
                 print(f"dtype of first element in list (NumPy array): {video_frames[0].dtype}")
            elif isinstance(video_frames[0], PIL.Image.Image):
                print(f"Mode of first element in list (PIL Image): {video_frames[0].mode}")  # e.g., "RGB"
                print(f"Size of first element in list (PIL Image): {video_frames[0].size}")  # width, height
            else:
                 print(f"Unknown type of element: {type(video_frames[0])}")

    elif isinstance(video_frames, np.ndarray):
        print(f"Shape of video_frames (NumPy array): {video_frames.shape}")
        print(f"dtype of video_frames (NumPy array): {video_frames.dtype}")

    else:
        print("video_frames is neither a list nor a NumPy array.")


# Correctly extract and format frames from the NumPy array
    formatted_frames = []
    if isinstance(video_frames, np.ndarray):
    # Iterate through the frames (dimension 1)
        for i in range(video_frames.shape[1]):  # Iterate over the 'frames' dimension (index 1)
            frame = video_frames[0, i]  # Access the i-th frame (and remove batch dimension)
            if frame.dtype != np.uint8:
                frame = (frame * 255).astype(np.uint8)
            formatted_frames.append(frame)
    else:
        raise TypeError("video_frames must be a NumPy array.")



# Save video directly with imageio
    output_path = f"output_video{x}.mp4"
    imageio.mimsave(output_path, formatted_frames, fps=10)



"""
from diffusers import LattePipeline
from diffusers.models import AutoencoderKLTemporalDecoder
from torchvision.utils import save_image
import torch
import imageio
import numpy as np

torch.manual_seed(0)
device = "cuda" if torch.cuda.is_available() else "cpu"
video_length = 16  # 1 (text-to-image) or 16 (text-to-video)
pipe = LattePipeline.from_pretrained("maxin-cn/Latte-1", torch_dtype=torch.float16).to(device)

# Using temporal decoder of VAE
vae = AutoencoderKLTemporalDecoder.from_pretrained(
    "maxin-cn/Latte-1", 
    subfolder="vae_temporal_decoder", 
    torch_dtype=torch.float16
).to(device)
pipe.vae = vae

prompt = "a cat wearing sunglasses and working as a lifeguard at pool."

# Generate the video frames
videos = pipe(prompt, video_length=video_length, output_type='pt').frames.cpu()

# Convert the frames to a format that can be saved by imageio
frames = []
for i in range(videos.shape[1]):
    # Extract each frame, convert to numpy array in the correct format
    frame = videos[0, i].permute(1, 2, 0).numpy()
    # Convert from float to uint8 (0-255 range)
    frame = (frame * 255).astype(np.uint8)
    frames.append(frame)

# Save the frames as a video file
output_path = "video.mp4"
try:
    # Try using imageio.mimsave with explicitly specified format
    imageio.mimsave(output_path, frames, fps=8, format='FFMPEG')
    print(f"Video saved to {output_path}")
except Exception as e:
    print(f"First attempt failed: {e}")
    try:
        # Alternative approach using imageio.get_writer
        writer = imageio.get_writer(output_path, fps=8, codec='libx264')
        for frame in frames:
            writer.append_data(frame)
        writer.close()
        print(f"Video saved to {output_path}")
    except Exception as e:
        print(f"Second attempt failed: {e}")
        # Fallback to saving a GIF if MP4 fails
        gif_path = "video.gif"
        imageio.mimsave(gif_path, frames, fps=8)
        print(f"Saved as GIF instead at {gif_path}")

# Optionally, you can also save individual frames as images
for i, frame in enumerate(frames):
    save_path = f"frame_{i:03d}.png"
    imageio.imwrite(save_path, frame)
"""