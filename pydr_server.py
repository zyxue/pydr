import pickle
import time
import copy

from flask import Flask, request, session, g

app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prep = request.form['prep']                 # rep: unicode
        rep = pickle.loads(str(prep))
        potential_energy = rep.potential_energy
        original = rep.current_temp
        to_change = rep.to_change
        # to_change TBD
        changed = exchange_or_not()
        # involve DRPE calculation etc.
        # Update global_temps
        Date = time.ctime()
        # Write to db
        # Generate New replica
        nrep = copy.copy(rep)
        nrep.potential_energy = None
        nrep.current_temp = changed
        pnrep = pickle.dumps(nrep)
        return pnrep

    elif request.method == "GET":
        return "hello"

@app.route('/ref_t', methods=['POST'])
def ref_t():
    if request.methods == 'POST':
        pass

if __name__ == "__main__":
    app.run()
