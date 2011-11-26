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

Base = declarative_base()                                   # essential for using sqlalchemy, not know why, there should be a better implementation, I guess.
app = Flask(__name__)                                       # essential for using Flask, not know why, there is probably not a better implementation, I guess.

def init_db(database):
    """initialize the database, create a Session instance"""
    engine = create_engine('sqlite:///{0}'.format(database), echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=True, autocommit=False)
    return Session

def connect_db(database):
    """connect to the database"""
    Session = init_db(database)
    return Session()

def DRPE(state, ts, u, c1, c2):
    """
    calculate the DRPE: Distributed Replica Potential Energy.
    state: a list of temperatures for all the current replicas
    ts: a list of preset temperatures
    u: as the name indicates
    
    check the supplemental info of Sarah's 2009 paper for details
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
    """
    The function implemented here is

    probability = exp(-(beta2 - beta1)* pot_ener + (a2 - a1) - (DRPE2 - DRPE1))
    
    and return prob, DRPE1, DRPE2

    check the supplemental info of Sarah's 2009 paper for details
    """

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
    """
    The following code will be executed each time at the beginning of the
    establishment of the connection between server and client
    """

    ts = cfg['miscellaneous']['init_temps']
    db = cfg['system']['database']

    g.ss = connect_db(db)                                      # g is a sub module from flask
    if g.ss.query(Exchange.exid).count() == 0:                 # prevent inserting init_temps multiple times
        g.ss.add(Exchange(exid=0, rid='--', repcount='--', t1='--', t2='--', 
                          DRPE1='--', DRPE2='--', pot_ener='--',
                          global_temp=' '.join(ts), date=time.ctime()))

@app.teardown_request
def teardown_request(exception):
    """
    The following code will be executed each time at the beinning of the
    closure of the connection between the server and client
    """
     if hasattr(g, 'ss'):
        g.ss.commit()                                       # commit the transactions to the database

# 1. This descriptor defines the address of the url, that's all what I know, but I
# am quite sure there are more about it. Learn flask.
# 2. I wrote GET there, but I don't think it useful because it will alway be POST
# as defined in connect_server method in the Job class
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST': # "request" is a submodule in flask, which will handle the request from the client side
        # transform request.form, which is a multidict, to a normal dict in
        # one-key-one-value pattern I forget though, multidict may have
        # one-key-multiple-value pattern or multiple-key-one-value? which won't
        # happen in this code.
        rep_info = dict((k, v) for k, v in request.form.to_dict().iteritems())
        
        if rep_info['firsttime'] == '1':                    # recall how rep_info is defined in the cliend side
            # if it's the firsttime the client is talking to the server, assign
            # the the parameters predefined for this replica according to where
            # it is located. I feel this way of identification is really awful.
            # And no exchange is attempted, and no calculation of DRPE will
            # happen.
            rid = rep_info['rid']
            replicas = cfg['replicas']                      # replicas will be a 2D dictionary, check the pydr.cfg for details.
            r = replicas[rid]                               # r will be a 1D dictionary, I seemed to be out of intuitive names. :)
            repcount = 1                                    # first time exchange. You could consider the previous one is 0.
            new_rep_info = {
                'rid': rid,
                'old_temp': None,                           # since it's first time, no old_temp.
                'temp': r['init_temp'],
                'directory': r['directory'],
                'repcount':repcount
                }
            # json.dumps the dictionary, pay attention to the name, it's
            # new_rep_info rather than rep_info. the info server sends is
            # considered relatively newer than the one received, always.
            return json.dumps(new_rep_info) 
        else: # if not first time, all the following parameters should be
              # available, and an exchange must have been attempted, DRPE will
              # be calculated
            rid = rep_info['rid']
            t1 = rep_info['temp']                           # so t1 is the same as temp, BAD NAME (BN)
            t2 = rep_info['temp_to_change']                 # so t2 is the same as temp_to_change (BN)
            pot_ener = rep_info['pot_ener']
            # repcount +1, this piece of info won't be used to calculate DRPE,
            # but keeping track of the simulations
            repcount = int(rep_info['repcount']) + 1


####################
# Above this line, preprocessing the incoming info from the client size is
# done. Next, some extra variables will be prepared for DRPE calculation, and
# then decide wheter the exchange should happen or not.
####################

            # This line queries the database: pydr.db, which stores the
            # global_temp (BN), which means the collection of current
            # temperatures for all the replica at a particular moment when a
            # new exchange is attempted. g is a submodule of flask, I forget
            # its exact function. ss is defined in the def before_request
            history_temps = g.ss.query(Exchange.exid, Exchange.global_temp).order_by('exid').all()
            current_temps = history_temps[-1][1].split()  # get current global_temp

            state1 = current_temps                          # current state of temperatures
            _state2 = copy.copy(current_temps)
            _state2[current_temps.index(t1)] = t2           
            state2 = _state2                                # potential future state of temperatures if the exchange is accepted.

            # This line calls the probability function, which will calculate
            # DRPE for the current and potential future state, and return the
            # probabily, check def probility for details.
            # t1: the current temperatue for the replica that attempt this exchange
            # t2: the new temperature that the replica is attempting to change to
            # state1 & 2: as explain above
            # ts, the global temperature (GV), u: uniform_spacing(GV)
            # a1, a2, c1, c2 are constants, the values here are chosen randomly.
            prob, DRPE1, DRPE2 = probability(t1, t2, pot_ener, state1, state2,
                                             ts, u, a1=1, a2=1, c1=0.005, c2=0.005)
            p = min(1, prob)                                # check the STDR algorithm

            if p >= 1:
                new_temp = t2                               # exchange attempt is accepted
            else:
                # else. the probability of acceptance is p, random.random will pick a value between [0, 1]
                if random.random() > p:
                    new_temp = t2
                else:
                    new_temp = t1

            # calculate the new global_temperature, which could be the same if the attempt is not accepted, but we still name it new.
            if new_temp == t2:
                new_current_temp = ' '.join(state2)         # attempt accepted
            else:
                new_current_temp = ' '.join(state1)         # attempt rejected

            # write it to the database
            g.ss.add(Exchange(rid=rid, repcount=repcount, t1=t1, t2=new_temp, 
                              DRPE1=DRPE1, DRPE2=DRPE2,pot_ener=pot_ener, 
                              global_temp=new_current_temp, date=time.ctime()))
        
            # collect the new_rep_info, and send it to the client.
            new_rep_info = {
                'rid': rid,
                'old_temp': t1,
                'temp': new_temp,
                'directory': rep_info['directory'],
                'repcount': repcount
                }
            return json.dumps(new_rep_info)

    if request.method == 'GET':                     # just for fun, never mind.
        return "hello"
    # That's the whole work flow, next I will annotate each of the rest function and classes.

class Exchange(Base):
    """
    This basically create a table using sqlalchemy for the database that is
    gonna store all the information of each exchange, but the following schema
    should be redesigned!!
    """

    # name of the table, I followed the tutorial of sqlalchemy, not sure if
    # this attribute is essential or not
    __tablename__ = "exchanges"

    exid = Column(Integer, primary_key=True)                # exchange id
    rid = Column(String)                                    # replica id, the one that attempts a particular exchange
    repcount = Column(String)                               # repcount for a particular exchange of a particular replica
    t1 = Column(String)                                     # current temperature
    # new temperature that assigned after the exchange calculation, could be same as current temperature
    t2 = Column(String)
    DRPE1 = Column(String)                                  # calculated DRPE using t1
    DRPE2 = Column(String)                                  # calculated DRPE using t2
    pot_ener = Column(String)                               # the potential energy when the exchange is calculated
    global_temp = Column(String)                            # the collection of current temperatures for all replicas
    date = Column(String)                                   # the time when the exchange is attempted

def parse_cmd():
    """parse the command line, new options could(should?) be added"""
    parser = optparse.OptionParser()
    parser.add_option('-c', '--cfg', dest='cfg_file', default='../../pydr.cfg', help="where's the configuration file")
    options, args = parser.parse_args()
    return options

def run_app(hostip, port, debug=False):
    """runs app, this function is written because otherwise I don't know how to start a new thread for running the server"""
    app.run(host=hostip, port=port, debug=False)
    # app.run(host='0.0.0.0', port=5000, debug=False)

