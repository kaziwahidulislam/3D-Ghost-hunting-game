from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# ============================================================
# Haunted Mansion: 3D Escape Quest - 3 Level Final Version
# Built in the same OpenGL/GLUT/GLU style as the supplied template.
# Only basic primitives are used: cubes, spheres, cylinders, quads,
# transformations, text overlay, camera, keyboard/mouse callbacks,
# GLUT idle loop, and GL_DEPTH_TEST.
# ============================================================

WIN_W = 1000
WIN_H = 800
fovY = 90
GRID_LENGTH = 650

# -----------------------------
# Level design
# -----------------------------
# The 20 required project features are implemented and distributed as gameplay:
# Level 1 EASY:      features 1,2,3,4,5,10,11,12,13,14,18 basics
# Level 2 MODERATE:  features 6,7,8,9,15,17,18 advanced, plus progression
# Level 3 HARD:      features 16,19,20, final puzzle, final key, escape zone
# Shield Mode and camera mode work in all levels.

current_level = 1
level_name = "LEVEL 1 - EASY"

LEVEL_DATA = {
    1: {"name": "LEVEL 1 - EASY", "time": 390.0, "health": 5, "speed": 12.5,
        "goal": "Collect all 3 Level-1 key pieces, open the Library door, and enter the Library."},
    2: {"name": "LEVEL 2 - MODERATE", "time": 260.0, "health": 4, "speed": 14.5,
        "goal": "Press the Library switch, solve the Blue-Green rune puzzle, collect Key 2, and Level 3 starts automatically."},
    3: {"name": "LEVEL 3 - HARD", "time": 165.0, "health": 3, "speed": 16.0,
        "goal": "Solve Red-Blue-Green, collect Key 3, open the Final Gate, and escape."},
}

# -----------------------------
# Player state
# -----------------------------
player_x = 0.0
player_y = -380.0
player_z = 0.0
player_angle = 0.0
player_radius = 62.0       # strict body-sized collision radius; player stops before touching walls/doors
COLLISION_MARGIN = 10.0     # extra safety buffer so the visible human model never intersects walls
player_speed = 14.0
walk_phase = 0.0
player_health = 5
max_health = 5

# -----------------------------
# Game state
# -----------------------------
game_state = "PLAYING"     # PLAYING, WIN, LOSE
cheat_mode = False  # Shield Mode flag: ON means protective shield active
camera_mode = "THIRD"      # THIRD or FIRST
camera_distance = 360
camera_height = 260
camera_orbit_x = 0
camera_orbit_y = 0

time_left = 300.0
frame_clock = 0.0
key_spin = 0.0
message_text = "Level 1: Find all 3 key pieces in the Dining Room and Entrance area."
message_timer = 0
message_history = [message_text]
level_banner_timer = 180

# Inventory and puzzle state
has_key_1 = False
has_key_2 = False
has_key_3 = False
key1_collected = False
key1b_collected = False
key1c_collected = False
key1_count = 0
key2_collected = False
key3_collected = False
health_collected = False

library_door_open = False
basement_door_open = False
final_door_open = False
library_switch_on = False
bookshelf_offset = 0.0
final_door_angle = 0.0
chest_open = False
switch_sequence = []
correct_sequence = ["red", "blue", "green"]

# Level 2 moderate puzzle state: after the Library switch opens the route,
# the player must press two Secret Room rune switches in order before Key 2 appears.
l2_rune_sequence = []
l2_correct_sequence = ["blue", "green"]
l2_puzzle_solved = False

# Ghost damage pacing and dynamic hard-level pressure
damage_cooldown = 0
curse_power = 0.0

# -----------------------------
# World layout helpers
# Rectangles are (x1, y1, x2, y2) in top-down coordinates.
# -----------------------------
WALL_H = 120
WALL_T = 24
DOOR_T = 28

walls = [
    # Outer boundary, final exit gap at north center is blocked by final door.
    (-600, -520, 600, -496),
    (-600, 496, -75, 520),
    (75, 496, 600, 520),
    (-600, -520, -576, 520),
    (576, -520, 600, 520),

    # Vertical room dividers.  Door gaps are intentionally wide enough
    # for the player's round body radius, so the player never clips walls
    # while still being able to enter rooms smoothly.
    (-280, -520, -256, -390),
    (-280, -150, -256, -40),
    (256, -520, 280, -390),
    (256, -170, 280, -40),

    # Horizontal middle dividers.  The central gap leads toward the
    # Secret Room after Level 2 begins.  The earlier tiny reversed wall
    # segment was removed because it made the route confusing.
    (-600, -64, -430, -40),
    (-280, -64, -170, -40),
    (170, -64, 600, -40),

    # Upper room dividers.
    (-120, -40, -96, 220),
    (-120, 340, -96, 520),
    (96, -40, 120, 80),
    (96, 250, 120, 520),

    # Bedroom / secret divider and basement detail walls.  The center
    # opening is kept broad so Key 2 in the Secret Room can be reached.
    (-600, 236, -360, 260),
    (-220, 236, -135, 260),
    (135, 236, 170, 260),
    (250, 236, 600, 260),

    # Basement trap-like maze walls.
    (360, 40, 384, 260),
    (250, 120, 475, 144),
]

# Level 1 uses a more open training layout so new players can collect Key 1
# and reach the Library door without fighting narrow corridors. The later
# levels keep the tighter mansion layout for extra challenge.
level1_easy_walls = [
    (-600, -520, 600, -496),
    (-600, 496, -75, 520),
    (75, 496, 600, 520),
    (-600, -520, -576, 520),
    (576, -520, 600, 520),

    # Very wide left/right openings near the entrance hall.
    # The player has a large collision body, so the doorway must be
    # much taller than it looks visually. These wider gaps let the
    # player enter Dining Room and Library smoothly in Level 1.
    (-280, -520, -256, -460),
    (-280, -90, -256, -40),
    (256, -520, 280, -460),
    (256, -90, 280, -40),

    # Softer middle divider, with bigger walkable openings.
    (-600, -64, -470, -40),
    (-220, -64, 160, -40),
    (330, -64, 600, -40),

    # Upper areas are still present visually, but Level 1 does not force the
    # player through narrow advanced sections.
    (-120, 320, -96, 520),
    (96, 300, 120, 520),
]


# Level 2 uses a guided moderate layout. It keeps real wall collision,
# but the intended route from Library -> Mansion Hall -> Secret Room is wide
# enough for the player's large circular collision body. This fixes the bug
# where the glowing path looked open but the player was blocked in normal mode.
level2_guided_walls = [
    # Outer boundary, with the final gate still blocked by its own door logic.
    (-600, -520, 600, -496),
    (-600, 496, -75, 520),
    (75, 496, 600, 520),
    (-600, -520, -576, 520),
    (576, -520, 600, 520),

    # Entrance / room dividers with much larger walkable gaps. The player
    # radius is 62 plus margin, so tiny gaps visually look open but collide.
    (-280, -520, -256, -455),
    (-280, -85, -256, -40),
    (256, -520, 280, -455),
    (256, -85, 280, -40),

    # Middle dividers. Keep wall collision, but leave a broad corridor from
    # Library into the center and toward Secret Room.
    (-600, -64, -470, -40),
    (-280, -64, -190, -40),
    (335, -64, 600, -40),

    # Secret room side walls with wide gaps at bottom and middle.
    (-120, 330, -96, 520),
    (96, 330, 120, 520),

    # Upper divider pieces, split to leave a route to the Blue/Green runes
    # and Key 2. These pieces remain solid, but no longer block the path.
    (-600, 236, -360, 260),
    (-250, 236, -170, 260),
    (170, 236, 250, 260),
    (360, 236, 600, 260),
]

library_door_rect = (256, -360, 280, -200)
basement_door_rect = (96, 80, 120, 250)
final_door_rect = (-75, 496, 75, 520)
bookshelf_rect_base = (-120, 220, -96, 340)

key1_pos = (-445, -300)
key1b_pos = (-350, -155)
key1c_pos = (-115, -300)
key2_pos = (-20, 300)
key3_pos = (460, 420)
health_pos = (-455, -120)
library_switch_pos = (430, -300)
chest_pos = (-455, 355)
exit_zone = (0, 555)

