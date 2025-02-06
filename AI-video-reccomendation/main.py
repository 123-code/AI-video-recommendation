import torch
import torchvision.transforms as transforms
import torchvision.models as models
import cv2
import numpy as np
from PIL import Image
#from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai



video_embeddings = {
    "video":{"embedding":23,"metadata":{"title":"title","genre":"Action"}}
}



def get_video_metadata():
    pass

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
        
        # Convert BGR (OpenCV format) to RGB (PIL format)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(frame)

        # Apply transformations and move to the GPU if available
        frame = transform(frame).unsqueeze(0).to(device)
    
        with torch.no_grad():
            embedding = model(frame).squeeze().cpu().numpy()  # Extract embedding
        
        frame_embeddings.append(embedding)

    cap.release()
    return np.array(frame_embeddings)

def average_pool_video_embedding(frame_embeddings):
    """Averages the frame embeddings to create a single video embedding."""
    return np.mean(frame_embeddings, axis=0)

def get_video_embedding(video_path, use_cuda=False, pooling_method="average"):
    """
    Extracts a single video embedding by processing its frames through a pretrained model.
    """
    device = torch.device("cuda" if torch.cuda.is_available() and use_cuda else "cpu")

    # Load Pretrained ResNet Model
    resnet = models.resnet18(pretrained=True)  # Use ResNet-18 for simplicity
    model = torch.nn.Sequential(*list(resnet.children())[:-1])  # Remove the classification head
    model = model.to(device)
    model.eval()  # Set model to evaluation mode

    # Define Transformations (Image preprocessing)
    transform = transforms.Compose([
         transforms.Resize((224, 224)),  # ResNet expects 224x224 images
         transforms.ToTensor(),
         transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Standard normalization for ResNet
    ])

    # Extract Frame Embeddings
    frame_embeddings = extract_frame_embeddings(video_path, model, transform, device)

    # Aggregate Frame Embeddings into a Video Embedding
    if pooling_method == "average":
       video_embedding = average_pool_video_embedding(frame_embeddings)
       return video_embedding
    else:
        raise ValueError("Unsupported pooling method. Only 'average' pooling is supported.")

if __name__ == '__main__':
    video_path = 'video.mp4'  # Replace with your video path
    try:
        video_embedding1 = get_video_embedding(video_path, use_cuda=True)
        video_embedding2 = get_video_embedding("video1.mp4",use_cuda=True)
        similarity_score = cosine_similarity(video_embedding1.reshape(1, -1), video_embedding2.reshape(1, -1))
        print("Cosine Similarity:", similarity_score[0][0])

    except FileNotFoundError as e:
        print(e)


