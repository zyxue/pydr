import pickle
import time
import copy
import threading
import socket
from configobj import ConfigObj

from flask import Flask, request, session, g
import sqlalchemy as sqlmy
from sqlalchemy.orm import sessionmaker
from cls import Replica

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    cfg = ConfigObj('/home/zyxue/projects/pydr/sq1e/pydr.cfg')
    database = cfg['system']['database']
    db = sqlmy.create_engine('sqlite:///{0}'.format(database), echo=True)
    Session = sessionmaker(bind=db)
    Session.configure(bind=db)
    ss = Session()
    if request.method == 'POST':
        q = ss.query(Replica)
        # check what Replica has been run yet, if not, send it to the request
        print q.all()
        # print request.form['pbs_jobname']
        return 'great!'

    elif request.method == "GET":
        return "hello"

if __name__ == "__main__":
    # print socket.gethostbyname(socket.gethostname())
    # def run_app():
    app.run(host='127.0.0.1', port=5000, debug=True)

    # thread = threading.Thread(target=run_app)
    # thread.start()

    # time.sleep(2)
    # for i in range(1):
    #     data = json.dumps({'data': 'POST time: %s' % time.ctime()})
    #     u = urllib2.urlopen(url='http://127.0.0.1:5000/', data=data)
    #     rep = u.read()
    #     time.sleep(1)
