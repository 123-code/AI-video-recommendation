import torch 
import torch.nn as nn 
import numpy as np 
from UserInteractions import user_interactions,user_embeddings 
from VideoMetadata import video_embeddings 
import pickle 
import os 
#neural network, supposed to predict score of engagement from 0-1 , with user_embedding,video embedding and interaction featurees
class DeepFM(nn.Module):
    def __init__(self,embedding_dim=512,hidden_dims=[128,64],dropout=0.3):
        super(DeepFM,self).__init__()
        self.embedding_dim = embedding_dim 
        self.fm_linear = nn.Linear(embedding_dim *  2 + 2,1)
        self.fm_embedding = nn.Embedding(embedding_dim *  2 + 2,10)
        self.dnn = nn.Sequential(
            nn.Linear(embedding_dim * 2 + 2,hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dims[0],hidden_dims[1]),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dims[1],1),
            nn.Sigmoid()
        )
    def forward(self,x):
        linear_part = self.fm_linear(x)
        fm_emb = self.fm_embedding(torch.arange(x.size(1)).to(x.device))
        fm_interactions = torch.sum(x * fm_emb,dim=1,keepdim=True) **  2 - torch.sum(x**2 * fm_emb **2 ,dim=1,keepdim=True)
        fm_part = linear_part + 0.5 * fm_interactions.sum(dim=2)
        dnn_part = self.dnn(x)
        output = torch.sigmoid(fm_part + dnn_part)
        return output