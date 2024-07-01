import numpy as np
import random
import math


class Exp4():
    def __init__(self, gamma, num_actions, num_experts):
        self.gamma = gamma
        self.num_actions = num_actions
        self.num_experts = num_experts
        self.weights = np.ones(num_experts)
        self.expert_advice = np.zeros((num_experts, num_actions))
        self.name = "EXP4"

    def initialize(self, actionNum):
        pass

    def act(self, env, actionmappedIndex):
        pass

    def update(self, action, reward):
        pass
