#! /usr/bin/env python

import os
import socket
import optparse
import json
import time
import copy
import random
import subprocess

import requests
import threading
import StringIO
from string import Template

from configobj import ConfigObj
from numpy import exp

from flask import Flask, request, g, session
from collections import deque

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

app = Flask(__name__)

def init_db(database):
    engine = create_engine('sqlite:///{0}'.format(database), echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=True, autocommit=False)
    return Session

def connect_db(database):
    Session = init_db(database)
    return Session()

def DRPE(state, ts, u, c1, c2):
    """
    state: a list of temperatures for all the present replicas
    ts: a list of preset temperatures
    u: as the name indicates
    """

    lambda_ = dict(zip(ts, u))

    sstate = sorted(state)                        # sorted state
    us_sstate = [lambda_[a] for a in sstate]      # uniform spacing of sorted state
    w = len(ts) / float(len(us_sstate))

    ll = range(len(us_sstate) + 1)
    ll.remove(0)

    ep = 0                                                # energetic penalty
    for k1, i1 in zip(us_sstate, ll):
        for k2, i2 in zip(us_sstate, ll):
            ep += ((k1 - k2) - w * (i1 - i2)) ** 2
    ep *= c1
    dp = c2 * (sum(us_sstate) - w * sum(ll)) ** 2 # drift penalty
    return ep + dp

def probability(t1, t2, pot_ener, state1, state2, ts, u, a1=1, a2=1, c1=0.005, c2=0.005):
    """exp(-(beta2 - beta1)* pot_ener + (a2 - a1) - (DRPE2 - DRPE1))"""
    k = 1.3806503e-23  # Unit: (m2 kg s-2 K-1)
    beta1 = 1 / (k * float(t1))
    beta2 = 1 / (k * float(t1))

    state1 = [float(s) for s in state1]
    state2 = [float(s) for s in state2]
    ts = [float(t) for t in ts]
    u = [int(i) for i in u]

    DRPE1 = DRPE(state1, ts, u, c1, c2)
    DRPE2 = DRPE(state2, ts, u, c1, c2)
    prob = exp(-(beta2 - beta1) * float(pot_ener) + (a2 - a1) - (DRPE2 - DRPE1))
    return prob, DRPE1, DRPE2

@app.before_request
def before_request():
    ts = cfg['miscellaneous']['init_temps']
    db = cfg['system']['database']

    g.ss = connect_db(db)
    if g.ss.query(Exchange.exid).count() == 0:                 # prevent inserting init_temps multiple times
        g.ss.add(Exchange(exid=0, rid='--', repcount='--', t1='--', t2='--', 
                          DRPE1='--', DRPE2='--', pot_ener='--',
                          global_temp=' '.join(ts), date=time.ctime()))

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'ss'):
        g.ss.commit()

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # transform multidict to a normal dict in one-key-one-value pattern
        rep_info = dict((k, v) for k, v in request.form.to_dict().iteritems())
        
        if rep_info['firsttime'] == '1':
            # assign the the replica where this pydr.py is located
            rid = rep_info['rid']
            replicas = cfg['replicas']
            r = replicas[rid]
            repcount = 1
            new_rep_info = {
                'rid': rid,
                'old_temp': None,
                'temp': r['init_temp'],
                'directory': r['directory'],
                'repcount':repcount
                }
            return json.dumps(new_rep_info)
        else:
            rid = rep_info['rid']
            t1 = rep_info['temp']
            t2 = rep_info['temp_to_change']
            pot_ener = rep_info['pot_ener']
            repcount = int(rep_info['repcount']) + 1

            history_temps = g.ss.query(Exchange.exid, Exchange.global_temp).order_by('exid').all()
            current_temps = history_temps[-1][1].split()  # get current global_temp

            state1 = current_temps
            _state2 = copy.copy(current_temps)
            _state2[current_temps.index(t1)] = t2
            state2 = _state2

            prob, DRPE1, DRPE2 = probability(t1, t2, pot_ener, state1, state2,
                                             ts, u, a1=1, a2=1, c1=0.005, c2=0.005)
            p = min(1, prob)

            if p >= 1:
                new_temp = t2
            else:
                if random.random() > p:
                    new_temp = t2
                else:
                    new_temp = t1

            if new_temp == t2:
                new_current_temp = ' '.join(state2)
            else:
                new_current_temp = ' '.join(state1)

            g.ss.add(Exchange(rid=rid, repcount=repcount, t1=t1, t2=new_temp, 
                              DRPE1=DRPE1, DRPE2=DRPE2,pot_ener=pot_ener, 
                              global_temp=new_current_temp, date=time.ctime()))
        
            new_rep_info = {
                'rid': rid,
                'old_temp': t1,
                'temp': new_temp,
                'directory': rep_info['directory'],
                'repcount': repcount
                }
            return json.dumps(new_rep_info)

    if request.method == 'GET':
        return "hello"

