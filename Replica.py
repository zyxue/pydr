class Replica(object):
    def __init__(self, potential_energy, current_temp):
        self.potential_energy = potential_energy
        self.current_temp = current_temp

    def to_change(self):
        # find a way to calc to_change based on current_temp
        pass

