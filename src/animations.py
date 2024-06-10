import pygame
from pygame.locals import RLEACCEL

import random

class ShootAnimation(pygame.sprite.Sprite):
    def __init__(self,typ='Tank'):
        if typ=='Tank':
            self.surf = pygame.image.load("data/images/tank_fire.png").convert_alpha()
            #self.surf.set_colorkey((255, 255, 255), RLEACCEL)
            self.rect = self.surf.get_rect()
        self.active = False
    def isActive(self):
        return self.active

class ExplosionAnimation(pygame.sprite.Sprite):
    def __init__(self):
        self._surf = pygame.image.load("data/images/explosion.png").convert_alpha()
        #self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self._rect = self._surf.get_rect()
        self._active = False
        self._hit = True
    def setActive(self):
        self._active = True
    def resetActive(self):
        self._active = False
    def isActive(self):
        return self._active
    def setTarget(self,p):
        x,y = p
        self._rect.x = x+20
        self._rect.y = y+20
    def hit(self):
        self._hit = True
    def miss(self):
        self._hit = False
    def getSurf(self):
        if not self._hit:
            x = random.choice([20,-20])
            y = random.choice([20,-20])
            self._rect.x += x
            self._rect.y += y
        return(self._surf, self._rect)

