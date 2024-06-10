from PIL.Image import new
from pandas.core import base
from yaml import load
import numpy as np
import copy
import time

tagToString = {
    1: "Truck",
    2: "LightTank",
    3: "HeavyTank",
    4: "Drone",
    }
stringToTag = {
    "Truck": 1,
    "LightTank": 2,
    "HeavyTank": 3,
    "Drone": 4,
    }

movement_grid = [[(0, 0), (-1, 0), (0, -1), (1, 0), (1, 1), (0, 1), (-1, 1)],
[(0, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 1), (-1, 0)]]


def getMovement(unit_position, action):
    return movement_grid[unit_position[1] % 2][action]


def decodeState(state):
    # score = state['score']
    # turn = state['turn']
    # max_turn = state['max_turn']
    units = state['units']
    hps = state['hps']
    bases = state['bases']
    res = state['resources']
    load = state['loads']
    
    blue = 0
    red = 1
    y_max, x_max = res.shape
    blue_units = []
    red_units = []
    resources = []
    blue_base = None
    red_base = None
    for i in range(y_max):
        for j in range(x_max):
            if units[blue][i][j] < 6 and units[blue][i][j] != 0 and hps[blue][i][j]>0:
                blue_units.append(
                    {
                        'unit': units[blue][i][j],
                        'tag': tagToString[units[blue][i][j]],
                        'hp': hps[blue][i][j],
                        'location': (i, j),
                        'load': load[blue][i][j]
                    }
                )
            if units[red][i][j] < 6 and units[red][i][j] != 0 and hps[red][i][j]>0:
                red_units.append(
                    {
                        'unit': units[red][i][j],
                        'tag': tagToString[units[red][i][j]],
                        'hp': hps[red][i][j],
                        'location': (i, j),
                        'load': load[red][i][j]
                    }
                )
            if res[i][j] == 1:
                resources.append((i, j))
            if bases[blue][i][j]:
                blue_base = (i, j)
            if bases[red][i][j]:
                red_base = (i, j)
    return [blue_units, red_units, blue_base, red_base, resources]


def getDistance(pos_1, pos_2):
    if pos_1 == None or pos_2 == None:
        return 999
    pos1 = copy.copy(pos_1)
    pos2 = copy.copy(pos_2)
    shift1 = (pos1[1]+1)//2
    shift2 = (pos2[1]+1)//2
    pos1[0] -= shift1
    pos2[0] -= shift2
    distance = (abs(pos1[0]-pos2[0]) + abs(pos1[1]-pos2[1]) + abs(pos1[0]+pos1[1]-pos2[0]-pos2[1]))//2
    return distance


def decode_location(my_units):
    locations = []
    for unit in my_units:
        locations.append(unit["location"])
    return locations



def enemy_locs(obs, team):
    enemy_units = obs['units'][(team+1) % 2]
    enemy_list1 = np.argwhere(enemy_units != -1)
    enemy_list1 = set((tuple(i) for i in enemy_list1))
    enemy_list2 = np.argwhere(enemy_units != 0)
    enemy_list2 = set((tuple(i) for i in enemy_list2))
    return np.asarray(list(enemy_list1.intersection(enemy_list2)))


def ally_locs(obs, team):

    ally_units = obs['units'][team]
    ally_list1 = np.argwhere(ally_units != -1)
    ally_list1 = set((tuple(i) for i in ally_list1))
    ally_list2 = np.argwhere(ally_units != 0)
    ally_list2 = set((tuple(i) for i in ally_list2))

    return list(ally_list1.intersection(ally_list2))

def truck_locs(obs, team):
    hps = np.array(obs['hps'][team])
    ally_units = np.array(obs['units'][team])
    ally_units[hps<1] = 0
    ally_list = np.argwhere(ally_units == 1)
    ally_list = ally_list.squeeze()

    return ally_list

def nearest_enemy(allied_unit_loc, enemy_locs):
    distances = []
    for enemy in enemy_locs:
        distances.append(getDistance(allied_unit_loc, enemy))
    nearest_enemy_loc = np.argmin(distances)

    return enemy_locs[nearest_enemy_loc]

def multi_forced_anchor(movement, obs, team): # birden fazla truck için
    bases = obs['bases'][team]
    units = obs['units'][team]
    loads = obs['loads'][team]
    resources = obs['resources']
    hps = obs["hps"][team]
    score = obs['score']
    unit_loc = np.argwhere(units == 1)
    unit_loc = unit_loc.squeeze()
    base_loc = np.argwhere(bases == 1)
    base_loc = base_loc.squeeze()
    loaded_loc = np.argwhere(loads != 0)
    loaded_trucks = loads[loads != 0]
    resource_loc = np.argwhere(resources == 1)
    allies = ally_locs(obs, team)
    trucks = truck_locs(obs, team)

    for i,ally in enumerate(allies):
        if len(trucks) == 0 or i>6:
            break
        if isinstance(trucks[0], np.int64):
            trucks = np.expand_dims(trucks, axis=0)
        for truck in trucks:
            if (ally == truck).all():
                for reso in resource_loc:
                    if loads[truck[0], truck[1]].max() != 3 and (reso == truck).all():
                        movement[i] = 0
                    elif loads[truck[0], truck[1]].max() != 0 and (truck == base_loc).all():
                        movement[i] = 0
                    else:
                        continue
    return movement

def light_tanks_locs(obs, team):
    hps = np.array(obs['hps'][team])
    ally_units = np.array(obs['units'][team])
    ally_units[hps<1] = 0
    ally_list = np.argwhere(ally_units == 2)
    ally_list = ally_list.squeeze()

    return ally_list

