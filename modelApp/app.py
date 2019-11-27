import json
import logging
import operator
import os
import time

import requests

import torch
import torch.nn as nn
import torch.optim as optim

from data_utils.dataset import CollabData
from flask import Flask, jsonify, request
from models.collabModel import CollabNN
from torch.utils.data import DataLoader

logging.basicConfig(filename="Models.log", level=logging.INFO)

app = Flask(__name__)


def getDataset(jsonData):
    return CollabData(jsonData)


def getLoader(dataset):
    return DataLoader(dataset=dataset, batch_size=16, shuffle=True)


def getModel(dataset):
    users = dataset.getTotalUsers()
    movies = dataset.getTotalMovies()
    embedding_size = 8
    return CollabNN(users, movies, embedding_size)


def getOptimizer(model):
    return optim.Adam(model.parameters(), lr=0.001)


def getCriterion():
    return nn.MSELoss()


def trainModel(dataloader, model, criterion, optimizer, size):
    for epoch in range(100):
        tloss = 0
        for i, (u, m, y) in enumerate(dataloader):
            model.train()
            optimizer.zero_grad()
            y_pred = model(u, m)
            loss = criterion(y_pred, y)
            tloss += loss.item()
            loss.backward()
            optimizer.step()
        logging.info("Epoch: "+str(epoch)+" Loss: "+str(tloss/size))
    return model


def startTraining(dataset):
    dataloader = getLoader(dataset)
    model = getModel(dataset)
    optimizer = getOptimizer(model)
    criterion = getCriterion()
    trainModel(dataloader, model, criterion, optimizer, len(dataset))
    return model


def saveModel(model):
    modelsPath = os.path.join(os.getcwd(), "SavedModel")
    if not os.path.exists(modelsPath):
        os.mkdir(modelsPath)
    torch.save(model.state_dict(), os.path.join(modelsPath, "collab.pth"))
    modelInfo = model.getModelInfo()
    with open(os.path.join(modelsPath, "collab.json"), "w") as writer:
        json.dump(modelInfo, writer)


def getData(key):
    sendJson = {"key":key}
    response = requests.post(
        url = "http://arnavkohli.pythonanywhere.com/api/userdata/",
        json = sendJson
    )
    return response.json()




def getModelInfo(modelsPath):
    with open(os.path.join(modelsPath, "collab.json")) as reader:
        modelInfo = json.load(reader)
    return modelInfo


def loadModel():
    modelsPath = os.path.join(os.getcwd(), "SavedModel")
    modelInfo = getModelInfo(modelsPath)
    model = CollabNN(modelInfo["Users"], modelInfo["Items"], modelInfo["Embed"])
    model.load_state_dict(torch.load(os.path.join(modelsPath, "collab.pth")))
    return model, modelInfo


def getUserDetails(userJson):
    return userJson["UserID"], userJson["Movies"]


def getRatings(userID, watchedMovies, model, totalMovies):
    ratings = {}
    for movieID in range(totalMovies):
        if movieID in watchedMovies:
            continue
        else:
            ratings[str(movieID)] = model(
                torch.tensor(userID - 1), torch.tensor(movieID)
            ).item()
    return sorted(ratings.items(), key=operator.itemgetter(1), reverse=True)


def makeRecommendation(userID, ratings, top):
    return {"Status":False, "UserID": userID, "Recommendation": ratings[:top]}


@app.route("/train", methods=["POST"])
def train():
    initiateJSON = request.get_json()
    key = initiateJSON['key']
    jsonData = getData(key)
    dataset = getDataset(jsonData)
    model = startTraining(dataset)
    saveModel(model)
    return jsonify({"Status": True})

@app.route("/predict", methods=["POST"])
def predict():
    userJSON = request.get_json()
    model, modelInfo = loadModel()
    userID, watchedMovies = getUserDetails(userJSON)
    if userID > modelInfo['Users']:
        return jsonify(
            {
                "Status" : False,
                "Remarks" : "User not trained"
            }
        )
    ratings = getRatings(userID, watchedMovies, model, modelInfo["Items"])
    recommend_response = makeRecommendation(userID, ratings, userJSON['Top'])
    return jsonify(recommend_response)

@app.route("/")
def hello_world():
    return "Perfect Flick Model ~~"


if __name__ == "__main__":
    app.run()
