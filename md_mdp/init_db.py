import sqlalchemy as sqlmy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

engine = sqlmy.create_engine('sqlite:////tmp/md_mdp.db', echo=True)

print dir(sqlmy)
Base = declarative_base()

class 