switches = {
    # Final Level 3 switches are placed well inside the Basement puzzle room,
    # away from wall collision buffers, so the player can stand near each one.
    "red":   (260, 345),
    "blue":  (360, 345),
    "green": (460, 345),
}

# Moderate Level 2 rune switches inside the Secret Room.
# They reuse the same draw_switch primitive as the final puzzle.
l2_switches = {
    "blue":  (-52, 210),
    "green": (52, 210),
}

ghosts = [
    {"x": -430.0, "y": -380.0, "spawn": (-430.0, -380.0),
     "path": [(-430, -380), (-430, -120), (-315, -120), (-315, -380)],
     "target": 1, "speed": 0.42, "active": True, "name": "Dining Ghost"},
    {"x": 430.0, "y": -330.0, "spawn": (430.0, -330.0),
     "path": [(430, -330), (430, -110), (325, -110), (325, -330)],
     "target": 1, "speed": 0.52, "active": False, "name": "Library Ghost"},
    {"x": 500.0, "y": 120.0, "spawn": (500.0, 120.0),
     "path": [(500, 120), (500, 420), (170, 420), (170, 120)],
     "target": 1, "speed": 0.62, "active": False, "name": "Basement Ghost"},
]

# ============================================================
# State helpers
# ============================================================
def set_message(txt):
    global message_text, message_timer, message_history
    message_text = txt
    message_timer = 220
    if not message_history or message_history[-1] != txt:
        message_history.append(txt)
    if len(message_history) > 4:
        message_history = message_history[-4:]


def reset_ghosts_for_level():
    for g in ghosts:
        g["x"], g["y"] = g["spawn"]
        g["target"] = 1

    # Level 2 balancing:
    # The Library Ghost's original spawn was very close to the Level 2
    # starting position, so it could touch the player almost immediately.
    # Move it to the far side of the Library at the beginning of Level 2 so
    # the player gets time to read the objective and reach the Library switch.
    if current_level == 2:
        ghosts[1]["x"], ghosts[1]["y"] = 525.0, -120.0
        ghosts[1]["target"] = 2

    ghosts[0]["active"] = current_level >= 1
    ghosts[1]["active"] = current_level >= 2
    ghosts[2]["active"] = current_level >= 3


def start_level(level):
    global current_level, level_name, player_x, player_y, player_angle, player_speed
    global time_left, max_health, player_health, game_state, cheat_mode, camera_mode
    global message_text, message_timer, message_history, level_banner_timer, damage_cooldown
    global curse_power, health_collected
    current_level = level
    level_name = LEVEL_DATA[level]["name"]
    time_left = LEVEL_DATA[level]["time"]
    max_health = LEVEL_DATA[level]["health"]
    player_health = max_health
    player_speed = LEVEL_DATA[level]["speed"]
    game_state = "PLAYING"
    cheat_mode = False  # Shield Mode flag: ON means protective shield active
    camera_mode = "THIRD"
    damage_cooldown = 0
    curse_power = 0.0
    health_collected = False
    level_banner_timer = 190

    if level == 1:
        player_x, player_y, player_angle = 0.0, -380.0, 0.0
        message_text = "Level 1 EASY: collect all 3 key pieces, then open the Library."
    elif level == 2:
        # Start the player in the open middle lane of the Library.
        # The older Level 2 start point was inside/too close to a Library shelf
        # collision area, so the player could not move forward/back/left/right.
        # This position is clear of walls, doors, shelves, and furniture buffers.
        player_x, player_y, player_angle = 430.0, -400.0, 0.0
        message_text = "Level 2 MODERATE: move to the Library switch, then solve Blue-Green runes for Key 2."
    else:
        # Start Level 3 in a clear Basement lane, safely away from maze-wall
        # and trap collision buffers, so the player can enter the final
        # puzzle room without being pushed/stuck at the doorway.
        player_x, player_y, player_angle = 250.0, 70.0, 0.0
        message_text = "Level 3 HARD: enter the puzzle room, solve Red, Blue, Green and escape."

    message_timer = 240
    message_history = [message_text]
    reset_ghosts_for_level()


def reset_game():
    global frame_clock, key_spin, walk_phase
    global has_key_1, has_key_2, has_key_3, key1_collected, key1b_collected, key1c_collected, key1_count, key2_collected, key3_collected
    global health_collected, library_door_open, basement_door_open, final_door_open
    global library_switch_on, bookshelf_offset, final_door_angle, chest_open, switch_sequence, l2_rune_sequence, l2_puzzle_solved

    frame_clock = 0.0
    key_spin = 0.0
    walk_phase = 0.0
    has_key_1 = False
    has_key_2 = False
    has_key_3 = False
    key1_collected = False
    key1b_collected = False
    key1c_collected = False
    key1_count = 0
    key2_collected = False
    key3_collected = False
    health_collected = False
    library_door_open = False
    basement_door_open = False
    final_door_open = False
    library_switch_on = False
    bookshelf_offset = 0.0
    final_door_angle = 0.0
    chest_open = False
    switch_sequence = []
    l2_rune_sequence = []
    l2_puzzle_solved = False
    start_level(1)


def advance_level():
    global has_key_1, has_key_2, library_door_open, basement_door_open
    if current_level == 1:
        has_key_1 = True
        globals()["key1_collected"] = True
        globals()["key1b_collected"] = True
        globals()["key1c_collected"] = True
        globals()["key1_count"] = 3
        library_door_open = True
        start_level(2)
        set_message("Level 1 complete! Level 2 begins inside the Library.")
    elif current_level == 2:
        has_key_2 = True
        globals()["key2_collected"] = True
        globals()["l2_puzzle_solved"] = True
        basement_door_open = True
        start_level(3)
        set_message("Level 2 complete! Level 3 begins in the Basement.")


def distance2d(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def rect_center(rect):
    x1, y1, x2, y2 = rect
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0, abs(x2 - x1), abs(y2 - y1))


def normalize_rect(rect):
    x1, y1, x2, y2 = rect
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def circle_hits_rect(cx, cy, radius, rect):
    # Strict player-body-vs-wall collision.
    # Instead of treating the player as a point, every wall/door rectangle is
    # expanded by the player's body radius + margin. If the player center enters
    # that expanded rectangle, the move is blocked. This is stricter than the
    # older circle check and prevents corner slipping, wall evasion, and visual
    # wall intersection in Level 1/2/3.
    x1, y1, x2, y2 = normalize_rect(rect)
    limit = radius + COLLISION_MARGIN
    return (x1 - limit <= cx <= x2 + limit) and (y1 - limit <= cy <= y2 + limit)


def bookshelf_current_rect():
    x1, y1, x2, y2 = bookshelf_rect_base
    return (x1 - bookshelf_offset, y1, x2 - bookshelf_offset, y2)


def secret_passage_open():
    return current_level >= 2 and (library_switch_on or cheat_mode or bookshelf_offset >= 45)


def level_wall_rects():
    # IMPORTANT: the same wall list is used for drawing and collision.
    # Level 1 uses its training layout, Level 2 uses a guided layout with
    # wider intended passages, and Level 3 keeps the previously fixed final
    # puzzle/escape layout unchanged.
    if current_level == 1:
        return level1_easy_walls
    if current_level == 2:
        return level2_guided_walls
    if current_level == 3:
        rects = []
        for r in walls:
            # Level 3 is the final basement puzzle. The old basement/secret
            # divider and maze wall rectangles made the entrance look open but
            # blocked the large player collision circle. For Level 3 only,
            # remove those specific blocking pieces and keep the remaining
            # mansion walls solid. This creates a clear puzzle-room entrance.
            if r in (
                (96, -40, 120, 80),
                (96, 250, 120, 520),
                (250, 236, 600, 260),
                (360, 40, 384, 260),
                (250, 120, 475, 144),
            ):
                continue

            # Final escape fix: widen the physical exit corridor only after
            # the final door opens, so the visible open gate is actually passable.
            if final_door_open and r == (-600, 496, -75, 520):
                rects.append((-600, 496, -180, 520))
                continue
            if final_door_open and r == (75, 496, 600, 520):
                rects.append((180, 496, 600, 520))
                continue

            rects.append(r)
        return rects
    return walls

