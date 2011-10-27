#!/usr/bin/env python

import requests
import subprocess
from configobj import ConfigObj
from cls import Job

import os
import random

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

from pprint import pprint as pp

def test_connect():
    url = 'http://127.0.0.1:5000'
    j = Job()
    task = j.connect_server(url)
    print task.content

def test_init_db():
    cfg = ConfigObj('/home/zyxue/projects/pydr/sq1e/pydr.cfg')
    database = cfg['system']['database']
    db = sqlmy.create_engine('sqlite:///{0}'.format(database), echo=True)
    Session = sessionmaker(bind=db)
    Session.configure(bind=db)
    ss = Session()
    if not os.path.exists(database):                              # first time
        Base.metadata.create_all(db)
        for r in cfg['replicas']:
            rep = cfg['replicas'][r]
            ss.add(Replica(rep['ref_t'], rep['gen_temp'], 0))
        ss.commit()
    else:
        q = ss.query(Replica)
        qf = q.filter(Replica.ref_t == '300')[0]
        pp(type(qf))
        pp(dir(qf))
        print type(qf.status)



if __name__ == "__main__":
    test_connect()
