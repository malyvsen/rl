import numpy as np


class RandomDiscrete:
    def __init__(self, num_possible_actions):
        self.num_possible_actions = num_possible_actions


    def act(self, episode):
        return np.random.randint(self.num_possible_actions)


    def train(self, steps):
        pass
