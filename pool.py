import pygame
import math

pygame.init()

# Screen
WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Advanced Pool Simulation")

clock = pygame.time.Clock()

# Colors
TABLE = (30, 100, 30)
WHITE = (255, 255, 255)
RED = (200, 50, 50)
BLACK = (20, 20, 20)

FRICTION = 0.985

POCKET_RADIUS = 18
BALL_RADIUS = 10

# Pocket positions
pockets = [
    (0, 0), (WIDTH//2, 0), (WIDTH, 0),
    (0, HEIGHT), (WIDTH//2, HEIGHT), (WIDTH, HEIGHT)
]

class Ball:
    def __init__(self, x, y, color=WHITE):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = BALL_RADIUS
        self.color = color
        self.active = True

    def move(self):
        if not self.active:
            return

        self.x += self.vx
        self.y += self.vy

        # Friction
        self.vx *= FRICTION
        self.vy *= FRICTION

        if abs(self.vx) < 0.01: self.vx = 0
        if abs(self.vy) < 0.01: self.vy = 0

        # Wall bounce
        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.vx *= -1
        if self.y <= self.radius or self.y >= HEIGHT - self.radius:
            self.vy *= -1

    def draw(self):
        if self.active:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def check_pocket(self):
        for px, py in pockets:
            dist = math.hypot(self.x - px, self.y - py)
            if dist < POCKET_RADIUS:
                self.active = False
                self.vx = self.vy = 0

def rotate(vx, vy, angle):
    return (
        vx * math.cos(angle) - vy * math.sin(angle),
        vx * math.sin(angle) + vy * math.cos(angle)
    )

def collide(b1, b2):
    if not b1.active or not b2.active:
        return

    dx = b2.x - b1.x
    dy = b2.y - b1.y
    dist = math.hypot(dx, dy)

    if dist < b1.radius + b2.radius:
        angle = math.atan2(dy, dx)

        v1 = rotate(b1.vx, b1.vy, angle)
        v2 = rotate(b2.vx, b2.vy, angle)

        # Elastic collision (equal mass)
        v1x, v2x = v2[0], v1[0]

        b1.vx, b1.vy = rotate(v1x, v1[1], -angle)
        b2.vx, b2.vy = rotate(v2x, v2[1], -angle)

        # Prevent sticking
        overlap = 0.5 * (b1.radius + b2.radius - dist + 1)
        b1.x -= overlap * math.cos(angle)
        b1.y -= overlap * math.sin(angle)
        b2.x += overlap * math.cos(angle)
        b2.y += overlap * math.sin(angle)

# Create balls
cue_ball = Ball(200, HEIGHT//2, WHITE)
balls = [
    cue_ball,
    Ball(600, HEIGHT//2, RED),
    Ball(630, HEIGHT//2 + 15, RED),
    Ball(630, HEIGHT//2 - 15, RED),
    Ball(660, HEIGHT//2, RED),
]

dragging = False
start_pos = (0, 0)

def all_stopped():
    return all(abs(b.vx) < 0.05 and abs(b.vy) < 0.05 for b in balls if b.active)

running = True
while running:
    clock.tick(60)
    screen.fill(TABLE)

    # Draw pockets
    for px, py in pockets:
        pygame.draw.circle(screen, BLACK, (px, py), POCKET_RADIUS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and all_stopped():
            dragging = True
            start_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONUP and dragging:
            dragging = False
            end_pos = pygame.mouse.get_pos()

            dx = start_pos[0] - end_pos[0]
            dy = start_pos[1] - end_pos[1]

            cue_ball.vx = dx * 0.12
            cue_ball.vy = dy * 0.12

    # Move balls
    for ball in balls:
        ball.move()
        ball.check_pocket()

    # Collisions
    for i in range(len(balls)):
        for j in range(i + 1, len(balls)):
            collide(balls[i], balls[j])

    # Draw balls
    for ball in balls:
        ball.draw()

    # Aim line
    if dragging:
        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.line(screen, WHITE, (int(cue_ball.x), int(cue_ball.y)), mouse_pos, 2)

    pygame.display.flip()

pygame.quit()