import os
import time
import google.generativeai as genai
from main import get_video_embedding



# ds to save video metadata

video_metadata = {}
video_embeddings = {}


def generate_video():
    
    api_key = "AIzaSyBuZRAro4cg9q3WQdj9i9UkvEHYZ6PUtuA"
    genai.configure(api_key=api_key) 
    video_key = f"video{len(video_metadata)+1}"
    video_embedding = get_video_embedding(f"{video_key}.mp4",use_cuda=False)
    video_embeddings[video_key] = {"embedding":video_embedding,"metadata":{}}
    video_embeddings[video_key]["metadata"]["title"] = "title"
    video_embeddings[video_key]["metadata"]["genre"] = "genre"
    video_embeddings[video_key]["metadata"]["file_path"] = f"{video_key}.mp4"

    video_data = {
        "title":"title",
        "file_path": f"{video_key}.mp4",
        "genre":"genre",
    }

    video_metadata[video_key] = video_data
    return video_key,video_embedding
generate_video()

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


