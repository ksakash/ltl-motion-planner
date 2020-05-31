import re
import sys
import copy
import random as rnd
import itertools as itr
import networkx as nx
from shapely.geometry import Polygon, LineString, Point
from gltl2ba import Ltl2baParser, parse_args, get_ltl_formula, run_ltl2ba

# DTS
class Ts (object):
    def __init__(self, x_0: 'Point' = None):
        self.X = [] # set of states
        self.x_0 = x_0 # initial states
        self.delta = dict() # set of transitions
        self.g = nx.DiGraph()

    # add a transition to system
    def update_transition(self, ts: list):
        for t in ts:
            if t[0] in self.delta:
                self.delta[t[0]].append(t[1])
            else:
                s = []
                s.append (t[1])
                self.delta[t[0]] = s

            if t[1] in self.delta:
                self.delta[t[1]].append(t[0])
            else:
                s = []
                s.append (t[0])
                self.delta[t[1]] = s

    # to update the observation function corresponding to that state
    def updateDTS(self, states: list, transitions: list):
        self.update_state (states)
        self.update_transition (transitions)

    # gives the observation corresponding to that state
    def update_state(self, states: list):
        for state in states:
            self.X.append (state)

    def h (self, x: 'Point'):
        pass

# buchi automata
class BuchiAutomata (object):
    def __init__(self):
        self.ba = dict()
        self.final_states = []
        self.states = []

    def get_automata(self):
        args = parse_args()
        ltl = get_ltl_formula(args.file, args.formula)
        (output, _, exit_code) = run_ltl2ba(args, ltl)

        if exit_code != 1:
            print(output)

            if (args.graph or args.output_graph is not None
                or args.dot or args.output_dot is not None):

                prog = re.compile("^[\s\S\w\W]*?"
                                  "(never\s+{[\s\S\w\W]+?})"
                                  "[\s\S\w\W]+$")
                match = prog.search(output)
                assert match, output

                _, self.ba, self.final_states = Ltl2baParser.parse(match.group(1))
                self.states = list(self.ba.keys())
                for state in self.states:
                    if state not in self.states:
                        self.states.append (state)
        else:
            print ("error")

# product automata
class ProductAutomata (object):
    def __init__(self, T, B):
        self.S = []
        self.final_states = []
        self.delta = dict()
        self.T = T
        self.B = B

    def beta (self, x) -> list:
        li = []
        for s in self.B:
            li.append ((x, s))
        return li

    def update_transition (self, ts):
        for t in ts:
            if t[0] in self.delta:
                self.delta[t[0]].append(t[1])
            else:
                s = []
                s.append (t[1])
                self.delta[t[0]] = s

    def update_state (self, Ss):
        for p in Ss:
            self.S.append (p)
            (_, s) = p
            if s in self.B.final_states and p not in self.final_states:
                self.final_states.append (p)

    def updatePA (self, S_P, Del_P):
        self.update_state (S_P)
        self.update_transition (Del_P)

# sample a state from the region
def sample(center: 'Point', length: float, breadth: float) -> 'Point':
    start = Point (center.x - (length)/2, center.y - (breadth)/2)
    point = Point (start.x + rnd.random()*length, start.y + rnd.random()*breadth)
    return point

# contains the set of points far from the sampled state
def far (x: 'Point', eta1: float, eta2: float, T: 'DTS') -> 'Point':
    X = T.X
    li = []

    for x_ in X:
        d = (x.x - x_.x)**2 + (x.y - x_.y)**2
        if d >= eta1 and d <= eta2:
            li.append (x_)

    return li

def near (x: 'Point', eta2: float, T: 'DTS') -> 'Point':
    X = T.X
    li = []

    for x_ in X:
        d = (x.x - x_.x)**2 + (x.y - x_.y)**2
        if d <= eta2:
            li.append (x_)

    return li