def solid_rects():
    rects = list(level_wall_rects())
    # Doors are always solid until opened. Level gates can be drawn/visible,
    # but the round player body cannot intersect any closed door.
    if not library_door_open:
        rects.append(library_door_rect)
    # In the current Level 2 design, collecting Key 2 automatically advances
    # to Level 3, so the Basement door should not physically block the Secret
    # Room rune area. Keep it solid in Level 1 and Level 3.
    if not basement_door_open and current_level != 2:
        rects.append(basement_door_rect)
    if not final_door_open:
        rects.append(final_door_rect)
    # The bookshelf is solid while it is closed or still sliding. Once it has
    # moved away enough in Level 2, its old doorway no longer blocks the path.
    # This prevents the normal-mode glowing path from being blocked while still
    # keeping the visible bookshelf solid during the animation.
    if current_level >= 2 and bookshelf_offset < 105:
        rects.append(bookshelf_current_rect())
    rects.extend(furniture_solid_rects())
    return rects



def furniture_solid_rects():
    # Large furniture is treated as solid in the puzzle levels.
    # In Level 1 and Level 2, furniture collision is disabled so the player
    # cannot get trapped by large shelf/table buffers. Wall, door, bookshelf,
    # and room collision still remain fully solid. Level 3 keeps furniture/trap
    # collision for the harder final challenge.
    rects = []
    if current_level in (1, 2):
        return rects
    rects.append((-40, -275, 40, -225))          # entrance table/statue base
    rects.append((-515, -275, -345, -215))      # dining table
    for yy in (-305, -185):
        for xx in (-500, -440, -380):
            rects.append((xx - 17, yy - 17, xx + 17, yy + 17))
    rects.append((332, -370, 368, -110))        # library shelf left
    rects.append((507, -370, 543, -110))        # library shelf right
    rects.append((-530, 35, -380, 125))         # bed
    rects.append((-232, 320, -178, 420))        # wardrobe
    rects.append((chest_pos[0] - 35, chest_pos[1] - 24, chest_pos[0] + 35, chest_pos[1] + 24))
    # The Level 3 sliding basement block remains visual only. Making it a
    # solid rectangle with the large player radius caused the player to be
    # pushed back near the puzzle-room entrance. Walls and doors still remain
    # fully solid, so collision realism is preserved without trapping the player.
    return rects


def push_out_of_rect(cx, cy, radius, rect):
    # Safety correction for the strict expanded-rectangle collision.
    # If the player center is inside a wall expanded by body radius, push the
    # player to the nearest legal side. This prevents the player from remaining
    # embedded in a wall after a reset, level transition, or numerical corner case.
    x1, y1, x2, y2 = normalize_rect(rect)
    limit = radius + COLLISION_MARGIN
    ex1, ey1, ex2, ey2 = x1 - limit, y1 - limit, x2 + limit, y2 + limit
    if not (ex1 <= cx <= ex2 and ey1 <= cy <= ey2):
        return cx, cy, False

    left = abs(cx - ex1)
    right = abs(ex2 - cx)
    bottom = abs(cy - ey1)
    top = abs(ey2 - cy)
    m = min(left, right, bottom, top)
    if m == left:
        return ex1, cy, True
    if m == right:
        return ex2, cy, True
    if m == bottom:
        return cx, ey1, True
    return cx, ey2, True


def resolve_player_penetration():
    global player_x, player_y
    # Repeat a few times because pushing out of one wall can bring the player
    # near another wall at corners. This keeps the player outside every solid.
    for _ in range(4):
        changed = False
        for rect in solid_rects():
            nx, ny, pushed = push_out_of_rect(player_x, player_y, player_radius, rect)
            if pushed:
                player_x, player_y = nx, ny
                changed = True
        if not changed:
            break

def can_move_to(nx, ny):
    # Use a body-sized radius in every level. Level 1 is easier because the
    # map is wider, not because collision is weakened.
    active_radius = player_radius

    # Hard safety boundary: prevents the player from ever evading/intersecting
    # the mansion's outer walls, even if a very small numerical step would skip
    # past a thin wall edge. This keeps Level 1 wall collision realistic.
    boundary_limit = 576 - active_radius - COLLISION_MARGIN
    if nx < -boundary_limit or nx > boundary_limit or ny < -496 + active_radius + COLLISION_MARGIN:
        return False
    if ny > 496 - active_radius - COLLISION_MARGIN and not (final_door_open and -180 <= nx <= 180):
        return False

    for rect in solid_rects():
        if circle_hits_rect(nx, ny, active_radius, rect):
            return False
    return True


def swept_move(dx, dy):
    global player_x, player_y
    distance = math.hypot(dx, dy)
    # Very small sweep steps stop high-speed tunneling through thin walls.
    steps = max(1, int(math.ceil(distance / 0.35)))
    safe_x, safe_y = player_x, player_y
    moved_any = False

    for _ in range(steps):
        step_x = dx / steps
        step_y = dy / steps
        full_x = safe_x + step_x
        full_y = safe_y + step_y

        if can_move_to(full_x, full_y):
            safe_x, safe_y = full_x, full_y
            moved_any = True
            continue

        # Controlled sliding: allow sliding only along a single legal axis.
        # If both axes are blocked, the player stands still at the wall, which
        # is the realistic collision behavior requested. This prevents diagonal
        # squeezing through wall corners and doorway edges.
        moved = False
        if abs(step_x) > 0 and can_move_to(safe_x + step_x, safe_y):
            safe_x += step_x
            moved = True
        elif abs(step_y) > 0 and can_move_to(safe_x, safe_y + step_y):
            safe_y += step_y
            moved = True

        if moved:
            moved_any = True
            continue

        player_x, player_y = safe_x, safe_y
        resolve_player_penetration()
        return moved_any

    player_x, player_y = safe_x, safe_y
    resolve_player_penetration()
    return moved_any

def current_room():
    if -250 <= player_x <= 250 and -496 <= player_y <= -64:
        return "Entrance Hall"
    if -576 <= player_x <= -280 and -496 <= player_y <= -64:
        return "Dining Room"
    if 280 <= player_x <= 576 and -496 <= player_y <= -64:
        return "Library"
    if -576 <= player_x <= -120 and -40 <= player_y <= 496:
        return "Bedroom"
    if -96 <= player_x <= 96 and -40 <= player_y <= 496:
        return "Secret Room"
    if 120 <= player_x <= 576 and -40 <= player_y <= 496:
        return "Basement"
    if ((final_door_open and -180 <= player_x <= 180) or (-75 <= player_x <= 75)) and player_y > 496:
        return "Exit Gate"
    return "Mansion Hall"


def level2_phase_text():
    # A small checklist for Level 2 so the player always knows what to do next.
    if current_level != 2:
        return ""
    if not library_switch_on:
        return "L2 Progress: [ ] Library Switch  [ ] Blue-Green Runes  [ ] Key 2"
    if not l2_puzzle_solved:
        return "L2 Progress: [X] Library Switch  [" + str(len(l2_rune_sequence)) + "/2] Blue-Green Runes  [ ] Key 2"
    if not has_key_2:
        return "L2 Progress: [X] Library Switch  [X] Blue-Green Runes  [ ] Key 2"
    return "L2 Progress: [X] Library Switch  [X] Blue-Green Runes  [X] Key 2"


def objective_text():
    if current_level == 1:
        if key1_count < 3:
            return "L1 Objective: collect all 3 key pieces (" + str(key1_count) + "/3)."
        if not library_door_open:
            return "L1 Objective: all 3 keys found; press E near Library door."
        return "L1 Objective: enter the Library to start Level 2."
    if current_level == 2:
        if not library_switch_on:
            return "L2 Step 1/3: go to the glowing Library switch and press E."
        if not l2_puzzle_solved:
            return "L2 Step 2/3: follow the trail and press Secret Room runes in order: Blue then Green."
        if not has_key_2:
            return "L2 Step 3/3: Key 2 appeared; collect it to start Level 3."
        return "L2 Complete: Key 2 collected; Level 3 is starting."
    if not has_key_3:
        return "L3 Objective: press switches in order Red, Blue, Green."
    if not final_door_open:
        return "L3 Objective: press E at Final Gate."
    return "L3 Objective: reach the green escape zone."


