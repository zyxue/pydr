#! /usr/bin/env python

import os
import socket
import optparse
from configobj import ConfigObj

from flask import Flask, request
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from cls import Replica
from collections import deque

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        formkeys = request.form.keys()
        if 'rep' not in formkeys:
            # dispatch a rep from the repository
            pass
        else:
            ll.append(request.form['rep'])
            r = ll.popleft()
            print ll
            return r
            # add rep to the repository
            # calc STDR, dispatch new mdp file

if __name__ == "__main__":
    
    parser = optparse.OptionParser()
    parser.add_option('-c', '--cfg', dest='cfg_file', default='./pydr.cfg', help="where's the configuration file")
    options, args = parser.parse_args()

    cfg = ConfigObj(options.cfg_file)
    database = os.path.join(cfg['system']['database'])
    db = sqlalchemy.create_engine('sqlite:///{0}'.format(database), echo=True)
    ss = sessionmaker(bind=db, autoflush=True, autocommit=False)()

    ll = deque(['a', 'b', 'c', 'd'])

    if os.path.exists(options.cfg_file):
        print socket.gethostbyname(socket.gethostname())
    # # def run_app():
        app.run(host='127.0.0.1', port=5000, debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=False)

    # thread = threading.Thread(target=run_app)
    # thread.start()
