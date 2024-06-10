from agents.BaseLearningGym import BaseLearningAgentGym
from game import Game
import yaml
import numpy as np
import gym
from gym import spaces
from utilities import  ally_locs, multi_reward_shape
import ray
from ray.rllib.agents.ppo import PPOTrainer
from ray.tune import run_experiments, register_env
from argparse import Namespace

class PlayerAgent(BaseLearningAgentGym):
    tagToString = {
            1: "Truck",
            2: "LightTank",
            3: "HeavyTank",
            4: "Drone",
        }
    config = {"use_critic": True,
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
    def read_hypers(self, map):
        self.map = map
        with open(f"data/config/{map}.yaml", "r") as f:   
            hyperparams_dict = yaml.safe_load(f)
            return hyperparams_dict

    def __init__(self, args, agents):
        super().__init__()
        configs = self.read_hypers(args.map)
        self.game = Game(args, agents)
        self.team = 0
        self.enemy_team = 1
        self.reward = 0
        self.episodes = 0
        self.steps = 0
        self.nec_obs = None
        self.height = configs['map']['y']
        self.width = configs['map']['x']
        self.reward = 0
        self.episodes = 0
        self.steps = 0
        self.observation_space = spaces.Box(
            low=-2,
            high=401,
            shape=(self.height*self.width*10+4,),
            dtype=np.int16
        )
        self.action_space = self.action_space = spaces.MultiDiscrete([7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5])
        self.previous_enemy_count = len(configs['red']['units'])
        self.previous_ally_count = len(configs['blue']['units'])
        self.previous_enemy_count_reset = self.previous_enemy_count
        self.previous_ally_count_reset = self.previous_ally_count
        self.temp_agents  = [None,"RandomAgent"]

        truck_model_path = "data/models/truck_model"
        light_tank_model_path = "data/models/light_tank_model"
        heavy_tank_model_path = "data/models/heavy_tank_model"
        drone_model_path = "data/models/drone_model"

        args_for_models = Namespace(map=self.map, render=False, gif=False, img=False)
        self.initiate_truck(truck_model_path, args_for_models)
        self.initiate_light_tank(light_tank_model_path, args_for_models)
        self.initiate_heavy_tank(heavy_tank_model_path, args_for_models)
        self.initiate_drone(drone_model_path, args_for_models)
    

    def initiate_truck(self, model_path, args):

        register_env("ray", lambda config: TruckAgent(args, self.temp_agents))
        ppo_agent = PPOTrainer(config=PlayerAgent.config, env="ray")
        ppo_agent.restore(checkpoint_path=model_path)
        self.truck_policy = ppo_agent.get_policy()

    def initiate_light_tank(self, model_path, args):
        register_env("ray", lambda config: LightTankAgent(args, self.temp_agents))
        ppo_agent = PPOTrainer(config=PlayerAgent.config, env="ray")
        ppo_agent.restore(checkpoint_path=model_path)
        self.light_tank_policy = ppo_agent.get_policy()
    
    def initiate_heavy_tank(self, model_path, args):
        register_env("ray", lambda config: HeavyTankAgent(args, self.temp_agents))
        ppo_agent = PPOTrainer(config=PlayerAgent.config, env="ray")
        ppo_agent.restore(checkpoint_path=model_path)
        self.heavy_tank_policy = ppo_agent.get_policy()
    
    def initiate_drone(self, model_path, args):
        register_env("ray", lambda config: DroneAgent(args, self.temp_agents))
        ppo_agent = PPOTrainer(config=PlayerAgent.config, env="ray")
        ppo_agent.restore(checkpoint_path=model_path)
        self.drone_policy = ppo_agent.get_policy()
    


    def setup(self, obs_spec, action_spec):
        self.observation_space = obs_spec
        self.action_space = action_spec
    def reset(self):
        self.previous_enemy_count = self.previous_enemy_count_reset
        self.previous_ally_count = self.previous_ally_count_reset
        self.episodes += 1
        self.steps = 0
        state = self.game.reset()
        self.nec_obs = state
        return self.decode_state(state)
    
    @staticmethod
    def _decode_state(obs, team, enemy_team):
        turn = obs['turn'] # 1
        max_turn = obs['max_turn'] # 1
        units = obs['units'] # 2x7x15
        hps = obs['hps'] # 2x7x15
        bases = obs['bases'] # 2x7x15
        score = obs['score'] # 2
        res = obs['resources'] # 7x15
        load = obs['loads'] # 2x7x15
        terrain = obs["terrain"] # 7x15 
        y_max, x_max = res.shape
        my_units = []
        enemy_units = []
        resources = []
        for i in range(y_max):
            for j in range(x_max):
                if units[team][i][j]<6 and units[team][i][j] != 0:
                    my_units.append(
                    {   
                        'unit': units[team][i][j],
                        'tag': PlayerAgent.tagToString[units[team][i][j]],
                        'hp': hps[team][i][j],
                        'location': (i,j),
                        'load': load[team][i][j]
                    }
                    )
                if units[enemy_team][i][j]<6 and units[enemy_team][i][j] != 0:
                    enemy_units.append(
                    {   
                        'unit': units[enemy_team][i][j],
                        'tag': PlayerAgent.tagToString[units[enemy_team][i][j]],
                        'hp': hps[enemy_team][i][j],
                        'location': (i,j),
                        'load': load[enemy_team][i][j]
                    }
                    )
                if res[i][j]==1:
                    resources.append((i,j))
                if bases[team][i][j]:
                    my_base = (i,j)
                if bases[enemy_team][i][j]:
                    enemy_base = (i,j)
        
        # print(my_units)
        unitss = [*units[0].reshape(-1).tolist(), *units[1].reshape(-1).tolist()]
        hpss = [*hps[0].reshape(-1).tolist(), *hps[1].reshape(-1).tolist()]
        basess = [*bases[0].reshape(-1).tolist(), *bases[1].reshape(-1).tolist()]
        ress = [*res.reshape(-1).tolist()]
        loads = [*load[0].reshape(-1).tolist(), *load[1].reshape(-1).tolist()]
        terr = [*terrain.reshape(-1).tolist()]
        
        state = (*score.tolist(), turn, max_turn, *unitss, *hpss, *basess, *ress, *loads, *terr)

        return np.array(state, dtype=np.int16), (x_max, y_max, my_units, enemy_units, resources, my_base, enemy_base)

    @staticmethod
    def just_decode_state(obs, team, enemy_team):
        state, _ = PlayerAgent._decode_state(obs, team, enemy_team)
        return state

    def decode_state(self, obs):
        state, info = self._decode_state(obs, self.team, self.enemy_team)
        self.x_max, self.y_max, self.my_units, self.enemy_units, self.resources, self.my_base, self.enemy_base = info
        return state

    
    def take_action(self, action):
        return self.just_take_action(action, self.nec_obs, self.team) 
    
    def compute_single_action(self,state,raw_state,unit): 
        if unit == 1:
            actions, _, _ = self.truck_policy.compute_single_action(state.astype(np.float32))
            location, movement, target, train = TruckAgent.just_take_action(actions,raw_state , self.team)
            return location, movement, target, train
        elif unit == 2:
            actions, _, _ = self.light_tank_policy.compute_single_action(state.astype(np.float32))
            location, movement, target, train = LightTankAgent.just_take_action(actions,raw_state , self.team)
            return location, movement, target, train

        elif unit == 3:
            actions, _, _ = self.heavy_tank_policy.compute_single_action(state.astype(np.float32))
            location, movement, target, train = HeavyTankAgent.just_take_action(actions,raw_state , self.team)
            return location, movement, target, train
        elif unit == 4:
            actions, _, _ = self.drone_policy.compute_single_action(state.astype(np.float32))
            location, movement, target, train = DroneAgent.just_take_action(actions,raw_state , self.team)
            return location, movement, target, train
    
    def just_take_action(self, action, raw_state, team):
        state, _ = PlayerAgent._decode_state(raw_state, team, 1-team)

        movement = action[0:7]
        movement = movement.tolist()
        target = action[7:14]
        train = action[14]
        allies = ally_locs(raw_state, team)
        
        # truck movement
        truck_location, truck_movement, truck_target, _ =  self.compute_single_action(state, raw_state, 1)
        # light tank movement
        light_tank_location, light_tank_movement, light_tank_target, _ = self.compute_single_action(state, raw_state, 2)
        # heavy tank movement
        heavy_tank_location, heavy_tank_movement, heavy_tank_target, _ = self.compute_single_action(state, raw_state, 3)
        # drone movement
        drone_location, drone_movement, drone_target, _ = self.compute_single_action(state, raw_state, 4)
        locations = []
        movement = []
        enemy_order = []

        for i, ally in enumerate(allies):
            if ally['unit'] == 1:
                locations.append(truck_location[i])
                movement.append(truck_movement[i])
                enemy_order.append(truck_target[i])
            elif ally['unit'] == 2:
                locations.append(light_tank_location[i])
                movement.append(light_tank_movement[i])
                enemy_order.append(light_tank_target[i])
            elif ally['unit'] == 3:
                locations.append(heavy_tank_location[i])
                movement.append(heavy_tank_movement[i])
                enemy_order.append(heavy_tank_target[i])
            elif ally['unit'] == 4:
                locations.append(drone_location[i])
                movement.append(drone_movement[i])
                enemy_order.append(drone_target[i])
                
        return [locations, movement, enemy_order, train]
    
    def step(self, action):
        harvest_reward = 0
        kill_reward = 0
        martyr_reward = 0
        action = self.take_action(action)
        next_state, _, done =  self.game.step(action)
        harvest_reward, enemy_count, ally_count = multi_reward_shape(self.nec_obs, self.team)
        if enemy_count < self.previous_enemy_count:
            kill_reward = (self.previous_enemy_count - enemy_count) * 5

        if ally_count < self.previous_ally_count:
            martyr_reward = (self.previous_ally_count - ally_count) * 5
        reward = harvest_reward + kill_reward - martyr_reward


        self.previous_enemy_count = enemy_count
        self.previous_ally_count = ally_count
        info = {}
        self.steps += 1
        self.reward += reward

        self.nec_obs = next_state
        return self.decode_state(next_state), reward, done, info

    def render(self,):
        return None

    def close(self,):
        return None
