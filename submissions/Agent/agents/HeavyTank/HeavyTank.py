from os import kill
from agents.BaseLearningGym import BaseLearningAgentGym
import gym
from gym import spaces
import numpy as np
import yaml
from game import Game
from utilities_heavy_tank import multi_forced_anchor, enemy_locs, ally_locs, getDistance, offensive_reward, rearrange_targets

class HeavyTank(BaseLearningAgentGym):
    """Simple agent works for every environment"""

    tagToString = {
            1: "Truck",
            2: "LightTank",
            3: "HeavyTank",
            4: "Drone",
        }
    def read_hypers(self, map):
            with open(f"data/config/{map}.yaml", "r") as f:
                hyperparams_dict = yaml.safe_load(f)
                return hyperparams_dict

    def __init__(self, args, agents, team=0):
        super().__init__()
        configs = self.read_hypers(args.map)
        self.game = Game(args, agents)
        self.team = team
        self.enemy_team = 1
        self.count = 2
        self.height = configs['map']['y']
        self.width = configs['map']['x']
        self.terrain = configs['map']['terrain']
        self.reward = 0
        self.episodes = 0
        self.steps = 0
        self.nec_obs = None
        self.observation_space = spaces.Box(
            low=-2,
            high=401,
            shape=(self.height*self.width*10+4,),
            dtype=np.int16
        )
        self.action_space = self.action_space = spaces.MultiDiscrete([7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5])
        self.previous_enemy_count = 4
        self.previous_ally_count = 4


    def setup(self, obs_spec, action_spec):
        self.observation_space = obs_spec
        self.action_space = action_spec
        # print("setup")

    def reset(self):
        self.previous_enemy_count = 1
        self.previous_ally_count = 1
        self.episodes += 1
        self.count = 2

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
                        'tag': HeavyTank.tagToString[units[team][i][j]],
                        'hp': hps[team][i][j],
                        'location': (i,j),
                        'load': load[team][i][j]
                    }
                    )
                if units[enemy_team][i][j]<6 and units[enemy_team][i][j] != 0:
                    enemy_units.append(
                    {
                        'unit': units[enemy_team][i][j],
                        'tag': HeavyTank.tagToString[units[enemy_team][i][j]],
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
        state, _ = HeavyTank._decode_state(obs, team, enemy_team)
        return state

    def decode_state(self, obs):
        state, info = self._decode_state(obs, self.team, self.enemy_team)
        self.x_max, self.y_max, self.my_units, self.enemy_units, self.resources, self.my_base, self.enemy_base = info
        return state


    def take_action(self, action):
        action[14] = 0
        # self.count -= 1

        return self.just_take_action(action, self.nec_obs, self.team, self.terrain)

    @staticmethod
    def just_take_action(action, raw_state, team, map_grid):

        movement = action[0:7]
        movement = movement.tolist()
        target = action[7:14]
        train = action[14]

        enemy_order = []

        allies = ally_locs(raw_state, team)
        enemies = enemy_locs(raw_state, team)

        if 0 > len(allies):
            print("Neden negatif adamların var ?")
            raise ValueError
        elif 0 == len(allies):
            locations = []
            movement = []
            target = []
            return [locations, movement, target, train]
        elif 0 < len(allies) <= 7:
            ally_count = len(allies)
            locations = allies

            counter = 0
            for j in target:
                if len(enemies) == 0:
                    enemy_order = [[6, 0] for i in range(ally_count)]
                    continue
                k = j % len(enemies)
                if counter == ally_count:
                    break
                if len(enemies) <= 0:
                    break
                enemy_order.append(enemies[k].tolist())
                counter += 1

            while len(enemy_order) > ally_count:
                enemy_order.pop()
            while len(movement) > ally_count:
                movement.pop()

        elif len(allies) > 7:
            ally_count = 7
            locations = allies

            counter = 0
            for j in target:
                if len(enemies) == 0:
                    enemy_order = [[6, 0] for i in range(ally_count)]
                    continue
                k = j % len(enemies)
                if counter == ally_count:
                    break
                if len(enemies) <= 0:
                    break
                enemy_order.append(enemies[k].tolist())
                counter += 1

            while len(locations) > 7:
                locations = list(locations)[:7]

        movement = multi_forced_anchor(movement, raw_state, team, map_grid)
        if len(locations) > 0:
            locations = list(map(list, locations))


        for i in range(len(locations)):
            close_enemy = []
            for k in range(len(enemy_order)):
                if getDistance(locations[i], enemy_order[k]) <= 2:
                    movement[i] = 0
                    close_enemy.append(enemy_order[k])
                    enemy_order[i] = enemy_order[k]

            close_rearranged = rearrange_targets(raw_state, team, close_enemy)
            if len(close_rearranged) > 0:
                enemy_order[i] = close_rearranged[0]


        locations = list(map(tuple, locations))
        return [locations, movement, enemy_order, train]


    def step(self, action):
        action = self.take_action(action)
        next_state, _, done =  self.game.step(action)
        each_distance_reward, distance_reward, enemy_count, ally_count = offensive_reward(self.nec_obs, self.team)

        coef1 = 90
        coef2 = 10

        reward = each_distance_reward * coef1 + distance_reward * coef2

        self.previous_enemy_count = enemy_count
        self.previous_ally_count = ally_count
        info = {}
        self.steps += 1
        self.reward += reward

        if ally_count == 0 or enemy_count == 0:
            done = True

        self.nec_obs = next_state
        return self.decode_state(next_state), reward, done, info

    def render(self,):
        return None

    def close(self,):
        return None
