from importlib.metadata import requires
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Bernoulli, Categorical, Multinomial, MultivariateNormal, Normal

from torch.autograd import Variable
from itertools import count
import matplotlib.pyplot as plt
import numpy as np
import gym
import pdb
from torch.autograd import Variable
from numpy.random.mtrand import RandomState

import math
torch.autograd.set_detect_anomaly(True)

class PolicyNet(nn.Module):
    # policy gradient network
    def __init__(self, K, N):
        super(PolicyNet, self).__init__()
        
        self.fc1 = nn.Linear(N, 32)
        self.fc2 = nn.Linear(32, 16)
        self.fc3 = nn.Linear(16, K) 

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.softmax(self.fc3(x))
        return x

def select_action(policy, state, K):
    state = torch.from_numpy(np.float32(state)).unsqueeze(0)
    state = Variable(state)
    x = policy(state)
    m = Normal(torch.tensor(x), torch.ones(K))
    probs = m.sample()
    #print(probs)
    return ((torch.exp(m.log_prob(probs))).detach().numpy()[0]/(torch.exp(m.log_prob(probs)).detach().numpy()[0]).sum(),m.log_prob(probs).requires_grad_())


def finish_episode(agent):
    R = (agent.reward)

    #print("agent : "+str(agent.prev_action))
    policy_loss =  -(agent.saved_probs*R)# -torch.sum(torch.log(agent.saved_probs)) *R #-agent.saved_probs*R #
    agent.optimizer.zero_grad()
    policy_loss.backward(torch.Tensor(4).unsqueeze(dim=0))#torch.Tensor([4])
    agent.optimizer.step()

def plot_durations(episode_durations):
    plt.figure(2)
    plt.clf()
    durations_t = torch.FloatTensor(episode_durations)
    plt.title('Training...')
    plt.xlabel('Episode')
    plt.ylabel('Duration')
    plt.plot(durations_t.numpy())
    # Take 100 episode averages and plot them too
    if len(durations_t) >= 100:
        means = durations_t.unfold(0, 100, 1).mean(1).view(-1)
        means = torch.cat((torch.zeros(99), means))
        plt.plot(means.numpy())

    plt.pause(0.001)  # pause a bit so that plots are updated

class PGAgent(object):
    # def __init__(self, action_space, seed, c, max_impressions):
    def __init__(self, env, seed,gamma=0.1,splitting_allowed= 4):
        self.name = "PG Agent"
        self.env = env
        self.values = {}
        self.np_random = RandomState(seed)
        self.prev_action = []
        self.gamma = gamma
        self.weights = [] #action_pool
        self.history = [] #state_pool
        step = 0
        self.numActions = len(env.actions)
        self.rewardVector = [] # reward_pool
        self.saved_probs = []
        self.keys = env.actions
        self.episode_durations = []

        self.num_episode = 5000
        self.batch_size = 1
        self.learning_rate = 0.011
        self.K = env.num_allocated_devices
        self.N = env.num_devices
        self.state = np.ones(self.K) # all devices are used
        self.policy = PolicyNet(self.K,self.N)
        self.optimizer = torch.optim.Adam(self.policy.parameters(),lr=self.learning_rate)
        print(self.policy)

    def act(self, observation, reward,mapping,step,done):
        if (step > 0):
            self.reward = reward
            self.rewardVector.append(reward)
            finish_episode(self)
            prev_prev_action = self.prev_action

        tmp_action, self.saved_probs = select_action(self.policy, np.asarray(mapping),self.K)
        self.prev_action = []
        i=0
        for el in mapping:
            if (el):
                self.prev_action.append(tmp_action[i])
                i += 1
            else : 
                self.prev_action.append(0)
        self.prev_action = np.asarray(self.prev_action)
        if (torch.isnan(self.saved_probs).any()):
            self.prev_action = prev_prev_action 
        self.best_action = self.prev_action
        step +=1
        return self.prev_action # Returns a tuple!

    
