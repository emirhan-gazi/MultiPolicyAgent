import pygame
from pygame.locals import RLEACCEL
import numpy
import copy
from math import cos,sin,sqrt
from random import randint
from HumanInterface import HumanInterface

terrain_images = ["data/images/terrain_grass.png",
"data/images/terrain_mud.png",
"data/images/terrain_mountain.png",
"data/images/terrain_water.png"]

#animation_images = {"explosion": "data/images/explosion.png"}

TERRAIN_MAP = {
      'g': 0, #grass
      'd': 1, #dirt(mud)
      'm': 2, #mountain
      'w': 3, #water
    }

class Tile:
    def __init__(self, terrain, radius, position, coordinate):
        self.color = (0,0,0)
        self.terrain = terrain
        self.radius = radius
        self.position = position
        self.coordinate = coordinate
        self.unit = None
        self.resource = None
        self.base = None

        #self.animations['explosion'] = pygame.image.load("data/images/explosion.png").convert_alpha()
    def drawTile(self, surface):
        self.draw_terrain(surface)
        self.draw_hexagon(surface)
    def draw_terrain(self, surface):
        self.terrain_surf = pygame.image.load(terrain_images[TERRAIN_MAP[self.terrain]]).convert()
        self.terrain_surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.terrain_rect = self.terrain_surf.get_rect()
        self.terrain_rect.x, self.terrain_rect.y = self.position
        self.terrain_rect.x -= self.radius*sqrt(3)/2 + 4
        self.terrain_rect.y -= self.radius*sqrt(3)/2
        surface.blit(self.terrain_surf, self.terrain_rect)
    def draw_hexagon(self, surface):
        x,y=self.position
        y_step = self.radius*sqrt(3)/2
        points = []
        points.append((x+self.radius,y))
        points.append((x+self.radius/2,y+y_step))
        points.append((x-self.radius/2,y+y_step))
        points.append((x-self.radius,y))
        points.append((x-self.radius/2,y-y_step))
        points.append((x+self.radius/2,y-y_step))
        pygame.draw.polygon(surface, self.color, points, width=1)
    def getPosition(self):
        return self.position
    def getCoor(self):
        return self.coordinate
    def getTerrain(self):
        return self.terrain
    def setUnit(self,unit):
        self.unit = unit
    def unsetUnit(self):
        self.unit = None
    def hasUnit(self):
        return True if self.unit else False
    def getUnit(self):
        return self.unit
    def setResource(self,resource):
        self.resource = resource
    def unsetResource(self):
        self.resource = None
    def hasResource(self):
        return True if self.resource else False
    def getResource(self):
        return self.resource
    def setBase(self,base):
        self.base = base
    def unsetBase(self):
        self.base = None
    def hasBase(self):
        return True if self.base else False
    def getBase(self):
        return self.base
    def getTop(self):
        if self.hasUnit():
            return self.getUnit()
        elif self.hasBase():
            return self.getBase()
        else:
            return None

