def calc_DRPE(state, ts, uniform_spacing, c1=0.005, c2=0.005):
    """
    state: a list of temperatures for all the present replicas
    ts: a list of preset temperatures
    unform_spacing: as the name indicates
    """

    lambda_ = dict(zip(ts, uniform_spacing))

    sstate = sorted(state)                        # sorted state
    us_sstate = [lambda_[a] for a in sstate]      # uniform spacing of sorted state
    w = len(ts) / float(len(us_sstate))

    ll = range(len(us_sstate) + 1)
    ll.remove(0)

    ep = 0                                                # energetic penalty
    for k1, i1 in zip(us_sstate, ll):
        for k2, i2 in zip(us_sstate, ll):
            ep += ((k1 - k2) - w * (i1 - i2)) ** 2
    ep *= c1

    dp = c2 * (sum(us_sstate) - w * sum(ll)) ** 2 # drift penalty

    return ep + dp

if __name__ == "__main__":
    ts = [280, 288, 296, 305, 314]                           # list of temperatures
    uniform_spacing = [1, 2, 3, 4, 5]                        # lambda_unit
    
    A = [305, 296, 288, 280, 288]
    B = [296, 296, 288, 280, 288]
    print calc_DRPE(A, ts, uniform_spacing, c1=0.02, c2=0.05)
    print calc_DRPE(B, ts, uniform_spacing, c1=0.02, c2=0.05)
