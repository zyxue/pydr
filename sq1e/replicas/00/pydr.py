#! /usr/bin/env python

import os
import socket
import optparse
import pickle
import json

from configobj import ConfigObj

from flask import Flask, request, g, session
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from collections import deque

app = Flask(__name__)

def connect_db():
    database = os.path.join(cfg['system']['database'])
    db = sqlalchemy.create_engine('sqlite:///{0}'.format(database), echo=True)
    ss = sessionmaker(bind=db, autoflush=True, autocommit=False)()
    return ss

@app.before_request
def before_request():
    g.db = connect_db()
    print type(g.db)

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.commit()

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # transform multidict to a normal dict in one-key-one-value pattern
        rep_info = dict((k, v) for k, v in request.form.to_dict().iteritems())
        print rep_info
        
        if rep_info['firsttime'] == '0':
            replicas = cfg['replicas']
            replicaid = os.path.basename(os.getenv('PWD'))
            replica = replicas[replicaid]
            rep_to_assign_info = {
                'replicaid': replicaid,
                'temperature': replica['init_temp'],
                'directory': replica['directory']
                }
            return json.dumps(rep_to_assign_info)
        else:
            return "Calculate STDR and replace a new rep"

    if request.method == 'GET':
        return "hello"

if __name__ == "__main__":
    
    parser = optparse.OptionParser()
    parser.add_option('-c', '--cfg', dest='cfg_file', default='../../pydr.cfg', help="where's the configuration file")
    options, args = parser.parse_args()

    cfg = ConfigObj(options.cfg_file)
    hostfile = cfg['system']['hostfile']
    hostname = socket.gethostname()
    hostip = socket.gethostbyname(hostname)
    port = os.getenv('PORT', 5000)
    if not os.path.exists(hostfile):
        with open(hostfile, 'w') as opf:
            opf.write('http://{0}:{1}\n{2}\n'.format(hostip, port, hostname))

    if os.path.exists(options.cfg_file):
    # # def run_app():
        app.run(host=hostip, port=port, debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=False)

    # thread = threading.Thread(target=run_app)
    # thread.start()
