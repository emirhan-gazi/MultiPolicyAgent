from agents.RiskyValley import RiskyValley
from game import Game
import yaml
import numpy as np
import gym
from gym import spaces
from utilities import  ally_locs,truck_locs,drones_locs, light_tanks_locs, heavy_tanks_locs
import ray
from ray.rllib.agents.ppo import PPOTrainer
from ray.tune import run_experiments, register_env
from argparse import Namespace
from agents.Attack import Attack
from agents.Collect import Collect
from agents.Drone import Drone


class MultiPolicyAgent:
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

    def __init__(self, team, action_length):
        super().__init__()
        self.team = team
        self.enemy_team = (team+1)%2
        self.temp_agents  = [None,"RandomAgent"]
       
        truck_model_path = "/submissions/Agent/models/Truck/checkpoint_000440/checkpoint-440"
        light_tank_model_path = "/submissions/Agent/models/LightTank/checkpoint_000070/checkpoint-70"
        heavy_tank_model_path = "/submissions/Agent/models/HeavyTank/checkpoint_000070/checkpoint-70"
        drone_model_path = "/submissions/Agent/models/Drone/checkpoint_000070/checkpoint-70"

        args_for_models = Namespace(map="RiskyValley", render=False, gif=False, img=False)
        self.config = self.read_hypers("RiskyValley")
        self.map_grid = self.config["map"]["terrain"]
        register_env("ray", lambda config: RiskyValley(args_for_models, self.temp_agents))
        self.ppo_agent = PPOTrainer(config=MultiPolicyAgent.config, env="ray")
        self.initiate_truck(truck_model_path)
        self.initiate_light_tank(light_tank_model_path)
        self.initiate_heavy_tank(heavy_tank_model_path)
        self.initiate_drone(drone_model_path)
    

    def initiate_truck(self, model_path):
        self.ppo_agent.restore(checkpoint_path=model_path)
        self.truck_policy = self.ppo_agent.get_policy()

    def initiate_light_tank(self, model_path):
        self.ppo_agent.restore(checkpoint_path=model_path)
        self.light_tank_policy = self.ppo_agent.get_policy()
    
    def initiate_heavy_tank(self, model_path):
        self.ppo_agent.restore(checkpoint_path=model_path)
        self.heavy_tank_policy = self.ppo_agent.get_policy()
    
    def initiate_drone(self, model_path):
        self.ppo_agent.restore(checkpoint_path=model_path)
        self.drone_policy = self.ppo_agent.get_policy()

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
                        'tag': MultiPolicyAgent.tagToString[units[team][i][j]],
                        'hp': hps[team][i][j],
                        'location': (i,j),
                        'load': load[team][i][j]
                    }
                    )
                if units[enemy_team][i][j]<6 and units[enemy_team][i][j] != 0:
                    enemy_units.append(
                    {   
                        'unit': units[enemy_team][i][j],
                        'tag': MultiPolicyAgent.tagToString[units[enemy_team][i][j]],
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
        state, _ = MultiPolicyAgent._decode_state(obs, team, enemy_team)
        return state

    def decode_state(self, obs):
        state, info = self._decode_state(obs, self.team, self.enemy_team)
        self.x_max, self.y_max, self.my_units, self.enemy_units, self.resources, self.my_base, self.enemy_base = info
        return state

    
    def action(self, state):
        return self.just_take_action(state, self.team) 
    
    def compute_single_action(self,state,raw_state,unit): 
        if unit == 1:
            actions, _, _ = self.truck_policy.compute_single_action(state.astype(np.float32))
            location, movement, target, train = Collect.just_take_action(actions,raw_state , self.team)
            return location, movement, target, train
        elif unit == 2:
            actions, _, _ = self.light_tank_policy.compute_single_action(state.astype(np.float32))
            location, movement, target, train = Attack.just_take_action(actions,raw_state , self.team, self.map_grid)
            return location, movement, target, train

        elif unit == 3:
            actions, _, _ = self.heavy_tank_policy.compute_single_action(state.astype(np.float32))
            location, movement, target, train = Attack.just_take_action(actions,raw_state , self.team, self.map_grid)
            return location, movement, target, train
        
        elif unit == 4:
            actions, _, _ = self.drone_policy.compute_single_action(state.astype(np.float32))
            location, movement, target, train = Drone.just_take_action(actions,raw_state , self.team, self.map_grid)
            return location, movement, target, train
    
    def just_take_action(self, raw_state, team):
        state, _ = MultiPolicyAgent._decode_state(raw_state, self.team, self.enemy_team)
        allies = ally_locs(raw_state, team)
        trucks = truck_locs(raw_state, team)
        drones = drones_locs(raw_state, team)
        light_tanks = light_tanks_locs(raw_state, team)
        heavy_tanks = heavy_tanks_locs(raw_state, team)
        # truck movement
        truck_location, truck_movement, truck_target, train =  self.compute_single_action(state, raw_state, 1)
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
            ally = list(ally)
            if i >= 7:
                break
            if ally in trucks:
                locations.append(truck_location[i])
                movement.append(truck_movement[i])
                enemy_order.append(truck_target[i])
            elif ally in light_tanks:
                locations.append(light_tank_location[i])
                movement.append(light_tank_movement[i])
                enemy_order.append(light_tank_target[i])
            elif ally in heavy_tanks:
                locations.append(heavy_tank_location[i])
                movement.append(heavy_tank_movement[i])
                enemy_order.append(heavy_tank_target[i])
            elif ally in drones:
                locations.append(drone_location[i])
                movement.append(drone_movement[i])
                enemy_order.append(drone_target[i])
        train = 0 
                
        return [locations, movement, enemy_order, train]
    