def main():
    
    cfg = ConfigObj('../../pydr.cfg')                       # read pydr.cfg, REDUNDANT
    hostfile = cfg['system']['hostfile']                    # get address for hostfile, REDUNDANT
    init_temps = cfg['miscellaneous']['init_temps']         # same as ts, REDUNDANT

    rep = None                                              # rep will be a instance of Replica class, but initialized as None
    count = 0                                               # for debugg use only, otherwise, the while loop will be forever.
    while True:                                             # if walltimg hasn't been reached, the STDR simulation shall keep working.
        if not os.path.exists(hostfile):
            logging.error('No hostfile!\n')                 # no hostfile found, error.
        else:
            with open(hostfile, 'r') as inf:
                # just 2 seconds, in case the hostfile has been opened by
                # another node, but the writting hasn't finished yet. more than
                # that means server died
                for i in range(2): # 2 means approximately 2 seconds, reason
                                   # explained in the above 3 lines, the
                                   # details like the usage of inf.tell,
                                   # inf.seek is referenced from stakeflow
                    where = inf.tell()
                    line = inf.readline().strip()
                    if not line.strip():
                        time.sleep(1)
                        inf.seek(where)
                    else:
                        uri = line                          # ip got, uri & ip are the same
                        break

    # part of to-do list.
    # 1. After unexpected scient crush, everything should be restarted, and cpt file will be used.
    # 2. functions and classes should be modulized

            j = Job() # create an instance of Job class, which will get all
                      # node specific attributes from environmental variables,
                      # check the class definition for details
            if rep is None: 
                # rep is None means it's the first time for self-job to prepare
                # replica relevant parameters (rep_info) so as to communicate
                # with the server. Here, the parameters I have defined are
                # "first time, rid, temp, temp_to_change, pot_ener, directory,
                # repcount", and stored in a dictionary as you will see in the
                # following lines. These would better be renamed to some
                # variables that make more sense, and we'd better make it
                # relatively easy to add new parameters if necessary in the
                # future.
                rep_info = {
                    # firsttime 1 means True, it is the first time, I didn't
                    # use True because after the http transfer, everything will
                    # be turned into a string, and True will be just string
                    # "True" rather than special variable type True.
                    'firsttime' : 1, 
                    # This line is awful, I get the rid from the environmental
                    # variable PWD, which will is also the directory where this
                    # replica is located,
                    # e.g. /Users/zyxue/Projects/pydr/sq1e/replicas/00, then,
                    # only basename ('00' in the example) will be used as rid.
                    'rid': os.path.basename(os.getenv('PWD')) 
                    }
            else: # not firsttime, rep will be assigned an instance of a
                  # Replica class as you will see in a line in the following
                rep_info = {
                    'firsttime': 0,                         # firsttime 0 means not first time anymore
                    'rid': rep.rid,                         # now, you can easily get rid from the rep, the instance of Replica class
                    'temp' : rep.temp,                      # so is temp
                    'temp_to_change': rep.get_temp_to_change(init_temps), # get the temp_to_change, from the method of Replica instance
                    # so is potential_energy. At first, I was thinking parseing
                    # a edrf, but it won't be necessary if every name of the
                    # files created follows a particular CONVENTION. This
                    # CONVENTION needs to be carefull desgined, I think
                    'pot_ener': rep.get_pot_ener(),
                    'directory': rep.directory,             # e.g. /Users/zyxue/Projects/pydr/sq1e/replicas/00
                    'repcount': rep.repcount}               # counting the time of exchanges for this replica only.

            # after all the rep_info is prepared, it's ready for the the job
            # instance (j) to connect to the server, after some calculation in
            # the server side, a json object r will be returned
            r = j.connect_server(uri, rep_info)
            print r.content, type(r.content)                # for debugging
            # loads the content of the the json object r. The content will be
            # in a dictionary as well, but values has been processed as
            # reassigned by the server. NOTE: I don't how json works, not even
            # what json is, but pass all the contents in the form of a
            # dictionary works for http communication after some trial & error.
            # I will be glab if someone could explain to me
            js = json.loads(r.content)
            # See, in this line, None is replaced with the content from the server, and assigned to rep. rep will no longer be None anymore.
            rep = Replica(js['rid'], js['old_temp'], js['temp'], js['directory'], js['repcount']) 

            # some addition awful lines again. The following several lines are
            # trying to rewrite a file called 0_mdrun.sh, which should include
            # lines like "grompp -f <some.gro> -s <some.tpr> ..." and "mdrun
            # -deffnm ..." (or "mpirun -np 8 mdrun_mpi -deffnm"), based on the
            # template: ../../0_mdrun.tmp, and then execute it. However, since
            # even python files could be submitted directory, I think we should
            # think about how to do every thing in python. When I was writing
            # this thing, I got quite tired at the end, and was trying to make
            # it run properly as soon as possible, no matter how ugly it was.
            kwargs = {'_MDPF_': rep.mdpf, # for attributes like mdpf,
                                          # old_deffnm, deffnm, have a look at
                                          # my 0_mdrun.sh file will make sense.
                      '_old_DEFFNM_': rep.old_deffnm,
                      '_DEFFNM_': rep.deffnm}
            with open('../../0_mdrun.tmp', 'r') as inf:
                with open('0_mdrun.sh', 'w') as opf:
                    opf.writelines([Template(l).safe_substitute(kwargs)
                                   for l in inf.readlines()])
            subprocess.call(['bash', '0_mdrun.sh'])
            # after the call in the upper line is finished, another loop will
            # start, remember rep is nolonger none anymore.
            # now let's turn to the server side, and have a look at "def index"
            count += 1                            # as mentioned, for debugging only
            if count == 4:                        # as mentioned, for debugging only, if reached 4 exchange, break.
                break


