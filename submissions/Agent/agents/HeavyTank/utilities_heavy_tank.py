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
    # if pos_1 == None or pos_2 == None:
    #     return 999
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
    enemy_hps = obs['hps'][(team+1) % 2]
    enemy_list3 = np.argwhere(enemy_hps != 0)
    enemy_list3 = set((tuple(i) for i in enemy_list3))
    enemy_list4 = np.argwhere(enemy_units != 4) # Drone'lar hedef alınmamalı
    enemy_list4 = set((tuple(i) for i in enemy_list4))
    return np.asarray(list(enemy_list1.intersection(enemy_list2).intersection(enemy_list3).intersection(enemy_list4)))

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

def light_tank_locs(obs, team):
    hps = np.array(obs['hps'][team])
    ally_units = np.array(obs['units'][team])
    ally_units[hps<1] = 0
    ally_list = np.argwhere(ally_units == 2)
    ally_list = ally_list.squeeze()

    return ally_list

def heavy_tank_locs(obs, team):
    hps = np.array(obs['hps'][team])
    ally_units = np.array(obs['units'][team])
    ally_units[hps<1] = 0
    ally_list = np.argwhere(ally_units == 3)
    ally_list = ally_list.squeeze()

    return ally_list

def nearest_enemy(allied_unit_loc, enemy_locs):
    distances = []
    if len(enemy_locs) == 0:
        return allied_unit_loc
    for enemy in enemy_locs:
        distances.append(getDistance(allied_unit_loc, enemy))
    nearest_enemy_loc = np.argmin(distances)

    return enemy_locs[nearest_enemy_loc]

def multi_forced_anchor(movement, obs, team, map_grid): # birden fazla truck için
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
    light_tanks = light_tank_locs(obs, team)
    heavy_tanks = heavy_tank_locs(obs, team)

    for i,ally in enumerate(allies):
        if len(heavy_tanks) == 0 or i>6:
            break
        if isinstance(heavy_tanks[0], np.int64):
            heavy_tanks = np.expand_dims(heavy_tanks, axis=0)
        for heavy_tank in heavy_tanks:
            if (ally == heavy_tank).all():
                movement[i] = probabilistic_move2enemy_with_astar(ally, nearest_enemy=nearest_enemy(list(ally), enemy_locs(obs, team)), map_grid=map_grid, movement=movement[i])
            else:
                continue

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

def nearest_resource(obs, truck_object):
    resources = obs['resources']
    resource_loc = np.argwhere(resources == 1)
    distances = []
    for reso in resource_loc:
        distances.append(getDistance(truck_object, reso))
    nearest_resource = np.argmin(distances)
    return resource_loc[nearest_resource]

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

def move_towards_enemy(tank_position, enemy_locs):
    best_movement = 0
    closest_distance = float('inf')
    for enemy in enemy_locs:
        for i in range(1, 7):
            move_x, move_y = getMovement(tank_position, i)
            new_position = [tank_position[0] + move_y, tank_position[1] + move_x]
            distance = getDistance(new_position, enemy)
            if distance < closest_distance and distance > 1:
                best_movement = i
                closest_distance = distance
    return best_movement

def probabilistic_move2enemy(tank_position, enemy_locs, movement):
    if np.random.rand() < 0.6:
        return move_towards_enemy(tank_position, enemy_locs)
    else:
        return movement

def multi_reward_shape(obs, team): # Birden fazla truck için
    load_rewards = []
    unload_rewards = []
    enemy_load_rewards = []
    enemy_unload_rewards = []
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
    distances = [getDistance(truck, base_loc) for truck in trucks if not isinstance(truck, np.int64)]
    distances = normalize_distances(distances)
    load3_coef = - 1
    load2_coef = - 0.5
    load1_coef = - 0.1

    for i, truck in enumerate(trucks):
        for reso in resource_loc:
            # print(reso,"RESOURCE")
            if not isinstance(truck, np.int64):
                # print(loads.shape, "load shape")
                # print(loads[truck[0], truck[1]].shape, "load at truck")
                # print(truck.shape, "Last Truck")
                if (reso == truck).all():
                    if loads[truck[0], truck[1]].max() == 3:
                        load_rewards.append(distances[i] * load3_coef * 10)
                    elif loads[truck[0], truck[1]].max() == 2:
                        load_rewards.append(distances[i] * load2_coef * 10)
                    elif loads[truck[0], truck[1]].max() == 1:
                        load_rewards.append(distances[i] * load1_coef * 10)
            else:
                pass
            if not isinstance(truck, np.int64):
                if loads[truck[0], truck[1]].max() != 0 and (truck == base_loc).all():
                    unload_rewards.append(20)
  
    harvest_reward = sum(load_rewards) + sum(unload_rewards) + sum(enemy_load_rewards) + sum(enemy_unload_rewards)
    return harvest_reward, len(enemy), len(ally)

def normalize_distances(distances):
    max_distance = np.sqrt(18**2 + 12**2)
    return [distance/max_distance for distance in distances]

