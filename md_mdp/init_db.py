import os
import time
import random

import sqlalchemy as sqlmy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float

Base = declarative_base()

class Variables(Base):
    __tablename__ = 'Variables'

    id = Column(Integer, primary_key=True)
    ref_t = Column(String)
    gen_temp = Column(String)

    def __init__(self, ref_t, gen_temp):
        self.ref_t = ref_t
        self.gen_temp = gen_temp

    def __repr__(self):
        return "<id: %d ref_t: %s>" % (id, ref_t)

class Exchanges(Base):
    __tablename__ = "Exchanges"
    
    exchangeid = Column(Integer, primary_key=True)
    potential_energy = Column(Float)
    original = Column(Integer)
    to_change = Column(Integer)
    changed = Column(Integer)
    global_temps = Column(String)
    date = Column(String)
    
    def __init__(self, potential_energy, original, to_change, changed, global_temps, date): # 
        self.potential_energy = potential_energy
        self.original = original
        self.to_change = to_change
        self.changed = changed
        self.global_temps = global_temps
        self.date = date

    def __repr__(self):
        return "<%r %r %r %r %r %r>" % (self.potential_energy, self.original, self.to_change, self.changed, self.global_temps, self.date)

def init_db(ref_ts):
    for t in ref_ts:
        gen_temp = '{t}\t{t}'.format(t=t)
        var = Variables(ref_t=t, gen_temp=gen_temp)
        ss.add(var)

def exchange_or_not(original, to_change):
    import random
    if random.randint(0, 1) == 1:
        changed = to_change
    else:
        changed = original
    return changed

def test_init_values():
    initial_temps = range(200, 301, 10)
    global_temps = ' '.join([str(i) for i in initial_temps])

    potential_energy = None
    original = None
    to_change = None
    changed = None
    date = time.ctime()

    return potential_energy, original, to_change, changed, global_temps, date

def test_firsttime_write_db(session):
    if not os.path.exists('/tmp/md_mdp.db'):
        init_db(initial_temps)
    
    ex = Exchanges(*test_init_values())
    ss.add(ex)

def test_write_db(session):
    potential_energy, original, to_change, changed, global_temps, date = test_init_values()

    gt = global_temps.split(' ')

    for i in range(10):
        k = random.randint(0,10)
        original = gt[k]
        if k == 10:
            to_change = gt[0]
        else:
            to_change = gt[k+1]
            changed = exchange_or_not(original, to_change)
            gt[k] = changed
            global_temps = ' '.join(gt)
            date = time.ctime()
            ex = Exchanges(potential_energy, original, to_change, changed, global_temps, date)
        ss.add(ex)

    session.commit()

def test_read_db(session):
    q = session.query(Exchanges)
    s = q.filter(Exchanges.exchangeid == '1')
    print "#" * 20
    print s[0].global_temps
    print "#" * 20

if __name__ == "__main__":
    engine = sqlmy.create_engine('sqlite:////tmp/md_mdp.db', echo=True)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    ss = Session()
    # firsttime_write_db(ss)
    # test_write_db(ss)
    test_read_db(ss)

