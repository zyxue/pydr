import pickle
import time
import copy
import json
import urllib
import urllib2
import threading

from flask import Flask, request, session, g

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print request.form['job_done']
        return json.dumps(['mdrun', '-v', '-deffnm', 'sq1e00_md'])

    elif request.method == "GET":
        return "hello"

if __name__ == "__main__":
    # def run_app():
    app.run(debug=True)

    # thread = threading.Thread(target=run_app)
    # thread.start()

    # time.sleep(2)
    # for i in range(1):
    #     data = json.dumps({'data': 'POST time: %s' % time.ctime()})
    #     u = urllib2.urlopen(url='http://127.0.0.1:5000/', data=data)
    #     rep = u.read()
    #     time.sleep(1)
