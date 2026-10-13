from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import os
import io
import wave

PYGAME_AUDIO = False
pistol_sfx = None
tower_sfx = None

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AUDIO = True
except Exception:
    PYGAME_AUDIO = False

def _create_synth_sound(freq, duration=0.05, volume=0.4):
    if not PYGAME_AUDIO:
        return None
    try:
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        bio = io.BytesIO()
        with wave.open(bio, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(1)
            wf.setframerate(sample_rate)
            data = bytearray()
            for i in range(n_samples):
                env = (1.0 - i / float(n_samples))
                val = int(128 + 120 * volume * env * math.sin(2.0 * math.pi * freq * i / sample_rate))
                data.append(max(0, min(255, val)))
            wf.writeframes(bytes(data))
        bio.seek(0)
        return pygame.mixer.Sound(bio)
    except Exception:
        return None

if PYGAME_AUDIO:
    pistol_sfx = _create_synth_sound(1250, 0.06, 0.5)
    tower_sfx = _create_synth_sound(680, 0.04, 0.3)

def play_mp3(filename):
    if not PYGAME_AUDIO:
        return
    try:
        full_path = os.path.abspath(filename)
        if os.path.exists(full_path):
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.play(-1)
    except Exception:
        pass

def stop_mp3():
    if not PYGAME_AUDIO:
        return
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

def play_sfx(sound_type):
    if not PYGAME_AUDIO:
        return
    try:
        if sound_type == "pistol" and pistol_sfx:
            pistol_sfx.play()
        elif sound_type == "tower" and tower_sfx:
            tower_sfx.play()
    except Exception:
        pass

WIN_WIDTH = 800
WIN_HEIGHT = 640
LINE_WIDTH = 1.0

STATE_MAIN_MENU = 0
STATE_MENU_CREDITS = 1
STATE_NAME_INPUT = 2
STATE_PROLOGUE = 3
STATE_CALL_CHOICE = 4
STATE_CALL_CONVO = 5
STATE_TD = 6
STATE_SULLY_AWAKENING = 7
STATE_FPS = 8
STATE_BOMB_PLANTED = 9
STATE_EPILOGUE_STORY = 10
STATE_EPILOGUE_CHOICE = 11
STATE_EPILOGUE_OUTCOME = 12
STATE_CREDITS_ROLL = 13
STATE_GAME_OVER = 14

game_state = STATE_MAIN_MENU

player_name = ""
called_mom = False
prologue_index = 0
call_convo_index = 0
sully_index = 0
epilogue_index = 0
moral_choice = 0
extraction_music_started = False

camera_pos = (0, -700, 750)
camera_mode = 0
CAMERA_PRESETS = [(0, -700, 750), (0, 0, 1100)]
fovY = 100
GRID_LENGTH = 600

CAMERA_ORBIT_STEP = 12
CAMERA_HEIGHT_STEP = 40
CAMERA_RADIUS = 700
CAMERA_HEIGHT_MIN = 250
CAMERA_HEIGHT_MAX = 1400
camera_orbit_angle = 0.0
camera_height = 750.0

quadric = None

player_pos = [320.0, -150.0, 25.0]
player_yaw = 140.0
player_pitch = 0.0
player_hp = 100
player_max_hp = 100
player_speed = 9.5
turn_speed = 7.0
pitch_speed = 4.5
pistol_cooldown = 0
fps_bullets = []

FACTORY_POS = (-570, 570)
EXTRACTION_POS = (350, -150)
EXTRACTION_RADIUS = 160
bomb_timer = 25.0 * 60
bomb_planted = False
explosion_radius = 10.0
factory_destroyed = False

def update_camera_pos():
    global camera_pos
    rad = math.radians(camera_orbit_angle)
    x = CAMERA_RADIUS * math.sin(rad)
    y = -CAMERA_RADIUS * math.cos(rad)
    camera_pos = (x, y, camera_height)

def DrawLine(x1, y1, x2, y2, point_size=None, z1=0.0, z2=0.0):
    glLineWidth(LINE_WIDTH if point_size is None else point_size)
    glBegin(GL_LINES)
    glVertex3f(float(x1), float(y1), float(z1))
    glVertex3f(float(x2), float(y2), float(z2))
    glEnd()

def draw_circle_outline(cx, cy, r, z=2.0, segments=32, point_size=None):
    glLineWidth(LINE_WIDTH if point_size is None else point_size)
    glBegin(GL_LINES)
    for i in range(segments):
        theta1 = 2.0 * math.pi * i / segments
        theta2 = 2.0 * math.pi * (i + 1) / segments
        glVertex3f(cx + r * math.cos(theta1), cy + r * math.sin(theta1), float(z))
        glVertex3f(cx + r * math.cos(theta2), cy + r * math.sin(theta2), float(z))
    glEnd()

CELL = 60
PATH = [
    (-570, 570), (-570, -330), (-150, -330), (-150, 330),
    (270, 330), (270, -150), (570, -150)
]

MAX_LEVEL = 4
CONVERT_COST = 40
PLACEMENT_MARGIN = 20

TOWER_TYPES = {
    "cannon": ((0.8, 0.1, 0.1), 12, 190, 48, 60),
    "frost":  ((0.2, 0.5, 0.9), 6,  170, 70, 70),
    "sniper": ((0.9, 0.8, 0.1), 30, 340, 108, 90),
}

KINDS = {
    "scout":   ((0.9, 0.9, 0.2), 18, 2.6, 5, 16),
    "soldier": ((0.8, 0.3, 0.1), 35, 1.7, 10, 24),
    "brute":   ((0.5, 0.1, 0.6), 70, 1.0, 20, 34),
}

COMBO_DISTANCE = CELL * 1.5
SHATTER_BONUS_MULT = 1.8
BURST_COMBO_MULT = 1.6
COMBO_SLOW_DURATION = 180

BRUTE_ATTACK_RANGE = 180
BRUTE_ATTACK_INTERVAL_BASE = 240
BRUTE_ATTACK_INTERVAL_MIN = 90
BRUTE_ATTACK_WAVE_STEP = 12
BRUTE_TOWER_DAMAGE_MIN = 1
BRUTE_TOWER_DAMAGE_MAX = 3
MIN_TOWER_DAMAGE = 3
TOWER_MAX_WEAR_TICKS = 4

def brute_attack_interval():
    return max(BRUTE_ATTACK_INTERVAL_MIN, BRUTE_ATTACK_INTERVAL_BASE - (wave - 1) * BRUTE_ATTACK_WAVE_STEP)

def brute_tower_damage():
    return min(BRUTE_TOWER_DAMAGE_MAX, BRUTE_TOWER_DAMAGE_MIN + (wave - 1) // 3)

coins = 150
lives = 5
wave = 1
cheat_mode = False

cursor = [0, 0]
selected_type = "cannon"

towers = []
enemies = []
projectiles = []
decorations = []
brute_attacks = []

spawn_timer = 0
wave_spawned = 0
wave_total = 4
spawn_interval_frames = 170
wave_message_timer = 0

rain_on = True
raindrops = []
RAIN_COUNT = 200
RAIN_FALL_SPEED = 5
RAIN_WIND = 1.2

day_timer = 0
DAY_CYCLE_LENGTH = 12000
current_daylight = 1.0
NIGHT_FADE_STEP = 1.0 / 600.0
night_mode_on = False
night_mode_recovering = False

def point_seg_dist(px, py, ax, ay, bx, by):
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    ab2 = abx * abx + aby * aby
    t = 0 if ab2 == 0 else max(0, min(1, (apx * abx + apy * aby) / ab2))
    cx, cy = ax + abx * t, ay + aby * t
    return math.hypot(px - cx, py - cy)

def dist_to_path(x, y):
    return min(
        point_seg_dist(x, y, PATH[i][0], PATH[i][1], PATH[i + 1][0], PATH[i + 1][1])
        for i in range(len(PATH) - 1)
    )

def find_tower_at_cursor():
    for t in towers:
        if abs(t['x'] - cursor[0]) < CELL / 2 and abs(t['y'] - cursor[1]) < CELL / 2:
            return t
    return None

def check_placement_validity():
    cost = TOWER_TYPES[selected_type][4]
    rng = TOWER_TYPES[selected_type][2]
    if coins < cost:
        return False, f"Need {cost} Coins"
    d_path = dist_to_path(cursor[0], cursor[1])
    if d_path < 55:
        return False, "Too Close to Road"
    if d_path > rng - PLACEMENT_MARGIN:
        return False, "Too Far from Road"
    for t in towers:
        if abs(t['x'] - cursor[0]) < CELL - 1 and abs(t['y'] - cursor[1]) < CELL - 1:
            return False, "Tile Occupied"
    return True, "Valid Placement (SPACE)"

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

def draw_wrapped_text(x, y, text, max_chars=68, line_spacing=24, font=GLUT_BITMAP_HELVETICA_18):
    words = text.split(' ')
    lines = []
    current_line = ""
    for w in words:
        if len(current_line) + len(w) + 1 <= max_chars:
            current_line = current_line + " " + w if current_line else w
        else:
            lines.append(current_line)
            current_line = w
    if current_line:
        lines.append(current_line)

    for i, line in enumerate(lines):
        draw_text(x, y - i * line_spacing, line, font)

def update_daynight():
    global day_timer, current_daylight, night_mode_recovering
    if game_state == STATE_BOMB_PLANTED:
        current_daylight = (math.sin(day_timer * 0.15) + 1) / 2
        day_timer += 1
        return
    if night_mode_on:
        current_daylight = max(0.0, current_daylight - NIGHT_FADE_STEP)
        return
    if night_mode_recovering:
        current_daylight = min(1.0, current_daylight + NIGHT_FADE_STEP)
        if current_daylight >= 1.0:
            night_mode_recovering = False
            day_timer = 0
        return
    day_timer = (day_timer + 1) % DAY_CYCLE_LENGTH
    current_daylight = (math.sin(2 * math.pi * day_timer / DAY_CYCLE_LENGTH) + 1) / 2

def init_raindrops():
    raindrops.clear()
    for _ in range(RAIN_COUNT):
        x = random.uniform(-GRID_LENGTH, GRID_LENGTH)
        y = random.uniform(-GRID_LENGTH, GRID_LENGTH)
        z = random.uniform(50, 500)
        raindrops.append([x, y, z])

def update_rain():
    if not rain_on:
        return
    for d in raindrops:
        d[1] -= RAIN_WIND
        d[2] -= RAIN_FALL_SPEED
        if d[2] < 0:
            d[0] = random.uniform(-GRID_LENGTH, GRID_LENGTH)
            d[1] = random.uniform(-GRID_LENGTH, GRID_LENGTH)
            d[2] = 500

def draw_rain():
    if not rain_on:
        return
    dim = 0.4 + 0.6 * current_daylight
    glColor3f(0.6 * dim, 0.7 * dim, 1.0 * dim)
    for x, y, z in raindrops:
        DrawLine(x, y, x, y + RAIN_WIND * 3, point_size=LINE_WIDTH, z1=z, z2=z - 15)

def init_decorations():
    decorations.clear()
    tries = 0
    while len(decorations) < 45 and tries < 500:
        tries += 1
        x = random.uniform(-GRID_LENGTH + 40, GRID_LENGTH - 40)
        y = random.uniform(-GRID_LENGTH + 40, GRID_LENGTH - 40)
        if dist_to_path(x, y) < 70 or math.hypot(x - FACTORY_POS[0], y - FACTORY_POS[1]) < 130:
            continue
        kind = random.choice(['tree', 'tree', 'rock'])
        decorations.append({'x': x, 'y': y, 'kind': kind, 'scale': random.uniform(0.8, 1.3)})

def draw_decorations():
    dim = 0.5 + 0.5 * current_daylight
    for d in decorations:
        glPushMatrix()
        glTranslatef(d['x'], d['y'], 0)
        glScalef(d['scale'], d['scale'], d['scale'])
        if d['kind'] == 'tree':
            glColor3f(0.35 * dim, 0.22 * dim, 0.12 * dim)
            gluCylinder(quadric, 8, 6, 50, 8, 8)
            glTranslatef(0, 0, 55)
            glColor3f(0.1 * dim, 0.5 * dim, 0.15 * dim)
            gluSphere(quadric, 30, 10, 10)
        else:
            glColor3f(0.45 * dim, 0.45 * dim, 0.48 * dim)
            glTranslatef(0, 0, 10)
            glutSolidCube(20)
        glPopMatrix()

MOUNTAIN_SEGS = 36

def stitch_loop(h_list, blend_steps=5):
    diff = h_list[0] - h_list[-1]
    n = len(h_list) - 1
    for step in range(blend_steps + 1):
        idx = n - blend_steps + step
        t = step / float(blend_steps)
        smooth_t = 0.5 * (1.0 - math.cos(math.pi * t))
        h_list[idx] += diff * smooth_t
    return h_list

RIDGE_NEAR_H = stitch_loop([260 + 80 * math.sin(i * 0.7) + 40 * math.cos(i * 1.5 + 0.3) for i in range(MOUNTAIN_SEGS + 1)])
RIDGE_VALLEY_H = stitch_loop([120 + 35 * math.sin(i * 0.7 + 0.5) + 20 * math.cos(i * 1.5) for i in range(MOUNTAIN_SEGS + 1)])
RIDGE_FAR_H = stitch_loop([540 + 190 * math.sin(i * 0.45 + 1.2) + 95 * math.cos(i * 1.25) for i in range(MOUNTAIN_SEGS + 1)])
FOOTHILL_TREES = []
for _ in range(45):
    ang = random.uniform(0, 2 * math.pi)
    dst = random.uniform(GRID_LENGTH + 35, 880)
    FOOTHILL_TREES.append((dst * math.cos(ang), dst * math.sin(ang), random.uniform(0.9, 1.4)))

def draw_border_walls():
    dim = 0.38 + 0.62 * current_daylight
    g_in = GRID_LENGTH
    g_skirt = 1150

    glBegin(GL_QUADS)
    glColor3f(0.13 * dim, 0.28 * dim, 0.13 * dim); glVertex3f(-g_in, g_in, 0); glVertex3f(g_in, g_in, 0)
    glColor3f(0.08 * dim, 0.18 * dim, 0.09 * dim); glVertex3f(g_skirt, g_skirt, 0); glVertex3f(-g_skirt, g_skirt, 0)

    glColor3f(0.13 * dim, 0.28 * dim, 0.13 * dim); glVertex3f(g_in, g_in, 0); glVertex3f(g_in, -g_in, 0)
    glColor3f(0.08 * dim, 0.18 * dim, 0.09 * dim); glVertex3f(g_skirt, -g_skirt, 0); glVertex3f(g_skirt, g_skirt, 0)

    glColor3f(0.13 * dim, 0.28 * dim, 0.13 * dim); glVertex3f(g_in, -g_in, 0); glVertex3f(-g_in, -g_in, 0)
    glColor3f(0.08 * dim, 0.18 * dim, 0.09 * dim); glVertex3f(-g_skirt, -g_skirt, 0); glVertex3f(g_skirt, -g_skirt, 0)

    glColor3f(0.13 * dim, 0.28 * dim, 0.13 * dim); glVertex3f(-g_in, -g_in, 0); glVertex3f(-g_in, g_in, 0)
    glColor3f(0.08 * dim, 0.18 * dim, 0.09 * dim); glVertex3f(-g_skirt, g_skirt, 0); glVertex3f(-g_skirt, -g_skirt, 0)
    glEnd()

    for tx, ty, s in FOOTHILL_TREES:
        glPushMatrix()
        glTranslatef(tx, ty, 0)
        glScalef(s, s, s)
        glColor3f(0.18 * dim, 0.12 * dim, 0.06 * dim)
        gluCylinder(quadric, 6, 4, 45, 6, 6)
        glTranslatef(0, 0, 45)
        glColor3f(0.07 * dim, 0.20 * dim, 0.09 * dim)
        gluSphere(quadric, 24, 8, 8)
        glPopMatrix()

    r0, r1, r2, r3, r4 = 920, 1150, 1380, 1780, 2500

    glBegin(GL_QUADS)
    for i in range(MOUNTAIN_SEGS):
        t1 = 2 * math.pi * i / MOUNTAIN_SEGS
        t2 = 2 * math.pi * (i + 1) / MOUNTAIN_SEGS

        c1, s1 = math.cos(t1), math.sin(t1)
        c2, s2 = math.cos(t2), math.sin(t2)

        x0a, y0a, x0b, y0b = r0 * c1, r0 * s1, r0 * c2, r0 * s2
        x1a, y1a, x1b, y1b = r1 * c1, r1 * s1, r1 * c2, r1 * s2
        x2a, y2a, x2b, y2b = r2 * c1, r2 * s1, r2 * c2, r2 * s2
        x3a, y3a, x3b, y3b = r3 * c1, r3 * s1, r3 * c2, r3 * s2
        x4a, y4a, x4b, y4b = r4 * c1, r4 * s1, r4 * c2, r4 * s2

        h1a, h1b = RIDGE_NEAR_H[i], RIDGE_NEAR_H[i + 1]
        h2a, h2b = RIDGE_VALLEY_H[i], RIDGE_VALLEY_H[i + 1]
        h3a, h3b = RIDGE_FAR_H[i], RIDGE_FAR_H[i + 1]

        glColor3f(0.12 * dim, 0.24 * dim, 0.12 * dim); glVertex3f(x0a, y0a, 0); glVertex3f(x0b, y0b, 0)
        glColor3f(0.22 * dim, 0.26 * dim, 0.28 * dim); glVertex3f(x1b, y1b, h1b); glVertex3f(x1a, y1a, h1a)

        glColor3f(0.22 * dim, 0.26 * dim, 0.28 * dim); glVertex3f(x1a, y1a, h1a); glVertex3f(x1b, y1b, h1b)
        glColor3f(0.11 * dim, 0.16 * dim, 0.20 * dim); glVertex3f(x2b, y2b, h2b); glVertex3f(x2a, y2a, h2a)

        glColor3f(0.11 * dim, 0.16 * dim, 0.20 * dim); glVertex3f(x2a, y2a, h2a); glVertex3f(x2b, y2b, h2b)
        glColor3f(0.44 * dim, 0.52 * dim, 0.68 * dim); glVertex3f(x3b, y3b, h3b); glVertex3f(x3a, y3a, h3a)

        glColor3f(0.44 * dim, 0.52 * dim, 0.68 * dim); glVertex3f(x3a, y3a, h3a); glVertex3f(x3b, y3b, h3b)
        glColor3f(0.30 * dim, 0.38 * dim, 0.50 * dim); glVertex3f(x4b, y4b, -20); glVertex3f(x4a, y4a, -20)
    glEnd()

def draw_spawner_spire():
    if factory_destroyed:
        return
    fx, fy = FACTORY_POS
    glPushMatrix()
    glTranslatef(fx, fy, 0)
    
    glColor3f(0.18, 0.16, 0.20)
    glTranslatef(0, 0, 45)
    glutSolidCube(90)
    
    glTranslatef(0, 0, 50)
    glColor3f(0.28, 0.18, 0.24)
    glutSolidCube(60)

    core_pulse = 0.6 + 0.4 * math.sin(day_timer * 0.1)
    glColor3f(1.0 * core_pulse, 0.1, 0.1)
    gluSphere(quadric, 22, 10, 10)

    glTranslatef(-25, -25, 30)
    glColor3f(0.12, 0.12, 0.12)
    gluCylinder(quadric, 8, 6, 50, 8, 8)
    glTranslatef(50, 0, 0)
    gluCylinder(quadric, 8, 6, 50, 8, 8)
    glPopMatrix()

    if game_state == STATE_FPS:
        glColor3f(1.0, 0.3, 0.1)
        draw_circle_outline(fx, fy, 90, z=2, segments=24)

def draw_bomb_and_blast():
    fx, fy = FACTORY_POS
    if bomb_planted and not factory_destroyed:
        glPushMatrix()
        glTranslatef(fx + 25, fy - 25, 12)
        blink = (int(bomb_timer) // 12) % 2 == 0
        if blink:
            glColor3f(1.0, 0.1, 0.1)
        else:
            glColor3f(0.2, 0.2, 0.2)
        glutSolidCube(18)
        glPopMatrix()

    if game_state in (STATE_EPILOGUE_STORY, STATE_EPILOGUE_CHOICE, STATE_EPILOGUE_OUTCOME, STATE_CREDITS_ROLL) and explosion_radius < 600:
        glPushMatrix()
        glTranslatef(fx, fy, 40)
        glColor3f(1.0, 0.45, 0.1)
        gluSphere(quadric, explosion_radius, 16, 16)
        glPopMatrix()

def draw_extraction_zone():
    if game_state != STATE_BOMB_PLANTED:
        return

    ex, ey = EXTRACTION_POS

    glColor3f(0.1, 0.95, 0.3)
    draw_circle_outline(ex, ey, EXTRACTION_RADIUS, z=2, segments=32)

    pulse_r = (day_timer * 3.0) % EXTRACTION_RADIUS
    glColor3f(0.2, 0.7, 0.3)
    draw_circle_outline(ex, ey, pulse_r, z=2, segments=24)

    glPushMatrix()
    glTranslatef(ex, ey, 0)
    glColor3f(0.1, 0.95, 0.3)
    gluCylinder(quadric, 3.0, 1.5, 240, 8, 8)
    glTranslatef(0, 0, 240)
    gluSphere(quadric, 6, 8, 8)
    glPopMatrix()

    strobe = (day_timer // 14) % 2 == 0
    for dx, dy in [(EXTRACTION_RADIUS, 0), (-EXTRACTION_RADIUS, 0), (0, EXTRACTION_RADIUS), (0, -EXTRACTION_RADIUS)]:
        glPushMatrix()
        glTranslatef(ex + dx, ey + dy, 5)
        if strobe:
            glColor3f(1.0, 0.9, 0.1)
        else:
            glColor3f(0.1, 0.3, 0.1)
        glutSolidCube(10)
        glPopMatrix()

def draw_fps_bullets():
    for b in fps_bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], b['z'])
        glColor3f(1.0, 0.85, 0.2)
        gluSphere(quadric, 3.5, 6, 6)
        glPopMatrix()

def spawn_enemy():
    kind = random.choice(list(KINDS.keys()))
    color, base_hp, base_speed, reward, base_radius = KINDS[kind]
    hp = base_hp * (1 + (wave - 1) * 0.22)
    speed = base_speed * (1 + (wave - 1) * 0.03)
    x, y = PATH[0]
    jitter = tuple(max(0.0, min(1.0, c + random.uniform(-0.12, 0.12))) for c in color)
    enemy_data = {
        'x': x, 'y': y, 'wp': 1, 'hp': hp, 'max_hp': hp,
        'speed': speed, 'kind': kind, 'color': jitter, 'radius': base_radius,
        'slow_timer': 0, 'reward': reward + wave,
        'size_mult': random.uniform(0.8, 1.3),
        'pulse': random.uniform(0.9, 1.1),
        'growing': random.choice([True, False]),
    }
    if kind == 'brute':
        enemy_data['attack_timer'] = brute_attack_interval()
    enemies.append(enemy_data)

def update_enemies():
    global lives, player_hp, game_state
    for e in enemies[:]:
        rate = 0.004
        if e['growing']:
            e['pulse'] += rate
            if e['pulse'] >= 1.15:
                e['growing'] = False
        else:
            e['pulse'] -= rate
            if e['pulse'] <= 0.85:
                e['growing'] = True

        if game_state in (STATE_FPS, STATE_BOMB_PLANTED):
            d_player = math.hypot(player_pos[0] - e['x'], player_pos[1] - e['y'])
            if d_player < 28:
                if not cheat_mode:
                    player_hp -= 0.6
                if player_hp <= 0:
                    player_hp = 0
                    game_state = STATE_GAME_OVER
            if d_player < 280:
                dx, dy = player_pos[0] - e['x'], player_pos[1] - e['y']
                spd = e['speed'] * 0.8
                e['x'] += (dx / d_player) * spd
                e['y'] += (dy / d_player) * spd
                continue

        if e['kind'] == 'brute':
            e['attack_timer'] = e.get('attack_timer', brute_attack_interval()) - 1
            if e['attack_timer'] <= 0:
                e['attack_timer'] = brute_attack_interval()
                best_tower, best_dist = None, None
                for t in towers:
                    dist = math.hypot(t['x'] - e['x'], t['y'] - e['y'])
                    if dist <= BRUTE_ATTACK_RANGE and (best_dist is None or dist < best_dist):
                        best_tower, best_dist = t, dist
                if best_tower is not None:
                    if not cheat_mode:
                        floor_dmg = max(MIN_TOWER_DAMAGE, int(TOWER_TYPES[best_tower['type']][1] * 0.4))
                        if best_tower['damage'] > floor_dmg:
                            best_tower['damage'] = max(floor_dmg, best_tower['damage'] - brute_tower_damage())
                            best_tower['wear_ticks'] = 0
                        else:
                            best_tower['wear_ticks'] = best_tower.get('wear_ticks', 0) + 1
                            if best_tower['wear_ticks'] >= TOWER_MAX_WEAR_TICKS:
                                towers.remove(best_tower)
                    brute_attacks.append({
                        'x1': e['x'], 'y1': e['y'], 'z1': e['radius'] * e['size_mult'] * 1.2,
                        'x2': best_tower['x'], 'y2': best_tower['y'], 'z2': 30,
                        'timer': 10,
                    })

        tx, ty = PATH[e['wp']]
        dx, dy = tx - e['x'], ty - e['y']
        d = math.hypot(dx, dy)
        spd = e['speed'] * (0.4 if e['slow_timer'] > 0 else 1.0)
        if e['slow_timer'] > 0:
            e['slow_timer'] -= 1
        if d < spd:
            e['x'], e['y'] = tx, ty
            e['wp'] += 1
            if e['wp'] >= len(PATH):
                enemies.remove(e)
                lives -= 1
                if lives <= 0:
                    game_state = STATE_GAME_OVER
        else:
            e['x'] += dx / d * spd
            e['y'] += dy / d * spd

def start_next_wave():
    global wave, wave_spawned, wave_total, spawn_interval_frames, wave_message_timer, game_state, sully_index
    if wave == 5:
        if called_mom:
            game_state = STATE_SULLY_AWAKENING
            sully_index = 0
            return

    wave += 1
    wave_spawned = 0
    wave_total = 4 + (wave - 1) * 3
    spawn_interval_frames = max(40, 170 - (wave - 1) * 15)
    wave_message_timer = 90

def place_tower():
    global coins
    is_valid, _ = check_placement_validity()
    if not is_valid:
        return
    cost = TOWER_TYPES[selected_type][4]
    _, dmg, rng, cd, _ = TOWER_TYPES[selected_type]
    towers.append({
        'x': cursor[0], 'y': cursor[1], 'type': selected_type,
        'level': 1, 'damage': dmg, 'range': rng,
        'cooldown_frames': cd, 'cooldown_left': 0,
        'wear_ticks': 0,
    })
    coins -= cost

def upgrade_tower():
    global coins
    t = find_tower_at_cursor()
    if t is None or t['level'] >= MAX_LEVEL:
        return
    _, base_dmg, base_rng, base_cd, base_cost = TOWER_TYPES[t['type']]
    cost = int(base_cost * 0.8 * t['level'])
    if coins < cost:
        return
    coins -= cost
    t['level'] += 1
    t['damage'] = int(base_dmg * (1 + 0.35 * (t['level'] - 1)))
    t['range'] = int(base_rng * (1 + 0.12 * (t['level'] - 1)))
    t['cooldown_frames'] = max(12, int(base_cd * (1 - 0.15 * (t['level'] - 1))))
    t['wear_ticks'] = 0

def change_tower_type():
    global coins
    t = find_tower_at_cursor()
    if t is None or coins < CONVERT_COST:
        return
    order = list(TOWER_TYPES.keys())
    nxt = order[(order.index(t['type']) + 1) % len(order)]
    coins -= CONVERT_COST
    _, dmg, rng, cd, _ = TOWER_TYPES[nxt]
    t['type'] = nxt
    t['level'] = 1
    t['damage'], t['range'], t['cooldown_frames'] = dmg, rng, cd
    t['cooldown_left'] = 0
    t['wear_ticks'] = 0

def update_towers():
    for t in towers:
        if t['cooldown_left'] > 0:
            t['cooldown_left'] -= 1

    fired_towers = set()
    cheat_mult = 2 if cheat_mode else 1

    for i in range(len(towers)):
        t1 = towers[i]
        if id(t1) in fired_towers or t1['cooldown_left'] > 0:
            continue

        partner = None
        for j in range(len(towers)):
            if i == j:
                continue
            t2 = towers[j]
            if id(t2) in fired_towers or t2['cooldown_left'] > 0:
                continue
            if t1['type'] != t2['type']:
                d_pair = math.hypot(t1['x'] - t2['x'], t1['y'] - t2['y'])
                if d_pair <= COMBO_DISTANCE:
                    partner = t2
                    break

        if partner is not None:
            t2 = partner
            mid_x = (t1['x'] + t2['x']) / 2.0
            mid_y = (t1['y'] + t2['y']) / 2.0
            best, best_d = None, None
            for e in enemies:
                d1 = math.hypot(e['x'] - t1['x'], e['y'] - t1['y'])
                d2 = math.hypot(e['x'] - t2['x'], e['y'] - t2['y'])
                if d1 <= t1['range'] or d2 <= t2['range']:
                    d_mid = math.hypot(e['x'] - mid_x, e['y'] - mid_y)
                    if best is None or d_mid < best_d:
                        best, best_d = e, d_mid

            if best is not None:
                types = {t1['type'], t2['type']}
                if types == {'cannon', 'frost'}:
                    dmg = int((t1['damage'] + t2['damage']) * 1.1 * cheat_mult)
                    kind = 'combo_shatter'
                    color = (0.9, 0.2, 0.85)
                elif types == {'cannon', 'sniper'}:
                    dmg = int((t1['damage'] + t2['damage']) * BURST_COMBO_MULT * cheat_mult)
                    kind = 'combo_burst'
                    color = (1.0, 0.5, 0.0)
                else:
                    dmg = int((t1['damage'] + t2['damage']) * 1.2 * cheat_mult)
                    kind = 'combo_freeze'
                    color = (0.1, 0.9, 0.95)

                projectiles.append({
                    'x': mid_x, 'y': mid_y, 'z': 70,
                    'target': best, 'dmg': dmg,
                    'kind': kind, 'color': color,
                    'size': 10,
                })
                play_sfx("tower")
                t1['cooldown_left'] = t1['cooldown_frames']
                t2['cooldown_left'] = t2['cooldown_frames']
                fired_towers.add(id(t1))
                fired_towers.add(id(t2))
                continue

    for t in towers:
        if id(t) in fired_towers or t['cooldown_left'] > 0:
            continue
        best, best_d = None, None
        for e in enemies:
            d = math.hypot(e['x'] - t['x'], e['y'] - t['y'])
            if d <= t['range'] and (best is None or d < best_d):
                best, best_d = e, d
        if best is not None:
            color = TOWER_TYPES[t['type']][0]
            dmg = int(t['damage'] * cheat_mult)
            projectiles.append({
                'x': t['x'], 'y': t['y'], 'z': 70,
                'target': best, 'dmg': dmg,
                'kind': t['type'], 'color': color,
                'size': 6,
            })
            play_sfx("tower")
            t['cooldown_left'] = t['cooldown_frames']
            fired_towers.add(id(t))

def apply_hit(p):
    global coins
    tgt = p['target']
    if tgt not in enemies:
        return
    dmg = p['dmg']
    kind = p['kind']
    if kind == 'combo_shatter':
        if tgt['slow_timer'] > 0:
            dmg = int(dmg * SHATTER_BONUS_MULT)
        tgt['slow_timer'] = 90
    elif kind == 'combo_freeze':
        tgt['slow_timer'] = COMBO_SLOW_DURATION
    elif kind == 'frost':
        tgt['slow_timer'] = 90

    tgt['hp'] -= dmg
    if tgt['hp'] <= 0:
        coins += tgt['reward']
        enemies.remove(tgt)

def update_projectiles():
    for p in projectiles[:]:
        tgt = p['target']
        if tgt not in enemies:
            projectiles.remove(p)
            continue
        dx, dy = tgt['x'] - p['x'], tgt['y'] - p['y']
        d = math.hypot(dx, dy)
        speed = 14
        if d < speed:
            apply_hit(p)
            projectiles.remove(p)
        else:
            p['x'] += dx / d * speed
            p['y'] += dy / d * speed

def update_fps_bullets():
    global coins
    for b in fps_bullets[:]:
        b['x'] += b['vx']
        b['y'] += b['vy']
        b['z'] += b['vz']
        b['life'] -= 1
        if b['life'] <= 0:
            fps_bullets.remove(b)
            continue
        for e in enemies[:]:
            dist_xy = math.hypot(e['x'] - b['x'], e['y'] - b['y'])
            ez = e['radius'] * e['size_mult'] * 0.9
            hit_r = e['radius'] * e['size_mult'] + 12
            if dist_xy <= hit_r and abs(b['z'] - ez) <= hit_r:
                e['hp'] -= b['dmg']
                if b in fps_bullets:
                    fps_bullets.remove(b)
                if e['hp'] <= 0:
                    coins += e['reward']
                    enemies.remove(e)
                break

def fire_pistol():
    global pistol_cooldown
    if pistol_cooldown > 0:
        return
    rad_yaw = math.radians(player_yaw)
    rad_pitch = math.radians(player_pitch)
    speed = 26.0
    vx = math.cos(rad_yaw) * math.cos(rad_pitch) * speed
    vy = math.sin(rad_yaw) * math.cos(rad_pitch) * speed
    vz = math.sin(rad_pitch) * speed
    dmg = 70 if cheat_mode else 35
    fps_bullets.append({
        'x': player_pos[0], 'y': player_pos[1], 'z': player_pos[2],
        'vx': vx, 'vy': vy, 'vz': vz, 'life': 55, 'dmg': dmg
    })
    play_sfx("pistol")
    pistol_cooldown = 12

def reset_game():
    global coins, lives, wave, game_state, cheat_mode
    global spawn_timer, wave_spawned, wave_total, spawn_interval_frames, wave_message_timer
    global day_timer, current_daylight
    global camera_orbit_angle, camera_height, camera_mode, camera_pos
    global night_mode_on, night_mode_recovering
    global player_pos, player_yaw, player_pitch, player_hp, bomb_planted, bomb_timer, factory_destroyed, explosion_radius, cursor
    global player_name, called_mom, prologue_index, call_convo_index, sully_index, epilogue_index, moral_choice, extraction_music_started

    stop_mp3()
    coins, lives, wave = 150, 5, 1
    game_state = STATE_MAIN_MENU
    player_name = ""
    called_mom = False
    prologue_index = 0
    call_convo_index = 0
    sully_index = 0
    epilogue_index = 0
    moral_choice = 0
    extraction_music_started = False

    cheat_mode = False
    cursor = [0, 0]
    spawn_timer, wave_spawned, wave_total = 0, 0, 4
    spawn_interval_frames = 170
    wave_message_timer = 0
    day_timer, current_daylight = 0, 1.0
    camera_orbit_angle, camera_height, camera_mode = 0.0, 750.0, 0
    camera_pos = CAMERA_PRESETS[0]
    night_mode_on, night_mode_recovering = False, False
    
    player_pos = [320.0, -150.0, 25.0]
    player_yaw = 140.0
    player_pitch = 0.0
    player_hp = 100
    bomb_planted = False
    factory_destroyed = False
    bomb_timer = 25.0 * 60
    explosion_radius = 10.0

    enemies.clear()
    towers.clear()
    projectiles.clear()
    fps_bullets.clear()
    brute_attacks.clear()

def draw_ground():
    dim = 0.35 + 0.65 * current_daylight
    glBegin(GL_QUADS)
    step = CELL
    for gx in range(-GRID_LENGTH, GRID_LENGTH, step):
        for gy in range(-GRID_LENGTH, GRID_LENGTH, step):
            if ((gx // step) + (gy // step)) % 2 == 0:
                glColor3f(0.15 * dim, 0.35 * dim, 0.15 * dim)
            else:
                glColor3f(0.12 * dim, 0.30 * dim, 0.12 * dim)
            glVertex3f(gx, gy, 0)
            glVertex3f(gx + step, gy, 0)
            glVertex3f(gx + step, gy + step, 0)
            glVertex3f(gx, gy + step, 0)
    glEnd()

def draw_path():
    dim = 0.5 + 0.5 * current_daylight
    glColor3f(0.55 * dim, 0.4 * dim, 0.25 * dim)
    glBegin(GL_QUADS)
    width = 50
    for i in range(len(PATH) - 1):
        ax, ay = PATH[i]
        bx, by = PATH[i + 1]
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        nx, ny = -dy / length * width, dx / length * width
        glVertex3f(ax + nx, ay + ny, 1)
        glVertex3f(bx + nx, by + ny, 1)
        glVertex3f(bx - nx, by - ny, 1)
        glVertex3f(ax - nx, ay - ny, 1)
    glEnd()

def draw_enemy(e):
    base_size = e['radius']
    s = base_size * e['size_mult'] * e['pulse']

    glPushMatrix()
    glTranslatef(e['x'], e['y'], s * 0.9)
    glColor3f(*e['color'])
    gluSphere(quadric, s, 12, 12)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(e['x'], e['y'], s * 0.9 + s * 0.85)
    glColor3f(0.05, 0.05, 0.05)
    gluSphere(quadric, s * 0.55, 10, 10)
    glPopMatrix()

    top = s * 1.9 + 12
    frac = max(0.0, e['hp'] / e['max_hp'])

    if game_state in (STATE_FPS, STATE_BOMB_PLANTED):
        cam_x, cam_y = player_pos[0], player_pos[1]
    else:
        cam_x, cam_y = camera_pos[0], camera_pos[1]

    edx = e['x'] - cam_x
    edy = e['y'] - cam_y
    dist_cam = math.hypot(edx, edy)
    if dist_cam > 0.1:
        nx = -edy / dist_cam * 22
        ny = edx / dist_cam * 22
    else:
        nx, ny = 22, 0

    bar_h = 5.0
    glBegin(GL_QUADS)
    glColor3f(0.15, 0.15, 0.15)
    glVertex3f(e['x'] - nx, e['y'] - ny, top)
    glVertex3f(e['x'] + nx, e['y'] + ny, top)
    glVertex3f(e['x'] + nx, e['y'] + ny, top + bar_h)
    glVertex3f(e['x'] - nx, e['y'] - ny, top + bar_h)

    glColor3f(1.0 - frac, frac, 0.1)
    glVertex3f(e['x'] - nx, e['y'] - ny, top + 0.6)
    glVertex3f(e['x'] - nx + 2 * nx * frac, e['y'] - ny + 2 * ny * frac, top + 0.6)
    glVertex3f(e['x'] - nx + 2 * nx * frac, e['y'] - ny + 2 * ny * frac, top + bar_h - 0.6)
    glVertex3f(e['x'] - nx, e['y'] - ny, top + bar_h - 0.6)
    glEnd()

def draw_tower(t):
    glPushMatrix()
    glTranslatef(t['x'], t['y'], 15)
    glColor3f(0.4, 0.4, 0.4)
    glutSolidCube(50)
    glPopMatrix()

    color = TOWER_TYPES[t['type']][0]
    glPushMatrix()
    glTranslatef(t['x'], t['y'], 40 + t['level'] * 8)
    glColor3f(*color)
    if t['type'] == 'sniper':
        gluCylinder(quadric, 8, 4, 40 + t['level'] * 6, 8, 8)
    else:
        glutSolidCube(24 + t['level'] * 4)
    glPopMatrix()

def draw_projectile(p):
    glPushMatrix()
    glTranslatef(p['x'], p['y'], p['z'])
    glColor3f(*p['color'])
    gluSphere(quadric, p.get('size', 6), 6, 6)
    glPopMatrix()

def update_brute_attacks():
    for b in brute_attacks[:]:
        b['timer'] -= 1
        if b['timer'] <= 0:
            brute_attacks.remove(b)

def draw_brute_attacks():
    if not brute_attacks:
        return
    glColor3f(0.85, 0.2, 0.9)
    for b in brute_attacks:
        DrawLine(b['x1'], b['y1'], b['x2'], b['y2'], point_size=LINE_WIDTH, z1=b['z1'], z2=b['z2'])
        DrawLine(b['x1'], b['y1'], b['x2'], b['y2'], point_size=LINE_WIDTH, z1=b['z1'] + 2, z2=b['z2'] + 2)
        draw_circle_outline(b['x2'], b['y2'], 28, z=3, segments=16, point_size=LINE_WIDTH)

def draw_cursor():
    if game_state != STATE_TD:
        return
    is_valid, _ = check_placement_validity()
    if is_valid:
        glColor3f(0.2, 1.0, 0.2)
    else:
        glColor3f(1.0, 0.2, 0.2)

    x1, x2 = cursor[0] - CELL / 2, cursor[0] + CELL / 2
    y1, y2 = cursor[1] - CELL / 2, cursor[1] + CELL / 2
    z = 3

    DrawLine(x1, y1, x2, y1, point_size=LINE_WIDTH, z1=z, z2=z)
    DrawLine(x2, y1, x2, y2, point_size=LINE_WIDTH, z1=z, z2=z)
    DrawLine(x2, y2, x1, y2, point_size=LINE_WIDTH, z1=z, z2=z)
    DrawLine(x1, y2, x1, y1, point_size=LINE_WIDTH, z1=z, z2=z)

    if not is_valid:
        DrawLine(x1, y1, x2, y2, point_size=LINE_WIDTH, z1=z, z2=z)
        DrawLine(x1, y2, x2, y1, point_size=LINE_WIDTH, z1=z, z2=z)

    color, _, rng, _, _ = TOWER_TYPES[selected_type]
    if is_valid:
        glColor3f(*color)
    else:
        glColor3f(0.8, 0.2, 0.2)
    draw_circle_outline(cursor[0], cursor[1], rng, z=z)

def keyboardListener(key, x, y):
    global selected_type, rain_on, cheat_mode, game_state
    global camera_orbit_angle, camera_height, camera_mode, night_mode_on, night_mode_recovering
    global player_pos, player_yaw, bomb_planted, player_name
    global prologue_index, call_convo_index, sully_index, called_mom
    global epilogue_index, moral_choice

    k = key.lower()

    if game_state == STATE_MAIN_MENU:
        if k in (b'1', b'n'):
            game_state = STATE_NAME_INPUT
        elif k in (b'2', b'c'):
            game_state = STATE_MENU_CREDITS
        return

    if game_state == STATE_MENU_CREDITS:
        if key in (b'\r', b'\n', b' ', b'\x1b', b'2'):
            game_state = STATE_MAIN_MENU
        return

    if game_state == STATE_NAME_INPUT:
        if key in (b'\r', b'\n'):
            if len(player_name.strip()) == 0:
                player_name = "Miller"
            else:
                player_name = player_name.strip()
            game_state = STATE_PROLOGUE
            prologue_index = 0
        elif key == b'\x08':
            if len(player_name) > 0:
                player_name = player_name[:-1]
        else:
            try:
                ch = key.decode('utf-8')
                if (ch.isalnum() or ch in (' ', '_', '-')) and len(player_name) < 18:
                    player_name += ch
            except:
                pass
        return

    if game_state == STATE_PROLOGUE:
        if key in (b'\r', b'\n', b' '):
            prologue_index += 1
            if prologue_index >= 10:
                game_state = STATE_CALL_CHOICE
        return

    if game_state == STATE_CALL_CHOICE:
        if k == b'1':
            called_mom = True
            game_state = STATE_CALL_CONVO
            call_convo_index = 0
        elif k == b'2':
            called_mom = False
            game_state = STATE_TD
            spawn_enemy()
        return

    if game_state == STATE_CALL_CONVO:
        if key in (b'\r', b'\n', b' '):
            call_convo_index += 1
            if call_convo_index >= 3:
                game_state = STATE_TD
                spawn_enemy()
        return

    if game_state == STATE_SULLY_AWAKENING:
        if key in (b'\r', b'\n', b' '):
            sully_index += 1
            if sully_index >= 4:
                game_state = STATE_FPS
                spawn_enemy()
        return

    if game_state == STATE_EPILOGUE_STORY:
        if key in (b'\r', b'\n', b' '):
            epilogue_index += 1
            if epilogue_index >= 2:
                game_state = STATE_EPILOGUE_CHOICE
        return

    if game_state == STATE_EPILOGUE_CHOICE:
        if k == b'1':
            moral_choice = 1
            game_state = STATE_EPILOGUE_OUTCOME
        elif k == b'2':
            moral_choice = 2
            game_state = STATE_EPILOGUE_OUTCOME
        return

    if game_state == STATE_EPILOGUE_OUTCOME:
        if key in (b'\r', b'\n', b' '):
            game_state = STATE_CREDITS_ROLL
        return

    if game_state in (STATE_GAME_OVER, STATE_CREDITS_ROLL):
        if k == b'r':
            reset_game()
        return

    if game_state in (STATE_FPS, STATE_BOMB_PLANTED):
        rad = math.radians(player_yaw)
        fx = math.cos(rad) * player_speed
        fy = math.sin(rad) * player_speed
        sx = math.sin(rad) * player_speed
        sy = math.cos(rad) * player_speed

        if k == b'w':
            player_pos[0] = max(-GRID_LENGTH + 25, min(GRID_LENGTH - 25, player_pos[0] + fx))
            player_pos[1] = max(-GRID_LENGTH + 25, min(GRID_LENGTH - 25, player_pos[1] + fy))
        elif k == b's':
            player_pos[0] = max(-GRID_LENGTH + 25, min(GRID_LENGTH - 25, player_pos[0] - fx))
            player_pos[1] = max(-GRID_LENGTH + 25, min(GRID_LENGTH - 25, player_pos[1] - fy))
        elif k == b'a':
            player_pos[0] = max(-GRID_LENGTH + 25, min(GRID_LENGTH - 25, player_pos[0] - sx))
            player_pos[1] = max(-GRID_LENGTH + 25, min(GRID_LENGTH - 25, player_pos[1] + sy))
        elif k == b'd':
            player_pos[0] = max(-GRID_LENGTH + 25, min(GRID_LENGTH - 25, player_pos[0] + sx))
            player_pos[1] = max(-GRID_LENGTH + 25, min(GRID_LENGTH - 25, player_pos[1] - sy))
        elif k == b'q':
            player_yaw = (player_yaw + turn_speed) % 360
        elif k == b'e':
            player_yaw = (player_yaw - turn_speed) % 360
        elif k in (b' ', b'f'):
            d_spire = math.hypot(player_pos[0] - FACTORY_POS[0], player_pos[1] - FACTORY_POS[1])
            if d_spire <= 110 and not bomb_planted:
                bomb_planted = True
                game_state = STATE_BOMB_PLANTED
        elif k == b'c':
            cheat_mode = not cheat_mode
        return

    if k == b'1':
        selected_type = 'cannon'
    elif k == b'2':
        selected_type = 'frost'
    elif k == b'3':
        selected_type = 'sniper'
    elif k == b' ':
        place_tower()
    elif k == b'u':
        upgrade_tower()
    elif k == b't':
        change_tower_type()
    elif k == b'r':
        rain_on = not rain_on
    elif k == b'c':
        cheat_mode = not cheat_mode
    elif k in (b'a', b'd', b'w', b's'):
        camera_mode = 0
        if k == b'a':
            camera_orbit_angle = (camera_orbit_angle - CAMERA_ORBIT_STEP) % 360
        elif k == b'd':
            camera_orbit_angle = (camera_orbit_angle + CAMERA_ORBIT_STEP) % 360
        elif k == b'w':
            camera_height = min(CAMERA_HEIGHT_MAX, camera_height + CAMERA_HEIGHT_STEP)
        elif k == b's':
            camera_height = max(CAMERA_HEIGHT_MIN, camera_height - CAMERA_HEIGHT_STEP)
        update_camera_pos()
    elif k == b'n':
        night_mode_on = not night_mode_on
        if not night_mode_on:
            night_mode_recovering = True

def specialKeyListener(key, x, y):
    global player_yaw, player_pitch

    if game_state in (STATE_FPS, STATE_BOMB_PLANTED):
        if key == GLUT_KEY_LEFT:
            player_yaw = (player_yaw + turn_speed) % 360
        elif key == GLUT_KEY_RIGHT:
            player_yaw = (player_yaw - turn_speed) % 360
        elif key == GLUT_KEY_UP:
            player_pitch = min(48.0, player_pitch + pitch_speed)
        elif key == GLUT_KEY_DOWN:
            player_pitch = max(-48.0, player_pitch - pitch_speed)
        return

    if game_state == STATE_TD:
        if key == GLUT_KEY_LEFT:
            cursor[0] = max(-GRID_LENGTH + CELL, cursor[0] - CELL)
        elif key == GLUT_KEY_RIGHT:
            cursor[0] = min(GRID_LENGTH - CELL, cursor[0] + CELL)
        elif key == GLUT_KEY_UP:
            cursor[1] = min(GRID_LENGTH - CELL, cursor[1] + CELL)
        elif key == GLUT_KEY_DOWN:
            cursor[1] = max(-GRID_LENGTH + CELL, cursor[1] - CELL)

def mouseListener(button, state, x, y):
    global camera_pos, camera_mode
    if game_state in (STATE_FPS, STATE_BOMB_PLANTED):
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            fire_pistol()
        return

    if game_state == STATE_TD:
        if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
            camera_mode = 1 - camera_mode
            if camera_mode == 1:
                camera_pos = CAMERA_PRESETS[1]
            else:
                update_camera_pos()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WIN_WIDTH / WIN_HEIGHT, 1.0, 3600)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if game_state in (STATE_EPILOGUE_STORY, STATE_EPILOGUE_CHOICE, STATE_EPILOGUE_OUTCOME):
        ex, ey, ez = player_pos[0], player_pos[1], player_pos[2] + 25
        fx, fy = FACTORY_POS
        gluLookAt(ex, ey, ez, fx, fy, 45, 0, 0, 1)
        return

    if game_state in (STATE_FPS, STATE_BOMB_PLANTED, STATE_CREDITS_ROLL):
        rad_yaw = math.radians(player_yaw)
        rad_pitch = math.radians(player_pitch)
        lx = math.cos(rad_yaw) * math.cos(rad_pitch)
        ly = math.sin(rad_yaw) * math.cos(rad_pitch)
        lz = math.sin(rad_pitch)
        ex, ey, ez = player_pos[0], player_pos[1], player_pos[2]
        gluLookAt(ex, ey, ez,
                  ex + lx * 100, ey + ly * 100, ez + lz * 100,
                  0, 0, 1)
        return

    x, y, z = camera_pos
    if abs(x) < 0.001 and abs(y) < 0.001:
        gluLookAt(x, y, z, 0, 0, 0, 0, 1, 0)
    else:
        gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)

def idle():
    global spawn_timer, wave_spawned, wave_message_timer, pistol_cooldown
    global bomb_timer, factory_destroyed, explosion_radius, game_state, epilogue_index
    global extraction_music_started

    if game_state in (STATE_TD, STATE_FPS, STATE_BOMB_PLANTED):
        update_daynight()
        update_enemies()
        update_towers()
        update_projectiles()
        update_fps_bullets()
        update_brute_attacks()
        update_rain()

        if pistol_cooldown > 0:
            pistol_cooldown -= 1

        if game_state == STATE_TD:
            spawn_timer += 1
            if spawn_timer >= spawn_interval_frames and wave_spawned < wave_total:
                spawn_enemy()
                wave_spawned += 1
                spawn_timer = 0
            if wave_message_timer > 0:
                wave_message_timer -= 1
            if wave_spawned >= wave_total and len(enemies) == 0:
                start_next_wave()

        elif game_state in (STATE_FPS, STATE_BOMB_PLANTED):
            spawn_timer += 1
            if spawn_timer >= 160:
                spawn_enemy()
                spawn_timer = 0

        if game_state == STATE_BOMB_PLANTED:
            bomb_timer -= 1
            d_extract = math.hypot(player_pos[0] - EXTRACTION_POS[0], player_pos[1] - EXTRACTION_POS[1])

            if d_extract <= EXTRACTION_RADIUS and not extraction_music_started:
                play_mp3("foo_fighters.mp3")
                extraction_music_started = True

            if bomb_timer <= 0:
                factory_destroyed = True
                if d_extract <= EXTRACTION_RADIUS:
                    game_state = STATE_EPILOGUE_STORY
                    epilogue_index = 0
                    enemies.clear()
                else:
                    game_state = STATE_GAME_OVER

    if game_state in (STATE_EPILOGUE_STORY, STATE_EPILOGUE_CHOICE, STATE_EPILOGUE_OUTCOME, STATE_CREDITS_ROLL):
        if explosion_radius < 550:
            explosion_radius += 7.0

    glutPostRedisplay()

def draw_dialog_frame(speaker_tag, speaker_color, hide_enter_hint=False):
    bx1, bx2 = int(WIN_WIDTH * 0.05), int(WIN_WIDTH * 0.95)
    by1, by2 = int(WIN_HEIGHT * 0.06), int(WIN_HEIGHT * 0.38)

    glColor3f(0.05, 0.06, 0.10)
    glBegin(GL_QUADS)
    glVertex3f(bx1, by1, 0); glVertex3f(bx2, by1, 0)
    glVertex3f(bx2, by2, 0); glVertex3f(bx1, by2, 0)
    glEnd()

    glColor3f(speaker_color[0] * 0.8, speaker_color[1] * 0.8, speaker_color[2] * 0.8)
    DrawLine(bx1, by1, bx2, by1, point_size=LINE_WIDTH)
    DrawLine(bx2, by1, bx2, by2, point_size=LINE_WIDTH)
    DrawLine(bx2, by2, bx1, by2, point_size=LINE_WIDTH)
    DrawLine(bx1, by2, bx1, by1, point_size=LINE_WIDTH)

    tag_w = len(speaker_tag) * 11 + 25
    glColor3f(speaker_color[0] * 0.3, speaker_color[1] * 0.3, speaker_color[2] * 0.3)
    glBegin(GL_QUADS)
    glVertex3f(bx1 + 15, by2 - 4, 0); glVertex3f(bx1 + 15 + tag_w, by2 - 4, 0)
    glVertex3f(bx1 + 15 + tag_w, by2 + 24, 0); glVertex3f(bx1 + 15, by2 + 24, 0)
    glEnd()

    glColor3f(*speaker_color)
    DrawLine(bx1 + 15, by2 - 4, bx1 + 15 + tag_w, by2 - 4, point_size=LINE_WIDTH)
    DrawLine(bx1 + 15 + tag_w, by2 - 4, bx1 + 15 + tag_w, by2 + 24, point_size=LINE_WIDTH)
    DrawLine(bx1 + 15 + tag_w, by2 + 24, bx1 + 15, by2 + 24, point_size=LINE_WIDTH)
    DrawLine(bx1 + 15, by2 + 24, bx1 + 15, by2 - 4, point_size=LINE_WIDTH)

    draw_text(bx1 + 25, by2 + 5, speaker_tag)
    if not hide_enter_hint:
        draw_text(bx2 - 155, by1 + 16, "[ ENTER / SPACE ]")
    return bx1 + 30, by2 - 35

def draw_hud_and_dialog():
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_WIDTH, 0, WIN_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    cx = WIN_WIDTH // 2
    cy = WIN_HEIGHT // 2

    if game_state == STATE_MAIN_MENU:
        glColor3f(0.02, 0.03, 0.05)
        glBegin(GL_QUADS)
        glVertex3f(0, 0, 0); glVertex3f(WIN_WIDTH, 0, 0)
        glVertex3f(WIN_WIDTH, WIN_HEIGHT, 0); glVertex3f(0, WIN_HEIGHT, 0)
        glEnd()

        glColor3f(0.85, 0.25, 0.2)
        draw_text(cx - 70, cy + 110, "DEATH PEAKS")

        glColor3f(0.12, 0.16, 0.24)
        glBegin(GL_QUADS)
        glVertex3f(cx - 150, cy - 65, 0); glVertex3f(cx + 150, cy - 65, 0)
        glVertex3f(cx + 150, cy + 45, 0); glVertex3f(cx - 150, cy + 45, 0)
        glEnd()
        glColor3f(0.3, 0.5, 0.7)
        DrawLine(cx - 150, cy - 65, cx + 150, cy - 65)
        DrawLine(cx + 150, cy - 65, cx + 150, cy + 45)
        DrawLine(cx + 150, cy + 45, cx - 150, cy + 45)
        DrawLine(cx - 150, cy + 45, cx - 150, cy - 65)

        glColor3f(0.2, 0.9, 0.4)
        draw_text(cx - 65, cy + 10, "[ 1 ]  NEW GAME")
        glColor3f(0.9, 0.8, 0.2)
        draw_text(cx - 50, cy - 35, "[ 2 ]  CREDITS")

        glColor3f(0.6, 0.6, 0.6)
        draw_text(cx - 170, cy - 120, "CSE423 [Computer Graphics] Final Project.")

    elif game_state == STATE_MENU_CREDITS:
        glColor3f(0.03, 0.04, 0.07)
        glBegin(GL_QUADS)
        glVertex3f(0, 0, 0); glVertex3f(WIN_WIDTH, 0, 0)
        glVertex3f(WIN_WIDTH, WIN_HEIGHT, 0); glVertex3f(0, WIN_HEIGHT, 0)
        glEnd()

        glColor3f(0.9, 0.8, 0.2)
        draw_text(cx - 85, cy + 130, "CREDITS")
        glColor3f(0.3, 0.8, 0.9)
        draw_text(cx - 95, cy + 70, "DEVELOPED BY:")

        glColor3f(1.0, 1.0, 1.0)
        draw_text(cx - 65, cy + 20, "Sk Fardeen Rahman")
        draw_text(cx - 65, cy - 20, "KM Mehrab Hossain")
        draw_text(cx - 65, cy - 60, "Abu Safwan Md Farhan")

        glColor3f(0.6, 0.6, 0.6)
        draw_text(cx - 135, cy - 130, "[ PRESS ENTER OR ESC TO RETURN ]")

    elif game_state == STATE_NAME_INPUT:
        glColor3f(0.04, 0.05, 0.08)
        glBegin(GL_QUADS)
        glVertex3f(0, 0, 0); glVertex3f(WIN_WIDTH, 0, 0)
        glVertex3f(WIN_WIDTH, WIN_HEIGHT, 0); glVertex3f(0, WIN_HEIGHT, 0)
        glEnd()

        glColor3f(0.3, 0.8, 0.9)
        draw_text(cx - 210, cy + 90, "--- MILITARY DOSSIER IDENTIFICATION ---")
        glColor3f(1.0, 1.0, 1.0)
        draw_text(cx - 190, cy + 30, "ENTER YOUR OFFICER SURNAME / CODENAME:")

        glColor3f(0.2, 0.4, 0.6)
        glBegin(GL_QUADS)
        glVertex3f(cx - 160, cy - 30, 0); glVertex3f(cx + 160, cy - 30, 0)
        glVertex3f(cx + 160, cy + 10, 0); glVertex3f(cx - 160, cy + 10, 0)
        glEnd()
        glColor3f(0.6, 0.8, 1.0)
        DrawLine(cx - 160, cy - 30, cx + 160, cy - 30)
        DrawLine(cx + 160, cy - 30, cx + 160, cy + 10)
        DrawLine(cx + 160, cy + 10, cx - 160, cy + 10)
        DrawLine(cx - 160, cy + 10, cx - 160, cy - 30)

        display_name = player_name if player_name else "Major "
        cursor_blink = "_" if (int(day_timer * 0.2) % 2 == 0) else ""
        glColor3f(1.0, 1.0, 0.2)
        draw_text(cx - 140, cy - 16, f"{display_name}{cursor_blink}")

        glColor3f(0.7, 0.7, 0.7)
        draw_text(cx - 180, cy - 70, "[ TYPE LETTERS | BACKSPACE TO EDIT | ENTER TO CONFIRM ]")

    elif game_state == STATE_PROLOGUE:
        name_tag = player_name.upper()

        if prologue_index == 0:
            tx, ty = draw_dialog_frame("GENERAL X", (0.9, 0.2, 0.2))
            draw_wrapped_text(tx, ty, f"General X: Hello there, Officer {name_tag}. Your performance so far has been incredibly below par. I ordered you to give the pay order to the gun company for the purchase of arms and equipments. Why didn't you do so?")

        elif prologue_index == 1:
            tx, ty = draw_dialog_frame(f"MAJOR {name_tag}", (0.2, 0.8, 0.9))
            draw_wrapped_text(tx, ty, f"Major {name_tag}: ..But General, we have enough arms and equipments at the imaginary barracks already. We are also not in active deployment. We do not need more guns at this point. Moreover, the gun company was asking for ludicrous prices...")

        elif prologue_index == 2:
            tx, ty = draw_dialog_frame("GENERAL X", (0.9, 0.1, 0.1))
            draw_wrapped_text(tx, ty, f"General X: SHUT UP. You bastard lowly major. I will rip your tongue out. Your problem is that you talk far too much. Under martial law 401(c), I hereby banish you from the imaginary barracks. You are stationed to the Death Peaks until further notice.")

        elif prologue_index == 3:
            tx, ty = draw_dialog_frame(f"MAJOR {name_tag}", (0.2, 0.8, 0.9))
            draw_wrapped_text(tx, ty, f"Major {name_tag}: .....The Death Peaks. That is the most remote and hazardoous outpost in the sector...")

        elif prologue_index == 4:
            tx, ty = draw_dialog_frame("GENERAL X", (0.9, 0.1, 0.1))
            draw_wrapped_text(tx, ty, f"General X: You will be dropped off there by my personal transport. No amount of pleading will work. If you utter a single word further, I will kill you.")

        elif prologue_index == 5:
            tx, ty = draw_dialog_frame("TRANSITION", (0.7, 0.7, 0.8))
            draw_wrapped_text(tx, ty, f"Major {name_tag} leaves headquarters in complete silence. He returns home, takes a warm bath to wash off the disgust, and lies in bed staring blankly at the ceiling.")

        elif prologue_index == 6:
            tx, ty = draw_dialog_frame(f"MAJOR {name_tag} (INTERNAL THOUGHT)", (0.7, 0.7, 0.9))
            draw_wrapped_text(tx, ty, "Man, why did I have to be so stubborn? I should have just signed off on the weapons and led a comfortable life. I should've just played along...")

        elif prologue_index == 7:
            tx, ty = draw_dialog_frame(f"MAJOR {name_tag}", (0.2, 0.8, 0.9))
            draw_wrapped_text(tx, ty, "Bruh. Why am I thinking like a 14 year old girl. I am a man of truth. It is better to live a life of truth than to live a life of lies. ")

        elif prologue_index == 8:
            tx, ty = draw_dialog_frame(f"MAJOR {name_tag}", (0.2, 0.8, 0.9))
            draw_wrapped_text(tx, ty, "Also, I just remembered. My friend Sully was stationed at the Death Peaks too. He was the best student in the academy. It will be good to see him again.")

        elif prologue_index == 9:
            tx, ty = draw_dialog_frame(f"MAJOR {name_tag}", (0.2, 0.8, 0.9))
            draw_wrapped_text(tx, ty, "Let me contact him. Actually, there are no direct comm lines to Death Peaks. Let me call his mother first to see if she knows anything.")

    elif game_state == STATE_CALL_CHOICE:
        tx, ty = draw_dialog_frame("DECISION CONDUIT", (0.9, 0.8, 0.2), hide_enter_hint=True)
        draw_text(tx, ty + 10, "WILL YOU CALL SULLY'S MOTHER BEFORE BEING DEPLOYED?")
        glColor3f(0.2, 0.9, 0.3)
        draw_text(tx, ty - 25, "[ 1 ] CALL SULLY'S MOTHER (Reach out and check on family)")
        glColor3f(0.9, 0.3, 0.3)
        draw_text(tx, ty - 55, "[ 2 ] DO NOT CALL (Accept your fate quietly and depart)")

    elif game_state == STATE_CALL_CONVO:
        name_tag = player_name.upper()
        if call_convo_index == 0:
            tx, ty = draw_dialog_frame("SULLY'S MOTHER", (0.9, 0.7, 0.4))
            draw_wrapped_text(tx, ty, f"Mother: Hello? ...{name_tag}?! Oh god, thank heaven you called! Do you know anything about my Sully?! There has been zero contact for months... I don't even know if he is alive or dead! I am worried sick!")
        elif call_convo_index == 1:
            tx, ty = draw_dialog_frame(f"MAJOR {name_tag}", (0.2, 0.8, 0.9))
            draw_wrapped_text(tx, ty, f"Major {name_tag}: Auntie, calm down. General X is banishing me to the Death Peaks right now. If Sully is still up there, I swear on my life I will find him.")
        elif call_convo_index == 2:
            tx, ty = draw_dialog_frame("SULLY'S MOTHER", (0.9, 0.7, 0.4))
            draw_wrapped_text(tx, ty, "Mother: God bless you, son! Please be careful...")

    elif game_state == STATE_SULLY_AWAKENING:
        name_tag = player_name.upper()
        if sully_index == 0:
            tx, ty = draw_dialog_frame("SULLY (HELICOPTER LOUDSPEAKER)", (1.0, 0.6, 0.1))
            draw_wrapped_text(tx, ty, f"Sully: MAJOR {name_tag}!! CAN YOU HEAR ME OVER THE ROTORS?! WAKE UP! WAKE UP TO REALITY! THIS WHOLE VALLEY IS A DEATH TRAP!")
        elif sully_index == 1:
            tx, ty = draw_dialog_frame("SULLY (HELICOPTER LOUDSPEAKER)", (1.0, 0.6, 0.1))
            draw_wrapped_text(tx, ty, "Sully: My mother told me they banished you here! The Spire is an automated AI factory built by corrupt upper officers to continuously pump out belligerent robots just to embezzle military budgets!")
        elif sully_index == 2:
            tx, ty = draw_dialog_frame("SULLY (HELICOPTER LOUDSPEAKER)", (1.0, 0.6, 0.1))
            draw_wrapped_text(tx, ty, "Sully: I escaped by swimming 100 kilometers through the glacial sea! I crafted an algorithm that completely neutralizes the factory's mainframe, but it must be detonated too after neutralization or it self-restarts!")
        elif sully_index == 3:
            tx, ty = draw_dialog_frame("SULLY (HELICOPTER LOUDSPEAKER)", (1.0, 0.6, 0.1))
            draw_wrapped_text(tx, ty, "Sully: I packaged the algorithm into this bomb! The algorithm makes stages the factory for detonation. The bomb blows it up to pieces. Take this pistol (Sully throws a pistol at him from the copter), infiltrate the valley floor, plant the bomb at the Spire core, and run to my extraction LZ before detonation!")

    elif game_state in (STATE_FPS, STATE_BOMB_PLANTED):
        glColor3f(1.0, 1.0, 1.0)
        DrawLine(cx - 9, cy, cx + 9, cy, point_size=LINE_WIDTH)
        DrawLine(cx, cy - 9, cx, cy + 9, point_size=LINE_WIDTH)

        d_spire = math.hypot(player_pos[0] - FACTORY_POS[0], player_pos[1] - FACTORY_POS[1])
        d_extract = math.hypot(player_pos[0] - EXTRACTION_POS[0], player_pos[1] - EXTRACTION_POS[1])

        cheat_tag = " [CHEAT: 2x DMG & INVULN]" if cheat_mode else ""
        draw_text(10, WIN_HEIGHT - 30, f"MAJOR {player_name.upper()} | HP: {int(player_hp)} / {player_max_hp}   COINS: {coins}{cheat_tag}")
        draw_text(10, WIN_HEIGHT - 55, "WASD Move | Q/E or Arrows Turn | LEFT-CLICK Shoot | F/SPACE Plant Bomb")

        if not bomb_planted:
            draw_text(10, WIN_HEIGHT - 80, f"OBJECTIVE: INFILTRATE SPIRE ({int(d_spire)}m)")
            if d_spire <= 110:
                draw_text(cx - 190, cy + 30, ">> PRESS [SPACE] OR [F] TO PLANT SULLY'S VIRUS BOMB <<")
        else:
            time_left = max(0.0, bomb_timer / 60.0)
            if d_extract <= EXTRACTION_RADIUS:
                draw_text(10, WIN_HEIGHT - 80, f"DETONATION IN: {time_left:.1f}s | [EXTRACTION ZONE SECURED]")
                draw_text(cx - 220, WIN_HEIGHT - 105, ">> IN SULLY'S LZ - HOLD POSITION UNTIL SPIRE DETONATES <<")
            else:
                draw_text(10, WIN_HEIGHT - 80, f"DETONATION IN: {time_left:.1f}s ! SULLY LZ DISTANCE: {int(d_extract)}m")
                draw_text(cx - 160, WIN_HEIGHT - 105, "!! ALARM: RETURN TO EXTRACTION ZONE !!")

        recoil = 18 if pistol_cooldown > 8 else 0
        rx = recoil * 0.4
        ry = recoil * 0.9

        glColor3f(0.12, 0.12, 0.14)
        glBegin(GL_QUADS)
        glVertex3f(WIN_WIDTH - 150 + rx, -30 + ry, 0)
        glVertex3f(WIN_WIDTH - 60 + rx, -30 + ry, 0)
        glVertex3f(WIN_WIDTH - 120 + rx, 70 + ry, 0)
        glVertex3f(WIN_WIDTH - 180 + rx, 50 + ry, 0)
        glEnd()

        glColor3f(0.25, 0.26, 0.28)
        glBegin(GL_QUADS)
        glVertex3f(WIN_WIDTH - 180 + rx, 50 + ry, 0)
        glVertex3f(WIN_WIDTH - 110 + rx, 70 + ry, 0)
        glVertex3f(cx + 85 + rx, 185 + ry, 0)
        glVertex3f(cx + 40 + rx, 175 + ry, 0)
        glEnd()

        glColor3f(0.38, 0.39, 0.42)
        glBegin(GL_QUADS)
        glVertex3f(cx + 40 + rx, 175 + ry, 0)
        glVertex3f(cx + 85 + rx, 185 + ry, 0)
        glVertex3f(cx + 42 + rx, 240 + ry, 0)
        glVertex3f(cx + 12 + rx, 230 + ry, 0)
        glEnd()

        glColor3f(0.08, 0.08, 0.08)
        glBegin(GL_QUADS)
        glVertex3f(cx + 24 + rx, 235 + ry, 0)
        glVertex3f(cx + 30 + rx, 237 + ry, 0)
        glVertex3f(cx + 28 + rx, 247 + ry, 0)
        glVertex3f(cx + 22 + rx, 245 + ry, 0)
        glEnd()

        if pistol_cooldown > 8:
            glColor3f(1.0, 0.85, 0.2)
            glBegin(GL_QUADS)
            glVertex3f(cx + 10 + rx, 240 + ry, 0)
            glVertex3f(cx + 44 + rx, 250 + ry, 0)
            glVertex3f(cx + 52 + rx, 290 + ry, 0)
            glVertex3f(cx + 0 + rx, 280 + ry, 0)
            glEnd()

    elif game_state == STATE_TD:
        is_valid_spot, place_msg = check_placement_validity()
        status_tag = "[BUILD OK]" if is_valid_spot else "[CANNOT BUILD]"

        draw_text(10, WIN_HEIGHT - 30, f"Major {player_name}   Coins: {coins}   Lives: {lives}   Wave: {wave}")
        draw_text(10, WIN_HEIGHT - 55, f"Selected: {selected_type.upper()}  (1 Cannon / 2 Frost / 3 Sniper)  Cost: {TOWER_TYPES[selected_type][4]}")
        draw_text(10, WIN_HEIGHT - 80, "SPACE place | U upgrade | T convert | R rain | C cheat")
        daynight_txt = "DAY" if current_daylight > 0.5 else "NIGHT"
        cheat_txt = "  CHEAT: invulnerable, 2x dmg" if cheat_mode else ""
        draw_text(10, WIN_HEIGHT - 105, f"Cycle: {daynight_txt}{cheat_txt}")
        night_txt = "  NIGHT MODE ON" if night_mode_on else ""
        draw_text(10, WIN_HEIGHT - 130, f"Right-click swap view | W/S height | A/D orbit | N night mode{night_txt}")
        draw_text(10, WIN_HEIGHT - 155, f"Placement: {status_tag} {place_msg}")

        if wave_message_timer > 0:
            draw_text(cx - 80, cy, f"WAVE {wave} INCOMING")

    elif game_state == STATE_EPILOGUE_STORY:
        name_tag = player_name.upper()
        if epilogue_index == 0:
            tx, ty = draw_dialog_frame("EXTRACTION & AFTERMATH", (0.3, 0.8, 0.9))
            draw_wrapped_text(tx, ty, f"The Spire collapses behind the gunship in a blinding flash. Sully and Major {name_tag} fly straight back to the Capital and corner General X inside his private office.")
        elif epilogue_index == 1:
            tx, ty = draw_dialog_frame("MAJOR SULLY", (1.0, 0.6, 0.1))
            draw_wrapped_text(tx, ty, f"Sully: We have him pinned, {name_tag}. He thought we'd die in the rain like the rest. What are we going to do with him?")

    elif game_state == STATE_EPILOGUE_CHOICE:
        tx, ty = draw_dialog_frame("THE FINAL JUDGMENT", (0.9, 0.8, 0.2), hide_enter_hint=True)
        draw_text(tx, ty + 10, "CHOOSE THE FATE OF GENERAL X:")
        glColor3f(0.2, 0.9, 0.3)
        draw_text(tx, ty - 25, "[ 1 ] PROVIDE INSURMOUNTABLE EVIDENCE TO MARTIAL COURT")
        glColor3f(0.9, 0.2, 0.2)
        draw_text(tx, ty - 55, "[ 2 ] DO A HIT (TAKE JUSTICE INTO YOUR OWN HANDS)")

    elif game_state == STATE_EPILOGUE_OUTCOME:
        name_tag = player_name.upper()
        if moral_choice == 1:
            tx, ty = draw_dialog_frame("COURT INDICTMENT", (0.2, 0.9, 0.4))
            draw_wrapped_text(tx, ty, f"Major {name_tag} and Major Sully live the rest of their lives with pride and an unburdened conscience, knowing justice was served through law.")
        else:
            tx, ty = draw_dialog_frame("THE HIT", (0.9, 0.2, 0.2))
            draw_wrapped_text(tx, ty, f"Major {name_tag} and Major Sully live the rest of their lives with a gnawing doubt about their actions.")

    elif game_state == STATE_CREDITS_ROLL:
        glColor3f(0.02, 0.03, 0.05)
        glBegin(GL_QUADS)
        glVertex3f(0, 0, 0); glVertex3f(WIN_WIDTH, 0, 0)
        glVertex3f(WIN_WIDTH, WIN_HEIGHT, 0); glVertex3f(0, WIN_HEIGHT, 0)
        glEnd()

        glColor3f(0.9, 0.2, 0.2)
        draw_text(cx - 85, cy + 130, "DEATH PEAKS")

        glColor3f(0.3, 0.8, 0.9)
        draw_text(cx - 95, cy + 45, "DEVELOPED BY:")
        glColor3f(1.0, 1.0, 1.0)
        draw_text(cx - 65, cy + 5, "Sk Fardeen Rahman")
        draw_text(cx - 65, cy - 30, "KM Mehrab Hossain")
        draw_text(cx - 65, cy - 65, "Abu Safwan Md Farhan")

        glColor3f(0.9, 0.8, 0.2)
        draw_text(cx - 150, cy - 120, "SOUNDTRACK: FOO FIGHTERS")

        glColor3f(0.6, 0.6, 0.6)
        draw_text(cx - 150, cy - 160, "[ PRESS 'R' TO RETURN TO MAIN MENU ]")

    elif game_state == STATE_GAME_OVER:
        if not called_mom:
            draw_text(cx - 240, cy + 30, "NO RESCUE CAME. SULLY NEVER KNEW YOU WERE HERE.")
            draw_text(cx - 190, cy, "YOU DIED A SLOW, FORGOTTEN DEATH IN DEATH PEAKS.")
        else:
            draw_text(cx - 140, cy + 30, "KILLED IN ACTION AT DEATH PEAKS")
        draw_text(cx - 90, cy - 20, "Press R to Restart")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_WIDTH, WIN_HEIGHT)

    df = current_daylight
    sky_day = (0.55, 0.75, 0.95)
    sky_night = (0.02, 0.02, 0.08)
    if game_state == STATE_BOMB_PLANTED:
        sky_night = (0.45, 0.02, 0.02)
    sr = sky_night[0] + (sky_day[0] - sky_night[0]) * df
    sg = sky_night[1] + (sky_day[1] - sky_night[1]) * df
    sb = sky_night[2] + (sky_day[2] - sky_night[2]) * df

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_WIDTH, 0, WIN_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(sr, sg, sb)
    glBegin(GL_QUADS)
    glVertex3f(0, 0, 0)
    glVertex3f(WIN_WIDTH, 0, 0)
    glVertex3f(WIN_WIDTH, WIN_HEIGHT, 0)
    glVertex3f(0, WIN_HEIGHT, 0)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glClear(GL_DEPTH_BUFFER_BIT)

    if game_state not in (STATE_MAIN_MENU, STATE_MENU_CREDITS, STATE_NAME_INPUT, STATE_CREDITS_ROLL):
        setupCamera()
        draw_ground()
        draw_path()
        draw_border_walls()
        draw_decorations()
        draw_spawner_spire()
        draw_extraction_zone()
        draw_bomb_and_blast()
        draw_fps_bullets()

        for t in towers:
            draw_tower(t)
        for e in enemies:
            draw_enemy(e)
        for p in projectiles:
            draw_projectile(p)

        draw_brute_attacks()
        draw_cursor()
        draw_rain()

    draw_hud_and_dialog()

    glutSwapBuffers()

def main():
    global quadric
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_WIDTH, WIN_HEIGHT)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Death Peaks - Breaking the Cycle")

    glEnable(GL_DEPTH_TEST)

    quadric = gluNewQuadric()

    init_raindrops()
    init_decorations()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()