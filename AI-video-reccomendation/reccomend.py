from sklearn.metrics.pairwise import cosine_similarity
from VideoMetadata import video_embeddings,generate_video
from User_Interactions import user_embeddings




def recomend_videos(user_id,video_embeddings,user_embeddings):
    user_embedding = user_embeddings
    reccomendations = {}

    # for now iterates through all the video embeddings 
    for video_id,video_data in video_embeddings.items():
        try:
            sim_score = cosine_similarity(user_embedding.reshape(1,-1),video_data["embedding"].reshape(1,-1))
            reccomendations[video_id] = sim_score[0][0]
        except KeyError:
            print(f"Warning: Missing embedding for video {id}")
            continue


    reccomended_videos = sorted(reccomendations.items(),key=lambda item:item[1],reverse=True)
    return reccomended_videos

print(video_embeddings)
print(user_embeddings)
recomendations = recomend_videos("user1",video_embeddings,user_embeddings)
print("reccomended videos",recomendations)


    




