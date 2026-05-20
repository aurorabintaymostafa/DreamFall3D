from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import glutBitmapCharacter, GLUT_BITMAP_HELVETICA_18

# Camera and world settings.
cam_pos = (0, 500, 500)

fovy = 120
plat_size = 600

# Player position and collision size.
px = 0
py = -420
pz = 35
player_size = 30

# Main game state values.
lvl = 0
layer = 0
stress = 0
captures = 0
pts = 0
focus = 100

mode = "play"
msg = "Find the broken memories."

frame_count = 0
cam_mode = 0

panel_progress = 0
cores = [False, False, False]
collapse_started = [False, False, False, False]
collapse_active = False
collapse_timer = 0
gate_unlocked = [False, False, False, False]

checkpoint_x = 0
checkpoint_y = -420

foe_x = -330
foe_y = 320
foe_direction = 1

# Collectible memory fragments for each level.
frags = [[(-330, -245, 0), (315, 230, 1)], [], [(-380, 330, 0), (30, -335, 1), (365, 260, 1)], []]

fragments_taken = [
    [False, False],
    [],
    [False, False, False],
    []
]

# Sanity orbs reduce stress and refill focus energy.
orbs = [
    [(410, -360), (-410, 380)],
    [(-420, 420), (420, -420)],
    [(-450, 60), (430, -280)],
    [(0, 420), (420, -420)]
]

orbs_taken = [[False, False],[False, False],[False, False],[False, False]]

# Echo terminals show hints when the player interacts with them.
echo_data = [
    [(-430, 120, "Echo: childhood repeats when fear rises. Shift layers to find missing memories.")],
    [(425, 420, "Echo: red, blue, yellow. The hospital only obeys the correct symbol order.")],
    [(-120, 420, "Echo: not every staircase exists in every layer. Look for stable fragments.")],
    [(420, -420, "Echo: rebuild the memory core before the nightmare learns your route.")]
]

echo_read = [[False],[False],[False],[False]]

# Safe zones lower stress and become checkpoints.
zones = [[(420, -410)],[(-430, 430)],[(-440, -420)],[(0, 420)]]

starts = [(0, -420),(0, -430),(-430, -410),(0, -430)]

exits = [(0, 500),(0, 500),(470, 440),(0, 520)]

# Objective text shown on the HUD for each level.
objective_texts = [
    "Level 1: collect both childhood fragments, then escape through the mirror gate.",
    "Level 2: activate symbol panels in order: red, blue, yellow.",
    "Level 3: collect all floating library fragments while avoiding the stalker.",
    "Level 4: activate all three memory-core nodes and reach the true exit."
]

def lim(v, a, b):
    """Keep a number inside the given minimum and maximum range."""
    if v < a:
        return a
    if v > b:
        return b
    return v


def d2(x1, y1, x2, y2):
    """Return squared distance between two 2D points for faster range checks."""
    dx = x1 - x2
    dy = y1 - y2
    return dx * dx + dy * dy


def frag_count(lv):
    """Count how many memory fragments the player collected in one level."""
    c = 0
    for v in fragments_taken[lv]:
        if v:
            c += 1
    return c


def core_count():
    """Count how many memory core nodes are active in the final level."""
    c = 0
    for n in cores:
        if n:
            c += 1
    return c


def frags_done(lv):
    """Check whether all required fragments are collected for a level."""
    if lv < 0 or lv >= len(frags) or lv >= len(fragments_taken):
        return False
    required = len(frags[lv])
    if required == 0:
        return False
    if len(fragments_taken[lv]) < required:
        return False
    for i in range(required):
        if not fragments_taken[lv][i]:
            return False
    return True


def lvl_done(lv):
    """Check whether the current level objective is finished."""
    if lv == 0 or lv == 2:
        return frags_done(lv)
    if lv == 1:
        return panel_progress >= 3
    if lv == 3:
        return core_count() >= 3
    return False


def gate_open(lv):
    """Check whether the exit gate for a level is already unlocked."""
    if lv < 0:
        return False
    if lv >= len(gate_unlocked):
        return False

    # Check if the gate for this level is unlocked
    return gate_unlocked[lv]


def gate_msg(lv):
    """Return the correct message to show when the exit gate opens."""
    if lv == 3:
        return "The true exit is open. Reach the final gate."
    return "The mirror gate is open. Reach the exit."


def gate_update(show_message=False):
    """Unlock the current level gate when the required objective is complete."""
    global msg
    if lvl < 0 or lvl >= len(gate_unlocked):
        return False
    if not gate_unlocked[lvl] and lvl_done(lvl):
        gate_unlocked[lvl] = True
        if show_message:
            msg = gate_msg(lvl)
    return gate_unlocked[lvl]


def stress_name():
    """Convert the current stress value into a short danger label for the HUD."""
    if stress < 25:
        return "Lucid"
    if stress < 55:
        return "Unstable"
    if stress < 80:
        return "Hunted"
    return "Nightmare"


def reset_foe():
    """Place the nightmare enemy back at its starting position for the current level."""
    global foe_x, foe_y, foe_direction

    if lvl == 0:
        foe_x = -360
        foe_y = 350
    elif lvl == 1:
        foe_x = 355
        foe_y = 320
    elif lvl == 2:
        foe_x = 140
        foe_y = 330
    else:
        foe_x = -360
        foe_y = 40

    foe_direction = 1


