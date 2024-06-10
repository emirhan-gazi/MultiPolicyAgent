from TemplateAgent import TemplateAgent
from agents.BaseLearningAgent import BaseLearningAgent
import gym

class BaseLearningAgentGym(gym.Env):
    """A base agent to write custom scripted agents.

    It can also act as a passive agent that does nothing.
    """

    def __init__(self, team=0):
        super().__init__()
        self.reward = 0
        self.episodes = 0
        self.steps = 0
        self.observation_space = None
        self.action_space = None

    def setup(self, obs_spec, action_spec):
        self.observation_space = obs_spec
        self.action_space = action_spec

    def reset(self):
        self.episodes += 1
        self.steps = 0

    def step(self, obs):
        self.steps += 1
        self.reward += obs.reward
        return (1, [0,0])

    def render(self,):
        return None

    def close(self,):
        return None