# ============================================================
# Drawing utilities: cube, sphere, cylinder and text like template.
# ============================================================
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_12):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_cube_box(cx, cy, cz, sx, sy, sz, color):
    glPushMatrix()
    glColor3f(color[0], color[1], color[2])
    glTranslatef(cx, cy, cz)
    glScalef(sx / 60.0, sy / 60.0, sz / 60.0)
    glutSolidCube(60)
    glPopMatrix()


def draw_rect_wall(rect, color, height=WALL_H):
    cx, cy, sx, sy = rect_center(rect)
    draw_cube_box(cx, cy, height / 2.0, sx, sy, height, color)


def draw_floor():
    glBegin(GL_QUADS)
    # Entrance Hall
    glColor3f(0.16, 0.12, 0.16)
    glVertex3f(-250, -496, 0); glVertex3f(250, -496, 0); glVertex3f(250, -64, 0); glVertex3f(-250, -64, 0)
    # Dining Room
    glColor3f(0.24, 0.13, 0.07)
    glVertex3f(-576, -496, 0); glVertex3f(-280, -496, 0); glVertex3f(-280, -64, 0); glVertex3f(-576, -64, 0)
    # Library
    glColor3f(0.10, 0.08, 0.19)
    glVertex3f(280, -496, 0); glVertex3f(576, -496, 0); glVertex3f(576, -64, 0); glVertex3f(280, -64, 0)
    # Bedroom
    glColor3f(0.20, 0.10, 0.15)
    glVertex3f(-576, -40, 0); glVertex3f(-120, -40, 0); glVertex3f(-120, 496, 0); glVertex3f(-576, 496, 0)
    # Secret Room
    glColor3f(0.07, 0.06, 0.18)
    glVertex3f(-96, -40, 0); glVertex3f(96, -40, 0); glVertex3f(96, 496, 0); glVertex3f(-96, 496, 0)
    # Basement
    glColor3f(0.07, 0.07, 0.08)
    glVertex3f(120, -40, 0); glVertex3f(576, -40, 0); glVertex3f(576, 496, 0); glVertex3f(120, 496, 0)
    # Exit Zone
    glColor3f(0.04, 0.30, 0.08)
    glVertex3f(-75, 520, 0); glVertex3f(75, 520, 0); glVertex3f(75, 610, 0); glVertex3f(-75, 610, 0)
    glEnd()


def draw_mansion():
    draw_floor()
    for r in level_wall_rects():
        draw_rect_wall(r, (0.20, 0.18, 0.20))

    if not library_door_open:
        draw_rect_wall(library_door_rect, (0.48, 0.14, 0.08), 105)
    if not basement_door_open:
        draw_rect_wall(basement_door_rect, (0.42, 0.08, 0.08), 105)

    glPushMatrix()
    glTranslatef(-75, 508, 0)
    glRotatef(final_door_angle, 0, 0, 1)
    draw_cube_box(75, 0, 55, 150, 24, 110, (0.05, 0.58, 0.12) if final_door_open else (0.20, 0.07, 0.04))
    glPopMatrix()

    bx1, by1, bx2, by2 = bookshelf_current_rect()
    draw_rect_wall((bx1, by1, bx2, by2), (0.20, 0.09, 0.03), 115)
    for yy in (245, 275, 305):
        draw_cube_box((bx1 + bx2) / 2.0, yy, 80, 18, 8, 50, (0.60, 0.10, 0.18))
        draw_cube_box((bx1 + bx2) / 2.0, yy + 12, 80, 18, 8, 50, (0.10, 0.20, 0.65))


def draw_table_and_furniture():
    # Entrance hall decoration
    draw_cube_box(0, -250, 28, 80, 50, 28, (0.25, 0.18, 0.12))
    glPushMatrix()
    glTranslatef(0, -250, 72)
    glColor3f(0.36, 0.36, 0.42)
    gluSphere(gluNewQuadric(), 28, 12, 12)
    glPopMatrix()

    # Dining table and chairs
    draw_cube_box(-430, -245, 45, 170, 55, 28, (0.35, 0.16, 0.06))
    for yy in (-305, -185):
        for xx in (-500, -440, -380):
            draw_cube_box(xx, yy, 30, 34, 34, 35, (0.22, 0.10, 0.04))

    # Library shelves
    for x in (350, 525):
        draw_cube_box(x, -240, 65, 35, 260, 110, (0.18, 0.08, 0.02))
    for y in (-410, -360, -310, -260, -210, -160):
        draw_cube_box(350, y, 90, 38, 12, 35, (0.08, 0.16, 0.50))
        draw_cube_box(525, y, 90, 38, 12, 35, (0.50, 0.10, 0.12))

    # Bedroom furniture and chest
    draw_cube_box(-455, 80, 35, 150, 90, 35, (0.35, 0.04, 0.13))
    draw_cube_box(-455, 105, 58, 130, 55, 18, (0.55, 0.50, 0.72))
    draw_cube_box(-205, 370, 70, 55, 100, 120, (0.22, 0.10, 0.04))
    draw_cube_box(chest_pos[0], chest_pos[1], 28, 70, 45, 38, (0.80, 0.55, 0.12) if chest_open else (0.52, 0.24, 0.06))

    # Basement trap/moving block, more active in level 3
    slide = 0 if current_level < 3 else 30 * math.sin(frame_clock * 0.04)
    draw_cube_box(230 + slide, 80, 45, 95, 30, 90, (0.25, 0.25, 0.28))


def draw_player():
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z)
    glRotatef(player_angle, 0, 0, 1)
    q = gluNewQuadric()

    arm_swing = 28 * math.sin(walk_phase)
    leg_swing = 30 * math.sin(walk_phase)
    body_bob = 3 * abs(math.sin(walk_phase))

    draw_cube_box(0, 0, 2, 46, 30, 3, (0.03, 0.03, 0.04))

    for ox, phase in ((-10, leg_swing), (10, -leg_swing)):
        glPushMatrix()
        glTranslatef(ox, 0, 20 + body_bob)
        glRotatef(phase, 1, 0, 0)
        glColor3f(0.05, 0.08, 0.22)
        gluCylinder(q, 5, 5, 45, 14, 14)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(ox, 7 if phase > 0 else -7, 10)
        draw_cube_box(0, 0, 0, 18, 28, 9, (0.02, 0.02, 0.025))
        glPopMatrix()

    draw_cube_box(0, 0, 55 + body_bob, 36, 22, 18, (0.08, 0.10, 0.22))
    draw_cube_box(0, 0, 82 + body_bob, 42, 28, 58, (0.08, 0.28, 0.68))

    glPushMatrix()
    glTranslatef(0, 0, 116 + body_bob)
    glColor3f(0.78, 0.58, 0.42)
    gluCylinder(q, 7, 7, 10, 12, 12)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 134 + body_bob)
    glColor3f(0.86, 0.67, 0.48)
    gluSphere(q, 20, 16, 16)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 2, 148 + body_bob)
    glColor3f(0.04, 0.025, 0.015)
    glScalef(1.0, 0.9, 0.45)
    gluSphere(q, 20, 14, 14)
    glPopMatrix()

    for ox in (-7, 7):
        draw_cube_box(ox, 18, 137 + body_bob, 4, 3, 4, (0.0, 0.0, 0.0))
    draw_cube_box(0, 19, 127 + body_bob, 10, 3, 3, (0.35, 0.04, 0.04))

    for ox, swing in ((-28, -arm_swing), (28, arm_swing)):
        glPushMatrix()
        glTranslatef(ox, 0, 94 + body_bob)
        glRotatef(swing, 1, 0, 0)
        glRotatef(8 if ox < 0 else -8, 0, 1, 0)
        glColor3f(0.08, 0.25, 0.60)
        gluCylinder(q, 5, 4, 38, 14, 14)
        glTranslatef(0, 0, 40)
        glColor3f(0.84, 0.64, 0.46)
        gluSphere(q, 7, 12, 12)
        glPopMatrix()

    # Lantern in front hand, gives life to the model
    glPushMatrix()
    glTranslatef(0, 32, 76 + body_bob)
    glColor3f(0.25, 0.20, 0.06)
    gluCylinder(q, 8, 8, 18, 12, 12)
    glTranslatef(0, 0, 22)
    glow = 0.65 + 0.35 * math.sin(frame_clock * 0.09)
    glColor3f(1.0, 0.72 * glow, 0.18)
    gluSphere(q, 10, 12, 12)
    glPopMatrix()

    glPopMatrix()


