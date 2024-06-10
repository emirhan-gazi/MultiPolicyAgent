from random import randint,random
import copy
import numpy as np
from utilities import *
import ray
from ray.rllib.agents.ppo import PPOTrainer
from ray.tune import run_experiments, register_env
from agents.GolKenari import GolKenari
from argparse import Namespace



class SelfPlay:
    def __init__(self, team, action_lenght):
        args = Namespace(map="RiskyValley", render=False, gif=False, img=False)

    
        # ray.init()
        config= {"use_critic": True,
             "num_workers": 1,
             "use_gae": True,
             "lambda": 1.0,
             "kl_coeff": 0.2,
             "rollout_fragment_length": 200,
             "train_batch_size": 4000,
             "sgd_minibatch_size": 128,
             "shuffle_sequences": True,
             "num_sgd_iter": 30,
             "lr": 5e-5,
             "lr_schedule": None,
             "vf_loss_coeff": 1.0,
             "framework": "torch",
             "entropy_coeff": 0.0,
             "entropy_coeff_schedule": None,
             "clip_param": 0.3,
             "vf_clip_param": 10.0,
             "grad_clip": None,
             "kl_target": 0.01,
             "batch_mode": "truncate_episodes",
             "observation_filter": "NoFilter"}
        register_env("ray", lambda config: GolKenari(args, agents))
        ppo_agent = PPOTrainer(config=config, env="ray")
        ppo_agent.restore(checkpoint_path="MODELIN BULUNDUGU YER") # Modelin Bulunduğu yeri girmeyi unutmayın!
        self.policy = ppo_agent.get_policy()

    def action(self, raw_state):
        '''
        pos=[3, 17]
        target=[10, 15]
        astar(pos,target,state)
        return
        '''
        state = GolKenari.just_decode_state(raw_state, self.team, self.enemy_team)
        actions, _, _ = self.policy.compute_single_action(state.astype(np.float32))
        location, movement, target, train = GolKenari.just_take_action(actions, raw_state, self.team)
        return (location, movement, target, train)