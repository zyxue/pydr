#! /usr/bin/env python

import os
import socket
import optparse
import logging
from configobj import ConfigObj

from flask import Flask, request
from cls import *
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from collections import deque

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if len(parametersets) == 0:
            return 'endjob'
        rf = request.form
        formkeys = rf.keys()
        if not rf['firsttime']:
            # check the last rep sent out to the job
            # calc STDR, select what mdp_file should be send
            pset = parametersets.popleft() 
            return pset.mdp_file
        else:
            parameters.append(request.form['mdp_file'])
            pset = parameters.popleft()
            return pset.mdp_file
        ss.add(Request(rf['pbs_jobid'], rf['pbs_o_workdir'], '00', 'parameter_rece', pset.mdp_file))
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

    parametersets = deque(ss.query(Parameterset).all())

    if os.path.exists(options.cfg_file):
        print socket.gethostbyname(socket.gethostname())
    # # def run_app():
        app.run(host='127.0.0.1', port=5000, debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=False)

    # thread = threading.Thread(target=run_app)
    # thread.start()
