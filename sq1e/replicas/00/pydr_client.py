#!/usr/bin/env python
import os
import random
import logging
import requests
import subprocess
import threading
import pickle
import json
import socket
import StringIO
from string import Template

from configobj import ConfigObj
from flask import Flask, request, session, g

from pprint import pprint as pp

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
            j = json.loads(r.content)
            rep = Replicas(j['rid'], j['old_temp'], j['temp'], j['directory'], j['repcount'])
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


class Replicas(object):                  # used to be sent from client to server
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
        def pe(edrf):
            i = 'Potential'
            p = subprocess.Popen(['g_energy', '-f', edrf], 
                                 stdin=subprocess.PIPE, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
            stdout, stderr = p.communicate(i)
            for line in StringIO.StringIO(stdout):
                if line.startswith('Potential'):
                    return line.split()[1]

        edrf = os.path.join(self.directory, '{0}.edr'.format(self.deffnm))
        if os.path.exists(edrf):
            return pe(edrf)
        else:
            logging.error("{0} doesn't exist when trying to get potential energy".format(edrf))
            return '0'

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
    main()
