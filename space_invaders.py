import pygame, random, json, os

# --- Init ---
pygame.init()
W, H = 780, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Space Invaders — Python Edition")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Comic Sans", 15)

# --- Colors ---
WHITE = (255,255,255)
CYAN = (124,242,255)
YELLOW = (255,213,107)
PINK = (255,143,177)
ORANGE = (255,184,107)
GREEN = (141,255,124)
MAGENTA = (255,124,242)
BG = (7,16,38)

# --- High score ---
score, high, level, lives = 0, 0, 1, 3
if os.path.exists("save.json"):
    with open("save.json","r") as f:
        high = json.load(f).get("high",0)

def save_high():
    with open("save.json","w") as f:
        json.dump({"high":high},f)

# --- Entities ---
player = {"x":W//2,"y":H-60,"w":48,"h":18,
          "speed":6,"cooldown":0,"fireRate":12,
          "dbl":False,"shield":False}

bullets = []
enemy_bullets = []
aliens = []
powerups = []

alien_state = {"dir":1,"speed":6,"step":14,"t":0,"shootProb":0.005}

def spawn_aliens(rows=4, cols=10):
    aliens.clear()
    startY = 70; gapX=18; gapY=18
    totalW = cols*36 + (cols-1)*gapX
    offsetX = (W - totalW)//2 + 18
    for r in range(rows):
        for c in range(cols):
            aliens.append({"x":offsetX + c*(36+gapX),
                           "y":startY + r*(28+gapY),
                           "w":36,"h":20,
                           "hp":1+(r//2)})

def reset_game():
    global score, level, lives
    score, level, lives = 0, 1, 3
    player.update({"dbl":False,"shield":False,"fireRate":12})
    bullets.clear(); enemy_bullets.clear(); powerups.clear()
    spawn_aliens(4,10)

def next_level():
    global level
    level += 1
    rows = 4 + level//2
    spawn_aliens(rows,10)
    alien_state["speed"] += 4
    alien_state["shootProb"] += 0.001 * level

def fire_player():
    if player["cooldown"] > 0: return
    bullets.append({"x":player["x"],"y":player["y"]-12,"vy":-10})
    if player["dbl"]:
        bullets.append({"x":player["x"]+12,"y":player["y"]-12,"vy":-10})
    player["cooldown"] = player["fireRate"]

def alien_shoot():
    if random.random() < alien_state["shootProb"]:
        # bottom-most alien from a random column
        cols = {}
        for a in aliens:
            col = int((a["x"]-20)/54)
            if col not in cols or a["y"] > cols[col]["y"]:
                cols[col] = a
        if cols:
            a = random.choice(list(cols.values()))
            enemy_bullets.append({"x":a["x"],"y":a["y"]+18,"vy":5})

def spawn_power(x,y):
    types = ["shield","rapid","double"]
    powerups.append({"x":x,"y":y,"type":random.choice(types),"t":0})

def apply_power(p):
    if p["type"]=="shield":
        player["shield"]=True
        pygame.time.set_timer(pygame.USEREVENT+1,7000,True)
    elif p["type"]=="rapid":
        player["fireRate"]=5
        pygame.time.set_timer(pygame.USEREVENT+2,7000,True)
    elif p["type"]=="double":
        player["dbl"]=True
        pygame.time.set_timer(pygame.USEREVENT+3,7000,True)

def rect_coll(a,b):
    return (a["x"]-a["w"]//2 < b["x"]+b["w"]//2 and
            a["x"]+a["w"]//2 > b["x"]-b["w"]//2 and
            a["y"]-a["h"]//2 < b["y"]+b["h"]//2 and
            a["y"]+a["h"]//2 > b["y"]-b["h"]//2)

# --- Game loop ---
reset_game()
running, paused, gameover = True, False, False
message = "Press SPACE to fire, ←/→ to move"

while running:
    for e in pygame.event.get():
        if e.type==pygame.QUIT: running=False
        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_p: paused = not paused
            if e.key==pygame.K_r: reset_game(); gameover=False
        # timers for power-up expiration
        if e.type==pygame.USEREVENT+1: player["shield"]=False
        if e.type==pygame.USEREVENT+2: player["fireRate"]=12
        if e.type==pygame.USEREVENT+3: player["dbl"]=False

    if not paused and not gameover:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: player["x"] -= player["speed"]
        if keys[pygame.K_RIGHT]: player["x"] += player["speed"]
        player["x"] = max(26,min(W-26,player["x"]))

        if keys[pygame.K_SPACE]: fire_player()
        if player["cooldown"]>0: player["cooldown"]-=1

        # update bullets
        for b in bullets[:]:
            b["y"] += b["vy"]
            if b["y"]<0: bullets.remove(b)

        for b in enemy_bullets[:]:
            b["y"] += b["vy"]
            if b["y"]>H: enemy_bullets.remove(b)

        # move aliens
        alien_state["t"] += 1
        if alien_state["t"]>20:
            alien_state["t"]=0
            edge=False
            for a in aliens: 
                a["x"] += alien_state["dir"]*alien_state["speed"]
                if a["x"]<16 or a["x"]>W-16: edge=True
            if edge:
                alien_state["dir"]*=-1
                for a in aliens: a["y"] += alien_state["step"]

        alien_shoot()

        # collisions bullets vs aliens
        for b in bullets[:]:
            for a in aliens[:]:
                if rect_coll({"x":b["x"],"y":b["y"],"w":8,"h":8},a):
                    bullets.remove(b)
                    a["hp"]-=1
                    if a["hp"]<=0:
                        aliens.remove(a)
                        score += 10 + (level*2)
                        if random.random()<0.12: spawn_power(a["x"],a["y"])
                    else:
                        score += 4
                    break

        # enemy bullets vs player
        for b in enemy_bullets[:]:
            if rect_coll({"x":b["x"],"y":b["y"],"w":8,"h":8},
                         {"x":player["x"],"y":player["y"],"w":player["w"],"h":player["h"]}):
                enemy_bullets.remove(b)
                if not player["shield"]:
                    lives -=1
                    if lives<=0:
                        gameover=True
                        message="Game Over — Press R to restart"
                break

        # aliens reach bottom
        for a in aliens:
            if a["y"]+a["h"]//2 >= player["y"]-20:
                gameover=True
                message="Game Over — Press R to restart"

        # powerups
        for p in powerups[:]:
            p["y"]+=2
            if rect_coll({"x":p["x"],"y":p["y"],"w":18,"h":18},
                         {"x":player["x"],"y":player["y"],"w":player["w"],"h":player["h"]}):
                apply_power(p)
                powerups.remove(p)
            elif p["y"]>H: powerups.remove(p)

        if not aliens: next_level()

        if score>high: high=score; save_high()

    # --- Draw ---
    screen.fill(BG)
    # player
    color = CYAN if not player["shield"] else (124,242,255,120)
    pygame.draw.rect(screen,color,(player["x"]-player["w"]//2,
                                   player["y"]-player["h"]//2,
                                   player["w"],player["h"]))
    # bullets
    for b in bullets:
        pygame.draw.rect(screen,WHITE,(b["x"],b["y"],4,12))
    for b in enemy_bullets:
        pygame.draw.rect(screen,ORANGE,(b["x"],b["y"],4,12))
    # aliens
    for a in aliens:
        c = PINK if a["hp"]>1 else YELLOW
        pygame.draw.rect(screen,c,(a["x"]-a["w"]//2,a["y"]-a["h"]//2,a["w"],a["h"]))
    # powerups
    for p in powerups:
        c = CYAN if p["type"]=="shield" else GREEN if p["type"]=="rapid" else MAGENTA
        pygame.draw.circle(screen,c,(p["x"],p["y"]),8)

    # HUD
    hud = font.render(f"Score:{score}  High:{high}  Lives:{lives}  Level:{level}",True,WHITE)
    screen.blit(hud,(10,10))
    msg = font.render(message,True,WHITE)
    screen.blit(msg,(10,H-30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()