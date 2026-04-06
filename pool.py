import pygame
import math

# Initialize
pygame.init()
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pool Simulation")

clock = pygame.time.Clock()

# Colors
GREEN = (40, 120, 40)
WHITE = (255, 255, 255)
RED = (200, 50, 50)
BLACK = (0, 0, 0)

FRICTION = 0.99

class Ball:
    def __init__(self, x, y, radius=10, color=WHITE):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = radius
        self.color = color

    def move(self):
        self.x += self.vx
        self.y += self.vy

        # Apply friction
        self.vx *= FRICTION
        self.vy *= FRICTION

        # Stop tiny movement
        if abs(self.vx) < 0.01: self.vx = 0
        if abs(self.vy) < 0.01: self.vy = 0

        # Wall collisions
        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.vx *= -1
        if self.y <= self.radius or self.y >= HEIGHT - self.radius:
            self.vy *= -1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

def collide(ball1, ball2):
    dx = ball2.x - ball1.x
    dy = ball2.y - ball1.y
    dist = math.hypot(dx, dy)

    if dist < ball1.radius + ball2.radius:
        angle = math.atan2(dy, dx)

        # Rotate velocities
        v1 = rotate(ball1.vx, ball1.vy, angle)
        v2 = rotate(ball2.vx, ball2.vy, angle)

        # Swap x velocities (equal mass elastic collision)
        v1x, v2x = v2[0], v1[0]

        # Rotate back
        ball1.vx, ball1.vy = rotate(v1x, v1[1], -angle)
        ball2.vx, ball2.vy = rotate(v2x, v2[1], -angle)

        # Separate balls to prevent sticking
        overlap = 0.5 * (ball1.radius + ball2.radius - dist + 1)
        ball1.x -= overlap * math.cos(angle)
        ball1.y -= overlap * math.sin(angle)
        ball2.x += overlap * math.cos(angle)
        ball2.y += overlap * math.sin(angle)

def rotate(vx, vy, angle):
    return (
        vx * math.cos(angle) - vy * math.sin(angle),
        vx * math.sin(angle) + vy * math.cos(angle)
    )

# Create balls
cue_ball = Ball(200, 200, color=WHITE)
balls = [
    cue_ball,
    Ball(500, 200, color=RED),
    Ball(530, 220, color=RED),
    Ball(530, 180, color=RED),
]

dragging = False
start_pos = (0, 0)

running = True
while running:
    clock.tick(60)
    screen.fill(GREEN)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            dragging = True
            start_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONUP:
            dragging = False
            end_pos = pygame.mouse.get_pos()

            dx = start_pos[0] - end_pos[0]
            dy = start_pos[1] - end_pos[1]

            cue_ball.vx = dx * 0.1
            cue_ball.vy = dy * 0.1

    # Move balls
    for ball in balls:
        ball.move()

    # Handle collisions
    for i in range(len(balls)):
        for j in range(i + 1, len(balls)):
            collide(balls[i], balls[j])

    # Draw balls
    for ball in balls:
        ball.draw(screen)

    # Draw aiming line
    if dragging:
        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.line(screen, BLACK, cue_ball_pos := (int(cue_ball.x), int(cue_ball.y)), mouse_pos, 2)

    pygame.display.flip()

pygame.quit()