def draw_cheat_shield():
    if not cheat_mode:
        return
    # Small, clean circular shield placed around the feet, outside the body.
    # It no longer cuts through the torso/head, so it reads as protection.
    q = gluNewQuadric()
    radius = 64 + 1.5 * math.sin(frame_clock * 0.08)
    bead = 3.0
    glow = 0.82 + 0.18 * math.sin(frame_clock * 0.10)
    glPushMatrix()
    glTranslatef(player_x, player_y, 8)
    glColor3f(0.18, 0.95 * glow, 1.0)
    for i in range(40):
        a = 2 * math.pi * i / 40.0
        glPushMatrix()
        glTranslatef(math.cos(a) * radius, math.sin(a) * radius, 0)
        gluSphere(q, bead, 8, 8)
        glPopMatrix()
    glColor3f(0.80, 1.0, 1.0)
    for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
        glPushMatrix()
        glTranslatef(math.cos(a) * radius, math.sin(a) * radius, 0)
        gluSphere(q, bead * 1.25, 10, 10)
        glPopMatrix()
    glPopMatrix()


def draw_key_at(pos, collected, color):
    # Once collected, the key/coin disappears in both normal play and Shield Mode.
    # Shield Mode still allows collection; it does not keep already-collected items on screen.
    if collected:
        return
    x, y = pos
    glPushMatrix()
    glTranslatef(x, y, 55 + 10 * math.sin(frame_clock * 0.08))
    glRotatef(key_spin, 0, 0, 1)
    glColor3f(color[0], color[1], color[2])
    glutSolidCube(24)
    glTranslatef(26, 0, 0)
    gluSphere(gluNewQuadric(), 11, 10, 10)
    glPopMatrix()


def draw_switch(pos, name):
    x, y = pos
    col = (1, 0, 0) if name == "red" else ((0, 0.2, 1) if name == "blue" else (0, 0.9, 0.2))
    draw_cube_box(x, y, 18, 38, 38, 24, col)
    glPushMatrix()
    glTranslatef(x, y, 45)
    glColor3f(col[0], col[1], col[2])
    gluCylinder(gluNewQuadric(), 8, 4, 35, 10, 10)
    glPopMatrix()

def draw_level2_guidance_path():
    # Moderate Level 2 guidance: the trail first guides the player
    # to the two rune switches. After Blue-Green is solved, it guides
    # the player to Key 2. This keeps the level clear but no longer too easy.
    if current_level < 2 or not (library_switch_on or cheat_mode) or key2_collected:
        return
    glow = 0.55 + 0.45 * math.sin(frame_clock * 0.08)
    if not l2_puzzle_solved and not cheat_mode:
        markers = [
            (430, -300), (365, -300), (300, -285), (250, -245),
            (205, -170), (160, -90), (95, -45), (35, -15),
            (0, 60), (0, 135), (0, 190), (-52, 210), (52, 210)
        ]
    else:
        markers = [
            (-52, 210), (0, 225), (52, 210), (30, 250),
            (0, 275), (key2_pos[0], key2_pos[1] - 35)
        ]
    for i, (mx, my) in enumerate(markers):
        if i % 2 == 0:
            color = (0.10, 0.75 * glow, 1.0)
        else:
            color = (0.55 * glow, 0.18, 1.0)
        draw_cube_box(mx, my, 5, 42, 22, 7, color)
        if i % 3 == 0:
            glPushMatrix()
            glTranslatef(mx, my, 45 + 8 * math.sin(frame_clock * 0.08 + i))
            glColor3f(color[0], color[1], color[2])
            gluSphere(gluNewQuadric(), 9, 10, 10)
            glPopMatrix()


def draw_level2_portal_and_signs():
    # Visual-only signposts for Level 2.  They do not affect collision.
    if current_level != 2:
        return
    glow = 0.55 + 0.45 * math.sin(frame_clock * 0.07)
    # Switch halo in Library before activation.
    if not library_switch_on:
        for i in range(16):
            a = 2 * math.pi * i / 16.0
            glPushMatrix()
            glTranslatef(library_switch_pos[0] + math.cos(a) * 45,
                         library_switch_pos[1] + math.sin(a) * 45,
                         12)
            glColor3f(0.2, 1.0 * glow, 0.25)
            gluSphere(gluNewQuadric(), 4, 8, 8)
            glPopMatrix()
    # Rune halos after the Library switch is activated.
    if library_switch_on and not l2_puzzle_solved:
        for nm, pos in l2_switches.items():
            sx, sy = pos
            for i in range(14):
                a = 2 * math.pi * i / 14.0
                glPushMatrix()
                glTranslatef(sx + math.cos(a) * 36, sy + math.sin(a) * 36, 12)
                if nm == "blue":
                    glColor3f(0.15, 0.35, 1.0 * glow)
                else:
                    glColor3f(0.10, 1.0 * glow, 0.25)
                gluSphere(gluNewQuadric(), 4, 8, 8)
                glPopMatrix()

    # Secret Room portal/pedestal appears only after the Blue-Green rune puzzle is solved.
    if library_switch_on and l2_puzzle_solved and not key2_collected:
        glPushMatrix()
        glTranslatef(key2_pos[0], key2_pos[1], 22)
        glColor3f(0.15, 0.65 * glow, 1.0)
        for i in range(24):
            a = 2 * math.pi * i / 24.0
            glPushMatrix()
            glTranslatef(math.cos(a) * 48, math.sin(a) * 48, 0)
            gluSphere(gluNewQuadric(), 4, 8, 8)
            glPopMatrix()
        glPopMatrix()
        draw_cube_box(key2_pos[0], key2_pos[1], 18, 70, 70, 12, (0.12, 0.28, 0.45))


def draw_items_and_puzzles():
    # Level 1 has three key pieces. All three are required for Key 1.
    if current_level == 1 or cheat_mode:
        draw_key_at(key1_pos, key1_collected, (1.0, 0.82, 0.08))
        draw_key_at(key1b_pos, key1b_collected, (0.95, 0.72, 0.05))
        draw_key_at(key1c_pos, key1c_collected, (1.0, 0.92, 0.18))

    # Level 2 key appears after the hidden passage puzzle.
    if current_level >= 2 and ((library_switch_on and l2_puzzle_solved) or cheat_mode or key2_collected):
        draw_key_at(key2_pos, key2_collected, (0.60, 0.90, 1.0))
        if not key2_collected:
            draw_cube_box(key2_pos[0], key2_pos[1], 12, 52, 52, 10, (0.18, 0.38, 0.55))

    # Final key appears only in Level 3 after switch sequence.
    if current_level >= 3 and (len(switch_sequence) == 3 or key3_collected):
        draw_key_at(key3_pos, key3_collected, (1.0, 0.45, 0.05))

    if current_level <= 2 and not health_collected:
        glPushMatrix()
        glTranslatef(health_pos[0], health_pos[1], 42)
        glColor3f(1.0, 0.0, 0.0)
        gluSphere(gluNewQuadric(), 20, 12, 12)
        glPopMatrix()

    # Library switch: Level 2 main puzzle.
    draw_cube_box(library_switch_pos[0], library_switch_pos[1], 18, 36, 36, 25,
                  (0.1, 0.8, 0.2) if library_switch_on else (0.8, 0.1, 0.1))
    glPushMatrix()
    glTranslatef(library_switch_pos[0], library_switch_pos[1], 45)
    glRotatef(35 if library_switch_on else -35, 1, 0, 0)
    glColor3f(0.8, 0.8, 0.8)
    gluCylinder(gluNewQuadric(), 5, 3, 35, 10, 10)
    glPopMatrix()

    draw_level2_portal_and_signs()

    # Moderate Level 2 rune switches appear after the Library switch.
    # Player must press BLUE then GREEN before Key 2 appears.
    if current_level == 2 and (library_switch_on or cheat_mode) and not l2_puzzle_solved:
        for nm in ("blue", "green"):
            draw_switch(l2_switches[nm], nm)

    # Basement final sequence switches appear only in Level 3, unless
    # Shield Mode is being used for demo visibility.
    if current_level >= 3 or cheat_mode:
        for nm in ("red", "blue", "green"):
            draw_switch(switches[nm], nm)

    # Clear glowing passage marker so the player can identify and enter the Secret Room.
    if current_level >= 2 and (library_switch_on or cheat_mode):
        draw_cube_box(0, -52, 6, 140, 20, 8, (0.15, 0.85, 1.0))
        draw_cube_box(0, 248, 6, 140, 20, 8, (0.45, 0.20, 0.95))
        draw_level2_guidance_path()
        draw_level2_portal_and_signs()

    # Secret-room magic object after hidden passage opens.
    if current_level >= 2:
        glPushMatrix()
        glTranslatef(0, 120, 55)
        glRotatef(key_spin, 0, 0, 1)
        glow = 0.5 + 0.5 * math.sin(frame_clock * 0.06)
        glColor3f(0.2 + glow * 0.3, 0.2, 0.65 + glow * 0.3)
        gluSphere(gluNewQuadric(), 28, 12, 12)
        glPopMatrix()


