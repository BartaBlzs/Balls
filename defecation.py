import hashlib
import json
import math
import os
import random
import sys
import time

try:
    import curses
except ImportError:
    sys.exit("curses not found. On Windows run: pip install windows-curses")

try:
    import pygame
except ImportError:
    sys.exit("pygame not found. Install it with: pip install pygame")

SAVE_PATH = os.path.join(os.path.expanduser("~"), ".pigeon_save.json")
WALLET_PATH = os.path.join(os.path.expanduser("~"), ".pigeon_wallet.json")
WALLET_SALT = "PIGEON_WALLET_V1"
ROUND_SECS = 120
MIN_W, MIN_H = 70, 20
PLAYER_HP_MAX = 100
PEOPLE_PER_DIFFICULTY = 3
MAX_PEOPLE = 10
GROUP_THREE_CHANCE = 0.25
GROUP_FIVE_CHANCE = 0.15
NEAR_PERSON_DISTANCE = 8.0
POST_SCORE_SPEED_STEP = 0.55
POST_SCORE_ROCK_RATE_STEP = 0.25
TARGETED_ROCK_NOISE = 0.15
ROCK_THROW_RANGES = ((3.0, 7.0), (2.5, 6.0), (2.0, 5.0), (1.0, 3.0))
ROCK_SPEED = 20.0
ROCK_GRAVITY = 40.0
ROCK_AIR_DRAG = 0.04
ROCK_LIFE = 3.0
ROCK_HIT_DAMAGE = 10
ROCK_HIT_IFRAMES = 0.7
ROCK_SALVO_SIZES = (3, 6, 9, 16)
ROCK_SHADOW_STEP = 0.12
ROCK_SHADOW_TIME = 1.5
POOP_HIT_LOCKOUT = 2.0
ROCK_SALVO_COOLDOWN_MIN = 1.0
ROCK_SALVO_COOLDOWN_MAX = 3.0
LOW_ALTITUDE_BAND = 10.0
LOW_ALTITUDE_HITBOX_X = 1.0
LOW_ALTITUDE_HITBOX_Y = 1.5
POOP_GRAVITY = 52.0
POOP_MAX_SPEED = 42.0
POOP_AIR_DRAG = 0.08
PERSON_DEATH_TIME = 0.85
PERSON_HIT_VERTICAL_MARGIN = 0.5

# --------------------------------------------------------------------------- content

# cost = ammo per poop, pts = base score, hw = extra hit-box half width
SIZES = [
    dict(key="small",  name="Small",  glyph=".",      splat=",",          cost=1, pts=10,  hw=0),
    dict(key="medium", name="Medium", glyph="o",      splat="-o-",        cost=2, pts=25,  hw=1),
    dict(key="large",  name="Large",  glyph="(@)",    splat="~(@)~",      cost=4, pts=60,  hw=2),
    dict(key="mega",   name="MEGA",   glyph="(@@@)",  splat="~~(@@@)~~",  cost=8, pts=150, hw=3),
]
SOUNDS = [
    dict(key="fart",    name="Poop",    file="fart.mp3"),
    dict(key="splat",   name="Splat",   file="splat.mp3"),
    dict(key="squelch", name="Squelch", file="squelch.mp3"),
    dict(key="boing",   name="Boing",   file="boing.mp3"),
    dict(key="bomb",    name="Bomb",    file="bomb.mp3"),
]
POOP_MODES = [
    dict(key="single", name="Single", count=1, cost=0, sound="fart"),
    dict(key="double", name="Double", count=2, cost=1500, sound="splat"),
    dict(key="triple", name="Triple", count=3, cost=2500, sound="squelch"),
    dict(key="shower", name="Shower", count=5, cost=5000, sound="bomb"),
]
SIZE_PRICES = {"small": 1200, "medium": 2200, "large": 3500, "mega": 6000}
SOUND_PRICES = {"fart": 1200, "splat": 1800, "squelch": 2600, "boing": 3400, "bomb": 5000}
FREE = {"size:small", "sound:fart"}
CODE_REDEEM_COST = 1000
ADMIN_WALLET_AMOUNT = 999999999
ADMIN_CODE_HASH = "395fcfb4f94a19b6242902470f4c80cca48eed86fdd65e60c2325339066a9edd"

# sha256 of the code (upper-cased, no spaces) -> what it unlocks.
CODES = {
    "9a9ecd556d5eb0f4b3402d2e81ae6f7913f4d5f0eb07fc411a4d85483cce133f": ["size:medium", "sound:splat"],   # PIGEON-PLUS
    "6bde136c8ac436b7ba67415a436d3a7000a62ebdb4b95c10ffa1a4c26aaf4007": ["sound:squelch", "sound:boing"], # SQUELCH-ME
    "025a44c68d135721dbd332b1e0406091ab36ca3388dc21c340f666786953abe1": ["size:large"],                   # BIG-ONE
    "74413f038c81ed7c50b744a156200abeb6e9307e1edd2591be14d1d7bd8ed29b": ["size:mega", "sound:bomb"],      # BOMBS-AWAY
}

SHOUTS = ["EW!", "MY HAT!", "WHY ME?!", "NOOOO!", "GROSS!", "AGAIN?!", "#$%@!", "MY SUIT!", "SERIOUSLY?!"]
VIP_SHOUTS = ["MY $500 JACKET!", "DO YOU KNOW WHO I AM?!", "MY LAWYER WILL HEAR OF THIS!"]

TITLE = r"""
 ____        __                _   _             
|  _ \  ___ / _| ___  ___ __ _| |_(_) ___  _ __  
| | | |/ _ \ |_ / _ \/ __/ _` | __| |/ _ \| '_ \ 
| |_| |  __/  _|  __/ (_| (_| | |_| | (_) | | | |
|____/ \___|_|  \___|\___\__,_|\__|_|\___/|_| |_|
""".strip("\n").splitlines()

PIGEON_R = [["  \\\\  ", "==(o> "], ["  --  ", "==(o> "]]
PIGEON_L = [["  //  ", " <o)=="], ["  --  ", " <o)=="]]

# --------------------------------------------------------------------------- save / codes

def code_hash(raw):
    return hashlib.sha256(raw.strip().upper().replace(" ", "").encode()).hexdigest()


