import pickle
import time
import copy
import json

from flask import Flask, request, session, g

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print request.form.keys()
        return json.dumps(time.ctime())

    elif request.method == "GET":
        return "hello"

if __name__ == "__main__":
    app.run()
