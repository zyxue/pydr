import sqlite3

def get_md_mdp_parameters(mdpf):                            # without temperatures
    varied_para, const_para = {}, {}
    with open(mdpf, 'r') as inf:
        for line in inf:
            ll = line.strip()
            if ll:
                if ll.startswith(';'):
                    pass
                elif ll.startswith('@'):
                    sl = ll.strip('@').split('=')
                    varied_para[sl[0].strip()] = sl[1].strip().split(',')
                else:
                    sl = ll.split('=')
                    const_para[sl[0].strip()] = sl[1].strip()
    return varied_para, const_para

def create_cmd_for_init_db(db, varied_para, const_para, table_name='md_mdp_para'):
    vkeys = varied_para.keys()
    vqm = ','.join(['?'] * len(vkeys))                      # varied_question_marks
    vkeys_cmd_format = 'CREATE TABLE {0} ({1})'.format(table_name, vqm)
    vkeys_cmd = (vkeys_cmd_format, vkeys)

    vvalues = zip(*[varied_para[k] for k in vkeys])         # a list of tuples/rows
    vvalues_cmd_format = 'INSERT INTO {0} VALUES {1}'.format(table_name, vqm)
    vvalues_cmd = (vvalues_cmd_format, vvalues)

    from pprint import pprint as pp
    pp(vkeys_cmd)
    pp(vvalues_cmd)

    import sys
    sys.exit
    mkeys = sorted(const_para.keys())
    headers = ','.join((['"{k}" text'.format(k=k) for k in vkeys] +
                        ['"{k}" text'.format(k=k) for k in mkeys]))

    # NEED CODE TO CHECK IF LALA HAS ALREADY EXISTED OR NOT
    # c.execute(cmd)                                          # create table

    vvalues = [varied_para[k] for k in vkeys]
    mvalues = [const_para[k] for k in mkeys]
    values = ','.join(['"{v}"'.format(v=v) for v in vvalues] +
                      ['"{v}"'.format(v=v) for v in mvalues])
    # for t in 
    #     cmd = 'INSERT INTO "{table_name}" values({t}'.format(
    #             table_name=table_name, t=t)
    #     print cmd
    #     # c.execute(cmd)
    
    # db.commit()
    # c.close()

def init_db(db_name, varied_para, const_para, table_name='const_para'):
    db = sqlite3.connect(db_name)
    with closing(db) as db:
        db.execute(cmd)
        db.commit()

if __name__ == "__main__":
    from pprint import pprint as pp

    varied_para, const_para = get_md_mdp_parameters('md.mdp')
    # pp(varied_para)
    # pp(const_para)

    create_cmd_for_init_db('db', varied_para, const_para)
