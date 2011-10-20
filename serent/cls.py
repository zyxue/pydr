import os
import socket
import requests
from configobj import ConfigObj

import sqlalchemy as sqlmy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
Base = declarative_base()

def init_db():
    cfg = ConfigObj('/home/zyxue/projects/pydr/sq1e/pydr.cfg')
    database = cfg['system']['database']
    db = sqlmy.create_engine('sqlite:///{0}'.format(database), echo=True)
    Session = sessionmaker(bind=db)
    Session.configure(bind=db)
    ss = Session()

    Base.metadata.create_all(db)
    for r in cfg['replicas']:
        rep = cfg['replicas'][r]
        ad =  Replica(rep['ref_t'], rep['gen_temp'], 0)
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
        
    def connect_server(self, url):
        return requests.post(url=url, data=self.__dict__)

    def check(self):
        for i in dir(self):
            print getattr(self, i)

class Replica(Base):
    # need further change: ss.add(Replica(cfg['job']['name'] + r, ['name'], rep['ref_t'], rep['gen_temp'], 0))
    __tablename__ = 'replicas'

    replicaid = Column(Integer, primary_key=True)
    ref_t = Column(String)
    gen_temp = Column(String)
    status = Column(Integer)

    def __init__(self, ref_t, gen_temp, status):
        self.ref_t = ref_t
        self.gen_temp = gen_temp
        self.status = status

    def __repr__(self):
        return "<id: %d ref_t: %s gen_temp: %s status %d>" % (
            self.replicaid, self.ref_t, self.gen_temp, self.status)



if __name__ == "__main__":
    init_db()

