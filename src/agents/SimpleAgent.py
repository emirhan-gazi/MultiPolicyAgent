from random import randint,random
import copy
from utilities import *

# Tank moves to enemy truck, if within attack parameter, shoots
# Truck moves to collect resource greedly


class SimpleAgent:
    def __init__(self, team, action_lenght):
        self.team = team
        self.enemy_team = (team+1) % 2
        self.action_lenght = action_lenght

    def action(self, state):
        '''
        pos=[3, 17]
        target=[10, 15]
        astar(pos,target,state)
        return
        '''
        self.y_max, self.x_max = state['resources'].shape
        decoded = decodeState(state)
        self.my_units = decoded[self.team]
        self.enemy_units = decoded[self.enemy_team]
        self.my_base = decoded[self.team + 2]
        self.enemy_base = decoded[self.enemy_team + 2]
        self.resources = decoded[4]
        movement = []
        target = []
        location = []
        counter = {"Truck":0,"LightTank":0,"HeavyTank":0,"Drone":0}
        for unit in self.my_units:
            counter[unit['tag']]+=1
            location.append(unit['location'])
            unt_pos = [unit['location'][0], unit['location'][1]]
            if unit['tag'] == 'LightTank' or unit['tag'] == 'Drone' or unit['tag'] == 'HeavyTank':
                target_type = 9
                target_pos = None
                distance = 99
                for e_unit in self.enemy_units:
                    temp_dist = getDistance(unt_pos, list(e_unit['location']))
                    if temp_dist < 2:
                        distance = temp_dist
                        target_type = e_unit['unit']
                        target_pos = [e_unit['location'][0], e_unit['location'][1]]
                    elif e_unit['unit'] < target_type and e_unit['hp']>0 and distance>1:
                        distance = temp_dist
                        target_type = e_unit['unit']
                        target_pos = [e_unit['location'][0], e_unit['location'][1]]
                
                if target_pos and unit['tag'] == 'Drone' and getDistance(unt_pos, target_pos) <= 1: # shoot
                    movement.append(0)
                    target.append((target_pos[0], target_pos[1]))
                elif target_pos and unit['tag'] == 'LightTank' and getDistance(unt_pos, target_pos) <= 2: # shoot
                    movement.append(0)
                    target.append((target_pos[0], target_pos[1]))
                elif target_pos and unit['tag'] == 'HeavyTank' and getDistance(unt_pos, target_pos) <= 2: # shoot
                    movement.append(0)
                    target.append((target_pos[0], target_pos[1]))
                else:
                    possible_actions = []
                    for m_action in range(7):
                        move_x, move_y = getMovement(unt_pos, m_action)
                        act_pos = [unt_pos[0] + move_y, unt_pos[1] + move_x]
                        if act_pos[0] < 0 or act_pos[1] < 0 or act_pos[0] > self.y_max-1 or act_pos[1] > self.x_max-1:
                            act_pos = [unt_pos[0], unt_pos[1]]
                        if unit['tag'] == 'HeavyTank' and state['terrain'][act_pos[0]][act_pos[1]] == 1:
                            # Heavy avoiding dirt
                            continue
                        if unit['tag'] != 'Drone' and state['terrain'][act_pos[0]][act_pos[1]] == 3:
                            # Ground units avoiding water
                            continue
                        if target_pos:
                            possible_actions.append([getDistance(target_pos, act_pos), target_pos, act_pos, m_action])
                        else:
                            possible_actions.append([random(), target_pos, act_pos, m_action])
                    possible_actions.sort()
                    if random() < 0.20:
                        movement.append(copy.copy(randint(1,6)))
                    else:
                        movement.append(copy.copy(possible_actions[0][-1]))
                    target.append(copy.copy(target_pos))
            elif unit['tag'] == 'Truck':
                dis = 999
                target_pos = None
                unt_pos = [unit['location'][0], unit['location'][1]]
                if unit['load'] > 0:
                    target_pos = [self.my_base[0], self.my_base[1]]
                elif len(self.resources) > 0:
                    for res in self.resources:
                        res_pos = [res[0], res[1]]
                        dist_tmp = getDistance(unt_pos, res_pos)
                        res_busy = False
                        
                        for u in self.my_units+self.enemy_units:
                            if u['location'][0] == res_pos[0] and u['location'][1] == res_pos[1] and not u['unit'] == unit['unit']:
                                res_busy = True
                                break
                        if dist_tmp < dis and not res_busy:
                            dis = dist_tmp
                            target_pos = res_pos
                else:
                    target_pos = unt_pos
                if target_pos is None:
                    target_pos = unt_pos
                possible_actions = []
                for m_action in range(7):
                    move_x, move_y = getMovement(unt_pos, m_action)
                    act_pos = [unt_pos[0] + move_y, unt_pos[1] + move_x]
                    if act_pos[0] < 0 or act_pos[1] < 0 or act_pos[0] > self.y_max - 1 or act_pos[1] > self.x_max-1:
                        act_pos = [unt_pos[0] ,unt_pos[1]]
                    possible_actions.append([getDistance(target_pos, act_pos), target_pos, act_pos, m_action])
                possible_actions.sort()

                if random()<0.20:
                    movement.append(copy.copy(randint(1,6)))
                else:
                    movement.append(copy.copy(possible_actions[0][-1]))
                target.append(copy.copy(target_pos))
            else:
                movement.append(2)
                target.append([0,0])  
        train = 0
        #if random() < 0.2:
        #    train = randint(1,4)
        if state["score"][self.team]>state["score"][self.enemy_team]+2:
            if counter["Truck"]<2:
                train = stringToTag["Truck"]
            elif counter["LightTank"]<1:
                train = stringToTag["LightTank"]
            elif counter["HeavyTank"]<1:
                train = stringToTag["HeavyTank"]
            elif counter["Drone"]<1:
                train = stringToTag["Drone"]
            elif len(self.my_units)<len(self.enemy_units):
                train = randint(2,4)
        elif state["score"][self.team]+2<state["score"][self.enemy_team] and len(self.my_units)<len(self.enemy_units)*2:
            train = randint(2,4)
        return (location, movement, target, train)