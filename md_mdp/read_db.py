import sqlite3

conn = sqlite3.connect('./md_mdp.db')

c = conn.cursor()

c.execute('PRAGMA table_info')
# c.execute('select * from replicas, other_variables')
# for row in c:
#     print row
