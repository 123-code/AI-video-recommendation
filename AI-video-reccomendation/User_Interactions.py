import numpy as np 


user_interactions = {
    "user1":{
    "likes":["video1","video2"],
    "comments":{"video1": "Great video!", "video2": "Interesting content."},
    "watch_time": {"video1": 30, "video3": 120}
    }
}
user_embeddings = {}


def update_interaction(user_id,video_id,interaction_type,value):
    if user_id not in user_interactions:
        user_interactions[user_id] = {
            "likes": [],
            "comments": {},
            "watch_time": {}
        }
    if interaction_type =='like':
        if video_id not in user_interactions[user_id]['likes']:
            user_interactions[user_id]['likes'].append(video_id)

    elif interaction_type =='comment':

        user_interactions[user_id]['comments'][video_id] = value

        if video_id in user_interactions[user_id]['watchtime']:
            user_interactions[user_id]['watch_time'][video_id] += value
        else:
            user_interactions[user_id]["watch_time"][video_id] = value

        

    
def compute_user_embeddings(user_id,interactions):
    if user_id not in interactions:
        return np.zeros(512)

    likes = len(interactions[user_id]["likes"]) * 1.0
    comments = len(interactions[user_id]["comments"]) * 0.5
    total_watch_time = sum(interactions[user_id]["watch_time"].values())*0.01
    embedding = np.array([likes,comments,total_watch_time])
    embedding = np.tile(embedding,171)[:512]
    return embedding

def save_user_embeddings(user_id,embedding):
    global user_embeddings
    user_embeddings[user_id] = embedding

def get_user_embedding(user_id):
    global user_embeddings 
    return user_embeddings.get(user_id)


user_id = "user1"
interactions = {
        "user1":{
    "likes":["video1","video2"],
    "comments":{"video1": "Great video!", "video2": "Interesting content."},
    "watch_time": {"video1": 30, "video3": 120}
    }
}
user_embeddings = {"user1":compute_user_embeddings("user1",user_interactions)}
print("user embedding",user_embeddings)


"""
user_embeddings = {"user1":compute_user_embeddings("user1",user_interactions)}
print("user embeddings",user_embeddings)
"""



user_interactions = {
    "user1":{
    "likes":["video1","video2"],
    "comments":{"video1": "Great video!", "video2": "Interesting content."},
    "watch_time": {"video1": 30, "video3": 120}
    }
}
