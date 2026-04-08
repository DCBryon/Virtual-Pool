import pygame
import math
import random

pygame.init()
pygame.mixer.init()


hit_sound = pygame.mixer.Sound("Pool Ball Hit Sound Effect - Edit.wav")

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
PINK = (255, 150, 150)
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

# ROTATE VECTOR (useless)
def rotate(vx, vy, angle):
    return (vx * math.cos(angle) - vy * math.sin(angle), vx * math.sin(angle) + vy * math.cos(angle))

def collide_sound(relVel):
    impact = abs(relVel)
    volume = min(impact * 0.05, 1.0) * random.uniform(0.7, 1.0)
    hit_sound.set_volume(volume)
    hit_sound.play()

def collide(b1, b2):
    if not b1.active or not b2.active:
        return

    dx = b2.x - b1.x
    dy = b2.y - b1.y
    dist = math.hypot(dx, dy)

    if dist == 0:
        return

    if dist < b1.radius + b2.radius:

        # Normal vector
        nx = dx / dist
        ny = dy / dist

        # --- ONLY collide if moving toward each other ---
        relVel = (b2.vx - b1.vx) * nx + (b2.vy - b1.vy) * ny
        if relVel > 0:
            return
        
        collide_sound(relVel)

        # Tangent vector
        tx = -ny
        ty = nx

        # Decompose velocities
        v1n = b1.vx * nx + b1.vy * ny
        v1t = b1.vx * tx + b1.vy * ty
        v2n = b2.vx * nx + b2.vy * ny
        v2t = b2.vx * tx + b2.vy * ty

        # --- Equal mass swap (this is the key simplification) ---
        v1n, v2n = v2n, v1n

        # Optional realism (slight energy loss)
        restitution = 1.0
        v1n *= restitution
        v2n *= restitution

        # Reconstruct velocities
        b1.vx = tx * v1t + nx * v1n
        b1.vy = ty * v1t + ny * v1n
        b2.vx = tx * v2t + nx * v2n
        b2.vy = ty * v2t + ny * v2n

        # --- Positional correction ---
        percent = 0.8
        slop = 0.01

        overlap = max(b1.radius + b2.radius - dist - slop, 0)
        correction = overlap * percent / 2  # divide by 2 for equal mass

        b1.x -= correction * nx
        b1.y -= correction * ny
        b2.x += correction * nx
        b2.y += correction * ny

def draw_prediction(ball, mouse_pos):
    temp_x, temp_y = ball.x, ball.y
    # Fixed physics: vector from ball to mouse
    dx, dy = mouse_pos[0] - ball.x, mouse_pos[1] - ball.y
    dx, dy = max_power(dx, dy, 150)

    vx, vy = dx * 0.05, dy * 0.05
    
    collision_point = None
    hit_ball = None

    for _ in range(120):
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
                        hit_ball = b
                        break
        pygame.draw.circle(screen, WHITE, (int(temp_x), int(temp_y)), 2)
    
    if collision_point and hit_ball:
            cx, cy = collision_point

            # Draw collision point
            pygame.draw.circle(screen, YELLOW, (int(cx), int(cy)), 6)

            # Direction from cue → collision
            pygame.draw.line(screen, WHITE, (ball.x, ball.y), (cx, cy), 2)

            # Compute normal (impact direction)
            nx = hit_ball.x - cx
            ny = hit_ball.y - cy
            dist = math.hypot(nx, ny)
            if dist == 0: return
            nx, ny = nx / dist, ny / dist

            # --- OBJECT BALL PATH ---
            obj_end = (hit_ball.x + nx * 100, hit_ball.y + ny * 100)
            pygame.draw.line(screen, RED, (hit_ball.x, hit_ball.y), obj_end, 3)

            # --- CUE BALL DEFLECTION ---
            # Reflect incoming velocity
            dot = vx * nx + vy * ny
            rx = vx - 2 * dot * nx
            ry = vy - 2 * dot * ny

            cue_end = (cx + rx * 20, cy + ry * 20)
            pygame.draw.line(screen, PINK, (cx, cy), cue_end, 3)

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
types_list = ["Red"] * 7 + ["Pink"] * 7
random.shuffle(types_list)

# Insert 8-ball EXACTLY in center (index 10)
types_list.insert(4, "eight")

# Now assign balls
for i, pos in enumerate(rack_positions):
    t = types_list[i]

    if t == "Red":
        b = Ball(pos[0], pos[1], RED)
    elif t == "Pink":
        b = Ball(pos[0], pos[1], PINK)
    else:
        b = Ball(pos[0], pos[1], BLACK)

    ball_types[b] = t
    balls.append(b)

dragging = False
running = True

# Max shot strength
def max_power(dx, dy, max_force):
    length = math.hypot(dx, dy)
    
    if length == 0:
        return 0, 0
    
    if length > max_force:
        scale = max_force / length
        dx *= scale
        dy *= scale
    
    return dx, dy

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
                dx = event.pos[0] - cue_ball.x
                dy = event.pos[1] - cue_ball.y

                dx, dy = max_power(dx, dy, 150)  # <-- adjust max strength here

                cue_ball.vx = dx * 0.12
                cue_ball.vy = dy * 0.12

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
                        winner = 3 - player_turn
                    else:
                        # Assign sets if first time
                        if player_types[player_turn] is None:
                            player_types[player_turn] = ball_types[b]
                            player_types[3 - player_turn] = "Pink" if ball_types[b] == "Red" else "Red"
                        
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