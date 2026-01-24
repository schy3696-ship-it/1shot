import pygame
import sys
import math

pygame.init()

# --------------------
# Window
# --------------------
WIDTH = 900
HEIGHT = 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("One Shot - Solid Walls & Ground Bounce")

clock = pygame.time.Clock()

# --------------------
# Colors
# --------------------
BG_COLOR = (25, 25, 30)
PLAYER_COLOR = (80, 200, 255)
BULLET_COLOR = (255, 220, 120)
AIM_COLOR = (255, 90, 90)
ZOMBIE_COLOR = (120, 220, 120)
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (70, 70, 200)
BUTTON_HOVER = (100, 100, 255)
GROUND_COLOR = (150, 75, 0)
WALL_COLOR = (180, 180, 180)

# --------------------
# Fonts
# --------------------
font = pygame.font.SysFont(None, 36)

# --------------------
# Ground
# --------------------
GROUND_HEIGHT = 10
GROUND_Y = HEIGHT - 20

# --------------------
# Soldier
# --------------------
class Soldier:
    def __init__(self, x, y):
        self.width = 30
        self.height = 50
        self.start_x = x
        self.start_y = y
        self.speed = 6
        self.aim_angle = 0
        self.x = x
        self.y = GROUND_Y - self.height

    def move(self, keys, walls):
        old_x = self.x
        if keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_d]:
            self.x += self.speed

        # keep within screen
        self.x = max(0, min(self.x, WIDTH - self.width))

        # collision with walls
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for wall in walls:
            if wall.rect.colliderect(player_rect):
                self.x = old_x  # revert

    def aim_control(self, keys):
        if keys[pygame.K_j]:
            self.aim_angle -= 3
        if keys[pygame.K_l]:
            self.aim_angle += 3
        self.aim_angle %= 360

    def gun_position(self):
        return (
            self.x + self.width // 2,
            self.y + self.height // 2
        )

    def draw(self, surface):
        pygame.draw.rect(surface, PLAYER_COLOR,
                         (self.x, self.y, self.width, self.height))
        rad = math.radians(self.aim_angle)
        for i in range(10, 200, 15):
            dot_x = self.x + self.width // 2 + math.cos(rad) * i
            dot_y = self.y + self.height // 2 + math.sin(rad) * i
            pygame.draw.circle(surface, AIM_COLOR, (int(dot_x), int(dot_y)), 3)

    def reset_position(self):
        self.x = self.start_x
        self.y = GROUND_Y - self.height
        self.aim_angle = 0

# --------------------
# Wall/Platform
# --------------------
class Wall:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, surface):
        pygame.draw.rect(surface, WALL_COLOR, self.rect)

# --------------------
# Zombie
# --------------------
class Zombie:
    def __init__(self, x, y, speed=0, range_left=None, range_right=None, on_wall=False):
        self.width = 25
        self.height = 35
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.alive = True
        self.speed = speed
        self.direction = 1
        self.range_left = range_left if range_left is not None else 0
        self.range_right = range_right if range_right is not None else WIDTH - self.width
        self.on_wall = on_wall

    def update(self):
        if not self.alive:
            return
        if self.on_wall:
            self.rect.x += self.speed * self.direction
            if self.rect.x < self.range_left or self.rect.x > self.range_right:
                self.direction *= -1

    def draw(self, surface):
        if self.alive:
            pygame.draw.rect(surface, ZOMBIE_COLOR, self.rect)

    def reset(self):
        self.alive = True

# --------------------
# Bullet
# --------------------
class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.radius = 6
        self.speed = 12
        rad = math.radians(angle)
        self.vx = math.cos(rad) * self.speed
        self.vy = math.sin(rad) * self.speed
        self.spawn_time = pygame.time.get_ticks()

    def update(self, walls):
        self.x += self.vx
        self.y += self.vy

        # screen edges
        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.vx *= -1
        if self.y <= self.radius:
            self.vy *= -1

        # ground bounce
        if self.y + self.radius >= GROUND_Y:
            self.vy *= -1
            self.y = GROUND_Y - self.radius

        # wall collisions
        bullet_rect = pygame.Rect(self.x - self.radius, self.y - self.radius,
                                  self.radius*2, self.radius*2)
        for wall in walls:
            if wall.rect.colliderect(bullet_rect):
                if bullet_rect.right >= wall.rect.left and bullet_rect.left < wall.rect.left:
                    self.vx *= -1
                    self.x = wall.rect.left - self.radius
                elif bullet_rect.left <= wall.rect.right and bullet_rect.right > wall.rect.right:
                    self.vx *= -1
                    self.x = wall.rect.right + self.radius
                if bullet_rect.bottom >= wall.rect.top and bullet_rect.top < wall.rect.top:
                    self.vy *= -1
                    self.y = wall.rect.top - self.radius
                elif bullet_rect.top <= wall.rect.bottom and bullet_rect.bottom > wall.rect.bottom:
                    self.vy *= -1
                    self.y = wall.rect.bottom + self.radius

    def expired(self):
        return pygame.time.get_ticks() - self.spawn_time > 6000

    def draw(self, surface):
        pygame.draw.circle(surface, BULLET_COLOR,
                           (int(self.x), int(self.y)), self.radius)

