import pygame
import math

pygame.init()

# =====================================================
# SETTINGS
# =====================================================

WIDTH, HEIGHT = 1000, 600
GROUND_Y = HEIGHT - 60
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("One Shot - Level 4 TNT")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 38)

WHITE = (240, 240, 240)
BLACK = (30, 30, 30)
RED = (200, 60, 60)
GREEN = (60, 200, 60)
GRAY = (120, 120, 120)
ORANGE = (255, 140, 0)


# =====================================================
# CLASSES
# =====================================================

class Soldier:
    def __init__(self):
        self.rect = pygame.Rect(40, GROUND_Y - 50, 30, 50)
        self.speed = 5
        self.angle = 0

    def move(self, keys):
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))

    def aim(self, keys):
        if keys[pygame.K_j]:
            self.angle -= 2
        if keys[pygame.K_l]:
            self.angle += 2

    def draw(self):
        pygame.draw.rect(screen, GREEN, self.rect)

        # dotted aim line
        for i in range(0, 260, 14):
            x = self.rect.centerx + math.cos(math.radians(self.angle)) * i
            y = self.rect.centery + math.sin(math.radians(self.angle)) * i
            pygame.draw.circle(screen, WHITE, (int(x), int(y)), 2)


# -----------------------------------------------------

class Bullet:
    def __init__(self, x, y, vx, vy):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = 360  # 6 seconds

    def rect(self):
        return pygame.Rect(self.x-4, self.y-4, 8, 8)

    # ⭐ Anti-tunneling physics
    def update(self, walls):
        steps = 4

        for _ in range(steps):
            self.x += self.vx / steps
            self.y += self.vy / steps

            r = self.rect()

            for w in walls:
                if r.colliderect(w):
                    if abs(self.vx) > abs(self.vy):
                        self.vx *= -1
                    else:
                        self.vy *= -1

            if self.x <= 0 or self.x >= WIDTH:
                self.vx *= -1
            if self.y <= 0:
                self.vy *= -1
            if self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.vy *= -1

        self.life -= 1

    def dead(self):
        return self.life <= 0

    def draw(self):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 4)


# -----------------------------------------------------

class Zombie:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 25, 35)
        self.alive = True

    def draw(self):
        if self.alive:
            pygame.draw.rect(screen, RED, self.rect)


# -----------------------------------------------------

class TNT:
    def __init__(self, x, y, radius=90):  # ⭐ BIGGER radius
        self.rect = pygame.Rect(x, y, 22, 22)
        self.radius = radius
        self.alive = True

    def explode(self, zombies):
        for z in zombies:
            if z.alive:
                d = math.hypot(
                    z.rect.centerx - self.rect.centerx,
                    z.rect.centery - self.rect.centery
                )
                if d <= self.radius:
                    z.alive = False

    def draw(self):
        if self.alive:
            pygame.draw.rect(screen, ORANGE, self.rect)


# =====================================================
# LEVEL SETUP
# =====================================================

def reset_level():
    global player, bullets, zombies, walls, tnts
    global bullets_left, state

    player = Soldier()
    bullets = []

    bullets_left = 6
    state = "PLAY"

    # maze walls
    walls = [
        pygame.Rect(300, 450, 200, 20),
        pygame.Rect(550, 380, 200, 20),
        pygame.Rect(200, 320, 150, 20),
        pygame.Rect(700, 260, 200, 20),
        pygame.Rect(500, 200, 20, 180),
        pygame.Rect(420, 260, 20, 150),
    ]

    zombies = [
        Zombie(320, 415),
        Zombie(360, 415),
        Zombie(600, 345),
        Zombie(750, 225),
        Zombie(230, 285),
        Zombie(820, 225),
        Zombie(540, 165),
    ]

    # ⭐ 3 TNTs with larger radius
    tnts = [
        TNT(520, 160),
        TNT(330, 410),
        TNT(760, 230),
    ]


reset_level()


# =====================================================
# GAME LOOP
# =====================================================

running = True

while running:
    clock.tick(FPS)
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if state == "PLAY" and event.key == pygame.K_SPACE and bullets_left > 0:
                speed = 8
                vx = math.cos(math.radians(player.angle)) * speed
                vy = math.sin(math.radians(player.angle)) * speed
                bullets.append(Bullet(player.rect.centerx, player.rect.centery, vx, vy))
                bullets_left -= 1

            if event.key == pygame.K_r:
                reset_level()

    keys = pygame.key.get_pressed()

    # ================= PLAY =================
    if state == "PLAY":

        player.move(keys)
        player.aim(keys)

        for b in bullets[:]:
            b.update(walls)

            for z in zombies:
                if z.alive and b.rect().colliderect(z.rect):
                    z.alive = False

            for t in tnts:
                if t.alive and b.rect().colliderect(t.rect):
                    t.alive = False
                    t.explode(zombies)

            if b.dead():
                bullets.remove(b)

        if all(not z.alive for z in zombies):
            state = "WIN"

        elif bullets_left == 0 and len(bullets) == 0:
            state = "LOSE"

    # ================= DRAW =================
    pygame.draw.rect(screen, GRAY, (0, GROUND_Y, WIDTH, HEIGHT-GROUND_Y))

    for w in walls:
        pygame.draw.rect(screen, (100, 100, 100), w)

    for t in tnts:
        t.draw()

    for z in zombies:
        z.draw()

    for b in bullets:
        b.draw()

    player.draw()

    hud = font.render(f"Bullets: {bullets_left}", True, WHITE)
    screen.blit(hud, (10, 10))

    if state == "WIN":
        txt = font.render("WIN! Press R to Restart", True, GREEN)
        screen.blit(txt, (WIDTH//2 - 170, HEIGHT//2))

    if state == "LOSE":
        txt = font.render("Try harder! Press R to Restart", True, RED)
        screen.blit(txt, (WIDTH//2 - 200, HEIGHT//2))

    pygame.display.flip()

pygame.quit()
