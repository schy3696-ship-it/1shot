from turtle import right
import pygame, sys, math

from game import Soldier
from gamer import GREEN, RED

pygame.init()

# ---------------- GLOBAL ----------------
WIDTH, HEIGHT = 1100, 650
FPS = 60

GROUND_HEIGHT = 10
GROUND_Y = HEIGHT - 20
PLAYER_Y = GROUND_Y - 50
PLAYER_SIZE = (30, 50)
SPECIAL_RADIUS = 100


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("One Shot - All levels")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 40)

WHITE=(240,240,240)
BLACK=(20,20,20)

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
GRAY = (128, 128, 128)

# ---------------- GLOBAL EXPLOSIONS
explosions = []  # (pos, radius, timer)

def add_explosion(pos,radius):
    explosions.append([pos,radius,20])
def update_explosions():
    for e in explosions[:]:
        e[2]-=1
        if e[2]<=0: explosions.remove(e)
def draw_explosions():
    yellow = (255, 200, 40)
    for pos,radius,_ in explosions:
        pygame.draw.circle(screen,yellow,pos,radius,2)
        pygame.draw.circle(screen, yellow, pos, radius, 2)

#----------Classes----------------
# ---------- Player ----------
class Player:
    def __init__(self):
        self.rect = pygame.Rect(40, GROUND_Y - 50, 30, 50)
        self.speed = 3
        self.angle = 0

    def update(self, keys):
        if keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_d]:
            self.rect.x += self.speed

        if keys[pygame.K_j]:
            self.angle += 2
        if keys[pygame.K_l]:
            self.angle -= 2

        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))

    def draw(self):
        pygame.draw.rect(screen, GREEN, self.rect)

        cx, cy = self.rect.center
        rad = math.radians(self.angle)

        for i in range(18):
            px = cx + math.cos(rad) * i * 20
            py = cy - math.sin(rad) * i * 20
            pygame.draw.circle(screen, WHITE, (int(px), int(py)), 2)

# =====================
# WALL
# =====================
class Wall:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self):
        pygame.draw.rect(screen, WALL_COLOR, self.rect)
        
# =====================
# TNT
# =====================
class TNT:
    def __init__(self, x, y, radius=90):
        self.rect = pygame.Rect(x, y, 26, 26)
        self.radius = radius
        self.exploded = False

    def hit_by_bullet(self, bullet_rect):
        return self.rect.colliderect(bullet_rect)

    def explode(self, zombies):
        self.exploded = True

        # visual explosion
        add_explosion(self.rect.center, self.radius)

        # damage zombies in radius
        for z in zombies:
            if z.alive:
                dx = z.rect.centerx - self.rect.centerx
                dy = z.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist < self.radius:
                    z.alive = False

    def draw(self):
        if not self.exploded:
            pygame.draw.rect(screen, (220, 80, 60), self.rect)

#------------------Aim------------------
def draw_aim(player_rect,angle):
    px,py=player_rect.center
    for i in range(1,14):
        x=px+math.cos(angle)*i*20
        y=py+math.sin(angle)*i*20
        pygame.draw.circle(screen,WHITE,(int(x),int(y)),2)

# =====================
# BUTTON (with optional lock)
# =====================
def draw_button(rect, text, locked=False):
    mx, my = pygame.mouse.get_pos()
    
    if locked:
        color = (100, 100, 100)  # gray for locked
    else:
        color = BUTTON_HOVER if rect.collidepoint(mx, my) else BUTTON_COLOR
    
    pygame.draw.rect(screen, color, rect)
    t = font.render(text, True, TEXT_COLOR)
    screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))



# ---------------- LOBBY ----------------
NUM_LEVELS = 7
LEVEL_BUTTON_WIDTH = 180
LEVEL_BUTTON_HEIGHT = 60
LEVEL_BUTTON_SPACING = 30

# This should be saved/loaded from file for permanent unlocks
highest_level_unlocked = 0  # initially only level 0 (Level 1) unlocked

# Create button rects for all levels
level_buttons = []
start_x = (WIDTH - (LEVEL_BUTTON_WIDTH * NUM_LEVELS + LEVEL_BUTTON_SPACING * (NUM_LEVELS-1))) // 2
y = HEIGHT // 2 - LEVEL_BUTTON_HEIGHT // 2
for i in range(NUM_LEVELS):
    rect = pygame.Rect(
        start_x + i * (LEVEL_BUTTON_WIDTH + LEVEL_BUTTON_SPACING),
        y,
        LEVEL_BUTTON_WIDTH,
        LEVEL_BUTTON_HEIGHT
    )
    level_buttons.append(rect)