# --------------------
# Button helper
# --------------------
def draw_button(surface, rect, text):
    mx, my = pygame.mouse.get_pos()
    color = BUTTON_HOVER if rect.collidepoint(mx, my) else BUTTON_COLOR
    pygame.draw.rect(surface, color, rect)
    text_surf = font.render(text, True, TEXT_COLOR)
    surface.blit(text_surf, (rect.x + 10, rect.y + 5))

# --------------------
# Levels
# --------------------
levels = [
    {
        "walls": [Wall(300, GROUND_Y - 50, 120, 10), Wall(600, GROUND_Y - 100, 150, 10)],
        "zombies": [
            Zombie(320, GROUND_Y - 85, speed=1, range_left=300, range_right=420, on_wall=True),
            Zombie(650, GROUND_Y - 135, speed=0, on_wall=False),
            Zombie(620, GROUND_Y - 135, speed=0, on_wall=False)
        ],
        "bullets": 3
    },
    {
        "walls": [Wall(200, GROUND_Y - 70, 100, 10), Wall(500, GROUND_Y - 120, 150, 10)],
        "zombies": [
            Zombie(220, GROUND_Y - 105, speed=1, range_left=200, range_right=300, on_wall=True),
            Zombie(520, GROUND_Y - 155, speed=1, range_left=500, range_right=650, on_wall=True),
            Zombie(250, GROUND_Y - 35, speed=0, on_wall=False),
            Zombie(700, GROUND_Y - 35, speed=0, on_wall=False)
        ],
        "bullets": 5
    }
]

current_level = 0

# --------------------
# Game state
# --------------------
player = Soldier(50, HEIGHT - 70)  # LEFT corner start
bullets = []
walls = levels[current_level]["walls"]
zombies = levels[current_level]["zombies"]
bullet_limit = levels[current_level]["bullets"]
bullets_fired = 0
game_over = False
win_text_displayed = False
lose_text_displayed = False

restart_button = pygame.Rect(WIDTH//2 - 60, HEIGHT//2 + 40, 120, 40)
next_level_button = pygame.Rect(WIDTH//2 - 70, HEIGHT//2 + 40, 140, 40)

# --------------------
# Main loop
# --------------------
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                if bullets_fired < bullet_limit:
                    x, y = player.gun_position()
                    bullets.append(Bullet(x, y, player.aim_angle))
                    bullets_fired += 1

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if game_over and restart_button.collidepoint(event.pos):
                    bullets.clear()
                    bullets_fired = 0
                    player.reset_position()
                    for z in zombies:
                        z.reset()
                    game_over = False
                    win_text_displayed = False
                    lose_text_displayed = False
                if game_over and win_text_displayed and next_level_button.collidepoint(event.pos):
                    current_level += 1
                    if current_level >= len(levels):
                        current_level = 0
                    walls = levels[current_level]["walls"]
                    zombies = levels[current_level]["zombies"]
                    bullet_limit = levels[current_level]["bullets"]
                    bullets.clear()
                    bullets_fired = 0
                    player.reset_position()
                    game_over = False
                    win_text_displayed = False
                    lose_text_displayed = False

    keys = pygame.key.get_pressed()
    if not game_over:
        player.move(keys, walls)
        player.aim_control(keys)

    # update zombies
    for z in zombies:
        z.update()

    # update bullets
    all_walls = walls + [Wall(0, GROUND_Y, WIDTH, GROUND_HEIGHT)]  # include ground
    for bullet in bullets[:]:
        bullet.update(all_walls)
        bullet_point = pygame.Rect(bullet.x, bullet.y, 1, 1)
        for zombie in zombies:
            if zombie.alive and zombie.rect.colliderect(bullet_point):
                zombie.alive = False
        if bullet.expired():
            bullets.remove(bullet)

    # win/lose logic
    if not game_over:
        if not any(z.alive for z in zombies):
            game_over = True
            win_text_displayed = True
            lose_text_displayed = False
        elif bullets_fired >= bullet_limit and len(bullets) == 0 and any(z.alive for z in zombies):
            game_over = True
            lose_text_displayed = True
            win_text_displayed = False

    # --------------------
    # Draw everything
    # --------------------
    screen.fill(BG_COLOR)

    # ground
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, WIDTH, GROUND_HEIGHT))

    # walls
    for wall in walls:
        wall.draw(screen)

    # player
    player.draw(screen)

    # zombies
    for z in zombies:
        z.draw(screen)

    # bullets
    for b in bullets:
        b.draw(screen)

    # bullets info
    text = font.render(f"Bullets: {bullets_fired}/{bullet_limit}", True, TEXT_COLOR)
    screen.blit(text, (10, 10))

    # win/lose text
    if win_text_displayed:
        win_text = font.render("You Win! All zombies down!", True, (255, 215, 0))
        screen.blit(win_text, (WIDTH//2 - 180, HEIGHT//2 - 20))
        draw_button(screen, next_level_button, "Next Level")
        draw_button(screen, restart_button, "Restart")

    if lose_text_displayed:
        lose_text = font.render("You Lose! Try Again!", True, (255, 80, 80))
        screen.blit(lose_text, (WIDTH//2 - 140, HEIGHT//2 - 20))
        draw_button(screen, restart_button, "Restart")

    pygame.display.update()
    clock.tick(60)
