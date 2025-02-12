import random
from flask import Flask, request, jsonify, send_from_directory
import json
from VideoMetadata import generate_video, video_metadata, video_embeddings
from reccomend import recommend_videos
from User_Interactions import user_interactions, compute_user_embeddings
from main import get_video_embedding
from flask_cors import CORS
import os 
import numpy as np

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) 
video_embeddings = generate_video()
VIDEOS_DIR = os.path.join(os.getcwd(), "videos")


user_interactions = {
    "user1":{
    "likes":["video1","video2"],
    "comments":{"video1": "Great video!", "video2": "Interesting content."},
    "watch_time": {"video1": 30, "video3": 120}
    }
}

@app.route("/next_video", methods=['GET'])
def next_video():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    try:
        user_embedding = compute_user_embeddings(user_id, user_interactions)
        recommendations = recommend_videos(user_id, video_embeddings, user_embedding)

        if recommendations:
            # Sort recommendations by similarity score in descending order
            recommendations.sort(key=lambda item: item[1], reverse=True)  

            # Get the video with the highest similarity score
            best_video = recommendations[0]

            # Return only the best video
            return jsonify({
                'video_id': best_video[0],
                'similarity_score': best_video[1],
                'metadata': video_embeddings[best_video[0]]['metadata']
            })
        else:
            return jsonify({'message': 'No recommendations available'}), 200

    except KeyError:
        return jsonify({'error': 'User not found'}), 404
    except IndexError: #handles empty reccomendations
        return jsonify({'message': 'No recommendations available'}), 200
    


@app.route("/update_interaction", methods=["POST"])
def update_interaction():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        video_id = data.get('video_id')
        interaction_type = data.get('interaction_type')
        value = data.get('value')

        if user_id not in user_interactions:
            print(f"User {user_id} not found in user_interactions")
            return jsonify({'error': 'User not found'}), 404

        if video_id in user_interactions[user_id]['watch_time']:
            user_interactions[user_id]['watch_time'][video_id] += value
        else:
            user_interactions[user_id]["watch_time"][video_id] = value

        if not all([user_id, video_id, interaction_type]):
            print(user_id)
            print(video_id)
            print(interaction_type)
            print("Missing required parameters")
            return jsonify({'error': 'Missing required parameters'}), 400
        print(user_interactions)

        return jsonify({'message': 'Interaction updated successfully'})

    except Exception as e:
        print(f"Error in /update_interaction: {e}")
        return jsonify({'error': f'Internal server error: {e}'}), 500


@app.route("/random_videos", methods=['GET'])
def get_random_videos():
    #for video_id,video_data in video_embeddings.items():
    selected_videos = random.sample(list(video_embeddings.keys()), min(3, len(video_embeddings)))
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
    try:

        return send_from_directory(VIDEOS_DIR, filename)
    except FileNotFoundError:
        return jsonify({'error': 'Video not found'}), 404


    
if __name__ == '__main__':
    app.run(debug=True)