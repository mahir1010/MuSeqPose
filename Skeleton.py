from math import sqrt

import numpy as np


class Part(np.ndarray):
    def __new__(cls, arr, name, likelihood):
        if len(arr)==2:
            arr=np.append(arr,.0)
        obj = np.asarray(arr).view(cls)
        obj.name = name
        obj.likelihood = likelihood
        return obj

    def distance(self, obj):
        return sqrt(np.sum(np.square(np.subtract(obj, self))))

    def magnitude(self):
        return sqrt(np.sum(np.square(self)))

    def __lt__(self, other:float):
        return self.likelihood < other

    def __gt__(self, other:float):
        return self.likelihood > other

    def __ge__(self, other:float):
        return self.likelihood >= other

    def __le__(self, other:float):
        return self.likelihood <= other


class Skeleton:
    def __init__(self, body_parts: list, part_map: dict = None, likelihood_map: dict = None, behaviour=''):
        self.body_parts = body_parts
        self.body_parts_map = {}
        candidates = body_parts.copy()
        self.behaviour=behaviour
        for name in part_map.keys():
            candidates.remove(name)
            self.body_parts_map[name] = Part(part_map[name], name, likelihood_map[name])
        for name in candidates:
            self.body_parts_map[name] = Part([.0, .0, .0], name, .0)

    def __getitem__(self, item):
        return self.body_parts_map[item] if item in self.body_parts_map.keys() else None

    def __setitem__(self, name, val):
        self.body_parts_map[name] = val

    def __str__(self):
        ret = ""
        for p in self.body_parts_map:
            ret += f"{p:10}: {str(self[p])} ({np.round(p.likelihood,2)})\n"
        return ret

    def __rsub__(self, other):
        val = {}
        prob = {}
        for name in self.body_parts_map:
            val[name] = (other[name] - self[name]) if type(other) == Skeleton else other - self[name]
            if type(other) == Skeleton:
                prob[name] = min(self[name].likelihood, other[name].likelihood)
        return Skeleton(list(self.body_parts_map.keys()), None, val, prob)

    def __sub__(self, other):
        val = {}
        prob = {}
        for name in self.body_parts_map:
            val[name] = (self[name] - other[name]) if type(other) == Skeleton else self[name] - other
            if type(other) == Skeleton:
                prob[name] = min(self[name].likelihood, other[name].likelihood)
        return Skeleton(list(self.body_parts_map.keys()), None, val, prob)

    def __radd__(self, other):
        val = {}
        prob = {}
        for name in self.body_parts_map:
            val[name] = (self[name] + other[name]) if type(other) == Skeleton else self[name] + other
            if type(other) == Skeleton:
                prob[name] = min(self[name].likelihood, other[name].likelihood)
        return Skeleton(list(self.body_parts_map.keys()), None, val, prob)

    def __add__(self, other):
        val = {}
        prob = {}
        for name in self.body_parts_map:
            val[name] = (self[name] + other[name]) if type(other) == Skeleton else self[name] + other
            if type(other) == Skeleton:
                prob[name] = min(self[name].likelihood, other[name].likelihood)
        return Skeleton(list(self.body_parts_map.keys()), None, val, prob)

    def __mul__(self, other):
        val = {}
        prob = {}
        for name in self.body_parts_map:
            val[name] = (self[name] * other[name]) if type(other) == Skeleton else self[name] * other
            if type(other) == Skeleton:
                prob[name] = min(self[name].likelihood, other[name].likelihood)
        return Skeleton(list(self.body_parts_map.keys()), None, val, prob)

    def __rmul__(self, other):
        val = {}
        prob = {}
        for name in self.body_parts_map:
            val[name] = (self[name] * other[name]) if type(other) == Skeleton else self[name] * other
            if type(other) == Skeleton:
                prob[name] = min(self[name].likelihood, other[name].likelihood)
        return Skeleton(list(self.body_parts_map.keys()), None, val, prob)