def load_save():
    """Load player progress and recover safely from damaged/old save files."""
    defaults = {
        "unlocked": [], "size": "small", "sound": "poop",
        "poop_mode": "single", "poop_modes": ["single"],
        "respect": 0, "respect_plus": 0, "best": 0,
        "admin_unlimited": False,
    }
    data = defaults.copy()
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            data.update(loaded)
    except (OSError, ValueError, TypeError):
        pass

    valid_unlocks = FREE | {
        "size:" + item["key"] for item in SIZES
    } | {
        "sound:" + item["key"] for item in SOUNDS
    }
    unlocked = data.get("unlocked", [])
    if not isinstance(unlocked, (list, tuple, set)):
        unlocked = []
    unlocked = {item for item in unlocked if isinstance(item, str) and item in valid_unlocks}
    if data.get("sound") == "plop":
        data["sound"] = "poop"
        unlocked.discard("sound:plop")
        unlocked.add("sound:poop")
    data["unlocked"] = sorted(unlocked | FREE)

    size_keys = {item["key"] for item in SIZES}
    sound_keys = {item["key"] for item in SOUNDS}
    mode_keys = {item["key"] for item in POOP_MODES}
    if data.get("size") not in size_keys or "size:" + str(data.get("size")) not in data["unlocked"]:
        data["size"] = "small"
    if data.get("sound") not in sound_keys or "sound:" + str(data.get("sound")) not in data["unlocked"]:
        data["sound"] = "poop"
    if data.get("poop_mode") not in mode_keys:
        data["poop_mode"] = "single"
    modes = data.get("poop_modes", ["single"])
    if not isinstance(modes, (list, tuple, set)):
        modes = []
    data["poop_modes"] = sorted(({m for m in modes if isinstance(m, str) and m in mode_keys}) | {"single"})
    if data["poop_mode"] not in data["poop_modes"]:
        data["poop_mode"] = "single"

    for key in ("respect", "respect_plus", "best"):
        try:
            data[key] = max(0, int(data.get(key, 0)))
        except (ValueError, TypeError, OverflowError):
            data[key] = 0
    data["admin_unlimited"] = bool(data.get("admin_unlimited", False))
    return data


def clear_user_data(save, wallet):
    save.clear()
    save.update({
        "unlocked": sorted(FREE),
        "size": "small",
        "sound": "poop",
        "poop_mode": "single",
        "poop_modes": ["single"],
        "respect": 0,
        "respect_plus": 0,
        "best": 0,
        "admin_unlimited": False,
    })
    wallet["money"] = 0
    write_save(save)
    write_wallet(wallet["money"])


def write_save(save):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(save, f)
    except OSError:
        pass


def wallet_hash(money):
    return hashlib.sha256(("%d|%s" % (money, WALLET_SALT)).encode()).hexdigest()


