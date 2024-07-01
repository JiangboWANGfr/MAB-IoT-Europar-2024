import math
import random
import numpy as np


def indexMax(x):
    '''
    return the index of the max value in the list
    '''
    m = max(x)
    return x.index(m)


def key_selector(keys, weights, mapping_devices):
    '''
    select the key from the keys list according to the weights and mapping_devices
    the keys is the action list
    the weights is the ucb_values 
    the mapping_devices is the devices that have been mapped which is not allowed to be selected
    '''
    weights_copy = weights
    done = False
    while (~done):
        # get the max value index
        choice = indexMax(weights_copy)
        choice_action = keys[choice]
        # if the weight is not -1, which means the action is not selected
        if (weights_copy[choice] != -1):
            # if the action is not allowed to be selected, set the weight to -1
            if (np.logical_and(np.logical_not(mapping_devices), choice_action).any()):
                weights_copy[choice] = -1
            else:
                # print("np.logical_and(np.logical_not(mapping_devices), choice_action).any():{}".format(
                #     np.logical_and(np.logical_not(mapping_devices), choice_action).any()))
                return choice, 2
        else:
            choice = random.choice(keys)
            if (np.logical_and(np.logical_not(mapping_devices), choice_action).any()):
                return choice, 3


class UCB2(object):
    def __init__(self, alpha, actioncounts, actionvalues):
        '''
        alpha: the parameter of UCB2 
        actioncounts: the number of each action has been selected
        actionvalues: the value of each action
        __currentAction: the current action
        __nextUpdate: the next update step
        '''
        self.alpha = alpha
        self.actioncounts = actioncounts
        self.actionvalues = actionvalues
        self.__currentAction = 0
        self.__nextUpdate = 0
        self.name = "UCB2"
        return

    def __str__(self) -> str:
        '''
        return the name of the agent
        '''
        return 'UCB2'

    def initialize(self, actionNum):
        '''
        initialize the actioncounts and actionvalues
        r is the number of times each action has been selected
        '''
        self.actioncounts = [0 for col in range(actionNum)]
        self.actionvalues = [0.0 for col in range(actionNum)]
        self.r = [0 for col in range(actionNum)]
        self.__currentAction = 0
        self.__nextUpdate = 0

    def __exploration(self, n, r):
        '''
        n is the total number of times all actions have been selected
        r is the number of times the action has been selected
        return the exploration value
        '''
        tau = self.__tau(r)
        bonus = math.sqrt((1. + self.alpha) *
                          math.log(math.e * float(n) / tau) / (2 * tau))
        return bonus

    def __tau(self, r):
        '''
        the input is the number of times the action has been selected
        return the tau value
        '''
        return int(math.ceil((1 + self.alpha) ** r))

    def __set_action(self, action):
        """
        When choosing a new action, make sure we play that action for
        tau(r+1) - tau(r) episodes.
        """
        self.__currentAction = action
        self.__nextUpdate += max(1,
                                 self.__tau(self.r[action] + 1) - self.__tau(self.r[action]))
        self.r[action] += 1

    def act(self, actionSpace, actionmappedIndex):
        '''
        This function is used to select the action
        actionSpace: action Space
        actionmappedIndex: [0,0,0,1,1,0] 0 means we can select the action, 1 means we can't select the action because it is still under processing
        '''
        actionNum = len(self.actioncounts)
        # play each action once
        for action in range(actionNum):
            if self.actioncounts[action] == 0:
                self.__set_action(action)
                return action ,0

        # make sure we aren't still playing the previous action.
        if self.__nextUpdate > sum(self.actioncounts):
            return self.__currentAction ,1

        ucb_values = [0.0 for action in range(actionNum)]
        total_counts = sum(self.actioncounts)
        # calculate the ucb_values for each action
        for action in range(actionNum):
            exploitation = self.actionvalues[action]
            exploration = self.__exploration(total_counts, self.r[action])
            ucb_values[action] = exploitation + exploration

        chosen_action = indexMax(ucb_values)
        self.__set_action(chosen_action)
        # return chosen_action
        return key_selector(actionSpace, ucb_values, actionmappedIndex)

    def update(self, action, reward):
        '''
        This function is to update the actioncounts and actionvalues
        action: the action index 
        reward: the reward of the action
        '''
        # reward = ((reward-21)/700+0.5)**3
        self.actioncounts[action] = self.actioncounts[action] + 1
        n = self.actioncounts[action]

        value = self.actionvalues[action]
        new_value = ((n - 1) / float(n)) * value + (1 / float(n)) * reward
        self.actionvalues[action] = new_value
