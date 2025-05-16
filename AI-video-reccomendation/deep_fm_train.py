import torch 
from DeepFM import DeepFM
from User_Interactions import user_interactions,user_embeddings 
from VideoMetadata import video_embeddings

def create_training_data():

    data = []
    labels = []
    for user_id,interactions in user_interactions.items():
        if user_id not in user_embeddings:
            continue
        user_emb = user_embeddings[user_id]
        for video_id in interactions.get('likes',[]):
            if video_id in video_embeddings:
                video_emb = video_embeddings[video_id]['embedding']
                watch_time = interactions.get('watch_time',{}).get(video_id,0.0)
                features = np.concatenate([user_emb,video_emb,[watch_time/60.0,0.0]])
                data.append(features)
                labels.append(0.0)
    return torch.tensor(data,dtype=torch.float32),torch.tensor(labels,dtype=torch.float32)



    
