import os
import socket
import requests
import subprocess
from StringIO import StringIO
from subprocess import PIPE
from configobj import ConfigObj

import sqlalchemy as sqlmy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

def init_db():
    cfg = ConfigObj('./pydr.cfg')
    database = cfg['system']['database']
    db = sqlmy.create_engine('sqlite:///{0}'.format(database), echo=True)
    ss = sessionmaker(bind=db, autoflush=True, autocommit=False)()
    Base.metadata.create_all(db)
    for pset in cfg['parametersets']:
        s = cfg['parametersets'][pset]
        mdp_file = os.path.join(os.getenv('PWD'), s['mdp_file'])
        ad = Parameterset(s['ref_t'], s['gen_temp'], mdp_file)
        ss.add(ad)
    ss.commit()

class Job(object):
    def __init__(self):
        hostname = socket.gethostname()
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
        
    def connect_server(self, url, **kwargs):
        if kwargs:
            self.__dict__.update(kwargs)
        return requests.post(url=url, data=self.__dict__)

    def check(self):
        for i in dir(self):
            print getattr(self, i)

class Parameterset(Base):
    __tablename__ = 'parametersets'

    setid = Column(Integer, primary_key=True)
    ref_t = Column(String)
    gen_temp = Column(String)
    mdp_file = Column(String)

    def __init__(self, ref_t, gen_temp, mdp_file):
        self.ref_t = ref_t
        self.gen_temp = gen_temp
        self.mdp_file = mdp_file

    def __repr(self):
        return "setid {0}; ref_t {1}; gen_temp {2}; mdp_file{3}".format(
            self.setid, self.ref_t, self.gen_temp, self.mdp_file)


class Request(Base):
    __tablename__ = 'requests'

    requestid = Column(Integer, primary_key=True)
    pbs_jobid = Column(String)
    pbs_o_workdir = Column(String)
    replica = Column(String)
    parameterset_rece = Column(String)
    parameterset_sent = Column(String)

    def __init__(self, requestid, pbs_jobid, pbs_o_workdir, 
                 replica, parameterset_rece, parameterset_sent):
        self.requestid = requestid
        self.pbs_jobid = pbs_jobid
        self.pbs_o_workdir = pbs_o_workdir
        self.replica = replica
        self.parameterset_rece = parameterset_rece
        self.parameterset_sent = parameterset_sent
                 
    def __repr__(self):
        return "requestid {0}; pbs_jobid {1}; pbs_o_work {2}; replica {3}; parameterset_rece {4}; parameterset_sent {5}".format(requestid, pbs_jobid, pbs_o_workdir, replica, parameterset_rece, parameterset_sent)



class Rep(object):                       # used to be sent from client to server
    def __init__(self, repid):
        pwd = os.path.getenv['PWD']
        self.repid = repid
        self.dir = os.path.join(pwd, cfg['replicas'][repid])
        self.deffnm = str(repid)

    def get_pot_energy(self):
        def pe(edrf):
            i = 'Potential'
            p = subprocess.Popen(['g_energy', '-f', edrf], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate(i)
            for line in StringIO.StringIO(stdout):
                if line.startswith(t):
                    return line.split()[1]
            
        edrf = os.path.join(self.dir, '{0}.edr'.format(self.deffnm))
        if os.path.exists(edrf):
            return pe(edrf)
        
if __name__ == "__main__":
    init_db()


