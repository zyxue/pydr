#! /usr/bin/env python

import os
import socket
import optparse
import pickle
import json
import time

from configobj import ConfigObj
from numpy import exp

from flask import Flask, request, g, session
from collections import deque

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def init_db(database):
    engine = create_engine('sqlite:///{0}'.format(database), echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=True, autocommit=False)
    return Session

def connect_db(Session):
    return Session()

def test_connect_db():
    db = 'test.db'
    Session = init_db(db)
    ss = connect_db(Session)
    return ss

def test_insert_db():
    ss = test_connect_db()
    if ss.query(Exchange.exid).count() == 0:
        ss.add(Exchange(exid=0, rid=0, repcount=0, t1=0, t2=0, DRPE1=0, DRPE2=0, pot_ener=0,
                        global_temp='300 310 320 330', date=time.ctime()))

    for i in [[1, 2, 3, 4], [2,1,3,4], [4,3,1,2]]:
        ss.add(Exchange(rid=0, repcount=0, t1=0, t2=0, DRPE1=0, DRPE2=0, pot_ener=0,
                        global_temp=' '.join(str(k) for k in i), date=time.ctime()))
    ss.commit()

def test_query_db():
    ss = test_connect_db()
    x = ss.query(Exchange.exid, Exchange.global_temp).order_by('exid').all()
    print x[-1][1]                                          # current global_temp

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

def test_DRPE():
    state_A = [305, 296, 288, 280, 288]
    state_B = [296, 296, 288, 280, 288]
    ts = (280, 288, 296, 305, 314)
    u = (1, 2, 3, 4, 5)
    for state in [state_A, state_B]:
        print DRPE(state, ts, u, c1=0.02, c2=0.05)

def prob(t1, t2, pot_ener, state1, state2, ts, u, a1=1, a2=1, c1=0.005, c2=0.005):
    """exp(-(beta2 - beta1)* pot_ener + (a2 - a1) - (DRPE2 - DRPE1))"""
    k = 1.3806503e-23  # Unit: (m2 kg s-2 K-1)
    beta1 = 1 / (k * t1)
    beta2 = 1 / (k * t1)
    DRPE1 = DRPE(state1, ts, u, c1, c2)
    DRPE2 = DRPE(state2, ts, u, c1, c2)

    return exp(-(beta2 - beta1) * pot_ener + (a2 - a1) - (DRPE2 -DPRE1))

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

if __name__ == "__main__":
    test_insert_db()
    # test_query_db()

