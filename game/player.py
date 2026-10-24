"""Movimentação normalizada, com colisão independente por eixo."""
import pygame


class Player:
    def __init__(self):
        self.rect = pygame.Rect(590, 352, 22, 26)
        self.position = pygame.Vector2(self.rect.topleft)

    def update(self, keys, dt, walls):
        direction = pygame.Vector2(
            int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]))
        if direction.length_squared():
            direction = direction.normalize()
        # Passos pequenos evitam atravessar paredes mesmo com queda de FPS.
        movement = direction * 210 * min(dt, 0.05)
        for axis in (0, 1):
            self.position[axis] += movement[axis]
            if axis == 0:
                self.rect.x = round(self.position.x)
            else:
                self.rect.y = round(self.position.y)
            for wall in walls:
                if self.rect.colliderect(wall):
                    if axis == 0:
                        if movement.x > 0:
                            self.rect.right = wall.left
                        elif movement.x < 0:
                            self.rect.left = wall.right
                    else:
                        if movement.y > 0:
                            self.rect.bottom = wall.top
                        elif movement.y < 0:
                            self.rect.top = wall.bottom
            self.position[axis] = self.rect.x if axis == 0 else self.rect.y

    def draw(self, surface):
        pygame.draw.circle(surface, (24, 69, 87), self.rect.center, 21, 2)
        pygame.draw.rect(surface, (99, 222, 220), self.rect, border_radius=6)
        pygame.draw.line(surface, (230, 255, 255), self.rect.midtop, self.rect.center, 3)
