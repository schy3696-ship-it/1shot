import pygame
import sys
import math

pygame.init()

# =====================
# WINDOW
# =====================
WIDTH = 900
HEIGHT = 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("One Shot – Puzzle Level")

clock = pygame.time.Clock()

# =====================
# COLORS
# =====================
BG_COLOR = (25, 25, 30)
PLAYER_COLOR = (80, 200, 255)
BULLET_COLOR = (255, 220, 120)
AIM_COLOR = (255, 90, 90)
ZOMBIE_COLOR = (120, 220, 120)
TEXT_COLOR = (255, 255, 255)
GROUND_COLOR = (150, 75, 0)
WALL_COLOR = (180, 180, 180)
BUTTON_COLOR = (70, 70, 200)
BUTTON_HOVER = (100, 100, 255)

font = pygame.font.SysFont(None, 36)

# =====================
# GROUND
# =====================
GROUND_HEIGHT = 10
GROUND_Y = HEIGHT - 20

# =====================
# PLAYER
# =====================
class Soldier:
    def __init__(self):
        self.width = 30
        self.height = 50
        self.x = 50
        self.y = GROUND_Y - self.height
        self.speed = 6
        self.aim_angle = 0

    def move(self, keys, walls):
        old_x = self.x
        if keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_d]:
            self.x += self.speed

        self.x = max(0, min(self.x, WIDTH - self.width))

        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for w in walls:
            if w.rect.colliderect(rect):
                self.x = old_x

    def aim(self, keys):
        if keys[pygame.K_j]:
            self.aim_angle -= 3
        if keys[pygame.K_l]:
            self.aim_angle += 3
        self.aim_angle %= 360

    def gun_pos(self):
        return self.x + self.width//2, self.y + self.height//2

    def draw(self):
        pygame.draw.rect(screen, PLAYER_COLOR,
                         (self.x, self.y, self.width, self.height))

        rad = math.radians(self.aim_angle)
        for i in range(15, 220, 18):
            x = self.x + self.width//2 + math.cos(rad) * i
            y = self.y + self.height//2 + math.sin(rad) * i
            pygame.draw.circle(screen, AIM_COLOR, (int(x), int(y)), 3)

# =====================
# WALL
# =====================
class Wall:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self):
        pygame.draw.rect(screen, WALL_COLOR, self.rect)

# =====================
# ZOMBIE
# =====================
class Zombie:
    def __init__(self, x, y, speed=0, left=None, right=None):
        self.rect = pygame.Rect(x, y, 25, 35)
        self.alive = True
        self.speed = speed
        self.dir = 1
        self.left = left
        self.right = right

    def update(self):
        if not self.alive:
            return
        if self.speed > 0:
            self.rect.x += self.speed * self.dir
            if self.rect.x <= self.left or self.rect.x >= self.right:
                self.dir *= -1

    def draw(self):
        if self.alive:
            pygame.draw.rect(screen, ZOMBIE_COLOR, self.rect)

# =====================
# BULLET
# =====================
class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.r = 6
        self.speed = 12
        rad = math.radians(angle)
        self.vx = math.cos(rad) * self.speed
        self.vy = math.sin(rad) * self.speed
        self.birth = pygame.time.get_ticks()

    def update(self, walls):
        self.x += self.vx
        self.y += self.vy

        if self.x <= self.r or self.x >= WIDTH - self.r:
            self.vx *= -1
        if self.y <= self.r:
            self.vy *= -1
        if self.y + self.r >= GROUND_Y:
            self.vy *= -1
            self.y = GROUND_Y - self.r

        rect = pygame.Rect(self.x-self.r, self.y-self.r, self.r*2, self.r*2)
        for w in walls:
            if w.rect.colliderect(rect):
                if rect.right >= w.rect.left and rect.left < w.rect.left:
                    self.vx *= -1
                elif rect.left <= w.rect.right and rect.right > w.rect.right:
                    self.vx *= -1
                if rect.bottom >= w.rect.top and rect.top < w.rect.top:
                    self.vy *= -1
                elif rect.top <= w.rect.bottom and rect.bottom > w.rect.bottom:
                    self.vy *= -1

    def expired(self):
        return pygame.time.get_ticks() - self.birth > 6000

    def draw(self):
        pygame.draw.circle(screen, BULLET_COLOR,
                           (int(self.x), int(self.y)), self.r)

# =====================
# BUTTON
# =====================
def draw_button(rect, text):
    mx, my = pygame.mouse.get_pos()
    color = BUTTON_HOVER if rect.collidepoint(mx, my) else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect)
    t = font.render(text, True, TEXT_COLOR)
    screen.blit(t, (rect.x + 15, rect.y + 8))

# =====================
# LEVEL DESIGN
# =====================
walls = [
    Wall(250, GROUND_Y - 60, 120, 10),
    Wall(450, GROUND_Y - 120, 160, 10),
    Wall(650, GROUND_Y - 70, 100, 10),
    Wall(380, GROUND_Y - 200, 10, 120),
    Wall(580, GROUND_Y - 180, 10, 100)
]

zombies = [
    Zombie(270, GROUND_Y - 95),
    Zombie(480, GROUND_Y - 155),
    Zombie(680, GROUND_Y - 105, speed=1, left=650, right=740)
]

player = Soldier()
bullets = []
bullet_limit = 4
bullets_used = 0

game_over = False
win = False
lose = False

restart_btn = pygame.Rect(WIDTH//2 - 70, HEIGHT//2 + 40, 140, 40)

# =====================
# GAME LOOP
# =====================
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game_over:
                if bullets_used < bullet_limit:
                    x, y = player.gun_pos()
                    bullets.append(Bullet(x, y, player.aim_angle))
                    bullets_used += 1

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_over and restart_btn.collidepoint(event.pos):
                bullets.clear()
                bullets_used = 0
                for z in zombies:
                    z.alive = True
                game_over = win = lose = False

    keys = pygame.key.get_pressed()
    if not game_over:
        player.move(keys, walls)
        player.aim(keys)

    for z in zombies:
        z.update()

    for b in bullets[:]:
        b.update(walls)
        p = pygame.Rect(b.x, b.y, 1, 1)
        for z in zombies:
            if z.alive and z.rect.colliderect(p):
                z.alive = False
        if b.expired():
            bullets.remove(b)

    if not game_over:
        if not any(z.alive for z in zombies):
            game_over = True
            win = True
        elif bullets_used >= bullet_limit and len(bullets) == 0 and any(z.alive for z in zombies):
            game_over = True
            lose = True

    # =====================
    # DRAW
    # =====================
    screen.fill(BG_COLOR)
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, WIDTH, GROUND_HEIGHT))

    for w in walls:
        w.draw()
    player.draw()
    for z in zombies:
        z.draw()
    for b in bullets:
        b.draw()

    screen.blit(font.render(f"Bullets: {bullets_used}/4", True, TEXT_COLOR), (10, 10))

    if win:
        screen.blit(font.render("YOU WIN!", True, (255, 215, 0)),
                    (WIDTH//2 - 70, HEIGHT//2 - 30))
        draw_button(restart_btn, "Restart")

    if lose:
        screen.blit(font.render("YOU LOSE!", True, (255, 80, 80)),
                    (WIDTH//2 - 90, HEIGHT//2 - 30))
        draw_button(restart_btn, "Restart")

    pygame.display.update()
    clock.tick(60)
