import sys
import random as rnd
import itertools as itr

# configuration space of the robot
D = []

# set of regions
R = []

# DTS
class DTS (object):
    def __init__(self):
        self.X = [] # set of states
        self.x_0 = None # initial states
        self.delta = [] # set of transitions
        self.pi = [] # set of observations
    
    # add a transition to system
    def update_transition(self, transition):
        self.delta.append(transition)

    # gives the observation corresponding to that state
    def observation(self, x):
        pass

# buchi automata
class BuchiAutomata (object):
    def __init__(self):
        pass

    def get_automata(self):
        pass

# sample a state from the region
def sample():
    pass

# contains the set of points far from the sampled state
def far(x, eta1, eta2):
    pass

# to sample a state close to the final state
def steer(x, x_r):
    pass

# to check if the transition is betwn free space
def is_simple_segment(x1, x2):
    pass

# to update the product automaton
def update_pa():
    pass

# add state to the set of states
def add_state():
    pass