def load_wallet():
    try:
        with open(WALLET_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return 0
        money = max(0, int(data.get("money", 0)))
        if data.get("hash") == wallet_hash(money):
            return money
    except (OSError, ValueError, TypeError):
        pass
    return 0


def write_wallet(money):
    payload = {"money": max(0, int(money))}
    payload["hash"] = wallet_hash(payload["money"])
    try:
        with open(WALLET_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f)
    except OSError:
        pass


def wallet_display(save, wallet):
    return "UNLIMITED" if save.get("admin_unlimited", False) else "$%d" % wallet["money"]


def can_afford(save, wallet, price):
    return save.get("admin_unlimited", False) or wallet["money"] >= price


def spend_wallet(save, wallet, price):
    if not save.get("admin_unlimited", False):
        wallet["money"] -= price
        write_wallet(wallet["money"])


def label(unlock_id):
    kind, key = unlock_id.split(":")
    if kind == "size":
        return next(s["name"] for s in SIZES if s["key"] == key) + " poop"
    return next(s["name"] for s in SOUNDS if s["key"] == key) + " sound"


def redeem(save, wallet, raw):
    hashed = code_hash(raw)
    if hashed == ADMIN_CODE_HASH:
        save["admin_unlimited"] = True
        wallet["money"] = ADMIN_WALLET_AMOUNT
        write_save(save)
        write_wallet(wallet["money"])
        return True, "Admin mode enabled: unlimited money."

    unlocks = CODES.get(hashed)
    if not unlocks:
        return False, "Invalid code."
    new = [u for u in unlocks if u not in save["unlocked"]]
    if not new:
        return False, "You already redeemed that code."
    if not save.get("admin_unlimited", False) and wallet["money"] < CODE_REDEEM_COST:
        return False, "Need $%d to redeem a code." % CODE_REDEEM_COST
    spend_wallet(save, wallet, CODE_REDEEM_COST)
    save["unlocked"] = sorted(set(save["unlocked"]) | set(new))
    write_save(save)
    return True, "Unlocked: " + ", ".join(label(u) for u in new)


def owned_sizes(save):
    return [i for i, s in enumerate(SIZES) if "size:" + s["key"] in save["unlocked"]]


def owned_sounds(save):
    return [i for i, s in enumerate(SOUNDS) if "sound:" + s["key"] in save["unlocked"]]


def size_index(save):
    i = next((i for i, s in enumerate(SIZES) if s["key"] == save["size"]), 0)
    return i if i in owned_sizes(save) else 0


def sound_index(save):
    i = next((i for i, s in enumerate(SOUNDS) if s["key"] == save["sound"]), 0)
    return i if i in owned_sounds(save) else 0

# --------------------------------------------------------------------------- audio

VOLUME = 0.1
MAX_SIMULTANEOUS_SOUNDS = 16

class Audio:
    def __init__(self):
        self.dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(MAX_SIMULTANEOUS_SOUNDS)
        except pygame.error as exc:
            raise RuntimeError("Could not initialize audio: %s" % exc) from exc

        self.sounds = {}
        for sound in SOUNDS:
            path = os.path.join(self.dir, sound["file"])
            if not os.path.isfile(path):
                continue
            try:
                self.sounds[sound["key"]] = pygame.mixer.Sound(path)
            except pygame.error as exc:
                raise RuntimeError("Could not load audio file %s: %s" % (path, exc)) from exc

    def play(self, pack_i, size_i):
        pack = SOUNDS[pack_i]
        sound = self.sounds.get(pack["key"])
        if sound is None:
            curses.beep()
            return
        sound.set_volume(max(0.0, min(1.0, VOLUME)))
        sound.play()

    def play_pack(self, pack, size_i):
        pack_i = next(i for i, sound in enumerate(SOUNDS) if sound["key"] == pack)
        self.play(pack_i, size_i)

    def cleanup(self):
        pygame.mixer.quit()

# --------------------------------------------------------------------------- drawing helpers

COL = {}


def cursor(n):
    try:
        curses.curs_set(n)
    except curses.error:
        pass


def init_colors():
    names = ["white", "yellow", "green", "cyan", "magenta", "red", "blue"]
    if not curses.has_colors():
        COL.update({n: 0 for n in names})
        return
    curses.start_color()
    try:
        curses.use_default_colors()
        bg = -1
    except curses.error:
        bg = curses.COLOR_BLACK
    # Use the terminal's standard palette.  Redefining yellow with RGB values
    # produces different results across ncurses, PDCurses, and themed shells.
    cols = [curses.COLOR_WHITE, curses.COLOR_YELLOW, curses.COLOR_GREEN, curses.COLOR_CYAN,
            curses.COLOR_MAGENTA, curses.COLOR_RED, curses.COLOR_BLUE]
    for i, (n, c) in enumerate(zip(names, cols), 1):
        curses.init_pair(i, c, bg)
        COL[n] = curses.color_pair(i)


def put(win, y, x, s, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        s, x = s[-x:], 0
    s = s[: w - x]
    if s:
        try:
            win.addstr(y, x, s, attr)
        except curses.error:
            pass


def put_sprite(win, y, x, rows, attr=0):
    """Draw a sprite, skipping spaces so the skyline shows through."""
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch != " ":
                put(win, y + r, x + c, ch, attr)


def center(win, y, s, attr=0):
    _, w = win.getmaxyx()
    put(win, y, max(0, (w - len(s)) // 2), s, attr)


def segment_hits_rect(x0, y0, x1, y1, left, top, right, bottom):
    """Return whether a moving point crosses an axis-aligned rectangle."""
    dx, dy = x1 - x0, y1 - y0
    t_min, t_max = 0.0, 1.0
    for start, delta, low, high in ((x0, dx, left, right), (y0, dy, top, bottom)):
        if abs(delta) < 1e-9:
            if start < low or start > high:
                return False
            continue
        t1, t2 = (low - start) / delta, (high - start) / delta
        if t1 > t2:
            t1, t2 = t2, t1
        t_min, t_max = max(t_min, t1), min(t_max, t2)
        if t_min > t_max:
            return False
    return True


def score_difficulty(score):
    if score > 250:
        return "U ARE FUCKED", 3
    if score >= 150:
        return "HARDCORE", 2
    if score >= 50:
        return "MEDIUM", 1
    return "EASY", 0


def make_street(w, h, gl):
    grid = [[" "] * w for _ in range(h)]
    rng = random.Random()

    def paint(x, y, char):
        if 0 <= x < w and 0 <= y < h:
            grid[y][x] = char

    x = 0
    while x < w:
        width = rng.randint(8, 15)
        top = rng.randint(max(2, gl // 5), max(3, gl - 8))
        wall = rng.choice(("|", ":", "#", "+"))
        roof = rng.choice(("_", "=", "~"))

        for y in range(top, gl - 1):
            paint(x, y, wall)
            paint(x + width - 1, y, wall)
            if y == top:
                for cx in range(x + 1, x + width - 1):
                    paint(cx, y, roof)
            elif y % 2 == top % 2:
                for cx in range(x + 2, x + width - 2, 4):
                    if rng.random() < 0.75:
                        paint(cx, y, "o")
                        if cx + 1 < x + width - 1:
                            paint(cx + 1, y, "o")

        door_x = x + max(1, width // 2 - 1)
        paint(door_x, gl - 2, "[")
        paint(door_x + 1, gl - 2, "]")
        if rng.random() < 0.45:
            for cx in range(x + 1, x + width - 1, 2):
                paint(cx, gl - 3, "^")

        x += width + rng.randint(1, 3)

    for x in range(w):
        paint(x, gl - 1, "." if x % 2 else "_")
    return ["".join(row) for row in grid]

# --------------------------------------------------------------------------- game

class Person:
    KINDS = {
        "normal": dict(head="o", mult=1, speed=(4, 8),   color="green"),
        "chunky": dict(head="O", mult=1, speed=(3, 5),   color="cyan"),
        "vip":    dict(head="$", mult=3, speed=(9, 13),  color="magenta"),
    }

    def __init__(self, w, edge=None):
        self.respawn(w, edge)
        if edge is None:
            self.x = random.uniform(0, max(1, w - 3))

    def respawn(self, w, edge=None):
        r = random.random()
        self.kind = "vip" if r < 0.12 else ("chunky" if r < 0.4 else "normal")
        k = self.KINDS[self.kind]
        self.speed = random.uniform(*k["speed"])
        self.dir = random.choice((-1, 1)) if edge is None else edge
        self.x = -3.0 if self.dir > 0 else float(w)
        self.stun = 0.0
        self.dead = 0.0
        self.throws_rocks = getattr(self, "throws_rocks", False)
        self.group_id = getattr(self, "group_id", None)
        self.group_size = getattr(self, "group_size", 1)
        self.shout = ""
        self.anim = random.random() * 10

    def rows(self):
        k = self.KINDS[self.kind]
        if self.dead > 0:
            return ["   ", "_x_", "/ \\"]
        if self.stun > 0:
            return [" x ", "\\|/", "/ \\"]
        legs = "/ \\" if int(self.anim * 2) % 2 == 0 else " | "
        return [" " + k["head"] + " ", "/|\\", legs]


def play(stdscr, save, wallet, audio):
    cursor(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)
    h, w = stdscr.getmaxyx()
    if w < MIN_W or h < MIN_H:
        return None
    size_i = size_index(save)
    mode = next(m for m in POOP_MODES if m["key"] == save["poop_mode"])
    POOP_COOLDOWN, RELOAD_COOLDOWN = 0.28, 2.0
    # Give the player enough ammo for one full selected burst.
    MAX_AMMO = max(5, SIZES[size_i]["cost"] * mode["count"])

    def layout():
        nonlocal h, w, gl, bg, clouds
        h, w = stdscr.getmaxyx()
        gl = h - 2
        bg = make_street(w, h, gl)
        clouds = [[random.uniform(0, w), random.randint(3, max(3, gl // 3)), random.uniform(0.8, 2.0)]
                  for _ in range(max(3, w // 25))]

    gl, bg, clouds = 0, [], []
    layout()
    people = [Person(w) for _ in range(max(4, w // 14))]
    next_group_id = 0
    index = 0
    while index < len(people):
        roll = random.random()
        group_size = 5 if roll < GROUP_FIVE_CHANCE else (3 if roll < GROUP_FIVE_CHANCE + GROUP_THREE_CHANCE else 1)
        group_size = min(group_size, len(people) - index)
        group_id = next_group_id
        next_group_id += 1
        for offset, person in enumerate(people[index:index + group_size]):
            person.group_id = group_id
            person.group_size = group_size
            person.x = min(w - 3.0, max(0.0, w / 2 + (offset - (group_size - 1) / 2) * 3.0))
        index += group_size
    poops, rocks, particles, splats, floaters = [], [], [], [], []
    # Start each round over the middle of the skyline.
    px = max(0.0, (w - 6) / 2)
    py = (3.0 + (gl - 8.0)) / 2
    vx, vy, face, flap = 0.0, 0.0, 1, 0.0
    ammo, cooldown, score = MAX_AMMO, 0.0, 0
    poop_lockout = 0.0
    player_hp = PLAYER_HP_MAX
    no_ammo_flash = 0.0
    reloading = False
    retaliation_banner = 0.0
    hurt_iframes = 0.0
    hit_notice = 0.0
    reward_flash = 0.0
    announcement = ""
    announcement_time = 0.0
    # Larger bursts bring the rock pressure in earlier.
    mode_hardness = mode["count"]
    last_level = min(3, score_difficulty(score)[1] + mode_hardness - 1)
    near_people = False
    reward_tier = 0
    rock_salvo_remaining = 0
    rock_throw_queue = []
    rock_salvo_thrower = None
    rock_salvo_cooldown = 0.0
    rock_salvo_pending = False
    next_rock_throw = 0.0
    died = False
    start = None
    last = time.perf_counter()

    while True:
        now = time.perf_counter()
        # The scene keeps moving while the round clock waits for the first
        # poop.  Once the shot is fired, the same real-time delta drives both.
        dt = min(0.1, now - last)
        last = now
        left = ROUND_SECS if start is None else ROUND_SECS - (now - start)
        if left <= 0:
            break

        # ---- input
        want_drop = False
        while True:
            k = stdscr.getch()
            if k == -1:
                break
            if k == curses.KEY_RESIZE:
                layout()
            elif k in (curses.KEY_LEFT, ord("a"), ord("A")):
                vx, face = max(-24, vx - 14), -1
            elif k in (curses.KEY_RIGHT, ord("d"), ord("D")):
                vx, face = min(24, vx + 14), 1
            elif k in (curses.KEY_UP, ord("w"), ord("W")):
                vy = max(-11, vy - 8)
            elif k in (curses.KEY_DOWN, ord("s"), ord("S")):
                vy = min(11, vy + 8)
            elif k == ord(" "):
                want_drop = True
            elif k in (ord("q"), ord("Q"), 27):
                if score > save["best"]:
                    save["best"] = score
                    write_save(save)
                return score

        # ---- pigeon
        drag = math.exp(-3.0 * dt)
        vx, vy = vx * drag, vy * drag
        px = (px + vx * dt) % max(1, w - 6)
        py = min(max(3, py + vy * dt), gl - 8)
        flap += dt * (8 + abs(vx) * 0.3)
        cooldown = max(0.0, cooldown - dt)
        poop_lockout = max(0.0, poop_lockout - dt)
        no_ammo_flash = max(0.0, no_ammo_flash - dt)
        retaliation_banner = max(0.0, retaliation_banner - dt)
        hurt_iframes = max(0.0, hurt_iframes - dt)
        hit_notice = max(0.0, hit_notice - dt)
        reward_flash = max(0.0, reward_flash - dt)
        announcement_time = max(0.0, announcement_time - dt)
        rock_salvo_cooldown = max(0.0, rock_salvo_cooldown - dt)
        next_rock_throw = max(0.0, next_rock_throw - dt)
        _, score_tier = score_difficulty(score)
        difficulty_tier = min(3, score_tier + mode_hardness - 1)
        difficulty_name = ("EASY", "MEDIUM", "HARDCORE", "U ARE FUCKED")[difficulty_tier]
        if difficulty_tier != last_level:
            last_level = difficulty_tier
            announcement = "LEVEL UP: " + difficulty_name
            announcement_time = 2.0
        base_people = max(4, w // 14)
        target_people = min(
            MAX_PEOPLE,
            base_people + difficulty_tier * PEOPLE_PER_DIFFICULTY,
        )
        while len(people) < target_people:
            people.append(Person(w))
        if reloading and cooldown <= 0:
            ammo = MAX_AMMO
            reloading = False

        if want_drop and cooldown <= 0 and poop_lockout <= 0 and not reloading:
            s = SIZES[size_i]
            mode = next(m for m in POOP_MODES if m["key"] == save["poop_mode"])
            ammo_cost = s["cost"] * mode["count"]
            if ammo >= ammo_cost:
                if start is None:
                    start = now
                ammo -= ammo_cost
                cooldown = POOP_COOLDOWN
                for burst_i in range(mode["count"]):
                    poops.append(dict(
                        x=px + (2.5 if face > 0 else 3.5) + burst_i * face * 0.8,
                        y=py + 2.0 - burst_i * 0.2,
                        vx=vx * 0.65 + burst_i * face * 0.7,
                        vy=max(2.0, vy * 0.65 - burst_i * 0.2),
                        size=size_i,
                    ))
                audio.play_pack(mode["sound"], size_i)
                if ammo < ammo_cost:
                    reloading = True
                    cooldown = RELOAD_COOLDOWN
            else:
                no_ammo_flash = 0.6
                reloading = True
                cooldown = RELOAD_COOLDOWN
        elif want_drop and reloading:
            no_ammo_flash = 0.6

        # ---- people
        for p in people:
            if p.dead > 0:
                p.dead -= dt
                if p.dead <= 0:
                    p.respawn(w)
                continue
            p.anim += dt * p.speed
            if p.stun > 0:
                p.stun -= dt
                continue
            speed_multiplier = 1.0
            speed_multiplier += max(0, difficulty_tier - 1) * POST_SCORE_SPEED_STEP
            p.x += p.dir * p.speed * speed_multiplier * dt
            if p.x > w + 1 or p.x < -4:
                p.respawn(w, edge=-p.dir)

        closest = min(
            (min(abs((p.x + 1.5) - (px + 2.5)),
                 w - abs((p.x + 1.5) - (px + 2.5)))
             for p in people if p.dead <= 0),
            default=float("inf"),
        )
        close_now = closest <= NEAR_PERSON_DISTANCE
        if close_now and not near_people:
            announcement = "CLOSE TO PEOPLE: 2X POINTS!"
            announcement_time = 1.5
        near_people = close_now

        # ---- poops
        # A burst only counts people the poop actually crosses.
        direct_hits_this_moment = 0
        direct_hit_people = set()
        for poop in poops[:]:
            previous_x, previous_y = poop["x"], poop["y"]
            poop["vy"] = min(POOP_MAX_SPEED, poop["vy"] + POOP_GRAVITY * dt)
            drag = math.exp(-POOP_AIR_DRAG * dt)
            poop["vx"] *= drag
            poop["x"] += poop["vx"] * dt
            poop["y"] += poop["vy"] * dt
            s = SIZES[poop["size"]]
            hit = None
            for p in people:
                if p.dead > 0 or p.stun > 0:
                    continue
                # Include the head, torso, and legs.  Keep the horizontal
                # bounds at the actual three-column body so neighbors do not
                # share hitboxes.
                if segment_hits_rect(
                        previous_x, previous_y, poop["x"], poop["y"],
                        p.x, gl - 3.0 - PERSON_HIT_VERTICAL_MARGIN,
                        p.x + 3.0, gl + PERSON_HIT_VERTICAL_MARGIN):
                    hit = p
                    break
            if hit or poop["y"] >= gl - 1:
                poops.remove(poop)
                for _ in range(4 + 3 * poop["size"]):
                    particles.append([poop["x"], min(poop["y"], gl - 2), random.uniform(-12, 12),
                                      random.uniform(-14, -3), 0.5, random.choice(".,*'`")])
                if hit:
                    # One person cannot pad the same combo twice in one frame.
                    if id(hit) not in direct_hit_people:
                        direct_hit_people.add(id(hit))
                        direct_hits_this_moment += 1
                    # Group membership does not turn a miss into a hit.
                    victims = (hit,)
                    for victim in victims:
                        distance = min(abs((victim.x + 1.5) - (px + 2.5)),
                                       w - abs((victim.x + 1.5) - (px + 2.5)))
                        proximity_mult = 2 if distance <= NEAR_PERSON_DISTANCE else 1
                        gained = s["pts"] * Person.KINDS[victim.kind]["mult"] * proximity_mult
                        score += gained
                        new_tier = score // 30
                        if new_tier > reward_tier:
                            bonus = (new_tier - reward_tier) * 5
                            reward_tier = new_tier
                            wallet["money"] += bonus
                            write_wallet(wallet["money"])
                            reward_flash = 1.5
                            floaters.append([px + 1, max(2.0, py - 1.0), "+$%d" % bonus, 1.1])
                        floaters.append([victim.x + 1, gl - 5.0, "+%d$" % gained, 1.0])
                        victim.shout = random.choice(VIP_SHOUTS if victim.kind == "vip" else SHOUTS)
                        victim.throws_rocks = True
                        rock_throw_queue.append(victim)
                        victim.stun = PERSON_DEATH_TIME
                    rock_salvo_pending = True
                    retaliation_banner = 3.0
                else:
                    splats.append([poop["x"], s["splat"], 4.0])

        if direct_hits_this_moment >= 5:
            save["respect_plus"] += 1
            write_save(save)
            announcement = "AMAZING! FIVE HIT! RESPECT+ +1"
            announcement_time = 2.5
        elif direct_hits_this_moment >= 3:
            save["respect"] += 1
            write_save(save)
            announcement = "GOOD JOB! TRIPLE HIT! RESPECT +1"
            announcement_time = 2.5

        if rock_salvo_pending and rock_salvo_remaining == 0 and rock_salvo_cooldown <= 0:
            if rock_throw_queue:
                thrower = rock_throw_queue[0]
                if thrower in people and thrower.dead <= 0 and thrower.stun <= 0:
                    rock_throw_queue.pop(0)
                    rock_salvo_thrower = thrower
                    rock_salvo_remaining = ROCK_SALVO_SIZES[difficulty_tier]
                    rock_salvo_pending = False
                    next_rock_throw = random.uniform(1.0, 2.0)
        if rock_salvo_thrower is not None and rock_salvo_remaining > 0 and next_rock_throw <= 0:
            thrower = rock_salvo_thrower
            ox, oy = thrower.x + 1.5, gl - 2.0
            difficulty = 1.0 + difficulty_tier * 0.18
            rock_speed = ROCK_SPEED + difficulty_tier * 2.0
            target_lead = 0.45
            aim_noise = 0.8
            if difficulty_tier >= 2:
                target_lead = 0.65 + (difficulty_tier - 2) * 0.05
                aim_noise = max(TARGETED_ROCK_NOISE, 0.8 / (difficulty_tier + 1))
            tx = px + 2.5 + vx * target_lead
            ty = py + 1.0 + vy * target_lead
            dx, dy = tx - ox, ty - oy
            distance = math.hypot(dx, dy) or 1.0
            flight_time = min(1.5, max(0.65, distance / rock_speed))
            rocks.append(dict(
                x=ox,
                y=oy,
                vx=dx / flight_time + random.uniform(-aim_noise, aim_noise),
                vy=dy / flight_time - 0.5 * ROCK_GRAVITY * flight_time + random.uniform(-aim_noise, aim_noise),
                life=ROCK_LIFE,
            ))
            audio.play(4, 0)
            rock_salvo_remaining -= 1
            rock_rate = 1.0
            rock_rate += difficulty_tier * POST_SCORE_ROCK_RATE_STEP
            throw_min, throw_max = ROCK_THROW_RANGES[difficulty_tier]
            next_rock_throw = random.uniform(throw_min, throw_max) / (difficulty * rock_rate)
            if rock_salvo_remaining == 0:
                rock_salvo_thrower = None
                rock_salvo_pending = bool(rock_throw_queue)
                rock_salvo_cooldown = random.uniform(
                    ROCK_SALVO_COOLDOWN_MIN, ROCK_SALVO_COOLDOWN_MAX
                ) / rock_rate

        for pt in particles[:]:
            pt[2] *= 0.98
            pt[3] += 40 * dt
            pt[0] += pt[2] * dt
            pt[1] += pt[3] * dt
            pt[4] -= dt
            if pt[4] <= 0 or pt[1] >= gl:
                particles.remove(pt)
        for f in floaters[:]:
            f[1] -= 3 * dt
            f[3] -= dt
            if f[3] <= 0:
                floaters.remove(f)
        for sp in splats[:]:
            sp[2] -= dt
            if sp[2] <= 0:
                splats.remove(sp)
        for c in clouds:
            c[0] += c[2] * dt
            if c[0] > w + 8:
                c[0] = -8
        for rock in rocks[:]:
            previous_x, previous_y = rock["x"], rock["y"]
            rock["vx"] *= math.exp(-ROCK_AIR_DRAG * dt)
            rock["vy"] += ROCK_GRAVITY * dt
            rock["x"] += rock["vx"] * dt
            rock["y"] += rock["vy"] * dt
            rock["life"] -= dt
            if (rock["life"] <= 0 or rock["x"] < -1 or rock["x"] > w + 1 or
                    rock["y"] < 0 or rock["y"] > gl):
                rocks.remove(rock)
                continue
            # Flying low makes the pigeon easier to hit.
            low_altitude = max(0.0, min(1.0, (py - (gl - 8 - LOW_ALTITUDE_BAND)) / LOW_ALTITUDE_BAND))
            hitbox_x = LOW_ALTITUDE_HITBOX_X * low_altitude
            hitbox_y = LOW_ALTITUDE_HITBOX_Y * low_altitude
            if ((not reloading) and hurt_iframes <= 0 and
                    segment_hits_rect(
                        previous_x, previous_y, rock["x"], rock["y"],
                        px - 0.5 - hitbox_x, py - 0.5 - hitbox_y,
                        px + 5.5 + hitbox_x, py + 2.5 + hitbox_y)):
                rocks.remove(rock)
                hurt_iframes = ROCK_HIT_IFRAMES
                poop_lockout = POOP_HIT_LOCKOUT
                hit_notice = 1.2
                player_hp = max(0, player_hp - ROCK_HIT_DAMAGE)
                score = max(0, score - 10)
                vx = min(24, max(-24, vx + rock["vx"] * 0.15))
                vy = min(11, max(-11, vy + rock["vy"] * 0.08))
                if player_hp <= 0:
                    died = True
                    break

        if died:
            break

        # ---- draw
        stdscr.erase()
        for r, line in enumerate(bg):
            if line.strip():
                put(stdscr, r, 0, line, COL["blue"] | curses.A_DIM)
        for c in clouds:
            put_sprite(stdscr, int(c[1]), int(c[0]), [" .-~~-. ", "(______)"], COL["white"] | curses.A_DIM)
        put(stdscr, gl, 0, "=" * w, COL["green"])
        for sp in splats:
            put(stdscr, gl - 1, int(sp[0] - len(sp[1]) / 2), sp[1], COL["yellow"] | curses.A_DIM)
        for p in people:
            k = Person.KINDS[p.kind]
            attr = COL[k["color"]] | (curses.A_BOLD if p.kind == "vip" else 0)
            put_sprite(stdscr, gl - 3, int(p.x), p.rows(), attr)
            if (p.dead > 0 or p.stun > 0) and p.shout:
                put(stdscr, gl - 4, int(p.x + 1.5 - len(p.shout) / 2), p.shout, COL["red"] | curses.A_BOLD)
        for poop in poops:
            g = SIZES[poop["size"]]["glyph"]
            put(stdscr, int(poop["y"]), int(poop["x"] - len(g) / 2), g, COL["yellow"] | curses.A_BOLD)
        for pt in particles:
            put(stdscr, int(pt[1]), int(pt[0]), pt[5], COL["yellow"])
        # Red dots mark the rocks' projected paths.
        for rock in rocks:
            shadow_x, shadow_y = rock["x"], rock["y"]
            shadow_vx, shadow_vy = rock["vx"], rock["vy"]
            shadow_time = min(rock["life"], ROCK_SHADOW_TIME)
            while shadow_time > 0:
                step = min(ROCK_SHADOW_STEP, shadow_time)
                shadow_vx *= math.exp(-ROCK_AIR_DRAG * step)
                shadow_vy += ROCK_GRAVITY * step
                shadow_x += shadow_vx * step
                shadow_y += shadow_vy * step
                if shadow_x < 0 or shadow_x >= w or shadow_y < 0 or shadow_y > gl:
                    break
                put(stdscr, int(shadow_y), int(shadow_x), ".", COL["red"] | curses.A_DIM)
                shadow_time -= step
        for rock in rocks:
            put(stdscr, int(rock["y"]), int(rock["x"]), "O", COL["red"] | curses.A_BOLD)
        for f in floaters:
            put(stdscr, int(f[1]), int(f[0]), f[2], COL["yellow"] | curses.A_BOLD)
        frames = PIGEON_R if face > 0 else PIGEON_L
        put_sprite(stdscr, int(py), int(px), frames[int(flap) % 2], COL["white"] | curses.A_BOLD)
        if hit_notice > 0:
            put(stdscr, max(2, int(py) - 1), int(px) - 2, "-10 HP  -10 SCORE", COL["red"] | curses.A_BOLD)

        put(stdscr, 0, 1, "SCORE %05d" % score, COL["yellow"] | curses.A_BOLD)
        put(stdscr, 0, 16, "LV %d" % (difficulty_tier + 1), COL["magenta"] | curses.A_BOLD)
        put(stdscr, 0, 24, difficulty_name[:14], COL["magenta"] | curses.A_BOLD)
        hp_attr = (COL["red"] | curses.A_BOLD) if player_hp <= ROCK_HIT_DAMAGE else (COL["green"] | curses.A_BOLD)
        put(stdscr, 0, 41, "HP %03d" % player_hp, hp_attr)
        put(stdscr, 0, 51, "TIME %03d" % math.ceil(left), COL["white"] | curses.A_BOLD)
        if retaliation_banner > 0:
            center(stdscr, 2, "POOPED PEOPLE ARE THROWING ROCKS - DODGE!", COL["red"] | curses.A_BOLD)
        if announcement_time > 0:
            center(stdscr, 3, announcement, COL["yellow"] | curses.A_BOLD)
        if reward_flash > 0:
            center(stdscr, 4, "+$5 every 30 score!", COL["green"] | curses.A_BOLD)
        if start is None:
            center(stdscr, h // 2, "PRESS SPACE TO START", COL["yellow"] | curses.A_BOLD)
        bar = int(ammo / MAX_AMMO * 12)
        ammo_attr = COL["red"] | curses.A_BOLD if no_ammo_flash > 0 else COL["cyan"]
        put(stdscr, 1, 1, "AMMO [%s%s]" % ("#" * bar, "-" * (12 - bar)), ammo_attr)
        if poop_lockout > 0:
            cd_attr = COL["red"] | curses.A_BOLD
            cd_text = "ROCK HIT %.1fs" % poop_lockout
        else:
            cd_attr = (COL["red"] | curses.A_BOLD) if reloading else ((COL["yellow"] | curses.A_BOLD) if cooldown > 0 else (COL["green"] | curses.A_BOLD))
            cd_text = "RELOAD %.1fs" % cooldown if reloading else ("CD %.1fs" % cooldown if cooldown > 0 else "CD READY")
        put(stdscr, 1, 18, cd_text, cd_attr)
        put(stdscr, 1, 34, "RESPECT %d  RESPECT+ %d" %
            (save["respect"], save["respect_plus"]), COL["red"] | curses.A_BOLD)
        put(stdscr, h - 1, 1, "arrows/WASD fly   SPACE poop   Q menu", curses.A_DIM)
        stdscr.refresh()

        time.sleep(max(0.0, 1 / 30 - (time.perf_counter() - now)))

    # ---- results
    new_best = score > save["best"]
    if new_best:
        save["best"] = score
        write_save(save)
    curses.flushinp()
    stdscr.nodelay(False)
    stdscr.timeout(-1)
    stdscr.erase()
    cy = h // 2 - 3
    result_attr = (COL["red"] | curses.A_BOLD) if died else (COL["yellow"] | curses.A_BOLD)
    center(stdscr, cy, "YOU DIED!" if died else "TIME'S UP!", result_attr)
    center(stdscr, cy + 2, "You hit people for %d points" % score, COL["white"])
    center(stdscr, cy + 3, "NEW BEST!" if new_best else "Best: %d" % save["best"], COL["magenta"] | curses.A_BOLD)
    center(stdscr, cy + 4, "Wallet: %s" % wallet_display(save, wallet), COL["green"] | curses.A_BOLD)
    center(stdscr, cy + 5, "press any key", curses.A_DIM)
    stdscr.refresh()
    time.sleep(0.6)
    curses.flushinp()
    stdscr.getch()
    return score

# --------------------------------------------------------------------------- menus

def enter_code(stdscr, save, wallet):
    buf, msg, ok = "", "", False
    cursor(1)
    while True:
        stdscr.erase()
        h, _ = stdscr.getmaxyx()
        cy = h // 2 - 3
        center(stdscr, cy, "ENTER YOUR CODE", COL["yellow"] | curses.A_BOLD)
        center(stdscr, cy + 2, "> " + buf + "_")
        if msg:
            center(stdscr, cy + 4, msg, (COL["green"] if ok else COL["red"]) | curses.A_BOLD)
        center(stdscr, cy + 6, "Enter = redeem    Esc = back", curses.A_DIM)
        stdscr.refresh()
        k = stdscr.getch()
        if k in (10, 13, curses.KEY_ENTER):
            if buf.strip():
                ok, msg = redeem(save, wallet, buf)
            buf = ""
        elif k == 27:
            break
        elif k in (127, 8, curses.KEY_BACKSPACE):
            buf = buf[:-1]
        elif 32 <= k < 127 and len(buf) < 32:
            buf += chr(k)
    cursor(0)


def market(stdscr, save, wallet, audio):
    row = 0
    size_i, sound_i = size_index(save), sound_index(save)
    amount_i = next(
        (i for i, mode in enumerate(POOP_MODES) if mode["key"] == save["poop_mode"]),
        0,
    )
    while True:
        stdscr.erase()
        h, _ = stdscr.getmaxyx()
        cy = h // 2 - 8
        amount = POOP_MODES[amount_i]
        center(stdscr, cy, "MARKET", COL["yellow"] | curses.A_BOLD)
        center(stdscr, cy + 1, "Wallet: %s   Respect+: %d" %
               (wallet_display(save, wallet), save["respect_plus"]),
               COL["green"] | curses.A_BOLD)
        rows = [
            ("SIZE", SIZES[size_i]["name"], size_i in owned_sizes(save), SIZE_PRICES[SIZES[size_i]["key"]]),
            ("SOUND", SOUNDS[sound_i]["name"], sound_i in owned_sounds(save), SOUND_PRICES[SOUNDS[sound_i]["key"]]),
            ("AMOUNT", amount["name"], amount["key"] in save["poop_modes"], amount["cost"]),
        ]
        rows.extend([
            ("RESPECT+", "Premium random", save["respect_plus"] > 0, 1),
        ])
        for i, (kind, value, owned, price) in enumerate(rows):
            selectable_value = i < 3
            displayed_value = "< %s >" % value if selectable_value else value
            label_text = "%s %s: %s - %s" % (
                ">" if i == row else " ", kind, displayed_value, "OWNED" if owned else "$%d" % price)
            center(stdscr, cy + 3 + i, label_text, curses.A_BOLD if i == row else 0)
        center(stdscr, cy + 10, "Left/right select   Enter buy/use   C redeem   Esc back", curses.A_DIM)
        center(stdscr, cy + 11, "Current: %s (%d at a time)" % (amount["name"], amount["count"]), COL["cyan"])
        stdscr.refresh()
        k = stdscr.getch()
        if k in (curses.KEY_UP, ord("k")):
            row = (row - 1) % len(rows)
        elif k in (curses.KEY_DOWN, ord("j")):
            row = (row + 1) % len(rows)
        elif k in (curses.KEY_LEFT, curses.KEY_RIGHT, ord("h"), ord("l")):
            step = -1 if k in (curses.KEY_LEFT, ord("h")) else 1
            if row == 0:
                size_i = (size_i + step) % len(SIZES)
            elif row == 1:
                sound_i = (sound_i + step) % len(SOUNDS)
            elif row == 2:
                amount_i = (amount_i + step) % len(POOP_MODES)
        elif k in (10, 13, curses.KEY_ENTER, ord(" ")):
            if row == 0:
                item, owned, price = SIZES[size_i], size_i in owned_sizes(save), SIZE_PRICES[SIZES[size_i]["key"]]
                if owned or can_afford(save, wallet, price):
                    if not owned:
                        spend_wallet(save, wallet, price)
                        save["unlocked"].append("size:" + item["key"])
                    save["size"] = item["key"]
                    write_save(save)
            elif row == 1:
                item, owned, price = SOUNDS[sound_i], sound_i in owned_sounds(save), SOUND_PRICES[SOUNDS[sound_i]["key"]]
                if owned or can_afford(save, wallet, price):
                    if not owned:
                        spend_wallet(save, wallet, price)
                        save["unlocked"].append("sound:" + item["key"])
                    save["sound"] = item["key"]
                    write_save(save)
                    audio.play(sound_i, size_i)
            elif row == 2:
                selected = POOP_MODES[amount_i]
                if selected["key"] in save["poop_modes"] or can_afford(save, wallet, selected["cost"]):
                    if selected["key"] not in save["poop_modes"]:
                        spend_wallet(save, wallet, selected["cost"])
                        save["poop_modes"].append(selected["key"])
                    save["poop_mode"] = selected["key"]
                    write_save(save)
                    audio.play_pack(selected["sound"], size_i)
            elif row == 3 and save["respect_plus"] > 0:
                owned_keys = set(save["unlocked"])
                candidates = [
                    ("size", item, SIZE_PRICES[item["key"]])
                    for item in SIZES if "size:" + item["key"] not in owned_keys
                ] + [
                    ("sound", item, SOUND_PRICES[item["key"]])
                    for item in SOUNDS if "sound:" + item["key"] not in owned_keys
                ] + [
                    ("amount", item, item["cost"])
                    for item in POOP_MODES if item["key"] not in save["poop_modes"]
                ]
                premium = [candidate for candidate in candidates if candidate[2] > 2000] or candidates
                if premium:
                    kind, item, _ = random.choice(premium)
                    save["respect_plus"] -= 1
                    if kind == "size":
                        save["unlocked"].append("size:" + item["key"])
                        save["size"] = item["key"]
                    elif kind == "sound":
                        save["unlocked"].append("sound:" + item["key"])
                        save["sound"] = item["key"]
                    else:
                        save["poop_modes"].append(item["key"])
                        save["poop_mode"] = item["key"]
                    write_save(save)
        elif k in (ord("c"), ord("C")):
            enter_code(stdscr, save, wallet)
        elif k in (27, ord("q"), ord("Q")):
            return


def confirm_clear_user_data(stdscr, save, wallet):
    """Ask for explicit confirmation before resetting local player data."""
    stdscr.nodelay(False)
    stdscr.timeout(-1)
    cursor(0)
    stdscr.erase()
    h, _ = stdscr.getmaxyx()
    cy = h // 2
    center(stdscr, cy - 3, "CLEAR USER DATA?", COL["red"] | curses.A_BOLD)
    center(stdscr, cy - 1, "This permanently resets your local progress.")
    center(stdscr, cy, "Wallet, best score, unlocks, and settings will be erased.")
    center(stdscr, cy + 2, "Press Y to confirm, or any other key to cancel.", COL["yellow"])
    stdscr.refresh()
    key = stdscr.getch()
    if key in (ord("y"), ord("Y")):
        clear_user_data(save, wallet)
        return "User data cleared. Progress and wallet reset."
    return "Clear data cancelled."


def menu(stdscr, save, wallet, audio):
    items = ["PLAY", "MARKET", "CLEAR USER DATA", "QUIT"]
    sel, msg = 0, ""
    while True:
        stdscr.nodelay(False)
        stdscr.timeout(-1)
        cursor(0)
        stdscr.erase()
        h, _ = stdscr.getmaxyx()
        top = max(1, h // 2 - 8)
        for i, line in enumerate(TITLE):
            center(stdscr, top + i, line, COL["white"] | curses.A_BOLD)
        center(stdscr, top + len(TITLE) + 1, "shit on people.", curses.A_DIM)
        for i, it in enumerate(items):
            text = ("> %s <" % it) if i == sel else it
            center(stdscr, top + 8 + i * 2, text, (COL["yellow"] | curses.A_BOLD) if i == sel else 0)
        if msg:
            center(stdscr, top + 17, msg, COL["red"] | curses.A_BOLD)
        center(stdscr, top + 19, "Best: %d   Wallet: %s" % (save["best"], wallet_display(save, wallet)), COL["magenta"])
        stdscr.refresh()

        k = stdscr.getch()
        act = None
        if k in (curses.KEY_UP, ord("k")):
            sel = (sel - 1) % len(items)
        elif k in (curses.KEY_DOWN, ord("j")):
            sel = (sel + 1) % len(items)
        elif k in (10, 13, curses.KEY_ENTER):
            act = sel
        elif ord("1") <= k <= ord("4"):
            act = k - ord("1")
        elif k in (ord("q"), ord("Q"), 27):
            return
        msg = ""
        if act == 0:
            if play(stdscr, save, wallet, audio) is None:
                msg = "Terminal too small - need at least %dx%d" % (MIN_W, MIN_H)
        elif act == 1:
            market(stdscr, save, wallet, audio)
        elif act == 2:
            msg = confirm_clear_user_data(stdscr, save, wallet)
        elif act == 3:
            return


def main(stdscr):
    init_colors()
    save = load_save()
    wallet = {"money": ADMIN_WALLET_AMOUNT if save.get("admin_unlimited") else load_wallet()}
    write_wallet(wallet["money"])
    audio = Audio()
    try:
        menu(stdscr, save, wallet, audio)
    finally:
        audio.cleanup()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--hash":
        print(code_hash(sys.argv[2]))
        sys.exit(0)
    os.environ.setdefault("ESCDELAY", "25")
    curses.wrapper(main)