class Exchange(Base):
    __tablename__ = "exchanges"

    exid = Column(Integer, primary_key=True)
    rid = Column(String)
    repcount = Column(String)
    t1 = Column(String)
    t2 = Column(String)
    DRPE1 = Column(String)
    DRPE2 = Column(String)
    pot_ener = Column(String)
    global_temp = Column(String)
    date = Column(String)

def parse_cmd():
    parser = optparse.OptionParser()
    parser.add_option('-c', '--cfg', dest='cfg_file', default='../../pydr.cfg', help="where's the configuration file")
    options, args = parser.parse_args()
    return options

def run_app(hostip, port, debug=False):
    app.run(host=hostip, port=port, debug=False)
    # app.run(host='0.0.0.0', port=5000, debug=False)

def main():
    
    cfg = ConfigObj('../../pydr.cfg')
    hostfile = cfg['system']['hostfile']
    init_temps = cfg['miscellaneous']['init_temps']

    rep = None
    count = 0
    while True:
        if not os.path.exists(hostfile):
            logging.error('No hostfile!\n')
        else:
            with open(hostfile, 'r') as inf:
                # just 2 seconds, in case the hostfile has been opened by
                # another node, but the writting hasn't finished yet. more than
                # that means server died
                for i in range(2):
                    where = inf.tell()
                    line = inf.readline().strip()
                    if not line.strip():
                        time.sleep(1)
                        inf.seek(where)
                    else:
                        uri = line
                        break

    # 1. the server shall has been running, look for server address, could request for job now
    # 2. after unexpected scient crush, everything should be restarted, and cpt file will be used.
    # 1. Should check existence of hostfile to make sure server is running; how?

            j = Job()
            if rep is None:
                rep_info = {
                    'firsttime' : 1,
                    'rid': os.path.basename(os.getenv('PWD'))
                    }
            else:
                rep_info = {
                    'firsttime': 0,
                    'rid': rep.rid,
                    'temp' : rep.temp,
                    'temp_to_change': rep.get_temp_to_change(init_temps),
                    'pot_ener': rep.get_pot_ener(),
                    'directory': rep.directory,
                    'repcount': rep.repcount}

            r = j.connect_server(uri, rep_info)
            print r.content, type(r.content)
            js = json.loads(r.content)
            rep = Replica(js['rid'], js['old_temp'], js['temp'], js['directory'], js['repcount'])
            kwargs = {'_MDPF_': rep.mdpf,
                      '_OLD_DEFFNM_': rep.old_deffnm,
                      '_DEFFNM_': rep.deffnm}
            with open('../../0_mdrun.tmp', 'r') as inf:
                with open('0_mdrun.sh', 'w') as opf:
                    opf.writelines([Template(l).safe_substitute(kwargs)
                                   for l in inf.readlines()])
            subprocess.call(['bash', '0_mdrun.sh'])
            count += 1
            if count == 4:
                break