def draw_ghost(g):
    if not g["active"] and not cheat_mode:
        return
    frozen = cheat_mode and g["name"] == "Dining Ghost"
    anim_clock = 0.0 if frozen else frame_clock
    bob = 0 if frozen else 14 * math.sin(anim_clock * 0.08 + g["x"] * 0.01)
    sway = 0 if frozen else 9 * math.sin(anim_clock * 0.06 + g["y"] * 0.01)
    pulse = 1.0 if frozen else 1.0 + 0.06 * math.sin(anim_clock * 0.10)
    zfloat = 52 + bob
    dx = player_x - g["x"]
    dy = player_y - g["y"]
    face_angle = math.degrees(math.atan2(-dx, dy)) if abs(dx) + abs(dy) > 0.01 else 0
    glPushMatrix()
    glTranslatef(g["x"], g["y"], zfloat)
    glRotatef(face_angle, 0, 0, 1)
    glScalef(pulse, pulse, 1.0)
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, -22)
    glColor3f(0.42, 0.72, 0.95)
    glRotatef(180, 1, 0, 0)
    gluCylinder(q, 25, 5, 48, 16, 16)
    glPopMatrix()
    glPushMatrix()
    glColor3f(0.58, 0.82, 1.0)
    glScalef(0.95, 0.78, 1.18)
    gluSphere(q, 34, 18, 18)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 42)
    glColor3f(0.85, 0.96, 1.0)
    gluSphere(q, 23, 16, 16)
    glPopMatrix()
    for ox, rot in ((-30, -28 + sway), (30, 28 - sway)):
        glPushMatrix()
        glTranslatef(ox, 0, 14)
        glRotatef(rot, 0, 1, 0)
        glRotatef(90, 0, 1, 0)
        glColor3f(0.70, 0.90, 1.0)
        gluCylinder(q, 7, 3, 38, 12, 12)
        glPopMatrix()
    draw_cube_box(-8, 19, 47, 5, 4, 7, (0.0, 0.0, 0.0))
    draw_cube_box(8, 19, 47, 5, 4, 7, (0.0, 0.0, 0.0))
    draw_cube_box(0, 20, 34, 10, 3, 5, (0.02, 0.02, 0.04))
    for i, ox in enumerate((-18, 0, 18)):
        glPushMatrix()
        glTranslatef(ox + (0 if frozen else 4 * math.sin(frame_clock * 0.08 + i)), -6, -42 - i * 4)
        glColor3f(0.55, 0.82, 1.0)
        gluSphere(q, 7, 10, 10)
        glPopMatrix()
    if frozen:
        draw_cube_box(0, -4, 82, 44, 8, 8, (0.18, 0.95, 1.0))
    glPopMatrix()




def draw_minimap_box(x, y, w, h, color):
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_QUADS)
    glVertex3f(x, y, 0); glVertex3f(x + w, y, 0); glVertex3f(x + w, y + h, 0); glVertex3f(x, y + h, 0)
    glEnd()


def map_x(wx):
    return 770 + (wx + 600) * 0.17


def map_y(wy):
    return 560 + (wy + 520) * 0.17


def draw_minimap():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    draw_minimap_box(760, 550, 220, 220, (0.03, 0.03, 0.04))
    for r in level_wall_rects():
        x1, y1, x2, y2 = r
        draw_minimap_box(map_x(x1), map_y(y1), max(2, (x2 - x1) * 0.17), max(2, (y2 - y1) * 0.17), (0.55, 0.55, 0.58))
    if current_level == 1 and not key1_collected: draw_minimap_box(map_x(key1_pos[0]), map_y(key1_pos[1]), 5, 5, (1.0, 0.85, 0.0))
    if current_level == 1 and not key1b_collected: draw_minimap_box(map_x(key1b_pos[0]), map_y(key1b_pos[1]), 5, 5, (1.0, 0.85, 0.0))
    if current_level == 1 and not key1c_collected: draw_minimap_box(map_x(key1c_pos[0]), map_y(key1c_pos[1]), 5, 5, (1.0, 0.85, 0.0))
    if current_level >= 2 and not key2_collected: draw_minimap_box(map_x(key2_pos[0]), map_y(key2_pos[1]), 5, 5, (0.6, 0.9, 1.0))
    if current_level >= 3 and not key3_collected: draw_minimap_box(map_x(key3_pos[0]), map_y(key3_pos[1]), 5, 5, (1.0, 0.45, 0.05))
    for g in ghosts:
        if g["active"] or cheat_mode:
            draw_minimap_box(map_x(g["x"]), map_y(g["y"]), 6, 6, (1.0, 0.1, 0.1))
    draw_minimap_box(map_x(player_x), map_y(player_y), 7, 7, (0.2, 1.0, 0.2))
    draw_minimap_box(map_x(exit_zone[0]), map_y(exit_zone[1]), 8, 8, (0.0, 1.0, 0.0))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# ============================================================
# Game logic
# ============================================================
def try_collect_items():
    global has_key_1, has_key_2, has_key_3, key1_collected, key1b_collected, key1c_collected, key1_count, key2_collected, key3_collected
    global player_health, health_collected, basement_door_open

    if current_level == 1:
        collected_now = False
        if not key1_collected and distance2d(player_x, player_y, key1_pos[0], key1_pos[1]) < 55:
            key1_collected = True
            key1_count += 1
            collected_now = True
        if not key1b_collected and distance2d(player_x, player_y, key1b_pos[0], key1b_pos[1]) < 55:
            key1b_collected = True
            key1_count += 1
            collected_now = True
        if not key1c_collected and distance2d(player_x, player_y, key1c_pos[0], key1c_pos[1]) < 55:
            key1c_collected = True
            key1_count += 1
            collected_now = True
        if collected_now:
            if key1_count >= 3:
                has_key_1 = True
                set_message("All 3 Level-1 key pieces collected! Open the Library door.")
            else:
                set_message("Level-1 key piece collected: " + str(key1_count) + "/3.")

    if current_level == 2 and ((library_switch_on and l2_puzzle_solved) or cheat_mode) and not key2_collected and distance2d(player_x, player_y, key2_pos[0], key2_pos[1]) < 75:
        has_key_2 = True
        key2_collected = True
        basement_door_open = True
        set_message("Key 2 collected! Level 2 complete. Starting Level 3.")
        advance_level()
        return

    if current_level >= 3 and len(switch_sequence) == 3 and not key3_collected and distance2d(player_x, player_y, key3_pos[0], key3_pos[1]) < 50:
        has_key_3 = True
        key3_collected = True
        set_message("Final key collected! Now go to the Final Gate and press E.")

    if not health_collected and distance2d(player_x, player_y, health_pos[0], health_pos[1]) < 45:
        player_health = min(max_health, player_health + 1)
        health_collected = True
        set_message("Health restored by +1.")


