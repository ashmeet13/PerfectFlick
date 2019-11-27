import secrets
import os
import time
import json
from flask import Flask, jsonify, request
import hashlib
import requests
import logging
app = Flask(__name__)

logging.basicConfig(filename="Manager.log", level=logging.INFO)


def start(interval):
    i=0
    while True:
        newKey = secrets.token_hex(16)
        retrainKey = {'key':newKey}
        djangoResponse = requests.post(
            url = "http://arnavkohli.pythonanywhere.com/api/update/",
            json = retrainKey
        )
        djangoJson = djangoResponse.json()
        if(djangoJson['Status'] == True):
            logging.info("Django Key Updated")
            retrainResponse = requests.post(
                url = "https://collab-model.herokuapp.com/train",
                json = retrainKey
            )
            retrainJson = retrainResponse.json()
            if(retrainJson['Status'] == True):
                logging.info("Successs Retrain - "+str(i))
                i+=1
                time.sleep(interval)
            else:
                return {
                    "Status" : False,
                    "Remarks" : "Retrain Failure"
                }
        else:
            return {
                    "Status" : False,
                    "Remarks" : "Django Failure"
                }


@app.route("/register", methods=["POST"])
def register():
    adminPath = os.path.join(os.getcwd(), "AdminDetails")
    if not os.path.exists(adminPath):
        os.mkdir(adminPath)
    adminFile = os.path.join(adminPath,'admin.json')
    with open(adminFile, 'w') as writer:
        json.dump({"dummy":"dummy"}, writer)
    newAdminJSON = request.get_json()

    if(newAdminJSON['key'] == hashlib.md5("PerfectFlick".encode()).hexdigest()):
        newAdmin = {
            hashlib.md5(newAdminJSON['Username'].encode()).hexdigest() :hashlib.md5(newAdminJSON['Password'].encode()).hexdigest(),
        }
        with open(adminFile,'r') as reader:
            admins = json.load(reader)
        admins.update(newAdmin)
        with open(adminFile, 'w') as writer:
            json.dump(admins, writer)
        return {
            "Status" : True,
            "Remarks" : "New admin registerd"
        }
    
    else:
        return {
            "Status" : False
        }

@app.route("/login", methods=["POST"])
def login():
    adminPath = os.path.join(os.getcwd(), "AdminDetails")
    if not os.path.exists(adminPath):
        os.mkdir(adminPath)
    adminFile = os.path.join(adminPath,'admin.json')
    if(not os.path.exists(adminFile)):
        return {
            "Status" : False,
            "Remarks" : "No registered admin"
        }
    else:
        with open(adminFile,'r') as reader:
            admins = json.load(reader)
        adminJson = request.get_json()
        adminUsername = hashlib.md5(adminJson['Username'].encode()).hexdigest()
        adminPassword = hashlib.md5(adminJson['Password'].encode()).hexdigest()
        interval = int(adminJson['Interval'])
        try:
            if admins[adminUsername]:
                start(interval)
            else:
                return {
                    "Status" : False,
                    "Remarks" : "Invalid Username or Password"
                }
        except:
            return {
                "Status" : False,
                "Remarks" : "Invalid Username or Password"
            }


@app.route("/")
def home():
    return "Perfect Flick Manager ~~"

if __name__ == "__main__":
    app.run()