class Job(object):
    def __init__(self):
        hostname = socket.gethostname()
        self.pbs_hostname = hostname
        if hostname == "zyxue-desktop":
            self.pbs_jobid = 'zyxue_JOBID'
            self.pbs_jobname = 'zyxue_JOBNAME'
            self.pbs_nodenum = 'zyxue_NUM_NODES'
            self.pbs_queue = 'zyxue_QUEUE'         # batch_eth, batch_ib, debug
            self.pbs_o_workdir = 'zyxue_O_WORKDIR'

        else:                                               # assume on scinet
            self.pbs_jobid = os.getenv('PBS_JOBID')
            self.pbs_jobname = os.getenv('PBS_JOBNAME')
            self.pbs_nodenum = os.getenv('PBS_NUM_NODES')
            self.pbs_queue = os.getenv('PBS_QUEUE') # batch_eth, batch_ib, debug
            self.pbs_o_workdir = os.getenv('PBS_O_WORKDIR')
        
    def connect_server(self, uri, data):
        data.update(self.__dict__)
        return requests.post(uri, data)

    def check(self):
        for i in dir(self):
            print getattr(self, i)


class Replica(object):                  # used to be sent from client to server
    def __init__(self, rid, old_temp, temp, directory, repcount):
        self.rid  = rid                                 # e.g. 00 01
        self.old_temp = old_temp
        self.temp = temp
        self.directory = directory
        self.repcount = repcount
        self.mdpf = '../../parametersets/{0}.mdp'.format(temp)
        if repcount == 1:
            self.old_deffnm = '{0}_npt'.format(rid)
        else:
            self.old_deffnm = '{0}_{1}_p{2:04d}'.format(rid, old_temp, repcount-1)
        self.deffnm = '{0}_{1}_p{2:04d}'.format(rid, temp, repcount)

    def get_pot_ener(self):
        def pe(edrf, output='lala_energy.xvg'):
            i = 'Potential'
            p = subprocess.Popen(['g_energy', '-f', edrf, '-o', output], 
                                 stdin=subprocess.PIPE, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
            stdout, stderr = p.communicate(i)
            for line in StringIO.StringIO(stdout):
                if line.startswith('Potential'):
                    return line.split()[1]

        edrf = os.path.join(self.directory, '{0}.edr'.format(self.deffnm))
        output = '_energy.xvg'
        if os.path.exists(edrf):
            pot_ener = pe(edrf, output)
        else:
            logging.error("{0} doesn't exist when trying to get potential energy".format(edrf))
            pot_ener = '0'
        if os.path.exists(output):
            os.remove(output)
        return pot_ener

    def get_temp_to_change(self, temp_tuple):
        if not self.temp in temp_tuple:
            logging.error('{0} is not in the temp_list'.format(self.temp))
        else:
            index = temp_tuple.index(self.temp)
            if index == 0:
                t_to_change = temp_tuple[1]
            elif index == len(temp_tuple) - 1:
                t_to_change = temp_tuple[-1]
            else:
                t_to_change = temp_tuple[index + random.choice([-1, 1])]
            return t_to_change


if __name__ == "__main__":
    options = parse_cmd()
    cfg = ConfigObj(options.cfg_file)

    ts = cfg['miscellaneous']['init_temps']
    u = cfg['miscellaneous']['uniform_spacing']
    hostfile = cfg['system']['hostfile']

    hostname = socket.gethostname()
    hostip = socket.gethostbyname(hostname)
    port = os.getenv('PORT', 5000)
    debug = False
    if not os.path.exists(hostfile):
        with open(hostfile, 'w') as opf:
            opf.write('http://{0}:{1}\n{2}\n'.format(hostip, port, hostname))

    thread = threading.Thread(target=run_app, kwargs={'hostip':hostip, 'port':port, 'debug':debug})
    thread.start()

    time.sleep(5)
    main()
