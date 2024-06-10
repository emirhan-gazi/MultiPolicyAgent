import pygame
from pygame.locals import (
    RLEACCEL,
    K_TAB,
    K_QUOTEDBL,
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    K_RETURN,
    K_KP_ENTER,
    K_BACKSPACE,
    K_SPACE,
    KEYDOWN,
    MOUSEBUTTONDOWN,
    QUIT,
)
import yaml

from maps import GameMap
from HumanInterface import BUTTONEVENT
from units import *
from animations import ExplosionAnimation

import os, sys, gc, signal
import importlib

import copy
from PIL import Image
import time

class Game:
    def __import_agents(self,agents):
        self.has_human = False
        self.agents_classes = []
        game_path = os.path.abspath(__file__)
        dir_path = os.path.dirname(game_path)
        dir_path = os.path.join(dir_path,'agents')
        files_in_dir = [f[:-3] for f in os.listdir(dir_path)
                        if f.endswith('.py') and f != '__init__.py']
        self.human_class = False
        for ag in agents:
            if ag == None:
                self.agents_classes.append(None)
            elif ag in files_in_dir:
                mod = importlib.import_module('agents.'+ag)
                self.agents_classes.append(getattr(mod, ag))
                if ag == "HumanAgent":  # any other human class??
                    self.human_class = getattr(mod, ag)
                    self.has_human = True
            else:
                print('Agent "'+ag+'" could not be found!')
                exit()
    def _agent_timeout_handler(self, signum, frame):
        raise Exception("Agent Timeout")
    def __init__(self,args,agents):
        print(args)
        self.__import_agents(agents)
        self.agents = []
        signal.signal(signal.SIGALRM, self._agent_timeout_handler)
        self.config = None
        self.render = args.render or args.gif or args.img
        self.gif = args.gif
        self.img = args.img
        try:
            with open('data/config/'+args.map+'.yaml') as file:
                self.config = yaml.load(file, Loader=yaml.FullLoader)
        except:
            print('Map Could Not be Found!')
            exit()
        pygame.init()
        self.go_team = 0
        self.turn_timer = self.config['turn_timer']
        self.GAMESTEP = pygame.USEREVENT + 1
        if self.render: pygame.time.set_timer(self.GAMESTEP, self.turn_timer)
        self.ANIMATIONSTEP = pygame.USEREVENT + 2
        if self.render: pygame.time.set_timer(self.ANIMATIONSTEP, 10)
        self.font = pygame.font.SysFont(None, 24)

        self.gmap = GameMap(self)
        self.map_x = self.config['map']['x']
        self.map_y = self.config['map']['y']
        x = int(self.gmap.x_step)*self.map_x + self.gmap.x
        y = int(self.gmap.y_step)*self.map_y*2 + self.gmap.y +40

        self.human_console_size = 0
        if self.has_human:
            self.human_console_size = 400
        self.gmap.hcs = self.human_console_size
        self.SCREEN_WIDTH = x
        self.SCREEN_HEIGHT = y

        if self.render: self.screen = pygame.display.set_mode((self.SCREEN_WIDTH + self.human_console_size, self.SCREEN_HEIGHT))
        if self.render: self.explosion_animation = ExplosionAnimation()
        self.max_turn = self.config['max_turn']
        self.reset()

    def step(self, action):
        #step cadet
        location, movement, target, train = action
        self.__step(location, movement, target, train)
        while(len(self.move_animations) or len(self.shoot_animations)):
            event = pygame.event.poll()
            if event.type == self.ANIMATIONSTEP:
                self.handleAnimations()
                self.renderGame()
        self.__endTurn()
        half_state = self.gmap.getState(self.all_ubr)
        #step ai

        action = self.agents[self.go_team].action(half_state)
        
        location, movement, target, train = action
        self.__step(location, movement, target, train)
        while(len(self.move_animations) or len(self.shoot_animations)):
            event = pygame.event.poll()
            if event.type == self.ANIMATIONSTEP:
                self.handleAnimations()
                self.renderGame()
        self.__endTurn()
        next_state = self.gmap.getState(self.all_ubr)
        reward = self.bases[self.go_team].getScore() - self.bases[(self.go_team+1)%2].getScore()
        done = True if self.turn>self.max_turn else False
        return next_state,reward,done

    def __step(self, location, action, target, train):
        #if(len(action)==len(self.units[self.go_team]) and len(target)==len(self.units[self.go_team])):
        #print("Now:",self.go_team)
        #for a,b,c in zip(location,action,target):
        #    print("   ",a,b,c)
        #print("Train",train)
        #print("-----")
        for i in range(len(action)):
            current_units = self.units[self.go_team]
            active_unit = None
            for u in current_units:
                if u.getCoor() == location[i]:
                    active_unit = u
                    break
            #print(active_unit.getTag()[0],ids[i],action[i],target[i])
            result = active_unit.moveAction(action[i],target[i])
            if self.render:
                if action[i] == 0:
                    if not active_unit.loadable:
                        self.shoot_animations.append([active_unit,target[i],result])
                else:
                    self.move_animations.append(active_unit)
        self.bases[self.go_team].trainUnit(train)
        self.go_team += 1
        self.turn += self.go_team//2
        self.go_team %= 2
    def __endTurn(self):
        current_units = self.units[self.go_team]
        for u in current_units:
            if not u.alive:
                u.death_timer -= 1
                if u.death_timer == 0:
                    u.removeUnit()
                    self.units[self.go_team].remove(u)

    def reset(self, agents=None, switch_sides=False, reload_agents=False):
        self.gmap.reset()
        self.gmap.generateMap(self.config['map'])
        if self.render:
            self.gmap.drawMap()
        self.running = True
        self.go_team = 0
        self.turn = 1
        self.game_over = False
        self.moves = []
        self.move_animations = []
        self.shoot_animations = []
        self.counter = 0
        self.units = [[],[]]
        self.bases = []
        self.resources = []

        self.id_num = 0

        #Blue
        blue = self.config['blue']
        base = blue['base']
        self.bases.append(Base(self.gmap, base['x'], base['y'], team=0, id_num=self.idGeneretor()))
        for u in blue['units']:
            self.units[0].append(UNIT_TYPE_TO_CLASS_MAP[u['type']](self.gmap, u['x'], u['y'], team=0, id_num=self.idGeneretor()))

        #Red
        red = self.config['red']
        base = red['base']
        self.bases.append(Base(self.gmap, base['x'], base['y'], team=1, id_num=self.idGeneretor()))
        for u in red['units']:
            self.units[1].append(UNIT_TYPE_TO_CLASS_MAP[u['type']](self.gmap, u['x'], u['y'], team=1, id_num=self.idGeneretor()))

        #Resources
        for resource in self.config['resources']:
            self.resources.append(Resource(self.gmap,resource['x'], resource['y'], id_num=self.idGeneretor()))
        self.all_ubr = [self.units, self.bases, self.resources]
        self.num_of_units = len(self.units[0])
        self.state_space = [numpy.zeros([2]), numpy.zeros([self.map_x, self.map_y])]
        self.action_space = [numpy.zeros([self.num_of_units, 2])]

        if switch_sides:
            self.agents_classes[0], self.agents_classes[1] = self.agents_classes[1], self.agents_classes[0]
            self.agents[0], self.agents[1] = self.agents[1], self.agents[0]
        if agents or reload_agents or not len(self.agents):
            self.agents = []
            if agents:
                self.__import_agents(agents)
            for i in range(2):
                if self.agents_classes[i] == None:
                    self.agents.append(None)
                else:
                    self.agents.append(self.agents_classes[i](i,self.num_of_units))
        state = self.gmap.getState(self.all_ubr)
        return state
        #print(gc.get_count())
        #gc.collect()
        #print(gc.get_count())
    def sim(self):
        terminate = False
        ss = False
        ss_list = []
        #pygame.event.get()
        move_animation = False
        shoot_animation = False
        while self.running and self.turn <= self.max_turn:
            event = pygame.event.poll()
            #print(event)
            # input()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                    terminate = True
                elif event.key == K_TAB:  #debug key
                    None
                elif event.key == K_QUOTEDBL:  #debug key
                    None
                elif self.has_human and (event.key == K_RETURN or event.key == K_KP_ENTER):
                    self.gmap.human_interface.approveAction()
                elif self.has_human and event.key == K_BACKSPACE:
                    self.gmap.human_interface.clearConsoleSelection()
                elif self.has_human and event.key == K_SPACE:
                    action = self.gmap.human_interface.getConsoleAction()
                    location, movement, target, train = action
                    self.moves.append([location, movement, target, train])
                    self.__step(location, movement, target, train)
                    self.__endTurn()
            elif self.has_human and event.type == pygame.MOUSEBUTTONDOWN and type(self.agents[self.go_team]) is self.human_class:
                self.gmap.processHumanMouseInput(pygame.mouse.get_pos())
            elif event.type == BUTTONEVENT:
                if event.key == "Approve":
                    self.gmap.human_interface.approveAction()
                elif event.key == "Discard":
                    self.gmap.human_interface.clearConsoleSelection()
                elif event.key == "Execute":
                    action = self.gmap.human_interface.getConsoleAction()
                    location, movement, target, train = action
                    self.moves.append([location, movement, target, train])
                    self.__step(location, movement, target, train)
                    self.__endTurn()
                else:
                    self.gmap.human_interface.approveAction(production=int(event.key))
            elif event.type == self.ANIMATIONSTEP:
                if(len(self.move_animations) or len(self.shoot_animations)):
                    self.handleAnimations()
            elif event.type == self.GAMESTEP or not self.render:
                if(len(self.move_animations) or len(self.shoot_animations)):
                    #self.handleAnimations(force=True)
                    continue
                ss = False
                self.gmap.turn = self.turn
                self.gmap.go_team = self.go_team
                self.gmap.max_turn = self.max_turn
                state = self.gmap.getState(self.all_ubr)
                if not self.game_over and not type(self.agents[self.go_team]) is self.human_class:
                    signal.alarm(2)
                    action = self.agents[self.go_team].action(state)
                    # try:
                    # except:
                    #     # print("Agent did not return action in time")
                    #     action = [[], [], [], 0]
                    #     raise
                    signal.alarm(0)
                    location, movement, target, train = action
                    self.moves.append([location, movement, target, train])
                    self.__step(location, movement, target, train)
                    self.__endTurn()
            elif event.type == QUIT:
                self.running = False
                terminate = True
            if self.turn > self.max_turn:
                self.game_over = True
            self.renderGame()
            if (self.gif or self.img) and not ss:
                ss = True
                pil_string_image = pygame.image.tostring(self.screen, "RGB", False)
                pil_image = Image.frombytes('RGB', self.screen.get_size(), pil_string_image, 'raw')
                ss_list.append(pil_image)
                if self.img:
                    pygame.image.save(self.screen, "screenshot"+str(self.turn)+"_"+str(self.go_team)+".jpg")
            #printProgressBar(self.turn, self.max_turn, prefix = 'Progress:', suffix = 'Complete', length = 50)
            print('\rProgress: {}%'.format(int((self.turn/self.max_turn)*100)), end='\r')
        if self.gif:
            ss_list[0].save(fp="game.gif", format='GIF', append_images=ss_list, save_all=True, duration=200, loop=0)
        return terminate, self.all_ubr[1][0].getScore(), self.all_ubr[1][1].getScore()

    def idGeneretor(self):
        self.id_num += 1
        return self.id_num
    def handleAnimations(self, force=False):
        #print(len(self.move_animations),len(self.shoot_animations))
        if not self.render:
            force = True
        if force:
            self.shoot_animations = []
        if len(self.move_animations):
            for u in self.move_animations:
                u.moveAnimation(force=force)
                if not u.has_animation:
                    self.move_animations.remove(u)
        elif len(self.shoot_animations):
            shoot = self.shoot_animations[0]
            #[active_unit,target[i],result]
            #print(shoot[0].getCoor(),shoot[1],shoot[2])
            if not shoot[0].getAnimation():
                shoot[0].setAnimation("shoot")

                self.renderGame()
                time.sleep(0.1)#1/(self.turn_timer*4))

                if shoot[1]:
                    self.explosion_animation.setActive()
                    x,y = shoot[1]
                    rect = self.gmap.getTileFromIndex(y,x).terrain_rect
                    self.explosion_animation.setTarget((rect.x, rect.y))
                    if shoot[2]:
                        self.explosion_animation.hit()
                    else:
                        self.explosion_animation.miss()

                self.renderGame()
                time.sleep(0.1)#1/(self.turn_timer*4))

                self.explosion_animation.resetActive()

                self.renderGame()
                time.sleep(0.1)#1/(self.turn_timer*4))

                shoot[0].resetAnimation("shoot")

                self.renderGame()
                time.sleep(0.1)#1/(self.turn_timer*4))

                self.shoot_animations.pop(0)
                
    def renderGame(self):
        if self.render:
            self.screen.fill((200, 200, 255))
            self.screen.blit(self.gmap.surface, (0, 0))
            if self.has_human:
                self.screen.blit(self.gmap.console_surface,(self.SCREEN_WIDTH, 0))
            u1, u2 = self.units
            for r in self.resources:
                #not self.gmap.getTileFromIndex(r.x_coor, r.y_coor).hasUnit() and \
                if self.gmap.getTileFromIndex(r.x_coor, r.y_coor).hasResource():
                        self.screen.blit(r.surf, r.rect)
            for u in u1 + u2:
                surfs = u.getSurf()
                for s, r in surfs:
                    self.screen.blit(s, r)
            for b in self.bases:
                if not self.gmap.getTileFromIndex(b.x_coor, b.y_coor).hasUnit() and \
                    self.gmap.getTileFromIndex(b.x_coor, b.y_coor).hasBase():
                        self.screen.blit(b.surf, b.rect)
            if self.explosion_animation.isActive():
                s, r = self.explosion_animation.getSurf()
                self.screen.blit(s, r)
            color = (227, 60, 68) if self.go_team else (10, 203, 237)
            turn_surf = self.font.render('Turn: '+str(self.turn), True, color)
            self.screen.blit(turn_surf, (self.SCREEN_WIDTH-100, self.SCREEN_HEIGHT-20))
            if self.game_over:
                game_over_string = 'Game Over'
                game_over_surf = self.font.render(game_over_string, True, (0,0,0))
                self.screen.blit(game_over_surf, (self.SCREEN_WIDTH-100, self.SCREEN_HEIGHT-40))
            score_string = 'Blue: ' + str(self.all_ubr[1][0].getScore()) \
                + '   Red: ' + str(self.all_ubr[1][1].getScore())
            score_surf = self.font.render(score_string, True, (0,0,0))
            self.screen.blit(score_surf, (20, self.SCREEN_HEIGHT-20))
            #pygame.image.save(self.screen, "screenshot"+str(self.turn)+"_"+str(self.go_team)+".jpg")
            pygame.display.flip()


