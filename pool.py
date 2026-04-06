import pygame
import math

pygame.init()

# Screen
WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("8-Ball Pool Simulation")

clock = pygame.time.Clock()

# Colors
TABLE = (30, 100, 30)
WHITE = (255, 255, 255)
RED = (200, 50, 50)
STRIPE = (255, 200, 200)
BLACK = (20, 20, 20)

FRICTION = 0.985
BALL_RADIUS = 10
POCKET_RADIUS = 18

# Pockets
pockets = [
    (0, 0), (WIDTH//2, 0), (WIDTH, 0),
    (0, HEIGHT), (WIDTH//2, HEIGHT), (WIDTH, HEIGHT)
]

# Game state
player_turn = 1
player_types = {1: None, 2: None}
ball_types = {}
pocketed_this_turn = []

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

        self.vx *= FRICTION
        self.vy *= FRICTION

        if abs(self.vx) < 0.01: self.vx = 0
        if abs(self.vy) < 0.01: self.vy = 0

        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.vx *= -1
        if self.y <= self.radius or self.y >= HEIGHT - self.radius:
            self.vy *= -1

    def draw(self):
        if self.active:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def check_pocket(self):
        for px, py in pockets:
            if math.hypot(self.x - px, self.y - py) < POCKET_RADIUS:
                self.active = False
                self.vx = self.vy = 0
                pocketed_this_turn.append(self)

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

        v1x, v2x = v2[0], v1[0]

        b1.vx, b1.vy = rotate(v1x, v1[1], -angle)
        b2.vx, b2.vy = rotate(v2x, v2[1], -angle)

        overlap = 0.5 * (b1.radius + b2.radius - dist + 1)
        b1.x -= overlap * math.cos(angle)
        b1.y -= overlap * math.sin(angle)
        b2.x += overlap * math.cos(angle)
        b2.y += overlap * math.sin(angle)

def draw_prediction_line(ball, mouse_pos):
    temp_x, temp_y = ball.x, ball.y

    dx = ball.x - mouse_pos[0]
    dy = ball.y - mouse_pos[1]

    vx = dx * 0.12
    vy = dy * 0.12

    path = []

    for _ in range(80):
        temp_x += vx
        temp_y += vy

        vx *= FRICTION
        vy *= FRICTION

        if temp_x <= BALL_RADIUS or temp_x >= WIDTH - BALL_RADIUS:
            vx *= -1
        if temp_y <= BALL_RADIUS or temp_y >= HEIGHT - BALL_RADIUS:
            vy *= -1

        path.append((int(temp_x), int(temp_y)))

    for i in range(0, len(path), 5):
        pygame.draw.circle(screen, WHITE, path[i], 2)

def all_stopped():
    return all(abs(b.vx) < 0.05 and abs(b.vy) < 0.05 for b in balls if b.active)

# Create balls
cue_ball = Ball(200, HEIGHT//2, WHITE)
balls = [cue_ball]

# Solids
for i in range(3):
    b = Ball(600 + i*30, HEIGHT//2 + i*15, RED)
    ball_types[b] = "solid"
    balls.append(b)

# Stripes
for i in range(3):
    b = Ball(600 + i*30, HEIGHT//2 - i*15, STRIPE)
    ball_types[b] = "stripe"
    balls.append(b)

# 8-ball
eight_ball = Ball(660, HEIGHT//2, BLACK)
ball_types[eight_ball] = "eight"
balls.append(eight_ball)

dragging = False
start_pos = (0, 0)

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

    # Move + pocket check
    for ball in balls:
        ball.move()
        ball.check_pocket()

    # Collisions
    for i in range(len(balls)):
        for j in range(i + 1, len(balls)):
            collide(balls[i], balls[j])

    # Turn logic
    if all_stopped() and not dragging:
        if len(pocketed_this_turn) > 0:
            for b in pocketed_this_turn:
                if b == cue_ball:
                    player_turn = 3 - player_turn

                elif ball_types.get(b) == "eight":
                    print(f"Player {player_turn} wins!")
                    running = False

                else:
                    if player_types[player_turn] is None:
                        player_types[player_turn] = ball_types[b]
                        player_types[3 - player_turn] = (
                            "stripe" if ball_types[b] == "solid" else "solid"
                        )

                    if ball_types[b] != player_types[player_turn]:
                        player_turn = 3 - player_turn
        else:
            player_turn = 3 - player_turn

        pocketed_this_turn.clear()

    # Draw balls
    for ball in balls:
        ball.draw()

    # Prediction line
    if dragging:
        mouse_pos = pygame.mouse.get_pos()
        draw_prediction_line(cue_ball, mouse_pos)

    pygame.display.flip()

pygame.quit()