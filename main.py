from pygame.locals import QUIT, HWSURFACE, DOUBLEBUF, MOUSEBUTTONDOWN
from random import randint, randrange, choices, choice, uniform
from pygame.math import Vector2
from enum import Enum, auto
from numpy import arctan, degrees
from math import pi
import pygame
import time

VEC = type('CustomVec', (Vector2,), {"normalize": lambda self: self if not self.length() else VEC(Vector2(self).normalize())})
WIDTH, HEIGHT = 1024, 512
GRAVITY = 2600
SIZES = (15, 25)

inttup = lambda tup: tuple(map(int, tuple(tup)))

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), HWSURFACE | DOUBLEBUF)
clock = pygame.time.Clock()

font = pygame.font.Font("XiaolaiSC-Regular.ttf", 64)

pusheen_img = pygame.image.load("pusheen.png").convert_alpha()
pusheen_img = pygame.transform.smoothscale(pusheen_img, VEC(pusheen_img.get_size()) * 0.4)
pusheen_img_flipped = pygame.transform.flip(pusheen_img, True, False)
donut_img = pygame.image.load("donut.png").convert_alpha()

class Pusheen:
    def __init__(self, pos):
        self.pos = VEC(pos)
        self.vel = VEC(0, 0)
        self.image = pusheen_img
        self.size = VEC(self.image.get_size())
        self.rot = 0
        self.walking_max_time = uniform(0.5, 5)
        self.flip_max_time = uniform(1, 5)
        self.rot_max_time = uniform(0.5, 1.5)
        self.jump_max_time = uniform(3, 8)
        self.walking_time = self.flip_time = self.rot_time = self.jump_time = time.time()
        self.current_jump_height = 0
        self.walking = False
        self.behavior = self.aimless

    def update(self, dt):
        self.vel.y += GRAVITY * dt
        self.behavior()
        self.pos += self.vel * dt
        if self.vel.x > 0:
            self.image = pusheen_img_flipped
            if self.current_jump_height < -600:
                self.rot = -degrees(arctan(self.vel.y / self.vel.x)) * 0.8
        elif self.vel.x < 0:
            self.image = pusheen_img
            if self.current_jump_height < -600:
                self.rot = -degrees(arctan(self.vel.y / self.vel.x)) * 0.8
        
        if self.pos.x < self.size.x / 2:
            self.vel.x = 0
            self.pos.x = self.size.x / 2
        elif self.pos.x > WIDTH - self.size.x / 2:
            self.vel.x = 0
            self.pos.x = WIDTH - self.size.x / 2
        if self.pos.y < self.size.y / 2:
            self.vel.y = 0
            self.pos.y = self.size.y / 2
        elif self.pos.y > HEIGHT - self.size.y / 2:
            self.vel.y = 0
            self.pos.y = HEIGHT - self.size.y / 2
            self.rot = 0

    def draw(self, screen):
        rotated_img = pygame.transform.rotate(self.image, self.rot)
        screen.blit(rotated_img, self.pos - VEC(rotated_img.get_size()) / 2)

    def aimless(self):
        if time.time() - self.walking_time > self.walking_max_time:
            self.rot = 0
            if not self.walking:
                if self.pos.x - self.size.x // 2 <= WIDTH // 2:
                    self.vel.x = choice([200, 250, 300, 350, 400])
                else:
                    self.vel.x = choice([-200, -250, -300, -350, -400])
                if randint(0, 1):
                    self.current_jump_height = randint(-1600, -400)
                    self.vel.y = self.current_jump_height
                    self.vel.x *= 2
            else:
                self.vel.x = 0
            self.walking_time = time.time()
            self.walking = not self.walking
            self.walking_max_time = uniform(0.5, 5)
        if time.time() - self.flip_time > self.flip_max_time:
            if not self.walking:
                self.image = choice([pusheen_img, pusheen_img_flipped])
            self.flip_time = time.time()
            self.flip_max_time = uniform(1, 5)
        if time.time() - self.jump_time > self.jump_max_time:
            self.current_jump_height = randint(-1000, -400)
            self.vel.y = self.current_jump_height
            self.jump_time = time.time()
            self.jump_max_time = uniform(3, 8)

    def tempted(self):
        pass

    def chasing(self):
        pass

    def settled(self):
        pass

