import random
import math
import numpy as np


def key_selector(keys, weights, mapping_devices):
    '''
    This function is used to select the action based on the probability distribution
    keys: actions
    weights: probability distribution
    mapping_devices: the devices that have been mapped
    
    '''
    done = False
    while (~done):
        choice = draw(weights)
        if (~(np.logical_and(np.logical_not(mapping_devices), keys[choice]).any())):
            done = True
            return choice


def distr(weights, gamma=0.0):
    '''
    This function is used to calculate the probability distribution
    weights: the weights of each action
    gamma: the parameter of the probability distribution
    '''
    weight_sum = float(sum(weights))
    return tuple((1.0 - gamma) * (w / weight_sum) + (gamma / len(weights)) for w in weights)


def draw(probs):
    '''
    This function is used to draw a random number based on the probability distribution
    probs: the probability distribution
    '''
    choice = random.uniform(0, sum(probs))
    choiceIndex = 0
    for weight in probs:
        choice -= weight
        if choice <= 0:
            return choiceIndex

        choiceIndex += 1


def update_weights(weights, gamma, probability_distribution, choice, reward):
    '''
    This function is used to update the weights of each action
    weights: the weights of each action
    gamma: the parameter of the probability distribution
    probability_distribution: the probability distribution  
    choice: the action that has been selected
    reward: the reward of the selected action
    '''
    # iter through actions. up to n updates / rec
    estimated_reward = 1.0 * reward / probability_distribution[choice]
    weights[choice] *= math.exp(estimated_reward *
                                gamma / len(weights))  # important
    return weights


class EXP3():
    def __init__(self, gamma, weights):
        '''
        gamma: the parameter of the probability distribution
        weights: the weights of each action
        '''
        self.gamma = gamma
        self.weights = weights
        self.name = "EXP3"
        return

    def initialize(self, actionNum):
        '''
        actionNum: the number of actions
        '''
        self.firstStep = True
        self.weights = np.ones(actionNum)
        return

    def act(self, actionSpace, actionmappedIndex):
        '''
        This function is used to select the action
        actionSpace: action Space
        actionmappedIndex: [0,0,0,1,1,0] 0 means we can select the action, 1 means we can't select the action because it is still under processing
        '''
        if (not self.firstStep):
            self.probabilityDistribution = distr(self.weights, self.gamma)
            choice = key_selector(
                actionSpace, self.probabilityDistribution, actionmappedIndex)
        else:
            self.firstStep = False
            self.probabilityDistribution = distr(self.weights, self.gamma)
            choice = draw(self.probabilityDistribution)

        return choice,None

    def update(self, action, reward):
        '''
        action: the action that has been selected
        reward: the reward of the selected action
        '''
        scalereward = ((reward-5)/10+0.5)**3
        
        # scalereward = reward
        # reward = reward/700
        self.weights = update_weights(
            self.weights, self.gamma, self.probabilityDistribution, action, scalereward)