def get_each_distances(ally_locs):
    # Calculate the distance between each ally unit
    distances = []
    for i, ally_loc in enumerate(ally_locs):
        for j in range(i+1, len(ally_locs)):
            distances.append(getDistance(ally_loc, ally_locs[j]))

    normalize_distance = normalize_distances(distances)
    distances = [1 - distance for distance in normalize_distance]

    return sum(distances)

def offensive_reward(obs, team):
    ally_units = obs['units'][team]
    enemy_units = obs['units'][(team+1) % 2]
    hps = obs['hps'][(team+1) % 2]
    
    ally_locs = np.argwhere(ally_units != 0)
    enemy_locs = np.argwhere(enemy_units != 0)

    distance_reward = 0  # Reward for a successful attack

    if len(ally_units) > 1:
        each_distance_reward = get_each_distances(ally_locs)

    # Birbirine yakınlık reward

    if len(enemy_locs) != 0:
        for ally_loc in ally_locs:
            nearest_enemy_loc = nearest_enemy(ally_loc, enemy_locs)
            distance = getDistance(ally_loc, nearest_enemy_loc)
            
            distance_reward += 1 - distance/np.sqrt(18**2 + 12**2) # Normalize distance
    
    return each_distance_reward, distance_reward, len(enemy_locs), len(ally_locs)

def rearrange_targets(obs, team, enemies):
    enemy_units = obs['units'][(team+1) % 2]
    hps = obs['hps'][(team+1) % 2]
    enemy_locs = np.argwhere(enemy_units != 0)
    hps = hps[enemy_units != 0]
    
    close_hpswithenemy = []
    for enemy in enemies:
        idx = np.argwhere((enemy_locs == enemy).all(axis=1))

        if len(idx) > 0:
            close_hpswithenemy.append((enemy, hps[idx[0][0]]))
    
    close_hpswithenemy = sorted(close_hpswithenemy, key=lambda x: x[1])
    close_hpswithenemy = [list(enemy[0]) for enemy in close_hpswithenemy]

    return close_hpswithenemy
        
def is_valid_for_light_tank(x, y, map_grid):
    return 0 <= x < 24 and 0 <= y < 18 and map_grid[y][x] in ("g","d") 

class Node:
    def __init__(self, parent=None, position=None) ->None:
        self.parent = parent
        self.position = position
        self.g = 0
        self.h = 0
        self.f = 0
    
    def __lt__(self, other):
        return self.f < other.f

    def __eq__(self, other):
        return self.position == other.position
    
    def __repr__(self) -> str:
        return f"{self.position} - g: {self.g} h: {self.h} f: {self.f}"

def astar_path_finding(map_grid, start, end):
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    open_list = []
    closed_list = []
    # print("Start Node", start_node)
    # print("End Node", end_node)
    open_list.append(start_node)

    while open_list:
        current_node = min(open_list, key=lambda x: x.f)
        #print("Current Node", current_node)
        open_list.remove(current_node)
        #print("open_list", open_list)
        closed_list.append(current_node)
        #print("closed_list", closed_list)

        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]
        
        # use getMovement function to get the possible movements
        for i in range(1, 7):
            move_x, move_y = getMovement(current_node.position, i)
            new_position = [current_node.position[0] + move_y, current_node.position[1] + move_x]
            if not is_valid_for_light_tank(new_position[1], new_position[0], map_grid):
                continue
            new_node = Node(current_node, new_position)
            new_node.g = current_node.g + 1
            new_node.h = getDistance(new_node.position, end_node.position)
            new_node.f = new_node.g + new_node.h
            if new_node in closed_list:
                continue
            if new_node in open_list:
                continue
            open_list.append(new_node)
        
    return None

def change_path(map_grid, path):
    for i in range(len(path)):
        try: 
            if map_grid[path[i][0]][path[i][1]] == "m" or map_grid[path[i][0]][path[i][1]] == "w" or map_grid[path[i][0]][path[i][1]] == "d":
                return path[:i]
        except: 
            return None
    return path

def move_towards_enemy_with_astar(tank_position, nearest_enemy, map_grid):
    best_movement = 0
    closest_distance = float('inf')

    for i in range(1, 7):
        move_x, move_y = getMovement(tank_position, i)
        new_position = [tank_position[0] + move_y, tank_position[1] + move_x]
        path = astar_path_finding(map_grid, new_position, list(nearest_enemy))
        if path is None:
            continue
        path = change_path(map_grid, path)
        if path is None:
            continue
        distance = len(path)
        if distance < closest_distance and distance > 1:
            best_movement = i
            closest_distance = distance
    return best_movement

def probabilistic_move2enemy_with_astar(tank_position, nearest_enemy, map_grid, movement):
    print("nearest_enemy", nearest_enemy)
    if np.random.rand() < 0.98:
        return move_towards_enemy_with_astar(tank_position, nearest_enemy, map_grid)
    else:
        return movement