def reset_game():
    """Restart the whole game and restore all progress, pickups, and counters."""
    global px, py, pz, lvl, layer, stress, captures
    global pts, focus, mode, msg, frame_count, cam_mode
    global panel_progress, cores, collapse_started, collapse_active, collapse_timer
    global gate_unlocked
    global fragments_taken, orbs_taken, echo_read, checkpoint_x, checkpoint_y

    px, py = starts[0]
    pz = 500
    lvl = 0
    layer = 0
    stress = 0
    captures = 0
    pts = 0
    focus = 100
    mode = "play"
    msg = "Find the broken memories."
    frame_count = 0
    cam_mode = 0
    panel_progress = 0
    cores = [False, False, False]
    collapse_started = [False, False, False, False]
    collapse_active = False
    collapse_timer = 0
    gate_unlocked = [False, False, False, False]
    fragments_taken = [
        [False, False],
        [],
        [False, False, False],
        []
    ]
    orbs_taken = [
        [False, False],
        [False, False],
        [False, False],
        [False, False]
    ]
    echo_read = [
        [False],
        [False],
        [False],
        [False]
    ]
    checkpoint_x, checkpoint_y = starts[0]
    reset_foe()


def txt(x, y, text, font = GLUT_BITMAP_HELVETICA_18):
    """Draw text on the 2D user interface layer."""
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

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


def rectangular(x, y, w, h, r, g, b):
    """Draw a flat rectangle used for HUD panels, bars, and minimap markers."""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex3f(x, y, 0)
    glVertex3f(x + w, y, 0)
    glVertex3f(x + w, y + h, 0)
    glVertex3f(x, y + h, 0)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def bar(x, y, w, h, value, max_value, r, g, b):
    """Draw a filled progress bar for stress or focus energy."""
    rectangular(x, y, w, h, 0.08, 0.08, 0.10)
    fill = 0
    if max_value > 0:
        fill = w * value / max_value
    fill = lim(fill, 0, w)
    rectangular(x, y, fill, h, r, g, b)


def box(x, y, z, sx, sy, sz, r, g, b):
    """Draw a scaled cube used for walls, props, panels, and doors."""
    glPushMatrix()
    glColor3f(r, g, b)
    glTranslatef(x, y, z)
    glScalef(sx / 60, sy / 60, sz / 60)
    glutSolidCube(60)
    glPopMatrix()


def lvl_4_rotate_box(x, y, z, sx, sy, sz, angle, r, g, b):
    """Draw a rotated cube, mainly used for diagonal hazard beams."""
    glPushMatrix()
    glColor3f(r, g, b)
    glTranslatef(x, y, z)
    glRotatef(angle, 0, 0, 1)
    glScalef(sx / 60, sy / 60, sz / 60)
    glutSolidCube(60)
    glPopMatrix()


def ball(x, y, z, radius, r, g, b):
    """Draw a sphere used for the player, enemy, or glowing objects."""
    glPushMatrix()
    glColor3f(r, g, b)
    glTranslatef(x, y, z)
    gluSphere(gluNewQuadric(), radius, 12, 12)
    glPopMatrix()


def cylinder(x, y, z, radius1, radius2, height, r, g, b):
    """Draw a cylinder used for portals, pillars, zones, and decorations."""
    glPushMatrix()
    glColor3f(r, g, b)
    glTranslatef(x, y, z)
    gluCylinder(gluNewQuadric(), radius1, radius2, height, 12, 12)
    glPopMatrix()