def interact():
    global library_door_open, basement_door_open, final_door_open, library_switch_on
    global chest_open, switch_sequence, l2_rune_sequence, l2_puzzle_solved, time_left, player_health, curse_power
    if game_state != "PLAYING":
        return

    # Library door / Level 1 completion.
    # The player has a large collision radius, so standing exactly beside the
    # visible door can still be slightly far from the old door-center point.
    # This wider trigger zone fixes the issue where E seemed to do nothing.
    # Once all 3 Level-1 key pieces are collected, pressing E at this door
    # opens it and immediately starts Level 2, so the player does not need to
    # squeeze through the doorway just to trigger the level transition.
    if distance2d(player_x, player_y, 268, -280) < 145:
        if current_level == 1:
            if key1_count >= 3 or has_key_1 or cheat_mode:
                library_door_open = True
                set_message("Library door opened! Level 1 complete. Starting Level 2.")
                advance_level()
            else:
                set_message("Library door is locked. Collect all 3 Level-1 key pieces first.")
        elif has_key_1 or cheat_mode:
            library_door_open = True
            set_message("Library door opened.")
        else:
            set_message("Library door is locked. Collect all 3 Level-1 key pieces first.")
        return

    # Level 2 rune switches must be checked BEFORE the Basement door trigger.
    # The Green rune is close to the old Basement-door trigger point; previously
    # pressing E near Green was intercepted by the Basement-door message, so the
    # Green rune never activated and Key 2 never appeared.
    if current_level == 2 and library_switch_on and not l2_puzzle_solved:
        for name, pos in l2_switches.items():
            if distance2d(player_x, player_y, pos[0], pos[1]) < 95:
                expected = l2_correct_sequence[len(l2_rune_sequence)]
                if name == expected:
                    l2_rune_sequence.append(name)
                    set_message("Correct Level 2 rune: " + name.upper() + ".")
                    if len(l2_rune_sequence) == 2:
                        l2_puzzle_solved = True
                        set_message("Blue-Green rune puzzle solved! Key 2 appeared in the Secret Room.")
                else:
                    l2_rune_sequence = []
                    time_left = max(0.0, time_left - 8.0)
                    set_message("Wrong rune order! Press BLUE first, then GREEN. Time penalty: -8s.")
                return

    if distance2d(player_x, player_y, 108, 165) < 85:
        if current_level < 2:
            set_message("The Basement is not part of Level 1.")
        elif current_level == 2 and not has_key_2:
            set_message("Finish the Blue-Green rune puzzle and collect Key 2 first.")
        elif has_key_2 or cheat_mode:
            basement_door_open = True
            set_message("Basement door is open. In normal Level 2, collecting Key 2 starts Level 3 automatically.")
        else:
            set_message("Basement door is locked. Find Key 2 in Secret Room.")
        return

    if distance2d(player_x, player_y, 0, 505) < 95:
        if current_level < 3:
            set_message("The Final Gate opens only in Level 3.")
        elif has_key_3:
            final_door_open = True
            set_message("Final exit gate is opening. Run straight through the wide green escape path!")
        else:
            set_message("Final Gate locked: solve Red-Blue-Green and collect Key 3 first.")
        return

    if distance2d(player_x, player_y, library_switch_pos[0], library_switch_pos[1]) < 90:
        if current_level >= 2 or cheat_mode:
            if not library_switch_on:
                # Make Level 2 friendlier: the mansion reveals a safe magical trail.
                # This is still state-based puzzle logic, but easier for players to understand.
                library_switch_on = True
                set_message("Library switch activated. Follow the glowing path to the Secret Room!")
            else:
                set_message("Switch already ON. Now solve the Secret Room runes: BLUE then GREEN.")
        else:
            set_message("This switch activates in Level 2.")
        return

    if distance2d(player_x, player_y, chest_pos[0], chest_pos[1]) < 70:
        if has_key_1 or cheat_mode:
            chest_open = True
            set_message("Chest opened. It hints: find the switch behind the Library shelves.")
        else:
            set_message("Chest is locked. It needs all 3 Level-1 key pieces.")
        return

    for name, pos in switches.items():
        if distance2d(player_x, player_y, pos[0], pos[1]) < 65:
            if current_level < 3:
                set_message("The final switch puzzle activates in Level 3.")
                return
            if len(switch_sequence) < 3:
                expected = correct_sequence[len(switch_sequence)]
                if name == expected:
                    switch_sequence.append(name)
                    set_message("Correct switch: " + name.upper() + ".")
                    if len(switch_sequence) == 3:
                        set_message("Final switch puzzle solved! Key 3 appeared.")
                else:
                    switch_sequence = []
                    curse_power += 0.12
                    time_left = max(0.0, time_left - 10.0)
                    player_health = max(1, player_health - 1)
                    for g in ghosts:
                        g["speed"] = min(g["speed"] + 0.04, 0.65)
                    set_message("Wrong order! Puzzle reset, time lost, ghosts became slightly faster.")
            return
    set_message("Nothing to interact with here.")


def move_player(forward_amount, side_amount=0.0):
    global walk_phase
    r = math.radians(player_angle)
    fx = math.sin(-r)
    fy = math.cos(r)
    rx = math.cos(r)
    ry = math.sin(r)
    dx = (fx * forward_amount + rx * side_amount) * player_speed
    dy = (fy * forward_amount + ry * side_amount) * player_speed
    moved_full_distance = swept_move(dx, dy)
    if moved_full_distance:
        walk_phase += 0.45
    else:
        set_message("Collision: solid wall - player stopped.")


def update_ghosts():
    global player_health, damage_cooldown, game_state
    if game_state != "PLAYING":
        return
    # Balanced ghost pressure. Level 2 is still moderate, but the ghost
    # must not catch the player immediately after entering the Library.
    detection = 145 if current_level == 1 else (150 if current_level == 2 else 270)
    for g in ghosts:
        if not g["active"]:
            continue
        # Shield Mode freezes the left-side Dining Ghost as requested.
        if cheat_mode and g["name"] == "Dining Ghost":
            continue
        speed = g["speed"]
        local_detection = detection
        if current_level == 1:
            speed *= 0.65
        elif current_level == 2:
            # Level 2 ghost balancing:
            # Before the switch, the ghost patrols slowly and detects from a
            # short range, giving the player a fair start. After the Library
            # switch, it becomes more active, but still not instant-death fast.
            if not library_switch_on:
                speed *= 0.28
                local_detection = 80
            elif not l2_puzzle_solved:
                speed *= 0.42
                local_detection = 120
            else:
                speed *= 0.55
                local_detection = 145
        else:
            speed *= min(1.08 + curse_power * 0.35, 1.38)
        dplayer = distance2d(player_x, player_y, g["x"], g["y"])
        if dplayer < local_detection:
            dx = player_x - g["x"]
            dy = player_y - g["y"]
        else:
            tx, ty = g["path"][g["target"]]
            dx = tx - g["x"]
            dy = ty - g["y"]
            if math.hypot(dx, dy) < 10:
                g["target"] = (g["target"] + 1) % len(g["path"])
        dist = math.hypot(dx, dy)
        if dist > 0:
            g["x"] += (dx / dist) * speed
            g["y"] += (dy / dist) * speed
        shield_range = 72 if cheat_mode else 58
        if dplayer < shield_range and damage_cooldown <= 0:
            damage_cooldown = 75 if cheat_mode else 95
            g["x"], g["y"] = g["spawn"]
            if cheat_mode:
                set_message("Shield Mode blocked the ghost!")
            else:
                damage = 1 if current_level < 3 else 2
                player_health -= damage
                set_message("A ghost hit you!")
                if player_health <= 0:
                    player_health = 0
                    game_state = "LOSE"
                    set_message("GAME OVER - The ghosts caught you.")


def check_level_progress():
    global game_state
    if current_level == 1 and library_door_open and current_room() == "Library":
        advance_level()
    elif current_level == 2 and basement_door_open and current_room() == "Basement":
        advance_level()
    elif current_level == 3 and final_door_open and distance2d(player_x, player_y, exit_zone[0], exit_zone[1]) < 70:
        game_state = "WIN"
        set_message("YOU ESCAPED ALL THREE LEVELS OF THE MANSION!")


def update_game():
    global time_left, frame_clock, key_spin, message_timer, damage_cooldown
    global bookshelf_offset, final_door_angle, game_state, level_banner_timer
    if game_state == "PLAYING":
        frame_clock += 1.0
        key_spin = (key_spin + 2.5) % 360
        if message_timer > 0:
            message_timer -= 1
        if level_banner_timer > 0:
            level_banner_timer -= 1
        if damage_cooldown > 0:
            damage_cooldown -= 1
        if not cheat_mode:
            time_left -= 1.0 / 60.0
        if time_left <= 0:
            time_left = 0
            game_state = "LOSE"
            set_message("GAME OVER - Level time expired.")
        if library_switch_on and bookshelf_offset < 125:
            bookshelf_offset += 2.0
        if final_door_open and final_door_angle < 90:
            final_door_angle += 2.0
        resolve_player_penetration()
        try_collect_items()
        update_ghosts()
        check_level_progress()


