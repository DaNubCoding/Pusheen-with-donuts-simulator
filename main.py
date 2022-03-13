from pygame.locals import QUIT, HWSURFACE, DOUBLEBUF, MOUSEBUTTONDOWN
from random import randint, randrange, choices, choice, uniform
from enum import Enum, auto
from numpy import sin
from math import pi
import pygame
import time

VEC = pygame.math.Vector2
WIDTH, HEIGHT = 1024, 512
GRAVITY = 0.2
colors = range(50, 255, 10)
sizes = (15, 25)

inttup = lambda tup: tuple(map(int, tuple(tup)))

def fill(surface, color):
    """Fill all pixels of the surface with color, preserve transparency."""
    w, h = surface.get_size()
    r, g, b = color
    for x in range(w):
        for y in range(h):
            a = surface.get_at((x, y))[3]
            surface.set_at((x, y), pygame.Color(r, g, b, a))

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), HWSURFACE | DOUBLEBUF)
clock = pygame.time.Clock()

font = pygame.font.Font("XiaolaiSC-Regular.ttf", 64)

star_img = pygame.image.load("star.png").convert_alpha()
triangle_img = pygame.image.load("triangle.png").convert_alpha()
cannon = pygame.image.load("confetti_cannon.png").convert_alpha()
cannon_reversed = pygame.transform.flip(cannon, True, False)
pusheen_img = pygame.image.load("pusheen.png").convert_alpha()
donut_img = pygame.image.load("donut.png").convert_alpha()