# to sample a state close to the final state
def steer (x: 'Point', x_r: 'Point') -> 'Point':
    len_x = x_r.x - x.x
    len_y = x_r.y - x.y

    gamma = rnd.random()
    p1 = Point (x.x + gamma*len_x, x.y + gamma*len_y)
    return p1

# to check if the transition is betwn free space
def is_simple_segment (x1: 'Point', x2: 'Point', obstacles: list) -> bool:
    line = LineString ([x1, x2])

    for obstacle in obstacles:
        if line.intersection(obstacle.poly).is_empty is False:
            return False

    return True

# to update the product automaton
def update_pa (P: 'ProductAutomata', T: 'Ts', B: 'BuchiAutomata', props: list, t) -> bool:
    (x, x_) = t
    beta_P = P.beta (x)
    S_P_ = []
    Del_P_ = []
    for s in beta_P:
        O_x = T.h(x)
        for o in O_x:
            if s in B.ba and o in B.ba[s]:
                for s_ in B.ba[s][o]:
                    S_P_.append ((x_, s_))
                    Del_P_.append (((x, s), (x_, s_)))

    if len(S_P_) is not 0:
        P.updatePA (S_P_, Del_P_)
        stack = copy.deepcopy (S_P_)
        while len(stack) is not 0:
            p1 = stack.pop()
            (x1, s1) = p1
            O_x = T.h(x1)
            list_x2 = T.delta[x1]
            for x2 in list_x2:
                for o in O_x:
                    if s1 in B.ba and o in B.ba[s]:
                        for s2 in B.ba[s][o]:
                            p2 = (x2, s2)
                            if p2 not in P.S:
                                P.updatePA (p2, (p1, p2))
                                Del_P_.append ((p1, p2))
                                stack.append (p2)
                            elif (p1, p2) not in P.delta:
                                P.update_transition ((p1, p2))
                                Del_P_.append ((p1, p2))
        return True
    return False

# update the connected components in product
# automaton on adding a transition
def update_scc ():
    pass

T = Ts()
B = BuchiAutomata()
P = ProductAutomata (T, B)
n1 = 0.5
n2 = 1.0
center = Point (0, 0)
length = 6
breadth = 6

class Region (object):
    def __init__ (self, poly, name, color):
        self.poly = poly
        self.name = name
        self.color = color

# obstacles
o1 = Region (Polygon ([(0, 0), (1, 0), (1, 1), (0, 1)]), 'o1', 'gray')
O = [o1]

# set of regions
r1 = Region (Polygon ([(-2, -2), (0, -2), (0, -1), (-1, 0), (-2, 0)]), 'r1', 'green')
r2 = Region (Polygon ([(2, -1), (3, -1), (3, 1), (2, 1)]), 'r2', 'magenta')

R = [r1, r2]

regions = [o1, r1, r2]

def foundPolicy () -> 'bool':
    pass

def getObservations (point: 'Point', regions: list) -> list:
    obs = []
    for region in regions:
        poly = region.poly
        if point.within (poly):
            obs.append ((region.name, region.color))
    return obs

# TODO: put a condition for stopping the loop
while not foundPolicy():
    X_ = []
    Del_ = []
    DelP_ = []
    x_r = sample (center, length, breadth) # think about splitting the wspace into grids

    props = getObservations (x_r, regions)

    for x in far (x_r, n1, n2, T):
        x_r_ = steer (x, x_r)
        if is_simple_segment (x, x_r_, O):
            added = update_pa (P, T, B, props, (x, x_r_))
            if added is True:
                X_.append (x_r_)
                Del_.append ((x, x_r_))

    T.updateDTS (X_, Del_)
    Del_ = []
    DelP_ = []

    for x_r_ in X_:
        for x in near (x_r_, n2, T):
            x = steer (x_r_, x)
            if (x) and is_simple_segment (x_r_, x, O):
                added = update_pa (P, T, B, (x, x_r_))
                if added is True:
                    Del_.append ((x_r_, x))

    T.updateDTS (X_, Del_)