class Job(object):
    def __init__(self):
        hostname = socket.gethostname()
        self.pbs_hostname = hostname
        # for debugging only, when testing the code in my local system since
        # otherwise all the environmental variables will be empty
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
        """if you could recall from the def main, data is named rep_info"""
        data.update(self.__dict__)                          # including all the attributes defined in __init__
        return requests.post(uri, data)

    def check(self):                                        # for debug only
        for i in dir(self):
            print getattr(self, i)


class Replica(object):                  # used to be sent from client to server
    """I just added a few comments to this class since I have already explained it in our last meeting"""
    def __init__(self, rid, old_temp, temp, directory, repcount):
        self.rid  = rid                                 # e.g. 00 01
        self.old_temp = old_temp                            # we need this for writting the new 0_mdrun.sh, recall from def main, which is ugly design.
        self.temp = temp
        self.directory = directory
        self.repcount = repcount
        self.mdpf = '../../parametersets/{0}.mdp'.format(temp) # This is not pretty, either.
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
    options = parse_cmd()                                   # parse the command line
    cfg = ConfigObj(options.cfg_file)                       # read the pydr.cfg

    # ts means temperatures, the tuple of temperatures that is not gonna
    # change over the whole STDR simulation, better be global variables(GV)?
    ts = cfg['miscellaneous']['init_temps']                 
    u = cfg['miscellaneous']['uniform_spacing']             # uniform_spacing, necessary for calculating DRPE, GV?
    hostfile = cfg['system']['hostfile']                    # directory for hostfile, used to store the IP of the server

    hostname = socket.gethostname()                         # get the hostname
    # resolve the hostname, and get the ip address of the node that this
    # particular job (self-job) is running on (self-node)
    hostip = socket.gethostbyname(hostname)
    port = os.getenv('PORT', 5000)                          # pickt a port number, default(5000)
    
    # if True, more convenient for debugging. At the beginning, I have two
    # separate files, server.py & client.py. server.py will keep running all
    # the time, and restarts itself if anything in it changed. I don't
    # think it make sense any more when the two files are combined.
    debug = False

    # if no hostfile has been written, self-job will create a new hostfile with its
    # own ip, then self-node becomes the server
    if not os.path.exists(hostfile): 
        with open(hostfile, 'w') as opf:
            opf.write('http://{0}:{1}\n{2}\n'.format(hostip, port, hostname))

    # create a new thread for running server(self-server), if the ip in the
    # hostfile doesn't point to self-node, self-server will just be idling all
    # the time.
    thread = threading.Thread(target=run_app, kwargs={'hostip':hostip, 'port':port, 'debug':debug})
    thread.start()

    time.sleep(5)                                           # not sure what this does, yet.
    main()                                                  # continued at def main()

