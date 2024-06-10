from TemplateAgent import TemplateAgent

class BaseLearningAgent(TemplateAgent):
    """A base agent to write custom scripted agents.

    It can also act as a passive agent that does nothing.
    """

    def __init__(self, team, action_lenght ):
        super().__init__(action_lenght=6, team=1) 
        
        self.reward = 0
        self.episodes = 0
        self.steps = 0
        self.obs_space = None
        self.action_space = None

    def setup(self, obs_spec, action_spec):
        self.obs_space = obs_spec
        self.action_space = action_spec

    def reset(self):
        self.episodes += 1
        self.steps = 0

    def action(self, obs):
        self.steps += 1
        self.reward += obs.reward
        return (1, [0,0]) # This Should have been "do nothing" but it is not.

