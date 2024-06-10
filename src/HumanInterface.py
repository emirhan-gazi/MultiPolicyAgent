import pygame
from pygame.locals import RLEACCEL

BUTTONEVENT = pygame.USEREVENT + 3

button_paths = ["data/images/buttons_unclicked.png", \
    "data/images/buttons_clicked.png"]
action_images_paths = ["data/images/movement.png", \
    "data/images/attack.png", \
    "data/images/load.png", \
    "data/images/unload.png",
    "data/images/buy.png"]


class Button:
    def __init__(self, text,  pos, offset, b_color, size=(80,40),image=True):
        self.active = True
        self.image = image
        self.text = text
        self.button_state = 0
        self.x, self.y = [p+o for p,o in zip(pos,offset)]
        self.button_size = size
        if image:
            self.font = pygame.font.SysFont('Arial', 16)
            self.text_surf = self.font.render(self.text, True, (255, 255, 255))
            self.button_images = []
            self.button_images.append(pygame.image.load(button_paths[0]).convert_alpha())
            self.button_images.append(pygame.image.load(button_paths[1]).convert_alpha())
            self.button_images[0].blit(self.text_surf,(11, 13))
            self.button_images[1].blit(self.text_surf,(11, 13))
            self.surface = pygame.Surface(self.button_size)
            self.surface.fill(b_color)
            self.surface.blit(self.button_images[self.button_state],(0, 0))
        self.button_rect = pygame.Rect(self.x, self.y, self.button_size[0], self.button_size[1])
    def deactivate(self):
        self.active = False
    def activate(self):
        self.active = True
    def changeImage(self):
        if self.image:
            self.surface.blit(self.button_images[self.button_state],(0, 0))
    def getSurface(self):
        self.changeImage()
        return self.surface
    def isClickedMe(self, pos):
        if self.active:
            x, y = pos
            if self.button_rect.collidepoint(x, y):
                self.button_state = 1
                pygame.event.post(pygame.event.Event(BUTTONEVENT,{"key": self.text}))
            else:
                self.button_state = 0
    def deClick(self):
        self.button_state = 0

