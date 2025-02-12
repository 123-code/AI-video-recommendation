from sklearn.metrics.pairwise import cosine_similarity
from VideoMetadata import video_embeddings
from User_Interactions import user_embeddings
import numpy as np 

def recommend_videos(user_id, video_embeddings, user_embedding):
    try:
        print(user_id)
        user_embedding = user_embeddings[user_id]
        print("EMBEDDING FROM VIDEOS",user_embedding)
    except KeyError:
        print(f"Error: No embedding found for user {user_id}")
        return [] 

    recommendations = {}

    for video_id, video_data in video_embeddings.items():
        try:
            video_embedding = video_data['embedding']  
            sim_score = cosine_similarity(user_embedding.reshape(1, -1), video_embedding.reshape(1, -1)) # Reshape both embeddings
            recommendations[video_id] = sim_score[0][0]
        except KeyError:
            print(f"Warning: Missing embedding for video {video_id}")
            continue

    recommended_videos = sorted(recommendations.items(), key=lambda item: item[1], reverse=True)
    return recommended_videos

recommendations = recommend_videos("user1", video_embeddings, user_embeddings)
print("recommended videos", recommendations)





