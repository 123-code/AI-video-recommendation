import numpy as np 

user_interactions = {
    "user1":{
    "likes":["video1","video2"],
    "comments":{"video1": "Great video!", "video2": "Interesting content."},
    "watch_time": {"video1": 30, "video3": 120}
    }
}


def compute_user_embeddings(user_id,interactions):
    if user_id not in interactions:
        return np.array([0, 0, 0])

    likes = len(interactions[user_id]["likes"]) * 1.0
    comments = len(interactions[user_id]["comments"]) * 0.5
    total_watch_time = sum(interactions[user_id]["watch_time"].values())*0.01
    embedding = np.array([likes,comments,total_watch_time])
    return embedding


user_embeddings = {"user1":compute_user_embeddings("user1",user_interactions)}
print(user_embeddings)