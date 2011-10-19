import copy
import time
import json
import requests
import subprocess


u = requests.post(url='http://127.0.0.1:5000/', data={'job_done':True})
cmd = json.loads(u.content)
subprocess.call(cmd)


# rep = json.loads(u)
# print rep


# print rep.current_temp
# print type(rfpr)
# print rfpr
# x = pickle.loads(rfpr)
# print type(x)


# print f.read()

# u = urllib2.urlopen('http://127.0.0.1:5000')
# b = u.read()
# print b
# print type(b)
# c = json.loads(b)
# print c
# print type(c)
# print json.loads(b)
