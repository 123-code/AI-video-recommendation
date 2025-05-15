import numpy as np
import torch

def generate_synthetic_data(num_users=100, num_videos=200, embedding_dim=512):
    user_embeddings = {f"user_{i}": np.random.randn(embedding_dim) for i in range(num_users)}
    video_embeddings = {f"video_{j}": {'embedding': np.random.randn(embedding_dim)} for j in range(num_videos)}
    user_interactions = {}
    for user_id in user_embeddings:
        likes = np.random.choice(list(video_embeddings.keys()), size=10, replace=False).tolist()
        watch_time = {vid: np.random.uniform(10, 600) for vid in video_embeddings}
        user_interactions[user_id] = {'likes': likes, 'watch_time': watch_time}
    return user_interactions, user_embeddings, video_embeddings


user_interactions, user_embeddings, video_embeddings = generate_synthetic_data()