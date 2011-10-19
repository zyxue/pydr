import urllib
import urllib2
import pickle
import copy
from Replica import Replica

rep = Replica(123, 290)
nrep = copy.copy(rep)
print id(rep)
print id(nrep)

prep = pickle.dumps(rep)
data = urllib.urlencode(dict(prep=prep))
u = urllib2.urlopen(url='http://127.0.0.1:5000/', data=data)
rep = u.read()
print rep
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
