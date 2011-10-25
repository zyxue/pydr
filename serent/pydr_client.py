#!/usr/bin/env python

import copy
import time
import requests
import subprocess
import logging
import threading
from flask import Flask, request, session, g
from string import Template
from configobj import ConfigObj
from cls import *

import pydr
import os
import random

import sqlalchemy as sqlmy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float

from pprint import pprint as pp

Base = declarative_base()

def run_app():
    pydr.app.run()

def main():
    cfg = ConfigObj('/home/zyxue/projects/pydr/sq1e/pydr.cfg')
    database = cfg['system']['database']

    # should be done by the server
    if not os.path.exists(database):                              # first time
        init_db()

        # start_server
        # threading.Thread(target=run_app).start()
        uri = 'http://127.0.0.1:5000'
        # write server address to some file
        with open(cfg['system']['hostfile'], 'w') as opf:
            opf.write('{0}\n'.format(uri))

        # starts pydr in all directories
        for r in cfg['replicas']:
            rep = cfg['replicas'][r]
            rdir = os.path.join(cfg['system']['pwd'], r)
            os.chdir(rdir)
            if os.path.exists('0_mdrun.sh'):
                print rdir, '0_mdrun.sh'    
                # in real submit 0_mdrun.sh instead, 0_mdrun.sh contains the
                # code that run pydr.py in rdir
            else:
                logging.error('{0} has not 0_mdrun.sh'.format(rdir))

    # client:
    # get the replica number from the server

    else:
        # 1. the server shall has been running, look for server address, could request for job now
        # 2. after unexpected scient crush, everything should be restarted, and cpt file will be used.

        # 1. Should check existence of hostfile to make sure server is running; how?
        while True:
            with open(cfg['system']['hostfile'], 'r') as inf:
                uri = inf.readline().strip()
                j = Job()
                r = j.connect_server(uri)
                # done something with r
                print r.content

        # md_mdpf = os.path.join(rdir, '{0}_md.mdp'.format(pf))
        # with open(cfg['system']['smp_md_mdp'], 'r') as inf:
        #     with open(md_mdpf, 'w') as opf:
        #         opf.writelines([Template(l).safe_substitute(dict(rep))
        #                         for l in inf.readlines()])

if __name__ == "__main__":
    main()

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