class Confetti:
    instances = {}
    air_friction = 0.855

    def __init__(self, pos, vel):
        self.color = tuple(randrange(0, 255, 5) for _ in range(3))
        self.shape = choices(["rectangle", "star", "circle", "triangle"], weights=[4, 3, 2, 2])[0]
        self.orig_img = self.create_image(self.shape)
        try:
            self.__class__.instances[inttup(self.size)].append(self)
        except KeyError:
            self.__class__.instances[inttup(self.size)] = []
        self.size = VEC(self.orig_img.get_size())
        self.image = self.orig_img.copy()
        self.rect = self.image.get_rect()
        self.pos = VEC(pos)
        self.vel = VEC(vel)
        self.rect.center = (self.pos.x, 0)
        self.angle = randint(0, 360)
        self.rot_speed = choice([-9, -8, -7, -6, -5, 5, 6, 7, 8, 9]) / 10
        self.rot = 0
        self.scale_counter = VEC(randint(0, 360), randint(0, 360))
        self.scale_speed = VEC(2, 6) / 100

    def create_image(self, shape):
        if shape == "rectangle":
            self.size = VEC(randint(6, 12), randint(6, 12)) * 0.6
            image = pygame.Surface(self.size, pygame.SRCALPHA)
            image.fill(self.color)
        elif shape == "star":
            self.size = VEC(randint(12, 24), randint(12, 24)) * 0.6
            image = pygame.transform.scale(star_img, self.size)
            fill(image, self.color)
        elif shape == "circle":
            self.size = VEC(randint(8, 16), randint(8, 16)) * 0.6
            image = pygame.Surface(self.size, pygame.SRCALPHA)
            pygame.draw.circle(image, self.color, self.size // 2, self.size.x // 2)
        elif shape == "triangle":
            self.size = VEC(randint(9, 18), randint(9, 18)) * 0.6
            image = pygame.transform.scale(triangle_img, self.size)
            fill(image, self.color)

        return image

    def update(self):
        self.vel.y += GRAVITY * dt
        self.vel *= self.air_friction + (48 - sum(self.size)) / 48 * 0.1
        self.pos += self.vel
        self.animate()
        self.kill(self.pos.y > HEIGHT or self.pos.x < -50 or self.pos.x > WIDTH + 50)

    def animate(self):
        self.rot += self.rot_speed
        self.scale_counter += self.scale_speed
        self.scale = (self.size.x / 2 * sin(self.scale_counter.x), self.size.y / 2 * sin(self.scale_counter.y)) + self.size * 0.75
        self.image = pygame.transform.rotate(pygame.transform.scale(self.orig_img, self.scale), self.rot)
        self.rect = self.image.get_rect(center=self.pos)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def kill(self, condition=True):
        if condition:
            self.__class__.instances[inttup(self.size)].remove(self)
            del self

class Pusheen:
    def __init__(self, pos):
        self.pos = VEC(pos)
        self.vel = VEC(0, 0)
        self.image = pusheen_img
        self.move = self.aimless

    def update(self):
        self.move()

    def draw(self, screen):
        screen.blit(self.image, self.pos)

    def aimless(self):
        pass

    def tempted(self):
        pass

    def chasing(self):
        pass

    def settled(self):
        pass

class Ball:
    instances = []
    regions = {}
    air_friction = 0.99

    def __init__(self, pos):
        __class__.instances.append(self)
        self.pos = VEC(pos)
        self.region = inttup(self.pos // (sizes[1] * 2) + VEC(1, 1))
        if self.region in __class__.regions:
            __class__.regions[self.region].append(self)
        else:
            __class__.regions[self.region] = [self]
        self.vel = VEC(uniform(-12, 12), uniform(-8, 2))
        self.radius = randint(*sizes)
        self.mass = self.radius ** 2 * pi
        self.orig_img = pygame.transform.scale(donut_img, (self.radius * 2, self.radius * 2))
        self.image = self.orig_img
        self.rot = 0

    def update(self):
        self.vel.y += GRAVITY * dt
        self.vel *= self.air_friction
        if -0.1 < self.vel.x < 0.1:
            self.vel.x = 0
        if -0.1 < self.vel.y < 0.1:
            self.vel.y = 0
        self.rot -= self.vel.x
        self.pos += self.vel * dt
        new_region = inttup(self.pos // (sizes[1] * 2) + VEC(1, 1))
        if self.region != new_region:
            if new_region in __class__.regions:
                __class__.regions[new_region].append(self)
            else:
                __class__.regions[new_region] = [self]
            __class__.regions[self.region].remove(self)
            self.region = new_region

        for x in range(self.region[0] - 1, self.region[0] + 2):
            for y in range(self.region[1] - 1, self.region[1] + 2):
                if (x, y) in __class__.regions:
                    for ball in __class__.regions[(x, y)]:
                        dist = self.pos.distance_to(ball.pos)
                        if dist <= self.radius + ball.radius and ball != self:
                            overlap = -(dist - self.radius - ball.radius) / 2
                            self.pos += overlap * (self.pos - ball.pos) / dist
                            ball.pos -= overlap * (self.pos - ball.pos) / dist
                            self.vel *= 0.85
                            n = (ball.pos - self.pos).normalize()
                            k = self.vel - ball.vel
                            p = 2.0 * (n * k) / (self.mass + ball.mass)
                            self.vel -= p * ball.mass * n
                            ball.vel += p * self.mass * n

        if self.pos.x < self.radius:
            self.vel.x *= -0.8
            self.pos.x = self.radius
        elif self.pos.x > WIDTH - self.radius:
            self.vel.x *= -0.8
            self.pos.x = WIDTH - self.radius
        if self.pos.y < self.radius:
            self.pos.y = self.radius
        elif self.pos.y > HEIGHT - self.radius:
            if self.vel.y <= GRAVITY:
                self.vel.y = 0
            else:
                self.vel.y *= -0.8
            self.pos.y = HEIGHT - self.radius
        
    def draw(self, screen):
        self.image = pygame.transform.rotate(self.orig_img, self.rot)
        screen.blit(self.image, self.pos - VEC(self.image.get_size()) // 2)

timer = time.time()

running = True
while running:
    dt = clock.tick_busy_loop(144) / 6
    num_of_confettis = round(25 * dt)

    screen.fill((220, 220, 220))
    current_confettis = sum([len(Confetti.instances[size]) for size in Confetti.instances])
    pygame.display.set_caption(f"Happy Birthday!!! | FPS: {round(clock.get_fps())} | Confettis: {current_confettis}")
    text_surf = font.render("妈妈生日快乐！！！", True, (200, 0, 0))
    surf_w, surf_h = text_surf.get_size()
    screen.blit(text_surf, (WIDTH // 2 - surf_w // 2, HEIGHT // 3 - surf_h // 2))

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == MOUSEBUTTONDOWN:
            mpos = VEC(pygame.mouse.get_pos())
            if sum([len(balls) for balls in Ball.regions.values()]) <= 10:
                Ball(mpos)

    if (time_elapsed := time.time() - timer) < 0.1 or 1 < time_elapsed < 1.1 or 2 < time_elapsed < 2.1:
        vels = zip(choices(range(0, 60), [-0.2 * (i - 30) ** 2 + 200 for i in range(0, 60)], k=num_of_confettis), choices(range(-70, -10), [-0.2 * (i + 40) ** 2 + 200 for i in range(-70, -10)], k=num_of_confettis))
        for vel in vels:
            direc = choice([-1, 1])
            Confetti((-10 if direc == -1 else WIDTH, HEIGHT // 2 + 220), VEC(vel[0] * -direc, vel[1]))
    if current_confettis <= 0:
        timer = time.time()

    for size in sorted(Confetti.instances, key = lambda size: size[0] + size[1]):
        for confetti in Confetti.instances[size]:
            confetti.update()
            confetti.draw(screen)
            
    for region in sorted(Ball.regions.keys(), key=lambda region: region[1] * 100 + region[0], reverse=True):
        for ball in Ball.regions[region]:
            ball.update()
    for ball in Ball.instances:
        ball.draw(screen)

    screen.blit(cannon, (-20, HEIGHT // 2 + 100))
    screen.blit(cannon_reversed, (WIDTH - cannon.get_width() + 20, HEIGHT // 2 + 100))

    pygame.display.flip()

pygame.quit()