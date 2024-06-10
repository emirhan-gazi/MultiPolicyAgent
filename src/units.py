import pygame
from pygame.locals import RLEACCEL
import numpy
import random
import yaml
from copy import copy
from math import log

movement = [[(0,0),(-1,0),(0,-1),(1,0),(1,1),(0,1),(-1,1)],
    [(0,0),(-1,-1),(0,-1),(1,-1),(1,0),(0,1),(-1,0)]]
hp_images = ["data/images/hp_zero.png", \
    "data/images/hp_quarter.png", \
    "data/images/hp_half.png", \
    "data/images/hp_3quarter.png", \
    "data/images/hp_full.png"]
unit_config = None
try:
    with open('data/config/rules.yaml') as file:
        unit_config = yaml.load(file, Loader=yaml.FullLoader)
except:
    print('Rules Could Not be Found! Using Default Rules')
    unit_config = {
        'HeavyTank': {'attack': 2, 'max_hp': 4}, 
        'LightTank': {'attack': 2, 'max_hp': 2}, 
        'Truck': {'max_hp': 1, 'max_load': 3}, 
        'Drone': {'attack': 2, 'max_hp': 1},
        'Base': {'starting_resource': 5,'recruit': False},
        'Terrain': {'mountain_risk': 0.25, 'wreckage_time': 5},
        'Animation':{'enabled': False, 'speed': 1}}
    
