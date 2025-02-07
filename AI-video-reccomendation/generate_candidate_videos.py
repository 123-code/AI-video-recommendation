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