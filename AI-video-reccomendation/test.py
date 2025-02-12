import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from VideoMetadata import video_embeddings  # Assuming this provides video embeddings

user_interactions = {
    "user1": {
        "likes": ["video1", "video2"],
        "comments": {"video1": "Great video!", "video2": "Interesting content."},
        "watch_time": {"video1": 30, "video3": 120}
    }
}

user_embeddings = {}  # Initialize user_embeddings


def update_interaction(user_id, video_id, interaction_type, value=None):  # Added default value for 'value'
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
        # Assuming comment adds to watch time based on the original code's logic
        user_interactions[user_id]['watch_time'][video_id] = user_interactions[user_id]['watch_time'].get(video_id, 0) + len(value)  # Initialize watch_time if needed



def compute_user_embeddings(user_id):  # No need to pass interactions, it's already global
    interactions = user_interactions.get(user_id)  # Use .get() to handle missing users
    if interactions is None:
        return np.zeros(512)

    likes = len(interactions["likes"])
    comments = len(interactions["comments"])
    total_watch_time = sum(interactions["watch_time"].values()) # Sum watch time values


    # More robust embedding creation - no need for tiling if you have enough features
    embedding = np.array([likes, comments, total_watch_time])

    # Pad with zeros if embedding is shorter than 512
    if embedding.shape[0] < 512:
        padding = np.zeros(512 - embedding.shape[0])
        embedding = np.concatenate([embedding, padding])

    return embedding.reshape(1, -1) # Reshape to 2D


def save_user_embeddings(user_id, embedding):
    user_embeddings[user_id] = embedding


def get_user_embedding(user_id):
    return user_embeddings.get(user_id)




retrieved_embedding = get_user_embedding("user1")
print(retrieved_embedding)
# Make sure video_embeddings is also 2D (e.g., (num_videos, 512))

video_embeddings_2d = video_embeddings.reshape(-1,1) if video_embeddings.ndim == 1 else video_embeddings
if retrieved_embedding is not None:

    sim_score = cosine_similarity(retrieved_embedding, video_embeddings_2d)
    print(sim_score)








