import json
import os

import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset


class CollabData(Dataset):
    def __init__(self,jsonData):
        super(CollabData, self).__init__()
        self.jsonData = jsonData
        self.loadData()
        self.ratings = self.buildData()
        self.dataXU,self.dataXM,self.dataY = self.makeData()
        
    def loadData(self):
        self.total_users = self.jsonData['total_users']
        self.total_movies = self.jsonData['total_movies']
        self.userRatings = self.jsonData['userdata']

    def buildData(self):
        cleanedRatings = []
        for i in range(self.total_users):
            current_user = self.userRatings[str(i+1)]
            total_current_ratings = current_user['total']
            current_ratings = current_user['ratings']
            for current_rating in current_ratings:
                temp = [
                    i+1,
                    current_rating[0],
                    current_rating[1]
                ]
                cleanedRatings.append(temp)
        return cleanedRatings

    def makeData(self):
        dataXU, dataXM, dataY = [],[],[]
        for d in self.ratings:
            dataXU.append(d[0]-1)
            dataXM.append(d[1])
            dataY.append([float(d[2])])
        return dataXU,dataXM,dataY

    def getTotalUsers(self):
        return self.total_users
    
    def getTotalMovies(self):
        return self.total_movies
   
    def __len__(self):            
        return len(self.dataXU)
    
    def __getitem__(self,index):
        if torch.cuda.is_available():
            return torch.tensor(self.dataXU[index]).cuda(),torch.tensor(self.dataXM[index]).cuda(),torch.tensor(self.dataY[index]).cuda()
        else:
            return torch.tensor(self.dataXU[index]),torch.tensor(self.dataXM[index]),torch.tensor(self.dataY[index])