def floor():
    """Draw the main floor and tint it based on the player stress level."""
    s = plat_size
    fear = stress / 160
    if fear > 0.55:
        fear = 0.55

    glBegin(GL_QUADS)

    glColor3f(0.15 + fear, 0.14, 0.19 + fear)
    glVertex3f(-s, s, 0)
    glVertex3f(0, s, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(-s, 0, 0)

    glColor3f(0.25 + fear, 0.21, 0.33 + fear)
    glVertex3f(s, -s, 0)
    glVertex3f(0, -s, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(s, 0, 0)

    glColor3f(0.08 + fear, 0.08, 0.13 + fear)
    glVertex3f(-s, -s, 0)
    glVertex3f(-s, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, -s, 0)

    glColor3f(0.20 + fear, 0.18, 0.28 + fear)
    glVertex3f(s, s, 0)
    glVertex3f(s, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, s, 0)

    glEnd()


def walls_now():
    """Build and return the wall layout for the current level and dream layer."""
    shift = stress * 0.45
    walls = []

    if lvl == 0:
        walls += [(-530, 0, 40, 1050), (530, 0, 40, 1050), (0, -530, 1050, 40), (0, 530, 1050, 40)]
        if layer == 0:
            walls += [(-205, -60 + shift, 70, 370), (210, 95 - shift, 70, 370), (0, 135, 230, 55)]
        else:
            walls += [(0, -110, 270, 60), (-330, 150 - shift, 70, 360), (335, -130 + shift, 70, 360)]
        if stress > 65 and not gate_open(lvl):
            walls += [(0, 360, 340, 55)]

    elif lvl == 1:
        walls += [(-540, 0, 40, 1050), (540, 0, 40, 1050), (0, -540, 1050, 40), (0, 540, 1050, 40)]
        walls += [(-170, 0, 55, 720), (170, 0, 55, 720)]
        if layer == 0:
            walls += [(0, -145, 290, 45), (0, 175, 290, 45), (-355, 135, 180, 45), (355, -135, 180, 45)]
        else:
            walls += [(0, 0, 250, 45), (-355, -135, 180, 45), (355, 135, 180, 45)]
        if stress > 60 and not gate_open(lvl):
            walls += [(0, 380, 420, 50)]

    elif lvl == 2:
        walls += [(-540, 0, 40, 1050), (540, 0, 40, 1050), (0, -540, 1050, 40), (0, 540, 1050, 40)]
        platform_shift = frame_count % 160
        if platform_shift > 80:
            platform_shift = 160 - platform_shift
        platform_shift = platform_shift - 40

        if layer == 0:
            walls += [(-260, -95, 60, 520), (110, 120, 60, 470), (325, -185 + platform_shift, 60, 350)]
        else:
            walls += [(-100, 110, 60, 540), (245, 50, 60, 470), (-335, 210 - platform_shift, 60, 310)]
        if stress > 55 and not gate_open(lvl):
            walls += [(80, 370, 620, 50)]

    else:
        walls += [(-550, 0, 35, 1080), (550, 0, 35, 1080), (0, -550, 1080, 35), (0, 550, 1080, 35)]
        pulse = frame_count % 120
        if pulse > 60:
            pulse = 120 - pulse
        pulse = pulse + stress * 0.3

        walls += [(-260 + pulse, 0, 55, 610), (260 - pulse, 0, 55, 610)]
        if layer == 0:
            walls += [(0, 250 - stress * 0.2, 440, 45), (0, -250 + stress * 0.2, 440, 45)]
        else:
            walls += [(-260, 250, 45, 420), (260, -250, 45, 420)]
        if stress > 75 and not gate_open(lvl):
            walls += [(0, 395, 420, 60)]

    return walls


def blocked(x, y):
    """Check whether a position hits a wall or goes outside the play area."""
    if x < -500 or x > 500 or y < -500 or y > 500:
        return True

    walls = walls_now()
    for w in walls:
        cx, cy, sx, sy = w
        if x > cx - sx / 2 - player_size / 2 and x < cx + sx / 2 + player_size / 2:
            if y > cy - sy / 2 - player_size / 2 and y < cy + sy / 2 + player_size / 2:
                return True

    return False


def current_zone():
    """Return the safe zone the player is currently standing in, if any."""
    for z in zones[lvl]:
        zx, zy = z
        if d2(px, py, zx, zy) < 9000:
            return z
    return None


def inside_safe_zone(x, y):
    """Check whether any given position is inside a safe zone."""
    for z in zones[lvl]:
        zx, zy = z
        if d2(x, y, zx, zy) < 9000:
            return True
    return False


def move(dx, dy):
    """Move the player while applying wall collision and stress penalties."""
    global px, py, stress, msg

    if mode != "play":
        return

    nx = px + dx
    ny = py + dy

    if not blocked(nx, py):
        px = nx
    else:
        stress = lim(stress + 2.5, 0, 100)
        msg = "The dream shifted and blocked you."

    if not blocked(px, ny):
        py = ny
    else:
        stress = lim(stress + 2.5, 0, 100)
        msg = "The wall moved closer."

    px = lim(px, -500, 500)
    py = lim(py, -500, 500)


def keyboard(key, x, y):
    """Handle normal keyboard controls for movement, layer shift, interact, focus, and restart."""
    global layer, stress, msg, cam_mode, focus

    if key == b'r':
        reset_game()
        return

    if mode != "play":
        return

    step = 28
    if stress > 70:
        step = 22

    if key == b'w':
        move(0, step)
    if key == b's':
        move(0, -step)
    if key == b'a':
        move(-step, 0)
    if key == b'd':
        move(step, 0)
    if key == b'e':
        layer = 1 - layer
        stress = lim(stress + 3, 0, 100)
        if layer == 0:
            msg = "You returned to the waking dream layer."
        else:
            msg = "You entered the nightmare layer."
    if key == b'f':
        interact()
    if key == b'c':
        cam_mode = 1 - cam_mode
    if key == b'v':
        if focus >= 15:
            focus -= 15
            stress = lim(stress - 18, 0, 100)
            msg = "You used focus breathing to stabilize the dream."
        else:
            msg = "Not enough focus energy. Find a sanctuary or sanity orb."


def special_keys(key, x, y):
    """Handle arrow-key camera movement."""
    global cam_pos

    x, y, z = cam_pos

    if key == GLUT_KEY_UP:
        z += 20
    if key == GLUT_KEY_DOWN:
        z -= 20
    if key == GLUT_KEY_LEFT:
        x -= 25
    if key == GLUT_KEY_RIGHT:
        x += 25

    z = lim(z, 220, 760)
    x = lim(x, -520, 520)
    cam_pos = (x, y, z)


def mouse(button, state, x, y):
    """Handle mouse input for interaction and dream-layer shifting."""
    global layer, stress, msg

    if mode != "play":
        return

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        interact()

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        layer = 1 - layer
        stress = lim(stress + 3, 0, 100)
        msg = "Mouse shift: dream layer changed."


def cam_set():
    """Set the OpenGL camera position, including stress-based screen shake."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovy, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    x, y, z = cam_pos

    shake = 0
    if stress > 65:
        shake = (frame_count % 7) - 3

    if cam_mode == 0:
        gluLookAt(px + x + shake * 4, py - y, z + shake * 3, px, py, 35, 0, 0, 1)
    else:
        gluLookAt(px + x / 2 + shake * 5, py - 270, 220 + shake * 4, px, py + 80, 45, 0, 0, 1)


def walls_draw():
    """Draw all walls returned by the current level wall layout."""
    walls = walls_now()

    for w in walls:
        cx, cy, sx, sy = w
        height = 105
        if stress > 70:
            height = 140

        if layer == 0:
            box(cx, cy, height / 2, sx, sy, height, 0.18, 0.18, 0.26)
        else:
            box(cx, cy, height / 2, sx, sy, height, 0.29, 0.08, 0.19)


def arches():
    """Draw repeated arch decorations for the first dream level."""
    for i in range(5):
        y = -360 + i * 170
        box(-445, y, 65, 40, 70, 130, 0.18, 0.20, 0.30)
        box(445, y, 65, 40, 70, 130, 0.18, 0.20, 0.30)
        box(0, y, 125, 110, 24, 45, 0.24, 0.19, 0.35)


def hospital():
    """Draw hospital props for the second level."""
    for i in range(4):
        y = -305 + i * 190
        box(-355, y, 23, 130, 45, 28, 0.70, 0.72, 0.78)
        box(355, -y, 23, 130, 45, 28, 0.70, 0.72, 0.78)
        box(-410, y, 52, 25, 45, 58, 0.55, 0.57, 0.62)
        box(410, -y, 52, 25, 45, 58, 0.55, 0.57, 0.62)


def library():
    """Draw library shelves and floating platforms for the third level."""
    for i in range(5):
        x = -410 + i * 205
        box(x, 35, 90, 55, 360, 180, 0.32, 0.21, 0.13)
        box(x, 35, 190, 58, 370, 20, 0.16, 0.10, 0.08)

    t = frame_count % 160
    if t > 80:
        t = 160 - t
    t = t - 40

    box(-250, -305, 45 + t / 4, 135, 135, 18, 0.20, 0.24, 0.38)
    box(80, -80, 65 - t / 4, 135, 135, 18, 0.25, 0.27, 0.42)
    box(350, 165, 85 + t / 5, 135, 135, 18, 0.30, 0.29, 0.48)


def core_room():
    """Draw the pulsing memory core room in the final level."""
    pulse = frame_count % 100
    if pulse > 50:
        pulse = 100 - pulse

    ball(0, 0, 110, 65 + pulse / 5, 0.65, 0.10, 0.55)
    cylinder(0, 0, 0, 85, 20, 110, 0.20, 0.04, 0.18)
    box(0, 0, 16, 310, 310, 30, 0.18, 0.02, 0.14)


def lvl_props():
    """Draw level-specific scenery and decorations."""
    if lvl == 0:
        arches()
        box(0, 500, 85, 210, 30, 170, 0.32, 0.32, 0.44)
        ball(0, 500, 95, 42, 0.66, 0.75, 0.95)

    elif lvl == 1:
        hospital()
        cylinder(-470, 470, 0, 35, 20, 140, 0.55, 0.55, 0.62)
        cylinder(470, 470, 0, 35, 20, 140, 0.55, 0.55, 0.62)
        cylinder(-470, -470, 0, 35, 20, 140, 0.55, 0.55, 0.62)
        cylinder(470, -470, 0, 35, 20, 140, 0.55, 0.55, 0.62)

    elif lvl == 2:
        library()

    else:
        core_room()


def panel(x, y, active, r, g, b):
    """Draw one puzzle panel or core node, changing its look when active."""
    if active:
        box(x, y, 25, 78, 78, 34, 0.15, 0.95, 0.55)
        ball(x, y, 65, 22, 0.15, 1.00, 0.55)
    else:
        box(x, y, 25, 78, 78, 34, r, g, b)
        ball(x, y, 62, 18, r, g, b)


def puzzles():
    """Draw symbol panels in level 2 and memory core nodes in level 4."""
    if lvl == 1:
        panels = [
            (300, -285, 0.90, 0.12, 0.10),
            (0, 275, 0.15, 0.45, 0.95),
            (-300, -285, 0.95, 0.85, 0.12)
        ]

        for i in range(3):
            x, y, r, g, b = panels[i]
            panel(x, y, i < panel_progress, r, g, b)

    if lvl == 3:
        nodes = [
            (-355, 80, 0.80, 0.15, 0.35),
            (355, 80, 0.25, 0.70, 0.95),
            (0, -325, 0.95, 0.75, 0.25)
        ]

        for i in range(3):
            x, y, r, g, b = nodes[i]
            panel(x, y, cores[i], r, g, b)


def frag_seen(index):
    """Check whether a memory fragment should appear in the current dream layer."""
    frag = frags[lvl][index]
    layer_needed = frag[2]
    return layer_needed == -1 or layer_needed == layer


def frag_draw():
    """Draw all visible and uncollected memory fragments."""
    if lvl >= len(frags):
        return

    for i in range(len(frags[lvl])):
        if not fragments_taken[lvl][i] and frag_seen(i):
            x, y, layer_needed = frags[lvl][i]
            pulse = frame_count % 80
            if pulse > 40:
                pulse = 80 - pulse

            if layer_needed == 0:
                ball(x, y, 48 + pulse / 4, 21, 0.20, 0.85, 1.00)
            else:
                ball(x, y, 48 + pulse / 4, 21, 0.95, 0.25, 0.90)


def orb_draw():
    """Draw all uncollected sanity orbs."""
    for i in range(len(orbs[lvl])):
        if not orbs_taken[lvl][i]:
            x, y = orbs[lvl][i]
            pulse = frame_count % 70
            if pulse > 35:
                pulse = 70 - pulse
            ball(x, y, 50 + pulse / 5, 19, 0.25, 1.00, 0.55)
            cylinder(x, y, 0, 18, 6, 45, 0.08, 0.40, 0.18)


def echo_draw():
    """Draw all unread echo terminals that provide hints."""
    for i in range(len(echo_data[lvl])):
        if not echo_read[lvl][i]:
            x, y, text = echo_data[lvl][i]
            pulse = frame_count % 90
            if pulse > 45:
                pulse = 90 - pulse
            cylinder(x, y, 0, 22, 10, 70, 0.35, 0.10, 0.80)
            ball(x, y, 82 + pulse / 6, 16, 0.70, 0.35, 1.00)


def zone_draw():
    """Draw safe zones and highlight the one the player is standing in."""
    for z in zones[lvl]:
        x, y = z
        active = d2(px, py, x, y) < 9000
        if active:
            cylinder(x, y, 0, 85, 55, 18, 0.20, 0.85, 1.00)
            ball(x, y, 65, 22, 0.30, 1.00, 0.95)
        else:
            cylinder(x, y, 0, 75, 45, 16, 0.08, 0.35, 0.45)
            ball(x, y, 62, 17, 0.12, 0.55, 0.65)


def frag_pick():
    """Collect visible memory fragments when the player gets close enough."""
    global stress, msg, pts

    for i in range(len(frags[lvl])):
        if not fragments_taken[lvl][i] and frag_seen(i):
            x, y, layer_needed = frags[lvl][i]

            if d2(px, py, x, y) < 2300:
                fragments_taken[lvl][i] = True
                stress = lim(stress - 12, 0, 100)
                pts += 100
                msg = "Memory fragment recovered."
                gate_update(True)


def orb_pick():
    """Collect sanity orbs and reward the player with lower stress and more focus."""
    global stress, focus, pts, msg

    for i in range(len(orbs[lvl])):
        if not orbs_taken[lvl][i]:
            x, y = orbs[lvl][i]

            if d2(px, py, x, y) < 2400:
                orbs_taken[lvl][i] = True
                stress = lim(stress - 30, 0, 100)
                focus = lim(focus + 45, 0, 100)
                pts += 70
                msg = "Sanity orb absorbed. Fear pressure reduced."


def zone_tick():
    """Apply safe zone benefits and update the checkpoint location."""
    global stress, focus, checkpoint_x, checkpoint_y, msg

    zone = current_zone()
    if zone is not None:
        zx, zy = zone
        stress = lim(stress - 0.20, 0, 100)
        focus = lim(focus + 0.35, 0, 100)

        if checkpoint_x != zx or checkpoint_y != zy:
            checkpoint_x = zx
            checkpoint_y = zy
            msg = "Lucid sanctuary unlocked as checkpoint."


def interact():
    """Handle interaction with echo terminals, exits, symbol panels, and core nodes."""
    global panel_progress, stress, msg, pts
    global cores, focus

    if mode != "play":
        return

    for i in range(len(echo_data[lvl])):
        if not echo_read[lvl][i]:
            x, y, text = echo_data[lvl][i]
            if d2(px, py, x, y) < 5200:
                echo_read[lvl][i] = True
                focus = lim(focus + 20, 0, 100)
                pts += 60
                msg = text
                return

    if exit_ready() and d2(px, py, exits[lvl][0], exits[lvl][1]) < 6400:
        next_lvl()
        return

    did_something = False

    if lvl == 1:
        panels = [(300, -285), (0, 275), (-300, -285)]

        for i in range(3):
            if d2(px, py, panels[i][0], panels[i][1]) < 4200:
                did_something = True

                if i == panel_progress:
                    panel_progress += 1
                    stress = lim(stress - 8, 0, 100)
                    pts += 120
                    msg = "Correct symbol awakened."
                    gate_update(True)
                else:
                    stress = lim(stress + 17, 0, 100)
                    pts = lim(pts - 30, 0, 99999)
                    msg = "Wrong symbol order. The hospital noticed you."
                break

    if lvl == 3:
        nodes = [(-355, 80), (355, 80), (0, -325)]

        for i in range(3):
            if d2(px, py, nodes[i][0], nodes[i][1]) < 5200:
                did_something = True

                if not cores[i]:
                    cores[i] = True
                    stress = lim(stress + 7, 0, 100)
                    pts += 180
                    msg = "A piece of the memory core locked into place."
                    gate_update(True)
                else:
                    msg = "This core node is already active."
                break

    if not did_something:
        msg = "Nothing answers here."


def exit_ready():
    """Check whether the player can use the current level exit."""
    if lvl < 0 or lvl >= len(gate_unlocked):
        return False
    gate_update(False)
    return gate_unlocked[lvl]


def next_lvl():
    """Advance to the next level or finish the game after the final exit."""
    global lvl, px, py, layer, stress, msg
    global collapse_active, collapse_timer, mode, pts, checkpoint_x, checkpoint_y

    if lvl == 3:
        pts += int(500 + focus - stress - captures * 80)
        mode = "win"
        msg = "You escaped the dream core."
        return

    pts += 250
    lvl += 1
    px, py = starts[lvl]
    checkpoint_x, checkpoint_y = starts[lvl]
    layer = 0
    stress = lim(stress - 22, 0, 100)
    collapse_active = False
    collapse_timer = 0
    reset_foe()
    msg = "You fell into the next dream."


def col_tick():
    """Start and update the dream collapse timer after the exit unlocks."""
    global collapse_active, collapse_timer, mode, msg, stress

    if exit_ready() and not collapse_started[lvl]:
        collapse_started[lvl] = True
        collapse_active = True
        collapse_timer = 900 - lvl * 90
        stress = lim(stress + 8, 0, 100)
        msg = "The dream is collapsing. Reach the exit."

    if collapse_active:
        collapse_timer -= 1
        stress = lim(stress + 0.08 + lvl * 0.02, 0, 100)

        if collapse_timer <= 0:
            mode = "over"
            msg = "The dream collapsed before you escaped."


def foe_state():
    """Choose the enemy behavior state based on stress, distance, and safe zones."""
    if lvl == 0 and frag_count(0) == 0:
        return "Dormant"

    if inside_safe_zone(px, py):
        return "Repelled"

    near = d2(px, py, foe_x, foe_y)

    if collapse_active:
        return "Collapse Hunt"

    if near < 90000 or stress > 55:
        return "Hunting"

    return "Patrolling"


def caught():
    """Handle the player being caught by the nightmare enemy."""
    global captures, stress, px, py, mode, msg, pts

    captures += 1
    stress = lim(stress + 28, 0, 100)
    pts = lim(pts - 80, 0, 99999)

    px = checkpoint_x
    py = checkpoint_y
    reset_foe()

    if captures >= 3:
        mode = "over"
        msg = "A nightmare caught you too many times."
    else:
        msg = "A nightmare caught you. You returned to your checkpoint."


def foe_tick():
    """Move the enemy using patrol, chase, repel, and capture behavior."""
    global foe_x, foe_y, foe_direction, stress

    if mode != "play":
        return

    if lvl == 0 and frag_count(0) == 0:
        return

    state = foe_state()
    near = d2(px, py, foe_x, foe_y)
    speed = 1.5 + stress / 28 + lvl * 0.35

    if collapse_active:
        speed += 1.2

    if state == "Repelled":
        speed = speed * 0.35
        if foe_x < 0:
            foe_x -= speed
        else:
            foe_x += speed

        if foe_y < 0:
            foe_y -= speed
        else:
            foe_y += speed

        foe_x = lim(foe_x, -460, 460)
        foe_y = lim(foe_y, -460, 460)
        return

    if near < 170000 or stress > 48 or collapse_active:
        if foe_x < px:
            foe_x += speed
        if foe_x > px:
            foe_x -= speed
        if foe_y < py:
            foe_y += speed
        if foe_y > py:
            foe_y -= speed

        stress = lim(stress + 0.16 + lvl * 0.04, 0, 100)

    else:
        if lvl == 1:
            foe_y += foe_direction * speed
            if foe_y > 405 or foe_y < -405:
                foe_direction = -foe_direction
        else:
            foe_x += foe_direction * speed
            if foe_x > 405 or foe_x < -405:
                foe_direction = -foe_direction

    if d2(px, py, foe_x, foe_y) < 1700:
        if not inside_safe_zone(px, py):
            caught()


def core_tick():
    """Apply damage from final-level core hazard paths."""
    global stress, msg

    if mode != "play":
        return

    if lvl != 3:
        return

    active = core_count()

    if active == 0:
        return

    if inside_safe_zone(px, py):
        return

    phase = (frame_count // 90) % 4
    danger = False

    if phase == 0:
        if abs(px) < 45 and abs(py) < 470:
            danger = True

    if phase == 1:
        if abs(py) < 45 and abs(px) < 470:
            danger = True

    if phase == 2:
        if abs(px - py) < 55 and abs(px) < 470 and abs(py) < 470:
            danger = True

    if phase == 3:
        if abs(px + py) < 55 and abs(px) < 470 and abs(py) < 470:
            danger = True

    if danger:
        stress = lim(stress + 0.5 + active * 0.15, 0, 100)

        if frame_count % 45 == 0:
            msg = "Core shockwave detected. Move away from the red fracture path."


def fear_tick():
    """Update passive stress changes and trigger game over at maximum stress."""
    global stress, mode, msg

    if mode != "play":
        return

    if d2(px, py, foe_x, foe_y) > 220000 and not collapse_active:
        stress = lim(stress - 0.05, 0, 100)

    if stress >= 100:
        stress = 100
        mode = "over"
        msg = "Your fear rewrote the whole dream."


def player_draw():
    """Draw the player model and extra fear effects."""
    if layer == 0:
        ball(px, py, 42, 26, 0.20, 0.85, 1.00)
        box(px, py, 18, 34, 34, 34, 0.15, 0.40, 0.80)
    else:
        ball(px, py, 42, 26, 0.90, 0.30, 1.00)
        box(px, py, 18, 34, 34, 34, 0.45, 0.10, 0.55)

    if stress > 65:
        ball(px + 55, py - 40, 35, 18, 0.20, 0.05, 0.25)
        ball(px - 60, py + 35, 32, 16, 0.18, 0.04, 0.22)

    if stress > 82:
        ball(px + 95, py + 20, 31, 15, 0.25, 0.02, 0.02)
        ball(px - 95, py - 20, 31, 15, 0.25, 0.02, 0.02)


def foe_draw():
    """Draw the nightmare enemy and its hunting aura."""
    if lvl == 0 and frag_count(0) == 0:
        return

    red = 0.45 + stress / 190
    if red > 1:
        red = 1

    ball(foe_x, foe_y, 58, 34, red, 0.02, 0.03)
    cylinder(foe_x, foe_y, 0, 22, 34, 68, red, 0.02, 0.03)
    ball(foe_x - 12, foe_y - 18, 72, 7, 1, 1, 1)
    ball(foe_x + 12, foe_y - 18, 72, 7, 1, 1, 1)

    if foe_state() == "Hunting" or foe_state() == "Collapse Hunt":
        ball(foe_x, foe_y, 105, 18, 1.00, 0.10, 0.05)


def exit_draw():
    """Draw the exit portal only when the level gate is unlocked."""
    if exit_ready():
        ex, ey = exits[lvl]
        pulse = frame_count % 70
        if pulse > 35:
            pulse = 70 - pulse

        box(ex - 55, ey, 75, 24, 40, 150, 0.65, 0.70, 1.00)
        box(ex + 55, ey, 75, 24, 40, 150, 0.65, 0.70, 1.00)
        box(ex, ey, 148, 135, 40, 24, 0.65, 0.70, 1.00)
        ball(ex, ey, 80, 32 + pulse / 6, 0.30, 0.80, 1.00)


def false_doors():
    """Draw fake doors that appear when stress becomes high."""
    if stress < 60:
        return

    box(-500, -30, 90, 45, 130, 180, 0.35, 0.02, 0.06)
    box(500, 110, 90, 45, 130, 180, 0.35, 0.02, 0.06)

    if stress > 80:
        box(-120, 500, 90, 130, 45, 180, 0.42, 0.02, 0.09)
        box(160, -500, 90, 130, 45, 180, 0.42, 0.02, 0.09)


def core_hazard_draw():
    """Draw the active final-level red hazard beam pattern."""
    if lvl != 3:
        return

    active = core_count()

    if active == 0:
        return

    phase = (frame_count // 90) % 4

    if phase == 0:
        box(0, 0, 15, 70, 900, 18, 0.95, 0.05, 0.05)
    elif phase == 1:
        box(0, 0, 15, 900, 70, 18, 0.95, 0.05, 0.05)
    elif phase == 2:
        lvl_4_rotate_box(0, 0, 15, 900, 65, 18, 45, 0.95, 0.05, 0.05)
    else:
        lvl_4_rotate_box(0, 0, 15, 900, 65, 18, -45, 0.95, 0.05, 0.05)


def target():
    """Find the next objective position for the objective marker and minimap."""
    if exit_ready():
        ex, ey = exits[lvl]
        return ex, ey, "Exit"

    if lvl == 0 or lvl == 2:
        best_i = -1
        for i in range(len(frags[lvl])):
            if not fragments_taken[lvl][i]:
                best_i = i
                break

        if best_i >= 0:
            x, y, layer_needed = frags[lvl][best_i]
            return x, y, "Memory Fragment"

    if lvl == 1:
        panels = [(300, -285), (0, 275), (-300, -285)]
        if panel_progress < 3:
            x, y = panels[panel_progress]
            return x, y, "Next Symbol"

    if lvl == 3:
        nodes = [(-355, 80), (355, 80), (0, -325)]
        for i in range(3):
            if not cores[i]:
                x, y = nodes[i]
                return x, y, "Memory Core Node"

    return 0, 0, "Unknown"


def direction_name(tx, ty):
    """Convert the target direction into a readable compass direction."""
    dx = tx - px
    dy = ty - py

    vertical = ""
    horizontal = ""

    if dy > 60:
        vertical = "North"
    elif dy < -60:
        vertical = "South"

    if dx > 60:
        horizontal = "East"
    elif dx < -60:
        horizontal = "West"

    if vertical != "" and horizontal != "":
        return vertical + "-" + horizontal

    if vertical != "":
        return vertical

    if horizontal != "":
        return horizontal

    return "Here"


def mark_draw():
    """Draw the golden world marker that guides the player to the next objective."""
    tx, ty, label = target()

    pulse = frame_count % 80
    if pulse > 40:
        pulse = 80 - pulse

    ball(tx, ty, 130 + pulse / 4, 16, 1.00, 0.95, 0.30)
    cylinder(tx, ty, 85, 10, 4, 55, 1.00, 0.75, 0.20)

    if stress < 65:
        for i in range(1, 5):
            dot_x = px + (tx - px) * i / 5
            dot_y = py + (ty - py) * i / 5
            ball(dot_x, dot_y, 24, 8, 0.70, 0.85, 1.00)


def minimap():
    """Draw the minimap with walls, player, enemy, safe zones, and objective."""
    mx = 820
    my = 600
    size = 155
    scale = size / 1100

    rectangular(mx, my, size, size, 0.04, 0.04, 0.06)

    walls = walls_now()
    for w in walls:
        cx, cy, sx, sy = w
        wall_x = mx + size / 2 + cx * scale
        wall_y = my + size / 2 + cy * scale
        ww = sx * scale
        hh = sy * scale
        rectangular(wall_x - ww / 2, wall_y - hh / 2, ww, hh, 0.25, 0.20, 0.34)

    tx, ty, label = target()
    ox = mx + size / 2 + tx * scale
    oy = my + size / 2 + ty * scale
    pl_x = mx + size / 2 + px * scale
    pl_y = my + size / 2 + py * scale
    ex = mx + size / 2 + foe_x * scale
    ey = my + size / 2 + foe_y * scale

    for z in zones[lvl]:
        zx, zy = z
        zone_x = mx + size / 2 + zx * scale
        zone_y = my + size / 2 + zy * scale
        rectangular(zone_x - 4, zone_y - 4, 8, 8, 0.20, 0.90, 1.00)

    rectangular(ox - 4, oy - 4, 8, 8, 1.00, 0.90, 0.20)
    rectangular(ex - 4, ey - 4, 8, 8, 1.00, 0.10, 0.10)
    rectangular(pl_x - 5, pl_y - 5, 10, 10, 0.20, 1.00, 0.55)

    txt(mx, my - 22, "Mini-map: green player | red enemy | yellow objective")


def screenview_text():
    """Draw the full HUD with objectives, stats, bars, messages, and end screens."""
    tx, ty, label = target()
    direction = direction_name(tx, ty)

    rectangular(0, 636, 810, 164, 0.03, 0.03, 0.05)
    txt(10, 770, "DreamFall 3D")
    txt(10, 742, objective_texts[lvl])
    txt(10, 714, "Controls: W/S/A/D move | E layer shift | F interact/exit | V focus calm | C camera | R restart")
    txt(10, 686, "Layer: " + ("Waking Dream" if layer == 0 else "Nightmare Layer") + " | Fear Tier: " + stress_name() + " | Enemy: " + foe_state())
    txt(10, 658, "Objective: " + label + " | Direction: " + direction + " | Score: " + str(int(pts)))

    txt(10, 622, "Stress")
    bar(90, 622, 220, 18, stress, 100, 0.95, 0.15, 0.18)

    txt(330, 622, "Focus")
    bar(400, 622, 220, 18, focus, 100, 0.15, 0.75, 1.00)

    txt(640, 622, "Captures: " + str(captures) + "/3")

    if lvl == 0:
        txt(10, 594, "Fragments: " + str(frag_count(0)) + "/" + str(len(frags[0])))
    elif lvl == 1:
        txt(10, 594, "Symbol progress: " + str(panel_progress) + "/3")
    elif lvl == 2:
        txt(10, 594, "Fragments: " + str(frag_count(2)) + "/" + str(len(frags[2])))
    else:
        txt(10, 594, "Memory core: " + str(core_count()) + "/3")

    if collapse_active:
        txt(10, 566, "Collapse timer: " + str(collapse_timer))

    txt(10, 538, "Message: " + msg)

    minimap()

    if mode == "over":
        rectangular(290, 345, 430, 120, 0.08, 0.02, 0.03)
        txt(420, 425, "GAME OVER")
        txt(330, 390, "Press R to restart the dream.")

    if mode == "win":
        rank = "C"
        if captures <= 1 and stress < 60 and pts > 1700:
            rank = "A"
        elif captures <= 2 and pts > 1300:
            rank = "B"

        rectangular(250, 340, 520, 145, 0.02, 0.06, 0.08)
        txt(370, 440, "TRUE EXIT REACHED")
        txt(295, 405, "Final Score: " + str(int(pts)) + " | Dream Rank: " + rank)
        txt(265, 370, "You reconstructed the memory core. Press R to play again.")


def tick():
    """Run the main per-frame game updates and request a redraw."""
    global frame_count

    if mode == "play":
        frame_count += 1
        frag_pick()
        orb_pick()
        zone_tick()

        if frame_count % 2 == 0:
            foe_tick()

        col_tick()
        core_tick()
        fear_tick()

    glutPostRedisplay()


def screen():
    """Render the whole 3D scene and HUD every frame."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    cam_set()

    glPointSize(10)
    glBegin(GL_POINTS)
    glColor3f(1, 1, 1)
    glVertex3f(-plat_size, plat_size, 0)
    glEnd()

    floor()
    lvl_props()
    core_hazard_draw()
    walls_draw()
    false_doors()
    zone_draw()
    orb_draw()
    echo_draw()
    frag_draw()
    puzzles()
    exit_draw()
    mark_draw()
    foe_draw()
    player_draw()
    screenview_text()

    glutSwapBuffers()


def main():
    """Create the OpenGL window, register callbacks, and start the game loop."""
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"DreamFall 3D")

    reset_game()

    glutDisplayFunc(screen)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse)
    glutIdleFunc(tick)

    glutMainLoop()

if __name__ == "__main__":
    main()
