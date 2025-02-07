from flask import Flask, request, jsonify
import json
from VideoMetadata import generate_video, video_metadata, video_embeddings
from reccomend import recomend_videos
from User_Interactions import user_interactions, compute_user_embeddings
from main import get_video_embedding,get_random_videos


app = Flask(__name__)
generate_video()


@app.route("/next_video",methods=['GET'])
def next_video():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    try:
        user_embeddings = compute_user_embeddings(user_id,user_interactions)
        reccomendations = recomend_videos(user_id,video_embeddings,{user_id:user_embeddings})
        print(reccomendations)
        if reccomendations:
            next_video_id = reccomendations[0][0]
            return jsonify({'video_id': next_video_id})
        else:
            return jsonify({'message': 'No recommendations available'}), 200
        
    except KeyError:
        return jsonify({'error': 'User not found'}), 404
    


@app.route("/update_interaction",methods=["POST"])
def update_interaction():
    data = request.get_json()
    user_id = data.get('user_id')
    video_id = data.get('video_id')
    interaction_type = data.get('interaction_type')
    value = data.get('value')

    if not all([user_id,video_id,interaction_type]):
        return jsonify({'error': 'Missing required parameters'}), 400
    

    if user_id not in user_interactions:
        user_interactions[user_id] = {
            "likes": [],
            "comments": {},
            "watch_time": {}
        }

    if interaction_type == 'like':
        if video_id not in user_interactions[user_id]['likes']:
            user_interactions[user_id]['likes'].append(video_id)
    elif interaction_type == 'comment':
        user_interactions[user_id]['comments'][video_id] = value
    elif interaction_type == 'watch_time':
        user_interactions[user_id]['watch_time'][video_id] = value
    else:
        return jsonify({'error': 'Invalid interaction type'}), 400

    return jsonify({'message': 'Interaction updated successfully'})

@app.route("/random_videos",methods=['GET'])
def get_videos():
    reccomendations = get_random_videos()
    return jsonify(reccomendations)


    
if __name__ == '__main__':
    app.run(debug=True)