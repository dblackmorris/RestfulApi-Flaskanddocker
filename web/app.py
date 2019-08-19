from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import boto3

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SentencesDatabase
users = db["Users"]
def checkPostedData(postedData,functionName):
    if (functionName=="Register" or functionName=="Get"):
        if "username" not in postedData or "password" not in postedData:
            return 301
        else :
            return 200
    elif (functionName=="Store"):
        if "username" not in postedData or "password" not in postedData or "ec2" not in postedData:
            return 301
        elif (postedData["ec2"]==""):
            return 302
        else :
            return 200
    else :
        return 404
class Register(Resource):
    def post(self):
        
        postedData = request.get_json()
        sCode=checkPostedData(postedData,"Register")
        if sCode==200 :
            username = postedData["username"]
            password = postedData["password"]


            hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        
            users.insert({
                "Username": username,
                "Password": hashed_pw,
                "EC2-Details": "",
                "Tokens":3
            })

            retJson = {
                "status": sCode,
                "msg": "You successfully signed up for the API"
            }
            return jsonify(retJson)
        else :
            retJson = {
                    "status": sCode,
                    "msg": "Please enter the username and password both"
                    }
            return jsonify(retJson)

def verifyPw(username, password):
    hashed_pw = users.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        "Username":username
    })[0]["Tokens"]
    return tokens

class Store(Resource):
    def post(self):
        
        postedData = request.get_json()
        sCode=checkPostedData(postedData,"Store")
        if sCode==301:
            retJson={
                    "status":sCode,
                    "msg": "Please enter username,password and bucket"
                    }
            return jsonify(retJson)
        elif sCode==302:
            retJson={
                    "status":sCode,
                    "message": "empty sting as in bucket name is not supported"
                    }
            return jsonify(retJson)
        else :
            
        
            username = postedData["username"]
            password = postedData["password"]
            ec2 = postedData["ec2"]

        
            correct_pw = verifyPw(username, password)

            if not correct_pw:
                setJson = {
                    "status":502
                }
                return jsonify(setJson)
       
            num_tokens = countTokens(username)
            if num_tokens <= 0:
                qetJson = {
                    "status": 301
                    }
                return jsonify(qetJson)

            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=ec2)
            
            users.update({
                "Username":username
            }, {
                "$set":{
                    "EC2-Details":ec2,
                    "Tokens":num_tokens-1
                    }
            })

            retJson = {
                "status":sCode,
                "msg":"Data saved successfully"
            }
            return jsonify(retJson)

class Get(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        
        correct_pw = verifyPw(username, password)
        if not correct_pw:
            retJson = {
                "status":302
            }
            return jsonify(retJson)
        s3_client = boto3.client('s3')
        list1=str(s3_client.list_buckets())
        


        sentence = users.find({
            "Username": username
        })[0]["EC2-Details"]
        retJson = {
            "status":200,
            "last bucket created by user": str(sentence),
            "list of s3": list1
            
        }

        return jsonify(retJson)



api.add_resource(Register, '/register')
api.add_resource(Store, '/store')
api.add_resource(Get, '/get')


if __name__=="__main__":
    app.run(host='0.0.0.0')