class HumanInterface:
    def __init__(self, offset, hcs):
        self.x, self.y = offset
        self.hcs = hcs
        self.go_team = 0
        self.font = pygame.font.SysFont('Arial', 24)
        self.font2 = pygame.font.SysFont('Arial', 16)
        self.action_images = []
        for im in action_images_paths:
            self.action_images.append(pygame.image.load(im).convert_alpha())
        self.console_diff_line = [(0,0),(0,self.y)]
        self.line_color = (0,0,0)
        self.color = [(10,203,237),(227,60,68)]
        self.console_color = (200, 200, 200)
        self.caption_position =(120,15)
        self.selection_unit_position = (50, 50)
        self.selection_action_position = (50, 130)
        self.selection_tile_position = (50, 180)
        self.action_list_position = (50, 330)
        self.approve_button_position = (50, 270)
        self.discard_button_position = (160, 270)
        self.execute_button_position = (270, 270)
        self.approve_button = Button("Approve",self.approve_button_position,(self.x,0),self.console_color)
        self.discard_button = Button("Discard",self.discard_button_position,(self.x,0),self.console_color)
        self.execute_button = Button("Execute",self.execute_button_position,(self.x,0),self.console_color)
        self.truck_button = Button("1",(70, 180),(self.x,0),self.console_color, size=(50,50))
        self.tankl_button = Button("2",(130, 180),(self.x,0),self.console_color, size=(50,50))
        self.tankh_button = Button("3",(190, 180),(self.x,0),self.console_color, size=(50,50))
        self.drone_button = Button("4",(250, 180),(self.x,0),self.console_color, size=(50,50))
        self.truck_button.deactivate()
        self.tankl_button.deactivate()
        self.tankh_button.deactivate()
        self.drone_button.deactivate()
        self.human_action = [[], [], [], 0, []]
        self.human_action_base = None
        self.human_action_base_position = None
        self.clearConsoleSelection()
        self.draw()

    def setTeam(self,team):
        self.go_team = team
        self.caption_surf = self.font.render('HumanAgent', True, self.color[self.go_team])
    def draw(self):
        self.console_surface = pygame.Surface((self.hcs, self.y))
        self.console_surface.fill(self.console_color)
        pygame.draw.line(self.console_surface,self.line_color,self.console_diff_line[0],self.console_diff_line[1],width=5)
        if not self.selected_unit:
            font_surf = self.font.render('Select Unit', True, self.line_color)
            self.selected_unit_surf.blit(font_surf,(50,40))
        if not self.selected_tile:
            if not (self.selected_unit and self.selected_unit.base):
                font_surf = self.font.render('Select Tile', True, self.line_color)
                self.selected_tile_surf.blit(font_surf,(50,0))
        self.console_surface.blit(self.caption_surf,self.caption_position)
        self.console_surface.blit(self.selected_unit_surf, self.selection_unit_position)
        self.console_surface.blit(self.selected_action_surf, self.selection_action_position)
        self.console_surface.blit(self.selected_tile_surf, self.selection_tile_position)
        self.console_surface.blit(self.action_list_surf,self.action_list_position)
        self.console_surface.blit(self.approve_button.getSurface(), self.approve_button_position)
        self.console_surface.blit(self.discard_button.getSurface(), self.discard_button_position)
        self.console_surface.blit(self.execute_button.getSurface(), self.execute_button_position)
        return self.console_surface
    def update(self,tile):
        unit = None
        if not self.selected_unit:
            unit = tile.getTop() if tile else None
        if unit:
            self.selectUnit(unit)
        elif self.selected_unit and self.selected_unit.getTag()[0] != "Base" and tile:
            if self.selected_unit.getCoor() == tile.getCoor() and tile.getBase() and self.selected_tile:
                self.selectUnit(tile.getBase())
                self.selected_tile = None
            else:
                self.selectTile(tile)
        self.action_list_surf = pygame.Surface((300, self.y-350))
        self.action_list_surf.fill((255, 255, 255))
        self.actionListVisualition()

    def actionListVisualition(self):
        i = 0
        for i in range(len(self.human_action[0])):
            self.action_list_surf.blit(self.human_action[0][i].surf,(10,10+60*i))
            su_coor = self.human_action[0][i].getCoor()
            font_surf = self.font2.render('@ '+str(su_coor[0])+' - '+str(su_coor[1]), True, self.line_color)
            self.action_list_surf.blit(font_surf,(60,10+60*i))
            self.action_list_surf.blit(self.action_images[self.human_action[4][i]],(120,10+60*i))
            self.action_list_surf.blit(self.human_action[2][i].terrain_surf,(170,10+60*i))
            if self.human_action[2][i].getBase():
                self.action_list_surf.blit(self.human_action[2][i].getBase().surf,(170,10+60*i))
            elif self.human_action[2][i].getUnit():
                if self.human_action[4][i] == 2:
                    self.action_list_surf.blit(self.human_action[2][i].getResource().surf,(170,10+60*i))
                else:
                    self.action_list_surf.blit(self.human_action[2][i].getUnit().surf,(170,10+60*i))
            elif self.human_action[2][i].getResource():
                self.action_list_surf.blit(self.human_action[2][i].getResource().surf,(170,10+60*i))
            su_coor = self.human_action[2][i].getCoor()
            font_surf = self.font2.render('@ '+str(su_coor[0])+' - '+str(su_coor[1]), True, self.line_color)
            self.action_list_surf.blit(font_surf,(230,10+60*i))
        if self.human_action[3]>0:
            if len(self.human_action[0]):
                i+=1
            images = [
                "data/images/truck_"+str(self.human_action_base.getTeam())+".png",
                "data/images/tankl_"+str(self.human_action_base.getTeam())+".png",
                "data/images/tankh_"+str(self.human_action_base.getTeam())+".png",
                "data/images/drone_"+str(self.human_action_base.getTeam())+".png"]
            self.action_list_surf.blit(self.human_action_base.surf,(10,10+60*i))
            su_coor = self.human_action_base.getCoor()
            font_surf = self.font2.render('@ '+str(su_coor[0])+' - '+str(su_coor[1]), True, self.line_color)
            self.action_list_surf.blit(font_surf,(60,10+60*i))
            self.action_list_surf.blit(self.action_images[4],(120,10+60*i))
            surf = pygame.transform.scale(pygame.image.load(images[self.human_action[3]-1]).convert_alpha(), (50, 50))
            self.action_list_surf.blit(surf,(170,10+60*i))
    def selectUnit(self, unit):
        self.selected_unit = unit
        self.selected_unit_surf = pygame.Surface((300, 80))
        self.selected_unit_surf.fill((255, 255, 255))
        su_coor = self.selected_unit.getCoor()
        font_surf = self.font.render('@ '+str(su_coor[0])+' - '+str(su_coor[1]), True, self.line_color)
        self.selected_unit_surf.blit(self.selected_unit.surf,(20,30))
        self.selected_unit_surf.blit(font_surf,(120,40))
        if self.selected_unit.getTag()[0] == "Base":
            self.selected_tile_surf = pygame.Surface((300, 80))
            self.selected_tile_surf.fill((255, 255, 255))
            self.selected_tile_surf.blit(pygame.transform.scale(pygame.image.load("data/images/truck_"+str(self.selected_unit.getTeam())+".png").convert_alpha(), (50, 50)),(20,0))
            self.selected_tile_surf.blit(pygame.transform.scale(pygame.image.load("data/images/tankl_"+str(self.selected_unit.getTeam())+".png").convert_alpha(), (50, 50)),(80,0))
            self.selected_tile_surf.blit(pygame.transform.scale(pygame.image.load("data/images/tankh_"+str(self.selected_unit.getTeam())+".png").convert_alpha(), (50, 50)),(140,0))
            self.selected_tile_surf.blit(pygame.transform.scale(pygame.image.load("data/images/drone_"+str(self.selected_unit.getTeam())+".png").convert_alpha(), (50, 50)),(200,0))
            self.truck_button.activate()
            self.tankl_button.activate()
            self.tankh_button.activate()
            self.drone_button.activate()
            self.selected_action_surf = pygame.Surface((300, 50))
            self.selected_action_surf.fill((255, 255, 255))
            self.selected_action_surf.blit(self.action_images[4],(30,0))
    def selectTile(self, tile):
        self.selected_tile = tile
        self.selected_tile_surf = pygame.Surface((300, 80))
        self.selected_tile_surf.fill((255, 255, 255))
        self.selected_action_surf = pygame.Surface((300, 50))
        self.selected_action_surf.fill((255, 255, 255))
        su_coor = self.selected_tile.getCoor()
        font_surf = self.font.render('@ '+str(su_coor[0])+' - '+str(su_coor[1]), True, self.line_color)
        self.selected_tile_surf.blit(self.selected_tile.terrain_surf,(50,0))
        self.selected_action = 0
        if self.selected_tile.getBase():
            self.selected_tile_surf.blit(self.selected_tile.getBase().surf,(55,0))
            if self.selected_tile.getBase().getCoor() == self.selected_unit.getCoor() and self.selected_tile.getBase().getTeam() == self.selected_unit.getTeam() and self.selected_unit.getTag()[0] == "Truck":
                self.selected_action = 3
        elif self.selected_tile.getUnit():
            if self.selected_tile.getResource() and self.selected_tile.getUnit().getCoor() == self.selected_unit.getCoor():
                self.selected_tile_surf.blit(self.selected_tile.getResource().surf,(55,0))
                self.selected_action = 2
            elif self.selected_tile.getUnit().getTeam() != self.selected_unit.getTeam():
                self.selected_tile_surf.blit(self.selected_tile.getUnit().surf,(55,0))
                self.selected_action = 1
            else:
                self.selected_tile_surf.blit(self.selected_tile.getUnit().surf,(55,0))
        elif self.selected_tile.getResource():
            self.selected_tile_surf.blit(self.selected_tile.getResource().surf,(55,0))
        self.selected_action_surf.blit(self.action_images[self.selected_action],(30,0))
        self.selected_tile_surf.blit(font_surf,(150,10))
        #self.approveAction()
    def approveAction(self, production=None):
        if production:
            self.human_action[3] = production
            self.human_action_base = self.selected_unit
        elif self.selected_unit and self.selected_tile and self.selected_unit.getTeam() is self.go_team:
            action = self.isAdjacent(self.selected_unit, self.selected_tile)
            other_unit = self.selected_tile.getUnit()
            if other_unit and self.selected_unit.getTeam() is not other_unit.getTeam():
                action = 0
            try:
                ind = self.human_action[0].index(self.selected_unit)
                del self.human_action[0][ind]
                del self.human_action[1][ind]
                del self.human_action[2][ind]
                del self.human_action[4][ind]
            except:
                None
            self.human_action[0].append(self.selected_unit)
            self.human_action[1].append(action)
            self.human_action[2].append(self.selected_tile)
            self.human_action[4].append(self.selected_action)
        self.clearConsoleSelection()
    def getConsoleAction(self):
        actions = [[], [], [], 0]
        for i in range(len(self.human_action[0])):
            actions[0].append(self.human_action[0][i].getCoor())
            actions[1].append(self.human_action[1][i])
            actions[2].append(self.human_action[2][i].getCoor())
        actions[3] = self.human_action[3]
        self.human_action = [[], [], [], 0, []]
        self.human_action_base = None
        self.clearConsoleSelection()
        return actions
    def clearConsoleSelection(self):
        self.selected_unit = None
        self.selected_tile = None
        self.selected_unit_surf = pygame.Surface((300, 80))
        self.selected_unit_surf.fill((255, 255, 255))
        self.selected_action_surf = pygame.Surface((300, 50))
        self.selected_action_surf.fill((255, 255, 255))
        self.selected_tile_surf = pygame.Surface((300, 80))
        self.selected_tile_surf.fill((255, 255, 255))
        self.action_list_surf = pygame.Surface((100, self.y-50))
        self.action_list_surf.fill((255, 255, 255))
        self.truck_button.deactivate()
        self.tankl_button.deactivate()
        self.tankh_button.deactivate()
        self.drone_button.deactivate()
        self.actionListVisualition()
        self.caption_surf = self.font.render('HumanAgent', True, self.line_color)
    def buttonClickCheck(self,pos):
        self.approve_button.isClickedMe(pos)
        self.discard_button.isClickedMe(pos)
        self.execute_button.isClickedMe(pos)
        self.truck_button.isClickedMe(pos)
        self.tankl_button.isClickedMe(pos)
        self.tankh_button.isClickedMe(pos)
        self.drone_button.isClickedMe(pos)
    def deClickButtons(self):
        self.approve_button.deClick()
        self.discard_button.deClick()
        self.execute_button.deClick()
        self.truck_button.deClick()
        self.tankl_button.deClick()
        self.tankh_button.deClick()
        self.drone_button.deClick()
    def isAdjacent(self,unit,tile):
        movement = [[(0,0),(-1,0),(0,-1),(1,0),(1,1),(0,1),(-1,1)],
            [(0,0),(-1,-1),(0,-1),(1,-1),(1,0),(0,1),(-1,0)]]
        y,x = unit.getCoor()
        pos_tile = list(tile.getCoor())
        adj_list = []
        for i in movement[x%2]:
            a,b = i
            adj_list.append([y+b,x+a])
        try: 
            return adj_list.index(pos_tile)
        except:
            return -1
