import logging
import random
import numpy as np
import cv2
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)


VIDEOS_DIR = os.path.join(os.getcwd(), "videos")
EMBEDDING_DIM = 512  
DEFAULT_EMBEDDING = np.zeros(EMBEDDING_DIM)
ALPHA = 0.1 


video_embeddings = {} 
user_embeddings = {} 

user_interactions = {}
watched = []


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
resnet = models.resnet18(
    weights=models.ResNet18_Weights.DEFAULT) 

model = torch.nn.Sequential(*list(resnet.children())[:-1])
model = model.to(device)
model.eval() 


transform = transforms.Compose([
    transforms.Resize((224, 224)),  
    transforms.ToTensor(),

    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])



def extract_frame_embeddings(video_path, model, transform, device):
    """Extracts embeddings from each frame of a video using a pretrained model."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")

    frame_embeddings = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
 

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(frame)


        frame = transform(frame).unsqueeze(0).to(device)

        with torch.no_grad():
            embedding = model(
                frame).squeeze().cpu().numpy()  


            if embedding.ndim == 4:
                embedding = embedding.reshape(-1)

            frame_embeddings.append(embedding)

    cap.release()
    return np.array(frame_embeddings)


def average_pool_video_embedding(frame_embeddings):
    """Averages the frame embeddings to create a single video embedding."""
    return np.mean(frame_embeddings, axis=0)


def get_video_embedding(video_path):
    """Gets the pre-computed video embedding, or computes it if it doesn't exist."""
    video_filename = os.path.basename(video_path)
    video_id = os.path.splitext(
        video_filename)[0]  

    if video_id not in video_embeddings:
        try:
            frame_embeddings = extract_frame_embeddings(
                video_path, model, transform, device)
            if len(frame_embeddings) == 0:

                video_embedding = np.zeros(EMBEDDING_DIM)
            else:
                video_embedding = average_pool_video_embedding(
                    frame_embeddings)

            video_embeddings[video_id] = {
                'embedding': video_embedding,
                'metadata': {'title': f'Video {video_id}', 'genre': 'Unknown', 'file_path': f'videos/{video_filename}'}
            }
        except Exception as e:
            logging.error(
                f"Error generating embedding for video {video_id}: {e}")
            return None  

    return video_embeddings[video_id]['embedding']


def update_user_embedding(user_id, video_id, interaction_type, value):
    if video_id not in video_embeddings:
      return jsonify({'error': 'video_id does not exist'}), 404

    video_embedding = video_embeddings[video_id]['embedding']
    if user_id not in user_embeddings:
        user_embeddings[user_id] = np.zeros(
            EMBEDDING_DIM)  
    old_embedding = user_embeddings[user_id]

    # the difference between user and video embeddings determines the direction in which the user emedding needs to move 

    if interaction_type == 'watch_time':
        print(value)
        update = ALPHA * value * (video_embedding - old_embedding)

    elif interaction_type == 'like':
        update = ALPHA * (video_embedding - old_embedding)

    elif interaction_type == 'comment':
        update = ALPHA * (video_embedding - old_embedding)

    else:
      return jsonify({'error': 'invalid interaction_type'}), 400
    user_embeddings[user_id] = old_embedding + update


@app.route("/next_video", methods=['GET'])
def next_video():
  user_id = request.args.get('user_id')
  if not user_id:
    return jsonify({'error': 'user_id is required'}), 400

  if user_id not in user_embeddings:

    user_embeddings[user_id] = DEFAULT_EMBEDDING.copy()

  user_embedding = user_embeddings[user_id]


  video_ids = list(video_embeddings.keys())

  video_embeds = [video_embeddings[v_id]['embedding'].tolist()
                  for v_id in video_ids]
  user_embedding = user_embedding.reshape(
      1, -1) 
  similarities = cosine_similarity(user_embedding, video_embeds)[0]

 
  sorted_indices = np.argsort(similarities)[::-1]
  if not len(sorted_indices):
    return jsonify({'message': 'No recommendations available'}), 200
  
  best_video_id = video_ids[sorted_indices[0]]
  best_score = similarities[sorted_indices[0]]
  for x in range(len(sorted_indices)):
     video_index = sorted_indices[x]
     video_id = video_ids[video_index]

     if video_id in watched:
        if x + 1 < len(sorted_indices):
          next_video_index = sorted_indices[x+1] 
          best_video_id = video_ids[next_video_index]
          best_score = similarities[next_video_index]
        else:
           return jsonify({'message': 'No recommendations available'}), 200
        
     else:
        best_video_id = video_id
        best_score = similarities[video_index]
        break
  
  watched.append(best_video_id)

  return jsonify({
      'video_id': best_video_id,
      'similarity_score': float(best_score),  
      'metadata': video_embeddings[best_video_id]['metadata']
  })


@app.route("/update_interaction", methods=["POST"])
def update_interaction():
  data = request.get_json()
  user_id = data.get('user_id')
  video_id = data.get('video_id')
  interaction_type = data.get('interaction_type')
  value = data.get('value') 

  if not all([user_id, video_id, interaction_type]):
    return jsonify({'error': 'Missing required parameters'}), 400

  if user_id not in user_interactions:
    user_interactions[user_id] = {
        "likes": [],
        "comments": {},
        "watch_time": {}
    }

  if interaction_type == 'like':
    user_interactions[user_id]['likes'].append(video_id)
  elif interaction_type == 'comment':
    user_interactions[user_id]['comments'][video_id] = value
  elif interaction_type == 'watch_time':
    user_interactions[user_id]['watch_time'].setdefault(video_id, 0.0)
    user_interactions[user_id]['watch_time'][video_id] += value

  else:
    return jsonify({'error': 'invalid interaction_type'}), 400
  update_user_embedding(user_id, video_id, interaction_type, value)
  return jsonify({'message': 'Interaction updated successfully'})


@app.route("/random_videos", methods=['GET'])
def get_random_videos():
  selected_videos = random.sample(list(video_embeddings.keys()),
                                  min(3, len(video_embeddings)))
  response = []
  for video_id in selected_videos:
    video_data = {
        'video_id': video_id,
        'metadata': video_embeddings[video_id]['metadata']
    }
    response.append(video_data)

  return jsonify(response)
 

@app.route("/videos/<filename>", methods=['GET'])
def serve_video(filename):
  print("videos_dir",VIDEOS_DIR,filename)
  try:
    return send_from_directory(VIDEOS_DIR,filename)
  except FileNotFoundError:
    return jsonify({'error': 'Video not found'}), 404



for file in os.listdir(VIDEOS_DIR):
  if file.endswith(".mp4"):
    video_path = os.path.join(VIDEOS_DIR, file)
    get_video_embedding(video_path)

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=5050)
