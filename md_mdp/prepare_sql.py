import sqlite3

def get_md_mdp_parameters(mdpf):                            # without temperatures
    variables, md_mdp_para = {}, {}
    with open(mdpf, 'r') as inf:
        for line in inf:
            ll = line.strip()
            if ll:
                if ll.startswith(';'):
                    pass
                elif ll.startswith('@'):
                    sl = ll.strip('@').split('=')
                    variables[sl[0].strip()] = sl[1].strip().split(',')
                else:
                    sl = ll.split('=')
                    md_mdp_para[sl[0].strip()] = sl[1].strip()
    return variables, md_mdp_para

def create_table_cmd(db, table_name, variables, md_mdp_para):
    c = db.cursor()

    vkeys = sorted(variables.keys())
    mkeys = sorted(md_mdp_para.keys())
    headers = ','.join((['"{k}" text'.format(k=k) for k in vkeys] +
                        ['"{k}" text'.format(k=k) for k in mkeys]))
    cmd = 'CREATE TABLE {table_name} ({headers})'.format(
        table_name=table_name, headers=headers)

    # NEED CODE TO CHECK IF LALA HAS ALREADY EXISTED OR NOT
    c.execute(cmd)                                          # create table

    vvalues = [variables[k] for k in vkeys]
    mvalues = [md_mdp_para[k] for k in mkeys]
    values = ','.join(['"{v}"'.format(v=v) for v in vvalues] +
                      ['"{v}"'.format(v=v) for v in mvalues])
    from pprint import pprint as pp
    pp(values)
    # for t in 
    #     cmd = 'INSERT INTO "{table_name}" values({t}'.format(
    #             table_name=table_name, t=t)
    #     print cmd
    #     # c.execute(cmd)
    
    # db.commit()
    # c.close()

if __name__ == "__main__":
    from pprint import pprint as pp

    variables, md_mdp_para = get_md_mdp_parameters('md.mdp')
    db = sqlite3.connect('./example.db')

    create_table_cmd(db, 'lala', variables, md_mdp_para)
