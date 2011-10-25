#!/usr/bin/env python

import copy
import time
import requests
import subprocess
from configobj import ConfigObj
from Job import Job

import os
import random

import sqlalchemy as sqlmy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

from pprint import pprint as pp

def test_connect():
    url = 'http://127.0.0.1:5000'
    j = Job()
    task = j.connect_server(url)
    print task

def test_read_cfg():
    cfg = ConfigObj('/home/zyxue/projects/pydr/sq1e/pydr.cfg')

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

class Replica(Base):
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
    test_connect()


# class Exchanges(Base):
#     __tablename__ = "Exchanges"
    
#     exchangeid = Column(Integer, primary_key=True)
#     potential_energy = Column(Float)
#     original = Column(Integer)
#     to_change = Column(Integer)
#     changed = Column(Integer)
#     global_temps = Column(String)
#     date = Column(String)
    
#     def __init__(self, potential_energy, original, to_change, changed, global_temps, date): # 
#         self.potential_energy = potential_energy
#         self.original = original
#         self.to_change = to_change
#         self.changed = changed
#         self.global_temps = global_temps
#         self.date = date

#     def __repr__(self):
#         return "<%r %r %r %r %r %r>" % (self.potential_energy, self.original, self.to_change, self.changed, self.global_temps, self.date)


# def exchange_or_not(original, to_change):
#     import random
#     if random.randint(0, 1) == 1:
#         changed = to_change
#     else:
#         changed = original
#     return changed

# def test_init_values():
#     initial_temps = range(200, 301, 10)
#     global_temps = ' '.join([str(i) for i in initial_temps])

#     potential_energy = None
#     original = None
#     to_change = None
#     changed = None
#     date = time.ctime()

#     return potential_energy, original, to_change, changed, global_temps, date

# def test_write_db(session):
#     potential_energy, original, to_change, changed, global_temps, date = test_init_values()

#     gt = global_temps.split(' ')

#     for i in range(10):
#         k = random.randint(0,10)
#         original = gt[k]
#         if k == 10:
#             to_change = gt[0]
#         else:
#             to_change = gt[k+1]
#             changed = exchange_or_not(original, to_change)
#             gt[k] = changed
#             global_temps = ' '.join(gt)
#             date = time.ctime()
#             ex = Exchanges(potential_energy, original, to_change, changed, global_temps, date)
#         ss.add(ex)

#     session.commit()

# def test_read_db(session):
#     q = session.query(Exchanges)
#     s = q.filter(Exchanges.exchangeid == '1')
#     print "#" * 20
#     print s[0].global_temps
#     print "#" * 20

# if __name__ == "__main__":
#     # firsttime_write_db(ss)
#     # test_write_db(ss)
#     test_read_db(ss)

