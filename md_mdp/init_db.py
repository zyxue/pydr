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
        return "<%d %f %s %s %r>" % (potential_energy, to_change, changed, date)

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


if __name__ == "__main__":
    engine = sqlmy.create_engine('sqlite:////tmp/md_mdp.db', echo=True)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    ss = Session()

    initial_temps = range(200, 301, 10)

    if not os.path.exists('/tmp/md_mdp.db'):
        init_db(initial_temps)

    gt = [str(i) for i in initial_temps]
    global_temps = ' '.join(gt)

    potential_energy = 12.003
    original = None
    to_change = None
    changed = None
    date = time.ctime()

    for i in range(10):
        ex = Exchanges(potential_energy, original, to_change, changed, global_temps, date)
        ss.add(ex)
        k = random.randint(0,10)
        original = gt[k]
        if k == 10:
            to_change = gt[0]
        else:
            to_change = gt[k+1]
        changed = exchange_or_not(original, to_change)
        gt[k] = changed
        global_temps = ' '.join(gt)
        
    ss.commit()

    # for r in ss.query(Variables).all():
    #     print r.ref_t, r.gen_temp