class GameMap:
    def __init__(self, gm):
        self.game = gm
        self.tiles = []
        self.r = 30
        self.x = self.r
        self.y = 2*self.r
        self.x_step = 3*self.r/2
        self.y_step = self.r*sqrt(3)/2
        self.hcs = 0
    def reset(self):
        self.tiles = []
    def generateMap(self, map_config):
        self.size_x = map_config['x']
        self.size_y = map_config['y']
        self.map_terrain = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        x = int(self.x_step)*self.size_x + self.x
        y = int(self.y_step)*self.size_y*2 + self.y + 40
        self.surface = pygame.Surface((x, y))
        self.surface.fill((255, 255, 255))
        self.map_available = False
        if "terrain" in map_config:
            self.map_available = True
        for i in range(self.size_y):
            for j in range(self.size_x):
                self.position = (self.x+j*self.x_step,self.y-(j%2)*self.y_step+2*i*self.y_step)
                terrain = 'g' if not self.map_available else map_config['terrain'][i][j]
                self.tiles.append(Tile(terrain,self.r,self.position,(i,j)))
                self.map_terrain[i,j] = TERRAIN_MAP[terrain]
        if self.hcs > 0:
            self.human_interface = HumanInterface((x,y),self.hcs)
            
    def processHumanMouseInput(self, pos):
        x, y = pos
        self.human_interface.buttonClickCheck(pos)
        unit = None
        tile = None
        tile = self.getTileFromPosition(x, y)
        self.human_interface.update(tile)
        self.drawHumanConsole()
    def drawHumanConsole(self):
        self.human_interface.setTeam(self.game.go_team)
        self.console_surface = self.human_interface.draw()
    def drawMap(self):
        for tile in self.tiles:
            tile.drawTile(self.surface)
        if self.hcs > 0:
            self.drawHumanConsole()
    def updateHumanConsole(self):
        if self.hcs > 0:
            self.human_interface.deClickButtons()
            self.drawHumanConsole()
    def getTileFromIndex(self,x,y):
        assert x < self.size_x and y < self.size_y and x >= 0 and y >= 0
        k = self.size_x*y+x
        return self.tiles[k]
    def getUnitFromIndex(self,x,y):
        assert x < self.size_x and y < self.size_y and x >= 0 and y >= 0
        k = self.size_x*y+x
        return self.tiles[k].getUnit()
    def getTileFromPosition(self,x,y):
        min_dist = 999
        tile = None
        for t in self.tiles:
            tx,ty = t.getPosition()
            dist = sqrt((tx-x)*(tx-x) + (ty-y)*(ty-y))
            if dist < min_dist and dist < self.r:
                min_dist = dist
                tile = t
        return tile
    def getUnitFromPosition(self,x,y):
        tile = self.getTileFromPosition(x, y)
        return tile.getTop() if tile else None
    def getState(self, all_ubr):
        self.updateHumanConsole()
        units, bases, resources = all_ubr
        score = numpy.zeros((len(bases)))
        for i in range(len(bases)):
            score[i] = bases[i].getScore()
        blue_units = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        red_units = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        blue_ids = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        red_ids = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        blue_hps = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        red_hps = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        blue_load = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        red_load = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        #blue_base = numpy.zeros((2),dtype=numpy.int32)
        #red_base = numpy.zeros((2),dtype=numpy.int32)
        blue_base = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        red_base = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        map_resources = numpy.zeros((self.size_y,self.size_x),dtype=numpy.int32)
        u1, u2 = units
        blue_alive = False
        red_alive = False
        for unit in u1:
            blue_units[unit.y_coor, unit.x_coor] = unit.getTag()[1]
            #blue_ids[unit.y_coor, unit.x_coor] = unit.id_num
            blue_hps[unit.y_coor, unit.x_coor] = unit.getHp()
            if unit.loadable:
                blue_load[unit.y_coor, unit.x_coor] = unit.load
        for unit in u2:
            red_units[unit.y_coor, unit.x_coor] = unit.getTag()[1]
            #red_ids[unit.y_coor, unit.x_coor] = unit.id_num
            red_hps[unit.y_coor, unit.x_coor] = unit.getHp()
            if unit.loadable:
                red_load[unit.y_coor, unit.x_coor] = unit.load
        y,x = bases[0].getCoor()
        blue_base[y,x] = 1
        y,x = bases[1].getCoor()
        red_base[y,x] = 1
        for res in resources:
            if res.on_map:
                map_resources[res.y_coor, res.x_coor] = 1
        state = {
            "score": score,
            "turn": self.game.turn,
            "max_turn": self.game.max_turn,
            "units": [blue_units, red_units],
            "hps": [blue_hps, red_hps],
            "bases": [blue_base, red_base],
            "resources": map_resources,
            "loads": [blue_load,red_load],
            "terrain": self.map_terrain
        }
        return state
    def getDistance(self,pos_1,pos_2):
        pos1 = copy.copy(pos_1)
        pos2 = copy.copy(pos_2)
        shift1 = (pos1[0]+1)//2
        shift2 = (pos2[0]+1)//2
        pos1[1] -= shift1
        pos2[1] -= shift2
        distance = (abs(pos1[0]-pos2[0]) + abs(pos1[1]-pos2[1]) + abs(pos1[0]+pos1[1]-pos2[0]-pos2[1]))//2
        return distance