def show_lobby():
    global highest_level_unlocked
    in_lobby = True
    while in_lobby:
        screen.fill(BG_COLOR)

        # Draw level buttons
        for i, rect in enumerate(level_buttons):
            locked = i > highest_level_unlocked
            draw_button(rect, f"Level {i+1}", locked=locked)

        # Instructions
        instr = font.render("Select a level to play", True, WHITE)
        screen.blit(instr, (WIDTH//2 - instr.get_width()//2, y - 80))

        pygame.display.update()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(level_buttons):
                    if rect.collidepoint(event.pos) and i <= highest_level_unlocked:
                        # Player clicked an unlocked level
                        return i  # return the selected level index


# ---------------- BULLET ----------------
class Bullet:
    def __init__(self, x, y, angle, speed=12, radius=6, special=False):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.special = special  # for level 7 special bullet
        rad = math.radians(angle)
        self.vx = math.cos(rad) * self.speed
        self.vy = -math.sin(rad) * self.speed  # negative because pygame y increases downwards
        self.birth = pygame.time.get_ticks()

    def update(self, walls):
        self.x += self.vx
        self.y += self.vy

        # Screen edge collision
        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.vx *= -1
        if self.y <= self.radius:
            self.vy *= -1
        if self.y + self.radius >= GROUND_Y:
            self.vy *= -1
            self.y = GROUND_Y - self.radius

        # Wall collisions
        rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
        for w in walls:
            if w.rect.colliderect(rect):
                if rect.right >= w.rect.left and rect.left < w.rect.left:
                    self.vx *= -1
                    self.x = w.rect.left - self.radius
                elif rect.left <= w.rect.right and rect.right > w.rect.right:
                    self.vx *= -1
                    self.x = w.rect.right + self.radius

                if rect.bottom >= w.rect.top and rect.top < w.rect.top:
                    self.vy *= -1
                    self.y = w.rect.top - self.radius
                elif rect.top <= w.rect.bottom and rect.bottom > w.rect.bottom:
                    self.vy *= -1
                    self.y = w.rect.bottom + self.radius

    def expired(self, lifetime=6000):
        """ Returns True if bullet lifetime exceeded """
        return pygame.time.get_ticks() - self.birth > lifetime

    def draw(self):
        color = (255, 50, 50) if self.special else BULLET_COLOR
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)


# ---------------- ZOMBIE ----------------
class Zombie:
    def __init__(self, x, y, width=25, height=35, speed=0, left=None, right=None, special=False):
        """
        x, y       : initial position
        width, height : zombie size
        speed      : movement speed (0 = stationary)
        left, right : movement range if moving left-right
        special    : True for level 7 special zombie (shield, different color)
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = speed
        self.dir = 1  # 1 = right, -1 = left
        self.left = left
        self.right = right
        self.alive = True
        self.special = special

    def update(self):
        if not self.alive:
            return
        # moving zombie
        if self.speed > 0 and self.left is not None and self.right is not None:
            self.rect.x += self.speed * self.dir
            if self.rect.x <= self.left or self.rect.x >= self.right:
                self.dir *= -1

    def draw(self):
        if self.alive:
            color = (180, 180, 255) if self.special else ZOMBIE_COLOR
            pygame.draw.rect(screen, color, self.rect)

    def reset(self):
        """ Resets zombie to alive state """
        self.alive = True

#------------------levels------------------
# # =====================
# LEVEL 1
# =====================
def init_level_1():
    global walls, zombies, bullets, bullets_left, player, special_left, game_over,state
    
    # Walls
    walls = [
        Wall(300, GROUND_Y - 50, 120, 10),
        Wall(600, GROUND_Y - 100, 150, 10)
    ]
    
    # Zombies
    zombies = [
        Zombie(320, GROUND_Y - 85, speed=1, left=300, right=420),  # moving zombie
        Zombie(650, GROUND_Y - 135),  # stationary
        Zombie(620, GROUND_Y - 135)   # stationary
    ]
    
    # Player
    player = Player()
    player.rect.x = 50
    
    # Bullets
  
    bullets = []
    bullets_left = 4
    special_left = 0
    
    # Game state
    game_over = False
    

# =====================
# LEVEL 2
# =====================
def init_level_2():
    global walls, zombies, bullets, bullets_left, player, special_left, game_over,state
    
    # Walls
    walls = [
        Wall(200, GROUND_Y - 70, 100, 10),
        Wall(500, GROUND_Y - 120, 150, 10),
        Wall(380, GROUND_Y - 200, 10, 120),
        Wall(580, GROUND_Y - 180, 10, 100)
    ]
    
    # Zombies
    zombies = [
        Zombie(220, GROUND_Y - 105, speed=1, left=200, right=300),   # moving zombie
        Zombie(520, GROUND_Y - 155, speed=1, left=500, right=650),   # moving zombie
        Zombie(250, GROUND_Y - 35),                                   # stationary
        Zombie(700, GROUND_Y - 35)                                    # stationary
    ]
    
    # Player
    player = Player()
    player.rect.x = 50
    
    # Bullets
    global bullets_left, special_left
    bullets = []
    bullets_left = 3
    special_left = 0
    
    # Game state
    game_over = False
    

# =====================
# LEVEL 3
# =====================
def init_level_3():
    global walls, zombies, bullets, bullets_left, player, special_left, game_over,state

    # Walls
    walls = [
        Wall(200, GROUND_Y - 180, 350, 10),   # top long platform
        Wall(520, GROUND_Y - 90, 120, 10),    # small block
        Wall(420, GROUND_Y - 200, 10, 150)    # vertical bounce wall
    ]

    # Zombies
    zombies = [
        Zombie(220, GROUND_Y - 215, speed=1, left=210, right=520),  # walking
        Zombie(540, GROUND_Y - 125)  # static
    ]

    # Player
    player = Player()
    player.rect.x = 40

    # Bullets
   
    bullets = []
    bullets_left = 5
    special_left = 0

    # Game state
    game_over = False
   

#------------------ LEVEL 4 ------------------
def init_level_4():
    global player, bullets, zombies, walls, tnts
    global bullets,bullets_left, special_left, game_over,state

    player = Player()

    bullets = []
    bullets_left = 6
    special_left = 0

    # maze walls
    walls = [
        Wall(300, 450, 200, 20),
        Wall(550, 380, 200, 20),
        Wall(200, 320, 150, 20),
        Wall(700, 260, 200, 20),
        Wall(500, 200, 20, 180),
        Wall(420, 260, 20, 150),
    ]

    ZH = 35  # zombie height helper

    zombies = [
        Zombie(320,GROUND_Y - 450, speed=1, left=300,right=400),
        Zombie(360,GROUND_Y - 450),

        Zombie(600,GROUND_Y - 380 ),
        Zombie(750, GROUND_Y - 260,speed=1,left = 350,right=500 ),
        Zombie(820, GROUND_Y - 260 ),

        Zombie(230,GROUND_Y - 320, speed=1, left=200,right=350),
        Zombie(540, GROUND_Y - 200),
    ]

    tnts = [
        TNT(520, 200 - 22),
        TNT(330, 450 - 22),
        TNT(760, 260 - 22),
    ]
state = "PLAY"

#------------------ LEVEL 5 ------------------
def init_level_5():
    global player, bullets, zombies, walls, tnts
    global bullets_left, special_left, game_over,state

    player = Player()
    bullets = []
    bullets_left = 7
    special_left = 0

    ZH = 35
    TH = 22

    # =====================================================
    # WALLS  (multi-layer chaos maze)
    # =====================================================

    walls = [

        # bottom floor platforms
        Wall(280, 500, 260, 20),
        Wall(650, 500, 260, 20),

        # middle maze
        Wall(220, 380, 220, 20),
        Wall(580, 350, 250, 20),

        # upper
        Wall(420, 250, 260, 20),

        # vertical blockers (bank shots)
        Wall(520, 380, 20, 170),
        Wall(820, 260, 20, 260),
    ]


    # =====================================================
    # ZOMBIES (mix stationary + walkers)
    # =====================================================

    zombies = [

        # bottom pair
        Zombie(320,GROUND_Y - 500),
        Zombie(360,GROUND_Y - 500),

        # mid walker (corridor patrol)
        Zombie(260,GROUND_Y - 380, walk=True, left=240, right=400),

        # mid right stack
        Zombie(620,GROUND_Y - 350),
        Zombie(660,GROUND_Y - 350),
        Zombie(700,GROUND_Y - 350),

        # top walkers (hard shots)
        Zombie(450,GROUND_Y - 250, walk=True, left=430, right=620),
        Zombie(580,GROUND_Y - 250, walk=True, left=430, right=620),

        # sneaky corner
        Zombie(830,GROUND_Y - 260),
    ]


    # =====================================================
    # TNT (chain reaction puzzle)
    # =====================================================

    tnts = [

        # clears bottom group
        TNT(350, 500 - TH, radius=95),

        # clears middle corridor
        TNT(300, 380 - TH, radius=95),

        # clears top platform (important combo)
        TNT(540, 250 - TH, radius=110),

        # bonus far right
        TNT(840, 260 - TH, radius=90),
    ]


#------------------ Level 6 -------------------
def init_level_6():

    global bullets_left, bullets, zombies, tnts, walls, state

    player = Player()
    bullets_left = 3
    bullets = []

    ZH = 35
    TH = 20


    # =====================================================
    # WALLS  (OPEN DESIGN — no closed rooms)
    # =====================================================

    walls = [

        # player platform
        Wall(0, PLAYER_Y + 50, 260, 20),

        # mid platform (gap on right for entry)
        Wall(260, 380, 420, 20),

        # upper platform (gap on left)
        Wall(360, 240, 420, 20),

        # bounce guides (NOT closing anything)
        Wall(680, 260, 20, 160),
        Wall(300, 260, 20, 160),
    ]


    # =====================================================
    # ZOMBIES  (properly grounded)
    # =====================================================

    zombies = [

        # ground right group
        Zombie(620, GROUND_Y - 640),
        Zombie(680, GROUND_Y - 700),

        # mid platform
        Zombie(360,GROUND_Y - 380),
        Zombie(430,GROUND_Y - 380),

        # top platform walkers
        Zombie(420,GROUND_Y - 240, speed=1, left = 360, right = 780),
        Zombie(700,GROUND_Y - 240),

        # last survivor (skill shot)
        Zombie(920, GROUND_Y - 840)
    ]


    # =====================================================
    # TNT  (chain reaction but reachable)
    # =====================================================

    tnts = [

        # middle starter TNT (easy first bounce)
        TNT(440, 360),

        # chain
        TNT(500, 360),

        # top pair
        TNT(520, 220),
        TNT(620, 220),

        # ground clear
        TNT(660, GROUND_Y - TH)
    ]



#------------------ level 7 ------------------
def init_level_7():
    global walls, zombies, bullets, tnts, player, bullets_left, special_left, state
    
    # ---------- walls ----------
    ground  = pygame.Rect(0, 610, WIDTH, 40)

    middle  = pygame.Rect(120, 440, 760, 20)
    top     = pygame.Rect(220, 260, 560, 20)

    walls = [
        ground,
        middle,
        top,

        # bounce guides (NOT closed)
        Wall(420, 300, 20, 140),
        Wall(600, 300, 20, 140),

        # borders
        Wall(0,0,WIDTH,10),
        Wall(0,0,10,HEIGHT),
        Wall(WIDTH-10,0,10,HEIGHT)
    ]


    # ---------- player ----------
    start_x = 50
    start_y = GROUND_Y - 50
    player = Player()
    player.rect.x = start_x
    player.rect.y = start_y



    # ---------- zombies ----------
    zombies = []

    # ⭐ main shield boss (middle patrol)
    zombies.append(
        Zombie(350, GROUND_Y - 420, special = True)
    )

    # bodyguards on middle
    zombies += [
        Zombie(250,GROUND_Y - 440),
        Zombie(500, GROUND_Y - 440, speed=1, left=500,right=700),
        Zombie(700, GROUND_Y - 440)
    ]

    # ground crowd (explosion targets)
    for x in [180, 300, 420, 540, 660, 780]:
        zombies.append(Zombie(x,GROUND_Y - 60, speed=0, left=x-20, right=x+20))


    # ---------- TNT ----------
    tnts = [
        TNT(470, middle),   # chain start
        TNT(520, middle),   # chain combo
        TNT(450, ground),   # ground clear
    ]


    # ---------- ammo ----------
    bullets = []
    bullets_left = 4
    special_left = 1
    

#------------------ load level ------------------
def load_level(level_num):
    global walls, zombies, bullets, tnts, bullet_limit, bullets_left, special_left, player, game_over

    
    if level_num == 0:
        init_level_1()
    elif level_num == 1:
        init_level_2()
    elif level_num == 2:
        init_level_3()
    elif level_num == 3:
        init_level_4()
    elif level_num == 4:
        init_level_5()
    elif level_num == 5:
        init_level_6()
    elif level_num == 6:
        init_level_7()
    
    return player, bullets, zombies, walls, tnts, bullets_left, special_left

#------------------ result screen ------------------
def result_screen(state):
    # state = "WIN" or "LOSE"
   
    restart_btn = pygame.Rect(WIDTH//2-80, HEIGHT//2+40, 160, 40)
    next_btn = pygame.Rect(WIDTH//2-80, HEIGHT//2+100, 160, 40)
    lobby_btn = pygame.Rect(WIDTH//2-80, HEIGHT//2+160, 160, 40)

    while True:
        screen.fill(BG_COLOR)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if e.type == pygame.MOUSEBUTTONDOWN:
                if restart_btn.collidepoint(e.pos):
                    return "RESTART"

                if state == "WIN" and next_btn.collidepoint(e.pos):
                    return "NEXT"

                if lobby_btn.collidepoint(e.pos):
                    return "LOBBY"

        # text
        if state == "WIN":
            t = font.render("YOU WIN!", True, (255,215,0))
        else:
            t = font.render("YOU LOSE!", True, (255,80,80))

        screen.blit(t, (WIDTH//2-100, HEIGHT//2-40))

        
        draw_button(restart_btn, "Restart")

        if state == "WIN":
             draw_button(next_btn, "Next Level")

            

        draw_button(lobby_btn, "Lobby")

        pygame.display.update()
        clock.tick(FPS)

# =====================================================
# DRAW HUD
# =====================================================
def draw_hud():
    info = font.render(f"Bullets: {bullets_left}  Special: {special_left}",True,WHITE)
    screen.blit(info,(20,20))

# =====================================================
# MAIN GAME LOOP (ALL LEVELS)
# =====================================================
def game_loop():
    global current_level, highest_level_unlocked
    global player, bullets, zombies, walls, tnts
    global bullets_left, special_left, state, explosions

    running = True

    # ---------- start from lobby first ----------
    current_level = show_lobby()

    while running:

        # ---------- load selected level ----------
        player, bullets, zombies, walls, tnts, bullets_left, special_left = load_level(current_level)
        explosions.clear()
        state = "PLAY"

        # =================================================
        # PLAY LOOP (single level)
        # =================================================
        while state == "PLAY":

            clock.tick(FPS)
            keys = pygame.key.get_pressed()

            # ---------------- EVENTS ----------------
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:

                    # restart
                    if event.key == pygame.K_r:
                        player, bullets, zombies, walls, tnts, bullets_left, special_left = load_level(current_level)

                    # normal bullet
                    if event.key == pygame.K_SPACE and bullets_left > 0:
                        bullets.append(
                            Bullet(player.rect.centerx, player.rect.centery, player.angle)
                        )
                        bullets_left -= 1

                    # special bullet
                    if event.key == pygame.K_e and special_left > 0:
                        bullets.append(
                            Bullet(player.rect.centerx, player.rect.centery, player.angle, special=True)
                        )
                        special_left -= 1

            # ---------------- UPDATE ----------------
            player.update(keys)

            for z in zombies:
                z.update()

            update_explosions()

            # bullets
            remove = []
            for b in bullets:
                b.update(walls)

                for z in zombies:
                    if z.alive and pygame.Rect(b.x-b.radius, b.y-b.radius, b.radius*2, b.radius*2).colliderect(z.rect):
                        z.alive = False

                for t in tnts:
                    if not t.exploded and pygame.Rect(b.x-b.radius, b.y-b.radius, b.radius*2, b.radius*2).colliderect(t.rect):
                        t.explode(zombies)

                if b.expired():
                    remove.append(b)

            for r in remove:
                bullets.remove(r)

            # ---------------- WIN / LOSE CHECK ----------------
            if all(not z.alive for z in zombies):
                state = "WIN"

            elif bullets_left == 0 and special_left == 0 and not bullets:
                if any(z.alive for z in zombies):
                    state = "LOSE"

            # ---------------- DRAW ----------------
            screen.fill(BG_COLOR)

            for w in walls:
                if isinstance(w, pygame.Rect):
                    pygame.draw.rect(screen, GRAY, w)
                else:
                    w.draw()

            for t in tnts:
                t.draw()

            for z in zombies:
                z.draw()

            for b in bullets:
                b.draw()

            draw_explosions()
            player.draw()
            draw_hud()

            pygame.display.flip()