# ============================================================
# Camera and GLUT callbacks
# ============================================================
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    # Camera mode behavior:
    # THIRD mode keeps the original wide overview.
    # FIRST mode in this project is implemented as a CLOSE / ZOOMED game view:
    # it still shows the player and the mansion, but the camera is much closer
    # to the action. This matches the requested behavior: pressing C should not
    # become a narrow eye-only FPS camera; it should show the whole game closer.
    active_fov = 62 if camera_mode == "FIRST" else fovY
    gluPerspective(active_fov, WIN_W / WIN_H, 0.1, 1800)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camera_mode == "FIRST":
        # Close third-person / zoom camera.
        # The camera stays world-stable, so A/D/Q/X movement does not make
        # the whole mansion spin. It simply follows the player from closer range.
        close_distance = 185
        close_height = 145
        cx = player_x + camera_orbit_x
        cy = player_y - close_distance + camera_orbit_y
        cz = close_height
        gluLookAt(cx, cy, cz, player_x, player_y, 75, 0, 0, 1)
    else:
        cx = player_x + camera_orbit_x
        cy = player_y - camera_distance + camera_orbit_y
        cz = camera_height
        gluLookAt(cx, cy, cz, player_x, player_y, 70, 0, 0, 1)


def keyboardListener(key, x, y):
    global player_angle, camera_mode, cheat_mode
    if key in (b'r', b'R'):
        reset_game()
        return
    if game_state != "PLAYING":
        return
    if key in (b'w', b'W'):
        move_player(1, 0)
    elif key in (b's', b'S'):
        move_player(-1, 0)
    elif key in (b'a', b'A'):
        move_player(0, -1)
    elif key in (b'd', b'D'):
        move_player(0, 1)
    elif key in (b'q', b'Q'):
        player_angle += 8
    elif key in (b'x', b'X'):
        player_angle -= 8
    elif key in (b'e', b'E'):
        interact()
    elif key in (b'c', b'C'):
        camera_mode = "FIRST" if camera_mode == "THIRD" else "THIRD"
        set_message("Camera mode: " + ("CLOSE VIEW" if camera_mode == "FIRST" else "THIRD"))
    elif key in (b'f', b'F'):
        cheat_mode = not cheat_mode
        set_message("Shield Mode " + ("ON: shield protects you" if cheat_mode else "OFF"))
    elif key in (b't', b'T'):
        # Demo difficulty/level mode: cycles Easy -> Moderate -> Hard.
        # Normal gameplay still advances automatically by completing objectives.
        if current_level == 1:
            globals()["has_key_1"] = True
            globals()["key1_collected"] = True
            globals()["key1b_collected"] = True
            globals()["key1c_collected"] = True
            globals()["key1_count"] = 3
            globals()["library_door_open"] = True
            start_level(2)
        elif current_level == 2:
            globals()["has_key_1"] = True
            globals()["key1_collected"] = True
            globals()["key1b_collected"] = True
            globals()["key1c_collected"] = True
            globals()["key1_count"] = 3
            globals()["library_door_open"] = True
            globals()["has_key_2"] = True
            globals()["key2_collected"] = True
            globals()["library_switch_on"] = True
            globals()["bookshelf_offset"] = 125
            globals()["l2_puzzle_solved"] = True
            globals()["basement_door_open"] = True
            start_level(3)
        else:
            reset_game()
        return
    elif key in (b'1',):
        reset_game()
    elif key in (b'2',):
        # demo shortcut; normal gameplay still requires finishing Level 1
        globals()["has_key_1"] = True
        globals()["key1_collected"] = True
        globals()["key1b_collected"] = True
        globals()["key1c_collected"] = True
        globals()["key1_count"] = 3
        globals()["library_door_open"] = True
        start_level(2)
    elif key in (b'3',):
        # demo shortcut; normal gameplay still requires finishing Level 2
        globals()["has_key_1"] = True
        globals()["key1_collected"] = True
        globals()["key1b_collected"] = True
        globals()["key1c_collected"] = True
        globals()["key1_count"] = 3
        globals()["library_door_open"] = True
        globals()["has_key_2"] = True
        globals()["key2_collected"] = True
        globals()["library_switch_on"] = True
        globals()["bookshelf_offset"] = 125
        globals()["l2_puzzle_solved"] = True
        globals()["basement_door_open"] = True
        start_level(3)
    elif key == b'\x1b':
        raise SystemExit


def specialKeyListener(key, x, y):
    global camera_height, cheat_mode, player_angle
    if key == GLUT_KEY_LEFT:
        player_angle += 8
    elif key == GLUT_KEY_RIGHT:
        player_angle -= 8
    elif key == GLUT_KEY_UP:
        camera_height += 20
    elif key == GLUT_KEY_DOWN:
        camera_height -= 20
    elif key == GLUT_KEY_F1:
        cheat_mode = not cheat_mode
        set_message("Shield Mode " + ("ON: shield protects you" if cheat_mode else "OFF"))


def mouseListener(button, state, x, y):
    global camera_mode
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        interact()
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = "FIRST" if camera_mode == "THIRD" else "THIRD"
        set_message("Camera mode: " + ("CLOSE VIEW" if camera_mode == "FIRST" else "THIRD"))


def idle():
    update_game()
    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)
    setupCamera()
    draw_mansion()
    draw_table_and_furniture()
    draw_items_and_puzzles()
    for g in ghosts:
        draw_ghost(g)
    draw_player()
    draw_cheat_shield()

    # Clear only depth before overlays so text/minimap stay visible with GL_DEPTH_TEST.
    glClear(GL_DEPTH_BUFFER_BIT)
    # Minimap removed as requested: no black square overlay at top-right.

    keys_count = key1_count + (1 if has_key_2 else 0) + (1 if has_key_3 else 0)

    # HUD restored to the earlier clean top-left overlay style.
    # No opaque panel is drawn, so the updates stay visible without hiding gameplay.
    draw_text(15, 770, "Haunted Mansion: 3D Escape Quest - 3 Level Edition")
    draw_text(15, 742, level_name + "   Health: " + str(player_health) + "/" + str(max_health) + "   Time: " + str(int(time_left)) + "s   Total Keys: " + str(keys_count) + "/5   L1 Pieces: " + str(key1_count) + "/3")
    draw_text(15, 714, "Room: " + current_room() + "   Shield Mode: " + ("ON" if cheat_mode else "OFF") + "   Camera: " + camera_mode)
    draw_text(15, 686, objective_text())
    if current_level == 2:
        draw_text(15, 664, level2_phase_text())
        controls_y = 636
        demo_y = 608
        update_y = 580
    else:
        controls_y = 658
        demo_y = 630
        update_y = 602
    draw_text(15, controls_y, "Controls: W/S forward-back, A/D strafe, Q/X or arrows rotate, E interact, C camera, F shield, R restart")
    draw_text(15, demo_y, "Demo shortcuts: 1/2/3 jump to level. T cycles demo levels. Normal gameplay advances automatically.")
    if message_text:
        draw_text(15, update_y, "Latest Update: " + message_text)
    y_log = update_y - 28
    for old_msg in message_history[:-1][-3:]:
        draw_text(15, y_log, "- " + old_msg)
        y_log -= 24

    if level_banner_timer > 0 and game_state == "PLAYING":
        draw_text(360, 455, level_name)
        draw_text(245, 420, LEVEL_DATA[current_level]["goal"])

    if game_state == "WIN":
        draw_text(300, 440, "YOU ESCAPED ALL THREE LEVELS!")
        draw_text(350, 405, "Press R to restart")
    elif game_state == "LOSE":
        draw_text(360, 440, "GAME OVER")
        draw_text(310, 405, "Press R to restart the escape")

    glutSwapBuffers()


# ============================================================
# Main function
# ============================================================
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Haunted Mansion 3 Level Escape Quest")
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.01, 0.01, 0.018, 1.0)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    reset_game()
    glutMainLoop()


if __name__ == "__main__":
    main()