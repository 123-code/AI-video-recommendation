import os
import time
import pathlib
import google.generativeai as genai
from main import get_video_embedding



# ds to save video metadata

video_metadata = {}
video_embeddings = {}


videos_directory = os.path.join(os.getcwd(), "videos")
def generate_video():
    # Make sure the videos directory exists.
    if not os.path.exists(videos_directory):
        os.makedirs(videos_directory)

    for x in pathlib.Path(videos_directory).glob("*.mp4"):
        video_key = x.stem  # Use the filename (without extension) as the key
        video_path = str(x.resolve())  # Use the absolute path for the video file

        video_embedding = get_video_embedding(video_path, use_cuda=False)

        video_embeddings[video_key] = {"embedding": video_embedding, "metadata": {}}
        video_embeddings[video_key]["metadata"]["title"] = "title" # Update with your title retrieval logic or user input
        video_embeddings[video_key]["metadata"]["genre"] = "genre" # Update with actual genre information
        video_embeddings[video_key]["metadata"]["file_path"] = str(x)
        video_embeddings[video_key]["metadata"]["file_path"] = x.name  # Only the filename


        video_data = {
            "title": "title",  #Same as above; use actual title.
            "file_path": str(x),
            "genre": "genre",  # Use actual genre.
        }

        video_metadata[video_key] = video_data

    # Return all generated embeddings, not just the last.    
    return video_embeddings

    # label the video
    #video_file = f"content/{video_key}.mp4"
   # video_file = "city.mp4"
'''
    video_file = genai.upload_file(path=video_file)
    prompt = "answer only with two words about this video. 1 what title would you give it? 2. which genre would you assign it? "
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")
    response = model.generate_content([video_file, prompt],
                                   request_options={"timeout": 600})
    response_text = response.text
    lines = response_text.strip().split('\n')
    title = lines[0].split('. ')[1].strip()
    genre = lines[1].split('. ')[1].strip()
    '''

#ds tom save video emeddings 


