#!/usr/bin/env python
import os
import random
import logging
import requests
import subprocess
import threading
import pickle
import json
from configobj import ConfigObj
from flask import Flask, request, session, g
from cls import *

from pprint import pprint as pp

def main():
    cfg = ConfigObj('../../pydr.cfg')
    hostfile = cfg['system']['hostfile']
    temp_tuple = tuple(cfg['miscellaneous']['temp_tuple'])

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
                    'firsttime' : 0,
                    }
            else:
                rep_info = {
                    'firsttime': 1,
                    'replicaid': rep.replicaid,
                    'temperature' : rep.temperature,
                    'temperature_to_change': rep.get_temperature_to_change(temp_tuple),
                    'potential_energy': rep.get_potential_energy(),
                    'directory': rep.directory}

            r = j.connect_server(uri, rep_info)
            print r.content, type(r.content)
            d = json.loads(r.content)
            rep = Replicas(d['replicaid'], d['temperature'], d['directory'])
            print type(d['temperature'])
            print dir(rep)
            count += 1
            if count == 4:
                break

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