class Unit(pygame.sprite.Sprite):
    def __init__(self, gmap, x=0, y=0, offset=(0,0), id_num=0):
        self.id_num = id_num
        self.render = gmap.game.render
        self.offset = offset
        self.gmap = gmap
        self.alive = True
        self.load = 0
        self.death_timer = -1
        self._animation_target_x = x
        self._animation_target_y = y
        self.animation_enabled = unit_config['Animation']['enabled']
        self.animation_speed = unit_config['Animation']['speed']
        self.has_animation = False
        self.anim = []
        self.animations = {}
        capabilities = {}
        if self.render:
            if self.unit:
                self.hp_surf = pygame.image.load(hp_images[4]).convert()
                self.hp_rect = self.hp_surf.get_rect()
            if not self.resource:
                self.wreck = pygame.image.load("data/images/wreck_"+str(self.team)+".png").convert()
                self.wreck.set_colorkey((255, 255, 255), RLEACCEL)
        self.setMapPosition(x, y)

    def moveAnimation(self, force=False):
        deltax = self._animation_target_x - self.rect.x
        deltay = self._animation_target_y - self.rect.y
        if force:
            step_x = deltax
            step_y = deltay
        else:
            if abs(deltax) < self.animation_speed:
                step_x = deltax
            else:
                step_x = (deltax//abs(deltax))*self.animation_speed
            if abs(deltay) < self.animation_speed:
                step_y = deltay
            else:
                step_y = (deltay//abs(deltay))*self.animation_speed
        #print(self._animation_target_x, self.rect.x, self._animation_target_y, self.rect.y)
        self.setDeltaPosition((step_x, step_y))
    def setDeltaPosition(self, delta_position):
        #print(self._animation_target_x, self._animation_target_y, self.rect.x, self.rect.y)
        x, y = delta_position
        #print(x,y)
        self.rect.x += x
        self.rect.y += y
        if self.rect.x == self._animation_target_x and self.rect.y == self._animation_target_y:
            self.has_animation = False
    def setPosition(self, position):
        x, y = position
        off_x, off_y = self.offset
        self.rect.x = x - off_x
        self.rect.y = y - off_y
    def setMapPosition(self, x, y, force=True):
        self.x_coor = x
        self.y_coor = y
        tile = self.gmap.getTileFromIndex(x,y)
        if self.unit: tile.setUnit(self)
        elif self.resource: tile.setResource(self)
        elif self.base: tile.setBase(self)
        if self.render and force:
            self.setPosition(tile.getPosition())
    def setAnimationMoveTarget(self, x, y):
        self.has_animation = True
        x, y = self.gmap.getTileFromIndex(x, y).getPosition()
        off_x, off_y = self.offset
        self._animation_target_x = int(x) - off_x
        self._animation_target_y = int(y) - off_y
    def removeUnit(self):
        self.getTile().unsetUnit()
    def moveAction(self, m_action=0, target=0):
        if m_action < 0 or m_action > 6 or not self.alive:
            return
        if m_action == 0:
            if self.loadable:
                return self.loadUnload()
            else:
                return self.shoot(target)
        move_x, move_y = movement[self.x_coor % 2][m_action]
        map_size_x = self.gmap.size_x
        map_size_y = self.gmap.size_y
        x = self.x_coor + move_x
        y = self.y_coor + move_y
        invalid = False

        currentTile = self.getTile()
        try:
            nextTile = self.getTile(x, y)
        except:
            nextTile = None
        if x<0 or x>map_size_x-1 or y<0 or y>map_size_y-1: 
            invalid = True
        elif nextTile.hasUnit(): 
            invalid = True
        elif currentTile.getTerrain() == 'd' and self.heavy: #heavy units gets stucked on dirt
            invalid = True
        elif nextTile.getTerrain() == 'w' and not self.fly: #flying units can move over water
            invalid = True
        elif nextTile.getTerrain() == 'm' and not self.fly: #flying units can move over mountain
            invalid = True
        if not invalid: 
            self.getTile().unsetUnit()
            self.setMapPosition(x, y, force=not self.animation_enabled)
            if self.gmap.game.render: self.setAnimationMoveTarget(x, y)
            if nextTile.getTerrain() == 'm' and random.random() < unit_config['Terrain']['mountain_risk']:
                self.gotHit()
        else:
            self.has_animation = False
        
            
    def loadUnload(self):
        tile = self.getTile()
        if tile.hasResource() and self.load < self.max_load:
            self.load += 1
            tile.resource.on_map = False
            tile.resource = None
        elif tile.hasBase() and tile.getBase().getTeam() == self.team:
            tile.base.unloaded += self.load
            self.load = 0
        return self.load
    def getTag(self):
        key = self.map_key if self.alive else 8
        return type(self).__name__, key
    def getSurf(self):
        s = self.surf if self.alive else self.wreck
        self.hp_rect.x = self.rect.x+10
        self.hp_rect.y = self.rect.y-5
        surfs = []
        surfs.append((s, self.rect))
        surfs.append((self.hp_surf, self.hp_rect))
        for a in self.anim:
            #if a in self.animations.keys:
            rect = self.animations[a].get_rect()
            rect.x = self.rect.x+45
            rect.y = self.rect.y+10
            surfs.append((self.animations[a], rect))
        return surfs 
    def getTile(self,x=-1,y=-1):
        if x==-1: x = self.x_coor
        if y==-1: y = self.y_coor
        return self.gmap.getTileFromIndex(x, y)
    def getTeam(self):
        return self.team
    def gotHit(self):
        self.current_hp -=1
        if self.render:
            ratio = self.current_hp/self.max_hp
            if ratio <= 0.75:
                self.hp_surf = pygame.image.load(hp_images[3]).convert()
                self.hp_rect = self.hp_surf.get_rect()
            if ratio <= 0.50:
                self.hp_surf = pygame.image.load(hp_images[2]).convert()
                self.hp_rect = self.hp_surf.get_rect()
            if ratio <= 0.25:
                self.hp_surf = pygame.image.load(hp_images[1]).convert()
                self.hp_rect = self.hp_surf.get_rect()
            if ratio <= 0:
                self.hp_surf = pygame.image.load(hp_images[0]).convert()
                self.hp_rect = self.hp_surf.get_rect()
        if self.current_hp <= 0:
            self.alive = False
            self.death_timer = unit_config['Terrain']['wreckage_time']
    def getCoor(self):
        return (self.y_coor,self.x_coor)
    def getHp(self):
        return self.current_hp
    def shoot(self,idd):
        if idd == None:
            return 0
        y,x = idd
        target = self.gmap.getUnitFromIndex(x,y)
        if target == None:
            #print("Empty Shot")
            return
        if target.getTeam() == self.getTeam():
            #print("Same Team")
            return
        if target.fly and not self.aa:
            #print("Can not attack air unit")
            return
        distance = self.gmap.getDistance([target.x_coor , target.y_coor],[self.x_coor,self.y_coor])
        odds = 1-((1/self.attack)*log(distance,2)) if distance>=1 else 0
        hit = random.random() < odds
        team1 = "Red " if self.getTeam() else "Blue "
        team2 = "Red " if target.getTeam() else "Blue "
        #print(team1, self.getTag()[0], "shoot ",team2, target.getTag()[0],"distance: ",distance, "odds: ",odds, "hit: ",hit)
        if not target.alive:
            #print("Already Wrecked")
            None
        elif hit:
            target.gotHit()
        return hit
    def getAnimation(self):
        return self.anim
    def setAnimation(self,anim):
        if self.animations[anim]:
            self.anim.append(anim)
            return True
        return False
    def resetAnimation(self,anim):
        #self.surf = copy(self.base_surf)
        self.anim.remove(anim)
class HeavyTank(Unit):
    def __init__(self, gmap, x=0, y=0, team=0, id_num=0):
        self.team = team
        if gmap.game.render:
            self.base_surf = pygame.image.load("data/images/tankh_"+str(self.team)+".png").convert_alpha()
            self.base_surf = pygame.transform.scale(self.base_surf, (50, 50))
            self.surf = copy(self.base_surf)
            #self.surf.set_colorkey((255, 255, 255), RLEACCEL)
            self.rect = self.surf.get_rect()
        self.speed = 1
        self.map_key = 3
        self.attack = unit_config[type(self).__name__]['attack']
        self.max_hp = unit_config[type(self).__name__]['max_hp']
        self.current_hp = self.max_hp
        self.loadable = False
        self.heavy = unit_config[type(self).__name__]['heavy']
        self.fly = unit_config[type(self).__name__]['fly']
        self.aa = unit_config[type(self).__name__]['anti_air']
        self.unit = True
        self.resource = False
        self.base = False
        offset=(25,20)
        super().__init__(gmap, x, y, offset, id_num)
        if gmap.game.render:
            self.animations['shoot'] = pygame.image.load("data/images/fire_tank.png").convert_alpha() 

class LightTank(Unit):
    def __init__(self, gmap, x=0, y=0, team=0, id_num=0):
        self.team = team
        if gmap.game.render:
            #self.base_surf = pygame.Surface([60,50])
            self.base_surf = pygame.image.load("data/images/tankl_"+str(self.team)+".png").convert_alpha()
            self.base_surf = pygame.transform.scale(self.base_surf, (50, 50))
            #self.base_surf.blit(self.unit_surf, (0, 0))
            self.surf = copy(self.base_surf)
            #self.surf.set_colorkey((255, 255, 255), RLEACCEL)
            self.rect = self.surf.get_rect()
        self.speed = 1
        self.map_key = 2
        self.attack = unit_config[type(self).__name__]['attack']
        self.max_hp = unit_config[type(self).__name__]['max_hp']
        self.current_hp = self.max_hp
        self.loadable = False
        self.heavy = unit_config[type(self).__name__]['heavy']
        self.fly = unit_config[type(self).__name__]['fly']
        self.aa = unit_config[type(self).__name__]['anti_air']
        self.unit = True
        self.resource = False
        self.base = False
        offset=(25,20)
        super().__init__(gmap, x, y, offset, id_num)   
        if gmap.game.render:
            self.animations['shoot'] = pygame.image.load("data/images/fire_tank.png").convert_alpha()     

class Truck(Unit):
    def __init__(self, gmap, x=0, y=0, team=0, id_num=0):
        self.team = team
        if gmap.game.render:
            self.base_surf = pygame.image.load("data/images/truck_"+str(self.team)+".png").convert_alpha()
            self.base_surf = pygame.transform.scale(self.base_surf, (50, 50))
            #self.surf.set_colorkey((255, 255, 255), RLEACCEL)
            self.surf = copy(self.base_surf)
            self.rect = self.surf.get_rect()
        self.speed = 1
        self.map_key = 1
        self.max_load = unit_config[type(self).__name__]['max_load']
        self.max_hp = unit_config[type(self).__name__]['max_hp']
        self.current_hp = self.max_hp
        self.loadable = True
        self.heavy = unit_config[type(self).__name__]['heavy']
        self.fly = unit_config[type(self).__name__]['fly']
        self.aa = unit_config[type(self).__name__]['anti_air']
        self.unit = True
        self.resource = False
        self.base = False
        offset=(25,20)
        super().__init__(gmap, x, y, offset, id_num)    

class Drone(Unit):
    def __init__(self, gmap, x=0, y=0, team=0, id_num=0):
        self.team = team
        if gmap.game.render:
            self.base_surf = pygame.image.load("data/images/drone_"+str(self.team)+".png").convert_alpha()
            self.base_surf = pygame.transform.scale(self.base_surf, (50, 50))
            #self.surf.set_colorkey((255, 255, 255), RLEACCEL)
            self.surf = copy(self.base_surf)
            self.rect = self.surf.get_rect()
        self.speed = 1
        self.map_key = 4
        self.attack = unit_config[type(self).__name__]['attack']
        self.max_hp = unit_config[type(self).__name__]['max_hp']
        self.current_hp = self.max_hp
        self.loadable = False
        self.heavy = unit_config[type(self).__name__]['heavy']
        self.fly = unit_config[type(self).__name__]['fly']
        self.aa = unit_config[type(self).__name__]['anti_air']
        self.unit = True
        self.resource = False
        self.base = False
        offset=(25,20)
        super().__init__(gmap, x, y, offset, id_num)  
        if gmap.game.render:
            self.animations['shoot'] = pygame.image.load("data/images/fire_tank.png").convert_alpha()       

class Base(Unit):
    def __init__(self, gmap, x=0, y=0, team=0, id_num=0):
        self.team = team
        if gmap.game.render:
            self.surf = pygame.image.load("data/images/base_"+str(self.team)+".png").convert_alpha()
            self.surf = pygame.transform.scale(self.surf, (50, 50))
            #self.surf.set_colorkey((255, 255, 255), RLEACCEL)
            self.rect = self.surf.get_rect()
        self.speed = 0
        self.attack = 0
        self.map_key = 6
        self.unloaded = unit_config[type(self).__name__]['starting_resource']
        self.recruit = unit_config[type(self).__name__]['recruit']
        self.unit = False
        self.resource = False
        self.base = True
        offset=(25,20)
        super().__init__(gmap, x, y, offset, id_num)  
    def getScore(self):
            return self.unloaded
    def trainUnit(self,train_unit):
        if not self.recruit: return
        if train_unit == 0: return
        #print(train_unit,UNIT_MAP_KEY_TO_TYPE_MAP[train_unit])
        cost = unit_config[UNIT_MAP_KEY_TO_TYPE_MAP[train_unit]]['cost']
        if not self.getTile().hasUnit() and self.unloaded >= cost:
            y,x = self.getCoor()
            self.gmap.game.units[self.team].append(UNIT_MAP_KEY_TO_CLASS_MAP[train_unit](self.gmap,x,y,team=self.team, id_num = self.gmap.game.idGeneretor()))
            self.unloaded -= cost
        else:
            #print(Could not train unit)
            None
    def getSurf(self):
        return self.surf, self.rect
        

class Resource(Unit):
    def __init__(self, gmap, x=0, y=0, team=-1, id_num=0):
        self.team = team
        if gmap.game.render:
            self.surf = pygame.image.load("data/images/gold.png").convert()
            self.surf.set_colorkey((255, 255, 255), RLEACCEL)
            self.rect = self.surf.get_rect()
        self.speed = 0
        self.attack = 0
        self.map_key = 9
        self.on_map = True
        self.unit = False
        self.resource = True
        self.base = False
        offset=(25,20)
        super().__init__(gmap, x, y, offset, id_num) 
    def getSurf(self):
        return self.surf, self.rect     


UNIT_TYPE_TO_CLASS_MAP = {
      'HeavyTank': HeavyTank,
      'LightTank': LightTank,
      'Drone': Drone,
      'Truck': Truck,
    }
UNIT_MAP_KEY_TO_CLASS_MAP = {
      1: Truck,
      2: LightTank,
      3: HeavyTank,
      4: Drone,
}
UNIT_MAP_KEY_TO_TYPE_MAP = {
      1: 'Truck',
      2: 'LightTank',
      3: 'HeavyTank',
      4: 'Drone',
}