import pygame
import math

pygame.init()

# Screen
WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("8-Ball Pool Simulation")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.SysFont("Arial", 20)
big_font = pygame.font.SysFont("Arial", 40)

# Colors
TABLE = (30, 100, 30)
WHITE = (255, 255, 255)
RED = (200, 50, 50)
STRIPE = (255, 200, 200)
BLACK = (20, 20, 20)
YELLOW = (255, 255, 0)

# Constants
FRICTION = 0.985
BALL_RADIUS = 14
POCKET_RADIUS = 28  # Made slightly larger for better gameplay

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
winner = None
turn_processed = True # Start true so logic doesn't trigger at launch

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
        if not self.active: return
        self.x += self.vx
        self.y += self.vy
        self.vx *= FRICTION
        self.vy *= FRICTION
        if abs(self.vx) < 0.01: self.vx = 0
        if abs(self.vy) < 0.01: self.vy = 0

        # Wall bounce
        if self.x <= self.radius:
            self.x = self.radius
            self.vx *= -1
        elif self.x >= WIDTH - self.radius:
            self.x = WIDTH - self.radius
            self.vx *= -1
            
        if self.y <= self.radius:
            self.y = self.radius
            self.vy *= -1
        elif self.y >= HEIGHT - self.radius:
            self.y = HEIGHT - self.radius
            self.vy *= -1

    def draw(self):
        if self.active:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def check_pocket(self):
        if not self.active: return
        for px, py in pockets:
            if math.hypot(self.x - px, self.y - py) < POCKET_RADIUS:
                self.active = False
                self.vx = self.vy = 0
                pocketed_this_turn.append(self)

def rotate(vx, vy, angle):
    return (vx * math.cos(angle) - vy * math.sin(angle), vx * math.sin(angle) + vy * math.cos(angle))

def collide(b1, b2):
    if not b1.active or not b2.active: return
    dx, dy = b2.x - b1.x, b2.y - b1.y
    dist = math.hypot(dx, dy)
    if dist < b1.radius + b2.radius:
        angle = math.atan2(dy, dx)
        v1 = rotate(b1.vx, b1.vy, angle)
        v2 = rotate(b2.vx, b2.vy, angle)
        v1x, v2x = v2[0], v1[0]
        b1.vx, b1.vy = rotate(v1x, v1[1], -angle)
        b2.vx, b2.vy = rotate(v2x, v2[1], -angle)
        # Prevent sticking
        overlap = (b1.radius + b2.radius - dist + 1) * 0.5
        b1.x -= overlap * math.cos(angle)
        b1.y -= overlap * math.sin(angle)
        b2.x += overlap * math.cos(angle)
        b2.y += overlap * math.sin(angle)

def draw_prediction(ball, mouse_pos):
    temp_x, temp_y = ball.x, ball.y
    # Fixed physics: vector from ball to mouse
    dx, dy = mouse_pos[0] - ball.x, mouse_pos[1] - ball.y
    vx, vy = dx * 0.05, dy * 0.05 # Scaled for control
    
    collision_point = None
    for _ in range(100):
        temp_x += vx
        temp_y += vy
        vx *= FRICTION
        vy *= FRICTION
        if temp_x <= BALL_RADIUS or temp_x >= WIDTH - BALL_RADIUS: vx *= -1
        if temp_y <= BALL_RADIUS or temp_y >= HEIGHT - BALL_RADIUS: vy *= -1
        
        if collision_point is None:
            for b in balls:
                if b != ball and b.active:
                    if math.hypot(temp_x - b.x, temp_y - b.y) < BALL_RADIUS * 2:
                        collision_point = (int(temp_x), int(temp_y))
        pygame.draw.circle(screen, WHITE, (int(temp_x), int(temp_y)), 2)
    
    if collision_point:
        pygame.draw.circle(screen, YELLOW, collision_point, 6)

def all_stopped():
    return all(abs(b.vx) < 0.1 and abs(b.vy) < 0.1 for b in balls if b.active)

