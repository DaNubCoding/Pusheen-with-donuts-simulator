# from fishhook import hook_cls, hook, orig

# @hook(int)
# def __truediv__(self, other):
#     return other and self / other or 0

# print(6 / 3)

from pygame.math import Vector2

print(Vector2(1, 1).angle_to(Vector2(-1, -1)))