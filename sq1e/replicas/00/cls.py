import os
import socket
import requests
import subprocess
import StringIO
import logging
import random
from subprocess import PIPE
from configobj import ConfigObj

import sqlalchemy as sqlmy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

# def init_db():
#     cfg = ConfigObj('./pydr.cfg')
#     database = cfg['system']['database']
#     db = sqlmy.create_engine('sqlite:///{0}'.format(database), echo=True)
#     ss = sessionmaker(bind=db, autoflush=True, autocommit=False)()
#     Base.metadata.create_all(db)
#     for pset in cfg['parametersets']:
#         s = cfg['parametersets'][pset]
#         ad =  Replica(s['ref_t'], s['gen_temp'], s['mdp_file'])
#         ss.add(ad)
#     ss.commit()

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

# class Parameterset(object):
#     def __init__(self, temperature):
#         self.temperature = temperature
#         self.linked_mdpfile = 


class Parameterset(Base):
    __tablename__ = 'parametersets'

    id = Column(Integer, primary_key=True)
    psetid = Column(String)                                      # e.g. 300, 310
    ref_t = Column(String)
    gen_temp = Column(String)
    mdp_file = Column(String)

    def __init__(self, ref_t, gen_temp, mdp_file):
        self.ref_t = ref_t
        self.gen_temp = gen_temp
        self.mdp_file = mdp_file

    def __repr(self):
        return "setid {0}; ref_t {1}; gen_temp {2}; mdp_file{3}".format(
            self.psetid, self.ref_t, self.gen_temp, self.mdp_file)


class Replicas(object):                  # used to be sent from client to server
    def __init__(self, replicaid, temperature, directory):
        self.replicaid  = replicaid                                 # e.g. 00 01
        self.temperature = temperature
        self.directory = directory
        self.deffnm = '{0}_{1}'.format(replicaid, temperature)

    def get_potential_energy(self):
        def pe(edrf):
            i = 'Potential'
            p = subprocess.Popen(['g_energy', '-f', edrf], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate(i)
            for line in StringIO.StringIO(stdout):
                if line.startswith('Potential'):
                    return line.split()[1]

        edrf = os.path.join(self.directory, '{0}.edr'.format(self.deffnm))
        if os.path.exists(edrf):
            return pe(edrf)
        else:
            logging.error("{0} doesn't exist when trying to get potential energy".format(edrf))

    def get_temperature_to_change(self, temp_tuple):
        if not self.temperature in temp_tuple:
            logging.error('{0} is not in the temp_list'.format(self.temperature))
        else:
            index = temp_tuple.index(self.temperature)
            if index == 0:
                t_to_change = temp_tuple[1]
            elif index == len(temp_tuple) - 1:
                t_to_change = temp_tuple[-1]
            else:
                t_to_change = temp_tuple[index + random.choice([-1, 1])]
            return t_to_change

if __name__ == "__main__":
    init_db()


