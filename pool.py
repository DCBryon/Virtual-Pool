import pygame
import math
import random

# --- CONSTANTS ---
WIDTH, HEIGHT = 900, 500
TABLE = (30, 100, 30)
WHITE = (255, 255, 255)
RED = (200, 50, 50)
PINK = (255, 150, 150)
BLACK = (20, 20, 20)
YELLOW = (255, 255, 0)

FRICTION = 0.985
BALL_RADIUS = 14
POCKET_RADIUS = 28

# Pockets coordinates
pockets = [
    (0, 0), (WIDTH//2, 0), (WIDTH, 0),
    (0, HEIGHT), (WIDTH//2, HEIGHT), (WIDTH, HEIGHT)
]

# --- CLASSES ---
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

        # Wall bounce (Boundary Conditions)
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

    def draw(self, screen):
        if self.active:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def check_pocket(self, pocketed_list):
        if not self.active: return
        for px, py in pockets:
            if math.hypot(self.x - px, self.y - py) < POCKET_RADIUS:
                self.active = False
                self.vx = self.vy = 0
                pocketed_list.append(self)

# --- PHYSICS FUNCTIONS ---
def collide(b1, b2, hit_sound=None):
    if not b1.active or not b2.active:
        return

    dx = b2.x - b1.x
    dy = b2.y - b1.y
    dist = math.hypot(dx, dy)

    if dist < b1.radius + b2.radius and dist > 0:
        # Normal vector
        nx, ny = dx / dist, dy / dist

        # Relative velocity check
        relVel = (b2.vx - b1.vx) * nx + (b2.vy - b1.vy) * ny
        if relVel > 0: return
        
        if hit_sound:
            impact = abs(relVel)
            hit_sound.set_volume(min(impact * 0.05, 1.0))
            hit_sound.play()

        # Normal/Tangent Decompositon
        tx, ty = -ny, nx
        v1n = b1.vx * nx + b1.vy * ny
        v1t = b1.vx * tx + b1.vy * ty
        v2n = b2.vx * nx + b2.vy * ny
        v2t = b2.vx * tx + b2.vy * ty

        # Equal mass swap with restitution
        restitution = 0.9 
        v1n, v2n = v2n * restitution, v1n * restitution

        # Reconstruct velocities
        b1.vx, b1.vy = tx * v1t + nx * v1n, ty * v1t + ny * v1n
        b2.vx, b2.vy = tx * v2t + nx * v2n, ty * v2t + ny * v2n

        # Positional correction (Linear Projection)
        overlap = (b1.radius + b2.radius - dist - 0.01)
        correction = overlap * 0.8 / 2
        b1.x -= correction * nx
        b1.y -= correction * ny
        b2.x += correction * nx
        b2.y += correction * ny

def max_power(dx, dy, max_force):
    length = math.hypot(dx, dy)
    if length == 0: return 0, 0
    if length > max_force:
        scale = max_force / length
        dx, dy = dx * scale, dy * scale
    return dx, dy

# --- UI & PREDICTION ---
def draw_prediction(screen, ball, balls, mouse_pos):
    temp_x, temp_y = ball.x, ball.y
    dx, dy = mouse_pos[0] - ball.x, mouse_pos[1] - ball.y
    dx, dy = max_power(dx, dy, 200)
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
        pygame.draw.circle(screen, YELLOW, (cx, cy), 6)
        pygame.draw.line(screen, WHITE, (ball.x, ball.y), (cx, cy), 2)
        nx, ny = (hit_ball.x - cx), (hit_ball.y - cy)
        dist = math.hypot(nx, ny)
        if dist > 0:
            nx, ny = nx / dist, ny / dist
            pygame.draw.line(screen, RED, (hit_ball.x, hit_ball.y), (hit_ball.x + nx * 100, hit_ball.y + ny * 100), 3)
            dot = vx * nx + vy * ny
            rx, ry = vx - 2 * dot * nx, vy - 2 * dot * ny
            pygame.draw.line(screen, PINK, (cx, cy), (cx + rx * 20, cy + ry * 20), 3)

# --- MAIN GAME EXECUTION ---
def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("8-Ball Pool Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)
    big_font = pygame.font.SysFont("Arial", 40)

    try:
        hit_sound = pygame.mixer.Sound("Pool Ball Hit Sound Effect - Edit.wav")
    except:
        hit_sound = None

    cue_ball = Ball(200, HEIGHT//2, WHITE)
    balls = [cue_ball]
    ball_types = {}
    
    # Rack Setup
    start_x, start_y = 650, HEIGHT // 2
    spacing = BALL_RADIUS * 2 + 2
    types_list = (["Red"] * 7 + ["Pink"] * 7)
    random.shuffle(types_list)
    types_list.insert(4, "eight")

    idx = 0
    for row in range(5):
        for col in range(row + 1):
            x = start_x + row * spacing
            y = start_y - (row * spacing / 2) + col * spacing
            t = types_list[idx]
            color = RED if t == "Red" else PINK if t == "Pink" else BLACK
            b = Ball(x, y, color)
            ball_types[b] = t
            balls.append(b)
            idx += 1

    player_turn = 1
    player_types = {1: None, 2: None}
    pocketed_this_turn = []
    winner = None
    dragging = False
    turn_processed = True

    running = True
    while running:
        clock.tick(60)
        screen.fill(TABLE)

        # Draw Pockets
        for px, py in pockets:
            pygame.draw.circle(screen, (10,10,10), (px, py), POCKET_RADIUS)
            pygame.draw.circle(screen, BLACK, (px, py), POCKET_RADIUS - 4)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            stopped = all(abs(b.vx) < 0.1 and abs(b.vy) < 0.1 for b in balls if b.active)
            if winner is None and stopped:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if math.hypot(event.pos[0] - cue_ball.x, event.pos[1] - cue_ball.y) < BALL_RADIUS * 2:
                        dragging = True
                if event.type == pygame.MOUSEBUTTONUP and dragging:
                    dragging = False
                    turn_processed = False
                    dx, dy = max_power(event.pos[0] - cue_ball.x, event.pos[1] - cue_ball.y, 150)
                    cue_ball.vx, cue_ball.vy = dx * 0.12, dy * 0.12

        if winner is None:
            for b in balls:
                b.move()
                b.check_pocket(pocketed_this_turn)
            for i in range(len(balls)):
                for j in range(i + 1, len(balls)):
                    collide(balls[i], balls[j], hit_sound)

            # Turn Logic
            stopped = all(abs(b.vx) < 0.1 and abs(b.vy) < 0.1 for b in balls if b.active)
            if stopped and not dragging and not turn_processed:
                scored_own = False
                foul = False
                for b in pocketed_this_turn:
                    if b == cue_ball:
                        foul = True
                        b.active, b.x, b.y, b.vx, b.vy = True, 200, HEIGHT//2, 0, 0
                    elif ball_types.get(b) == "eight":
                        p_color = player_types[player_turn]
                        remaining = any(bl.active and ball_types.get(bl) == p_color for bl in balls if bl != cue_ball and ball_types.get(bl) != "eight")
                        winner = player_turn if (not remaining and player_types[player_turn] and not foul) else (3 - player_turn)
                    else:
                        if player_types[player_turn] is None:
                            player_types[player_turn] = ball_types[b]
                            player_types[3 - player_turn] = "Pink" if ball_types[b] == "Red" else "Red"
                        if ball_types.get(b) == player_types[player_turn]: scored_own = True
                
                if foul or not scored_own: player_turn = 3 - player_turn
                pocketed_this_turn.clear()
                turn_processed = True

        for b in balls: b.draw(screen)
        if dragging and winner is None: draw_prediction(screen, cue_ball, balls, pygame.mouse.get_pos())
        
        # UI
        screen.blit(font.render(f"Player {player_turn}'s Turn", True, YELLOW if winner is None else WHITE), (15, 15))
        screen.blit(font.render(f"""P1: {player_types[1] or 'Not set'}  P2: {player_types[2] or 'Not set'}""", True, WHITE), (15, 45))
        if winner: screen.blit(big_font.render(f"PLAYER {winner} WINS!", True, YELLOW), (WIDTH//2 - 160, HEIGHT//2 - 25))
        
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()