def draw_ui():
    turn_color = YELLOW if winner is None else WHITE
    screen.blit(font.render(f"Player {player_turn}'s Turn", True, turn_color), (15, 15))
    p1_type = player_types[1] if player_types[1] else "Not set"
    p2_type = player_types[2] if player_types[2] else "Not set"
    screen.blit(font.render(f"P1: {p1_type}", True, WHITE), (15, 45))
    screen.blit(font.render(f"P2: {p2_type}", True, WHITE), (15, 70))
    if winner is None:
        screen.blit(font.render("Drag from ball to aim", True, WHITE), (15, HEIGHT - 35))

# Setup
# --- SETUP ---

import random

# Create cue ball FIRST
cue_ball = Ball(200, HEIGHT//2, WHITE)

# Initialize balls list properly
balls = [cue_ball]

# --- REALISTIC TRIANGLE RACK (15 BALLS) ---


start_x = 650
start_y = HEIGHT // 2
spacing = BALL_RADIUS * 2 + 2

rack_positions = []

# Generate triangle (5 rows)
for row in range(5):
    for col in range(row + 1):
        x = start_x + row * spacing
        y = start_y - (row * spacing / 2) + col * spacing
        rack_positions.append((x, y))

# Create list WITHOUT 8-ball first
types_list = ["solid"] * 7 + ["stripe"] * 7
random.shuffle(types_list)

# Insert 8-ball EXACTLY in center (index 10)
types_list.insert(4, "eight")

# Now assign balls
for i, pos in enumerate(rack_positions):
    t = types_list[i]

    if t == "solid":
        b = Ball(pos[0], pos[1], RED)
    elif t == "stripe":
        b = Ball(pos[0], pos[1], STRIPE)
    else:
        b = Ball(pos[0], pos[1], BLACK)

    ball_types[b] = t
    balls.append(b)

dragging = False
running = True

while running:
    clock.tick(60)
    screen.fill(TABLE)

    for px, py in pockets:
        pygame.draw.circle(screen, (10,10,10), (px, py), POCKET_RADIUS)
        pygame.draw.circle(screen, BLACK, (px, py), POCKET_RADIUS - 4)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if winner is None and all_stopped():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if math.hypot(event.pos[0] - cue_ball.x, event.pos[1] - cue_ball.y) < BALL_RADIUS * 2:
                    dragging = True
            if event.type == pygame.MOUSEBUTTONUP and dragging:
                dragging = False
                turn_processed = False
                dx, dy = event.pos[0] - cue_ball.x, event.pos[1] - cue_ball.y
                cue_ball.vx, cue_ball.vy = dx * 0.12, dy * 0.12 # Apply force

    if winner is None:
        for ball in balls:
            ball.move()
            ball.check_pocket()
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                collide(balls[i], balls[j])

        # --- REPAIRED TURN LOGIC ---
        if all_stopped() and not dragging and not turn_processed:
            scored_own = False
            foul = False
            
            if len(pocketed_this_turn) > 0:
                for b in pocketed_this_turn:
                    if b == cue_ball:
                        foul = True
                        b.active = True # Respawn cue ball
                        b.x, b.y, b.vx, b.vy = 200, HEIGHT//2, 0, 0
                    elif ball_types.get(b) == "eight":
                        winner = player_turn
                    else:
                        # Assign sets if first time
                        if player_types[player_turn] is None:
                            player_types[player_turn] = ball_types[b]
                            player_types[3 - player_turn] = "stripe" if ball_types[b] == "solid" else "solid"
                        
                        if ball_types.get(b) == player_types[player_turn]:
                            scored_own = True

            # If you didn't score your own ball or you fouled, swap turns
            if foul or not scored_own:
                player_turn = 3 - player_turn
            
            pocketed_this_turn.clear()
            turn_processed = True

    for ball in balls: ball.draw()
    if dragging and winner is None: draw_prediction(cue_ball, pygame.mouse.get_pos())
    draw_ui()
    if winner:
        screen.blit(big_font.render(f"PLAYER {winner} WINS!", True, YELLOW), (WIDTH//2 - 160, HEIGHT//2 - 25))
    pygame.display.flip()

pygame.quit()