def heavy_tanks_locs(obs, team):
    hps = np.array(obs['hps'][team])
    ally_units = np.array(obs['units'][team])
    ally_units[hps<1] = 0
    ally_list = np.argwhere(ally_units == 3)
    ally_list = ally_list.squeeze()

    return ally_list

def drones_locs(obs, team):
    hps = np.array(obs['hps'][team])
    ally_units = np.array(obs['units'][team])
    ally_units[hps<1] = 0
    ally_list = np.argwhere(ally_units == 4)
    ally_list = ally_list.squeeze()

    return ally_list



def forced_anchor(movement, obs, team_no):
    bases = obs['bases'][team_no]
    units = obs['units'][team_no]
    loads = obs['loads'][team_no]
    resources = obs['resources']
    unit_loc = np.argwhere(units == 1)
    unit_loc = unit_loc.squeeze()
    base_loc = np.argwhere(bases == 1)
    base_loc = base_loc.squeeze()
    resource_loc = np.argwhere(resources == 1)
    for reso in resource_loc:
        if (reso == unit_loc).all() and loads.max() != 3:
            movement = [0]
        else:
            continue
        if (reso == base_loc).all() and loads.max() != 0:
            movement = [0]
    return movement

def Shoot(obs, loc, team):
    enemy_units = obs['units'][(team+1) % 2]
    enemy_list = np.argwhere(enemy_units != 0)
    enemy_list = enemy_list.squeeze()


def point_blank_shoot(allied_unit_loc, enemy_locs, action):
    distances = []
    for enemy in enemy_locs:
        distances.append(getDistance(allied_unit_loc, enemy))
    if min(distances) <= 2:
        nearest_enemy_loc = np.argmin(distances)
        return enemy_locs[nearest_enemy_loc]

def necessary_obs(obs, team):
    ally_base = obs['bases'][team]
    enemy_base = obs['bases'][(team+1) % 2]
    ally_units = obs['units'][team]
    enemy_units = obs['units'][(team+1) % 2]
    ally_loads = obs['loads'][team]
    resources = obs['resources']

    ally_unit_loc = np.argwhere(ally_units == 1).squeeze()
    enemy_unit_loc = np.argwhere(enemy_units == 1).squeeze()
    ally_base_loc = np.argwhere(ally_base == 1).squeeze()
    enemy_base_loc = np.argwhere(enemy_base == 1).squeeze()
    resource_loc = np.argwhere(resources == 1)
    truck_load = [ally_loads.max(), 0]
    resource = [coo for coords in resource_loc for coo in coords]

    new_obs = [*ally_unit_loc.tolist(), *enemy_unit_loc.tolist(), *ally_base_loc.tolist(), *enemy_base_loc.tolist(), *resource, *truck_load]
    
    if len(new_obs) == 20:
        print(new_obs)
        time.sleep(1)
    return new_obs

def reward_shape(obs, team):
    load_reward = 0
    unload_reward = 0
    bases = obs['bases'][team]
    units = obs['units'][team]
    loads = obs['loads'][team]
    resources = obs['resources']
    unit_loc = np.argwhere(units == 1)
    unit_loc = unit_loc.squeeze()
    base_loc = np.argwhere(bases == 1)
    base_loc = base_loc.squeeze()
    resource_loc = np.argwhere(resources == 1)
    for reso in resource_loc:
        if (reso == unit_loc).all() and loads.max() != 3:
            load_reward += 1
        else:
            continue
        if (reso == base_loc).all() and loads.max() != 0:
            unload_reward += 10

    return load_reward + unload_reward

def multi_reward_shape(obs, team): # Birden fazla truck için
    load_reward = 0
    unload_reward = 0
    enemy_load_reward = 0
    enemy_unload_reward = 0
    bases = obs['bases'][team]
    units = obs['units'][team]
    enemy_bases = obs['bases'][(team+1) % 2]
    enemy_units = obs['units'][(team+1) % 2]
    enemy_loads = obs['loads'][(team+1) % 2]
    loads = obs['loads'][team]
    resources = obs['resources']
    unit_loc = np.argwhere(units == 1)
    unit_loc = unit_loc.squeeze()
    base_loc = np.argwhere(bases == 1)
    base_loc = base_loc.squeeze()
    enemy_unit_loc = np.argwhere(enemy_units == 1)
    enemy_unit_loc = enemy_unit_loc.squeeze()
    enemy_base_loc = np.argwhere(enemy_bases == 1)
    enemy_base_loc = enemy_base_loc.squeeze()
    resource_loc = np.argwhere(resources == 1)
    enemy = enemy_locs(obs, team)
    ally = ally_locs(obs, team)
    trucks = truck_locs(obs, team)

    for truck in trucks:
        for reso in resource_loc:
            print(reso,"RESOURCE")
            if not isinstance(truck, np.int64):
                print(loads.shape, "load shape")
                print(loads[truck[0], truck[1]].shape, "load at truck")
                print(truck.shape, "Last Truck")
                if (reso == truck).all():
                    if loads[truck[0], truck[1]].max() != 3: 
                        load_reward += 10
            else:
                pass
            if not isinstance(truck, np.int64):
                if loads[truck[0], truck[1]].max() != 0 and (truck == base_loc).all():
                    unload_reward += 20

    harvest_reward = load_reward + unload_reward + enemy_load_reward + enemy_unload_reward
    return harvest_reward, len(enemy), len(ally)

