import math
import numpy as np
import random


def indexMax(x):
    m = max(x)
    return x.index(m)


def key_selector(keys, weights, mapping_devices):
    weights_copy = weights
    done = False
    while (~done):
        # get the max value index
        choice = indexMax(weights_copy)
        choice_action = keys[choice]

        if (weights_copy[choice] != -1):
            if (np.logical_and(np.logical_not(mapping_devices), choice_action).any()):
                weights_copy[choice] = -1
            else:
                return choice, 2
        else:
            choice = random.choice(range(len(keys)))
            if (np.logical_and(np.logical_not(mapping_devices), choice_action).any()):
                return choice, 3

class UCB1():
    def __init__(self, actioncounts, actionvalues):
        self.actioncounts = actioncounts
        self.actionvalues = actionvalues
        self.name = "UCB1"
        return

    def __str__(self) -> str:
        return 'UCB1'

    def initialize(self, actionNum):
        '''
        actionNum: the number of actions
        actioncounts: the number of each action has been selected        
        '''
        self.actionNum = actionNum
        self.actioncounts = [0 for _ in range(actionNum)]
        self.actionvalues = [0.0 for _ in range(actionNum)]
        return

    def __exploration(self, n, action):
        '''
        n: is the total number of times all actions have been selected
        r: is the number of times the action has been selected
        return the exploration value
        '''
        bonus = 2 * math.sqrt((math.log(n)) /
                              float(self.actioncounts[action]))
        return bonus

    def act(self, actionSpace, actionmappedIndex):
        '''
        This function is used to select the action
        env: the environment
        actionmappedIndex: [0,0,0,1,1,0] 0 means we can select the action, 1 means we can't select the action because it is still under processing
        '''
        for action in range(self.actionNum):
            if self.actioncounts[action] == 0:
                return action, 1

        ucb_values = [0.0 for action in range(self.actionNum)]
        total_counts = sum(self.actioncounts)
        for action in range(self.actionNum):
            exploitation = self.actionvalues[action]
            exploration = self.__exploration(total_counts, action)
            ucb_values[action] = exploitation + exploration
        # return indexMax(ucb_values)
        return key_selector(actionSpace, ucb_values, actionmappedIndex)

    def update(self, action, reward):
        '''
        This function is used to update the actioncounts and actionvalues
        action: the action
        reward: the reward of the action
        '''
        self.actioncounts[action] = self.actioncounts[action] + 1
        n = self.actioncounts[action]
        value = self.actionvalues[action]
        new_value = ((n - 1) / float(n)) * value + (1 / float(n)) * reward
        self.actionvalues[action] = new_value