class Ball:
    instances = []
    regions = {}
    air_friction = 100

    def __init__(self, pos):
        __class__.instances.append(self)
        self.pos = VEC(pos)
        self.region = inttup(self.pos // (SIZES[1] * 2) + VEC(1, 1))
        if self.region in __class__.regions:
            __class__.regions[self.region].append(self)
        else:
            __class__.regions[self.region] = [self]
        self.vel = VEC(uniform(-600, 600), uniform(-400, 100))
        self.radius = randint(*SIZES)
        self.mass = self.radius ** 2 * pi
        self.orig_img = pygame.transform.scale(donut_img, (self.radius * 2, self.radius * 2))
        self.image = self.orig_img
        self.rot = 0

    def update(self, dt, mrel):
        mpos = VEC(pygame.mouse.get_pos())
        mstate = pygame.mouse.get_pressed()[0]

        if mpos.distance_to(self.pos) <= self.radius and mstate == True:
            self.pos = VEC(mpos.copy())
            self.vel = VEC(mrel.copy() * 100)
        else:
            self.vel.y += GRAVITY * dt
            self.vel -= self.vel.normalize() * self.air_friction * dt
            if -0.1 < self.vel.x < 0.1:
                self.vel.x = 0
            if -0.1 < self.vel.y < 0.1:
                self.vel.y = 0
        self.rot -= self.vel.x * dt
        self.pos += self.vel * dt

        self.group_to_regions()
        self.ball_collisions()
        self.wall_collisions(dt)

    def group_to_regions(self):
        new_region = inttup(self.pos // (SIZES[1] * 2) + VEC(1, 1))
        if self.region != new_region:
            if new_region in __class__.regions:
                __class__.regions[new_region].append(self)
            else:
                __class__.regions[new_region] = [self]
            __class__.regions[self.region].remove(self)
            self.region = new_region

    def ball_collisions(self):
        for x in range(self.region[0] - 1, self.region[0] + 2):
            for y in range(self.region[1] - 1, self.region[1] + 2):
                if (x, y) in __class__.regions:
                    for ball in __class__.regions[(x, y)]:
                        dist = self.pos.distance_to(ball.pos)
                        if dist <= self.radius + ball.radius and ball != self:
                            overlap = -(dist - self.radius - ball.radius) / 2
                            if dist:
                                self.pos += overlap * (self.pos - ball.pos) / dist
                                ball.pos -= overlap * (self.pos - ball.pos) / dist
                            self.vel *= 0.85
                            n = VEC(ball.pos - self.pos).normalize()
                            k = self.vel - ball.vel
                            p = 2.0 * (n * k) / (self.mass + ball.mass)
                            self.vel -= p * ball.mass * n
                            ball.vel += p * self.mass * n

    def wall_collisions(self, dt):
        if self.pos.x < self.radius:
            self.vel.x *= -0.8
            self.pos.x = self.radius
        elif self.pos.x > WIDTH - self.radius:
            self.vel.x *= -0.8
            self.pos.x = WIDTH - self.radius
        if self.pos.y < self.radius:
            self.vel.y *= -0.8
            self.pos.y = self.radius
        elif self.pos.y > HEIGHT - self.radius:
            self.vel.y *= 0 if self.vel.y <= GRAVITY * dt else -0.8
            self.pos.y = HEIGHT - self.radius

    def draw(self, screen):
        self.image = pygame.transform.rotate(self.orig_img, self.rot)
        screen.blit(self.image, self.pos - VEC(self.image.get_size()) // 2)

pusheen = Pusheen((WIDTH // 2, HEIGHT // 2))

running = True
while running:
    dt = clock.tick_busy_loop(144) / 1000
    num_of_confettis = round(25 * dt)
    mrel = VEC(pygame.mouse.get_rel())

    screen.fill((220, 220, 220))
    pygame.display.set_caption(f"Happy Birthday!!! | FPS: {round(clock.get_fps())}")

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == MOUSEBUTTONDOWN:
            mpos = VEC(pygame.mouse.get_pos())
            for ball in sum(Ball.regions.values(), []):
                if mpos.distance_to(ball.pos) <= ball.radius:
                    break
            else:
                if sum([len(balls) for balls in Ball.regions.values()]) < 20:
                    Ball(mpos)

    for region in sorted(Ball.regions.keys(), key=lambda region: region[1] * 100 + region[0], reverse=True):
        for ball in Ball.regions[region]:
            ball.update(dt, mrel)
    for ball in Ball.instances:
        ball.draw(screen)

    pusheen.update(dt)
    pusheen.draw(screen)

    pygame.display.flip()

pygame.quit()