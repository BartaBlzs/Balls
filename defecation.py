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
PERSON_HIT_POINTS = 10
BOSS_HP = 12
BOSS_SPEED = 5.0
BOSS_ROCK_COOLDOWN = 1.8
BOSS_ROCK_DAMAGE = 15
FAMILY_PRICE = 10000

# --------------------------------------------------------------------------- content

# cost = ammo per poop, pts = base score, hw = extra hit-box half width
SIZES = [
    dict(key="small",  name="Small",  glyph=".",      splat=",",          cost=1, pts=10,  hw=0),
    dict(key="medium", name="Medium", glyph="o",      splat="-o-",        cost=2, pts=25,  hw=1),
    dict(key="large",  name="Large",  glyph="(@)",    splat="~(@)~",      cost=4, pts=60,  hw=2),
    dict(key="mega",   name="MEGA",   glyph="(@@@)",  splat="~~(@@@)~~",  cost=8, pts=150, hw=3),
]
SOUNDS = [
    dict(key="fart",  name="Fart",   file="fart.mp3"),
    dict(key="fart1", name="Fart 1", file="fart1.mp3"),
    dict(key="fart2", name="Fart 2", file="fart2.mp3"),
]
POOP_MODES = [
    dict(key="single", name="Single", count=1, cost=0, sound="fart"),
    dict(key="double", name="Double", count=2, cost=1500, sound="fart1"),
    dict(key="triple", name="Triple", count=3, cost=2500, sound="fart2"),
    dict(key="shower", name="Shower", count=5, cost=5000, sound="fart2"),
]
SIZE_PRICES = {"small": 1200, "medium": 2200, "large": 3500, "mega": 6000}
SOUND_PRICES = {"fart": 1200, "fart1": 1800, "fart2": 2600}
UPGRADES = [
    dict(key="shield", name="Shield", price=5000),
    dict(key="rapid_fire", name="Rapid-fire Laxative", price=6500),
    dict(key="fast_move", name="Faster Pigeon Movement", price=4500),
    dict(key="fast_reload", name="Faster Reload", price=4500),
]
FAMILY_OPTIONS = [
    dict(key="family", name="IM-PRESS HERE", price=FAMILY_PRICE, birds=3, partner="pink", baby=True, gender=None),
    dict(key="condoms", name="IM-PRESS HERE + CONDOMS", price=FAMILY_PRICE + 5000, birds=2, partner="pink", baby=False),
    dict(key="lesbian", name="LESBIAN", price=15000, birds=2, partner="pink", baby=False, gender="female"),
    dict(key="gay", name="GAY", price=15000, birds=2, partner="white", baby=False, gender="male"),
    dict(key="divorce", name="DIVORCE", price=0, birds=1, partner=None, baby=False, action="divorce"),
]
FREE = {"size:small", "sound:fart"}
CODE_REDEEM_COST = 1000
ADMIN_WALLET_AMOUNT = 999999999
ADMIN_CODE_HASH = "395fcfb4f94a19b6242902470f4c80cca48eed86fdd65e60c2325339066a9edd"

# sha256 of the code (upper-cased, no spaces) -> what it unlocks.
CODES = {
    "9a9ecd556d5eb0f4b3402d2e81ae6f7913f4d5f0eb07fc411a4d85483cce133f": ["size:medium", "sound:fart1"], # PIGEON-PLUS
    "6bde136c8ac436b7ba67415a436d3a7000a62ebdb4b95c10ffa1a4c26aaf4007": ["sound:fart2"],                # SQUELCH-ME
    "025a44c68d135721dbd332b1e0406091ab36ca3388dc21c340f666786953abe1": ["size:large"],                # BIG-ONE
    "74413f038c81ed7c50b744a156200abeb6e9307e1edd2591be14d1d7bd8ed29b": ["size:mega", "sound:fart2"],  # BOMBS-AWAY
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
PIGEON_BABY_R = ["  . ", "=(o>"]
PIGEON_BABY_L = [" .  ", ">o)="]

# --------------------------------------------------------------------------- save / codes

def code_hash(raw):
    return hashlib.sha256(raw.strip().upper().replace(" ", "").encode()).hexdigest()


def load_save():
    """Load player progress and recover safely from damaged/old save files."""
    defaults = {
        "unlocked": [], "size": "small", "sound": "fart",
        "poop_mode": "single", "poop_modes": ["single"],
        "respect_plus": 0, "best": 0, "upgrades": [],
        "equipped_upgrades": [],
        "family_unlocked": False,
        "family_unlocks": [],
        "family_type": "family",
        "gender": "male",
        "game_mode": "timed",
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
    data["unlocked"] = sorted(unlocked | FREE)

    size_keys = {item["key"] for item in SIZES}
    sound_keys = {item["key"] for item in SOUNDS}
    mode_keys = {item["key"] for item in POOP_MODES}
    if data.get("size") not in size_keys or "size:" + str(data.get("size")) not in data["unlocked"]:
        data["size"] = "small"
    if data.get("sound") not in sound_keys or "sound:" + str(data.get("sound")) not in data["unlocked"]:
        data["sound"] = "fart"
    if data.get("poop_mode") not in mode_keys:
        data["poop_mode"] = "single"
    modes = data.get("poop_modes", ["single"])
    if not isinstance(modes, (list, tuple, set)):
        modes = []
    data["poop_modes"] = sorted(({m for m in modes if isinstance(m, str) and m in mode_keys}) | {"single"})
    if data["poop_mode"] not in data["poop_modes"]:
        data["poop_mode"] = "single"
    upgrades = data.get("upgrades", [])
    if not isinstance(upgrades, (list, tuple, set)):
        upgrades = []
    upgrade_keys = {item["key"] for item in UPGRADES}
    data["upgrades"] = sorted({u for u in upgrades if isinstance(u, str) and u in upgrade_keys})
    equipped_upgrades = data.get("equipped_upgrades", [])
    if not isinstance(equipped_upgrades, (list, tuple, set)):
        equipped_upgrades = []
    equipped_upgrades = sorted({u for u in equipped_upgrades if u in data["upgrades"]})
    data["equipped_upgrades"] = equipped_upgrades[:1]
    data["family_unlocked"] = bool(data.get("family_unlocked", False))
    family_keys = {item["key"] for item in FAMILY_OPTIONS}
    family_unlocks = data.get("family_unlocks", [])
    if not isinstance(family_unlocks, (list, tuple, set)):
        family_unlocks = []
    if data["family_unlocked"]:
        family_unlocks = set(family_unlocks) | {"family"}
    data["family_unlocks"] = sorted({key for key in family_unlocks if key in family_keys})
    data["family_unlocked"] = bool(data["family_unlocks"])
    if data.get("family_type") not in data["family_unlocks"]:
        data["family_type"] = data["family_unlocks"][0] if data["family_unlocks"] else "family"
    if data.get("gender") not in ("male", "female"):
        data["gender"] = "male"
    if data.get("game_mode") not in ("timed", "endless"):
        data["game_mode"] = "timed"

    for key in ("respect_plus", "best"):
        try:
            data[key] = max(0, int(data.get(key, 0)))
        except (ValueError, TypeError, OverflowError):
            data[key] = 0
    data["admin_unlimited"] = bool(data.get("admin_unlimited", False))
    data.pop("respect", None)
    return data


def clear_user_data(save, wallet):
    save.clear()
    save.update({
        "unlocked": sorted(FREE),
        "size": "small",
        "sound": "fart",
        "poop_mode": "single",
        "poop_modes": ["single"],
        "respect_plus": 0,
        "best": 0,
        "upgrades": [],
        "equipped_upgrades": [],
        "family_unlocked": False,
        "family_unlocks": [],
        "family_type": "family",
        "gender": "male",
        "game_mode": "timed",
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


def redeem_random_respect_reward(save):
    """Spend one Respect+ to unlock one random item the player lacks."""
    if save["respect_plus"] <= 0:
        return "Need Respect+ to claim a random reward."

    rewards = []
    for item in SIZES:
        if "size:" + item["key"] not in save["unlocked"]:
            rewards.append(("size", item["key"], item["name"] + " poop"))
    for item in SOUNDS:
        if "sound:" + item["key"] not in save["unlocked"]:
            rewards.append(("sound", item["key"], item["name"] + " sound"))
    for item in POOP_MODES:
        if item["key"] not in save["poop_modes"]:
            rewards.append(("mode", item["key"], item["name"] + " mode"))
    for item in UPGRADES:
        if item["key"] not in save["upgrades"]:
            rewards.append(("upgrade", item["key"], item["name"]))

    if not rewards:
        return "All random rewards are already unlocked."

    kind, key, reward_name = random.choice(rewards)
    save["respect_plus"] -= 1
    if kind in ("size", "sound"):
        save["unlocked"].append(kind + ":" + key)
        save["unlocked"] = sorted(set(save["unlocked"]))
    elif kind == "mode":
        save["poop_modes"].append(key)
        save["poop_modes"] = sorted(set(save["poop_modes"]))
    else:
        save["upgrades"].append(key)
        save["upgrades"] = sorted(set(save["upgrades"]))
    write_save(save)
    return "Respect+ reward: " + reward_name


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


def family_allowed(option, gender=None):
    """All family options are available without a character-gender choice."""
    return True


def family_display_name(option, gender=None):
    """Return a short, gender-neutral shop label for a family option."""
    key = option["key"]
    if key == "family":
        return "IMPRESS A PARTNER"
    if key == "condoms":
        return "IMPRESS A PARTNER + CONDOMS"
    if key == "lesbian":
        return "LESBIAN PARTNERS"
    if key == "gay":
        return "GAY PARTNERS"
    if key == "divorce":
        return "DIVORCE (-50% POINTS)"
    return option["name"]

# --------------------------------------------------------------------------- audio

VOLUME = 0.1
MENU_MUSIC_VOLUME = 0.1
BACKGROUND_MUSIC_VOLUME = 0.1
MENU_MUSIC_FILE = "Star Wars Main Theme Cover (Handfarts).mp3"
BACKGROUND_MUSIC_FILE = "🌿 Nature Soundscape Relaxing Bird Songs for Study & Meditation 10 Min Mix 🎶.mp3"
ROMANTIC_MUSIC_FILE = "Romantic music sound effect.mp3"
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

        self.menu_music_path = os.path.join(self.dir, MENU_MUSIC_FILE)
        self.background_music_path = os.path.join(self.dir, BACKGROUND_MUSIC_FILE)
        self.romantic_music_path = os.path.join(self.dir, ROMANTIC_MUSIC_FILE)
        self.menu_volume = MENU_MUSIC_VOLUME
        self.menu_muted = False
        for path in (self.menu_music_path, self.background_music_path, self.romantic_music_path):
            if not os.path.isfile(path):
                raise RuntimeError("Could not find music file: %s" % path)

    def start_menu_music(self):
        try:
            pygame.mixer.music.load(self.menu_music_path)
        except pygame.error as exc:
            raise RuntimeError("Could not load menu music file %s: %s" % (self.menu_music_path, exc)) from exc
        self._apply_menu_volume()
        pygame.mixer.music.play(-1)

    def _apply_menu_volume(self):
        pygame.mixer.music.set_volume(0.0 if self.menu_muted else self.menu_volume)

    def adjust_menu_volume(self, delta):
        self.menu_volume = max(0.0, min(1.0, self.menu_volume + delta))
        self._apply_menu_volume()

    def toggle_menu_mute(self):
        self.menu_muted = not self.menu_muted
        self._apply_menu_volume()

    def start_background_music(self):
        try:
            pygame.mixer.music.load(self.background_music_path)
        except pygame.error as exc:
            raise RuntimeError("Could not load background music file %s: %s" % (self.background_music_path, exc)) from exc
        pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME)
        pygame.mixer.music.play(-1)

    def start_romantic_music(self):
        try:
            pygame.mixer.music.load(self.romantic_music_path)
        except pygame.error as exc:
            raise RuntimeError("Could not load romantic music file %s: %s" % (self.romantic_music_path, exc)) from exc
        pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME)
        pygame.mixer.music.play(-1)

    def stop_background_music(self):
        pygame.mixer.music.stop()

    def play(self, pack_i, size_i):
        if not 0 <= pack_i < len(SOUNDS):
            curses.beep()
            return
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
        self.stop_background_music()
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


def family_animation(stdscr, audio, save, wallet, family_option):
    """Play the family-unlock scene in the city street."""
    cursor(0)
    stdscr.nodelay(False)
    audio.start_romantic_music()
    h, w = stdscr.getmaxyx()
    gl = h - 2
    bg = make_street(w, h, gl)
    center_x = max(12, w // 2)
    for frame in range(28):
        stdscr.erase()
        for r, line in enumerate(bg):
            if line.strip():
                put(stdscr, r, 0, line, COL["blue"] | curses.A_DIM)
        put(stdscr, gl, 0, "=" * w, COL["green"])
        center(stdscr, 1, "FAMILY MOMENT", COL["magenta"] | curses.A_BOLD)

        if frame < 12:
            left_x = int(center_x - 22 + frame * 1.5)
            right_x = int(center_x + 18 - frame * 1.5)
            put_sprite(stdscr, gl - 5, left_x, PIGEON_R[frame % 2], COL["white"] | curses.A_BOLD)
            put_sprite(stdscr, gl - 5, right_x, PIGEON_L[frame % 2], COL["white"] | curses.A_BOLD)
        else:
            if family_option["key"] == "lesbian":
                left_color, right_color = COL["magenta"], COL["magenta"]
            elif family_option["key"] == "gay":
                left_color, right_color = COL["white"], COL["white"]
            else:
                left_color, right_color = COL["white"], COL["magenta"]
            put_sprite(stdscr, gl - 5, center_x - 6, PIGEON_R[frame % 2], left_color | curses.A_BOLD)
            put_sprite(stdscr, gl - 5, center_x + 2, PIGEON_L[frame % 2], right_color | curses.A_BOLD)
            center(stdscr, gl - 8, "<3", COL["red"] | curses.A_BOLD)
            if frame >= 15:
                center(stdscr, gl - 10, "MONEY: %s" % wallet_display(save, wallet), COL["green"] | curses.A_BOLD)
                center(stdscr, gl - 9, "YAY I IMPRESSED!", COL["yellow"] | curses.A_BOLD)
            if frame >= 18 and family_option["baby"]:
                put_sprite(stdscr, gl - 2, center_x - 1, PIGEON_BABY_R, COL["cyan"] | curses.A_BOLD)
                center(stdscr, gl - 10, "A BABY BIRD!", COL["yellow"] | curses.A_BOLD)

        stdscr.refresh()
        time.sleep(0.12)

    stdscr.erase()
    center(stdscr, h // 2 - 2, "########################", COL["red"] | curses.A_BOLD)
    center(stdscr, h // 2, "CENSORED", COL["red"] | curses.A_BOLD)
    center(stdscr, h // 2 + 2, "The rest we know.", COL["yellow"] | curses.A_BOLD)
    center(stdscr, h - 2, "Press any key to continue", curses.A_DIM)
    stdscr.refresh()
    stdscr.getch()
    audio.start_menu_music()

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
        self.umbrella = getattr(self, "umbrella", False)
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


class Boss:
    def __init__(self, w, gl):
        self.x = max(0.0, (w - 7) / 2)
        self.gl = gl
        self.hp = BOSS_HP
        self.dir = 1
        self.cooldown = BOSS_ROCK_COOLDOWN
        self.anim = 0.0

    def update(self, w, dt):
        self.anim += dt
        self.x += self.dir * BOSS_SPEED * dt
        if self.x <= 0 or self.x >= w - 7:
            self.x = max(0.0, min(float(w - 7), self.x))
            self.dir *= -1
        self.cooldown = max(0.0, self.cooldown - dt)

    def rows(self):
        return [" /!\\ ", "<BOSS>", " /|\\ "]


def play(stdscr, save, wallet, audio):
    cursor(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)
    h, w = stdscr.getmaxyx()
    if w < MIN_W or h < MIN_H:
        return None
    audio.start_background_music()
    game_mode = save.get("game_mode", "timed")
    family_unlocked = save.get("family_unlocked", False)
    family_type = save.get("family_type", "family") if family_unlocked else None
    family_option = next(
        (item for item in FAMILY_OPTIONS
         if item["key"] == family_type and not item.get("action")),
        None,
    )
    family_bird_count = family_option["birds"] if family_option else 1
    size_i = size_index(save)
    mode = next(m for m in POOP_MODES if m["key"] == save["poop_mode"])
    equipped_upgrades = set(save.get("equipped_upgrades", []))
    rapid_fire = "rapid_fire" in equipped_upgrades
    fast_move = "fast_move" in equipped_upgrades
    fast_reload = "fast_reload" in equipped_upgrades
    shield_charges = 3 if "shield" in equipped_upgrades else 0
    POOP_COOLDOWN = 0.14 if rapid_fire else 0.28
    RELOAD_COOLDOWN = 0.9 if fast_reload else 2.0
    movement_acceleration = 18 if fast_move else 14
    movement_limit = 32 if fast_move else 24
    # Give the player enough ammo for one full selected burst.
    MAX_AMMO = max(5, SIZES[size_i]["cost"] * mode["count"] * family_bird_count)

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
    boss = None
    boss_defeated = False
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
    respect_combo_hits = 0
    respect_combo_people = set()
    respect_combo_timer = 0.0
    reward_flash = 0.0
    announcement = ""
    announcement_time = 0.0
    # Multi-poop modes start at MEDIUM; score still controls later escalation.
    mode_hardness = min(2, mode["count"])
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
        if game_mode == "endless":
            left = float("inf")
        if game_mode == "timed" and left <= 0:
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
                vx, face = max(-movement_limit, vx - movement_acceleration), -1
            elif k in (curses.KEY_RIGHT, ord("d"), ord("D")):
                vx, face = min(movement_limit, vx + movement_acceleration), 1
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
                audio.stop_background_music()
                audio.start_menu_music()
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
        respect_combo_timer = max(0.0, respect_combo_timer - dt)
        if respect_combo_timer <= 0:
            respect_combo_hits = 0
            respect_combo_people.clear()
        reward_flash = max(0.0, reward_flash - dt)
        announcement_time = max(0.0, announcement_time - dt)
        rock_salvo_cooldown = max(0.0, rock_salvo_cooldown - dt)
        next_rock_throw = max(0.0, next_rock_throw - dt)
        _, score_tier = score_difficulty(score)
        difficulty_tier = score_tier
        difficulty_name = ("EASY", "MEDIUM", "HARDCORE", "U ARE FUCKED")[difficulty_tier]
        if difficulty_tier >= 3 and boss is None and not boss_defeated:
            boss = Boss(w, gl)
            if family_bird_count > 1:
                boss.cooldown *= 1.5
            announcement = "BOSS INCOMING: THE MAYOR!"
            announcement_time = 3.0
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
        if difficulty_tier >= 3:
            for person in people:
                if not getattr(person, "umbrella_checked", False):
                    person.umbrella = random.random() < 0.3
                    person.umbrella_checked = True
        if reloading and cooldown <= 0:
            ammo = MAX_AMMO
            reloading = False

        if want_drop and cooldown <= 0 and poop_lockout <= 0 and not reloading:
            s = SIZES[size_i]
            mode = next(m for m in POOP_MODES if m["key"] == save["poop_mode"])
            bird_positions = [(px, py)]
            if family_option:
                x_limit = max(1, w - 6)
                bird_positions.append(((px - face * 7) % x_limit, py + 1.0))
                if family_option["birds"] == 3:
                    bird_positions.append(((px - face * 4) % x_limit, py + 3.0))
            ammo_cost = s["cost"] * mode["count"] * len(bird_positions)
            if ammo >= ammo_cost:
                if start is None:
                    start = now
                ammo -= ammo_cost
                cooldown = POOP_COOLDOWN
                for bird_x, bird_y in bird_positions:
                    for burst_i in range(mode["count"]):
                        poops.append(dict(
                            x=bird_x + (2.5 if face > 0 else 3.5) + burst_i * face * 0.8,
                            y=bird_y + 2.0 - burst_i * 0.2,
                            vx=vx * 0.65 + burst_i * face * 0.7,
                            vy=max(2.0, vy * 0.65 - burst_i * 0.2),
                            size=size_i,
                        ))
                audio.play_pack(save["sound"], size_i)
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

        if boss is not None:
            boss.update(w, dt)
            if boss.cooldown <= 0:
                ox, oy = boss.x + 3.0, gl - 4.0
                tx, ty = px + 2.5 + vx * 0.6, py + 1.0 + vy * 0.6
                dx, dy = tx - ox, ty - oy
                distance = math.hypot(dx, dy) or 1.0
                flight_time = min(1.5, max(0.65, distance / (ROCK_SPEED + 6)))
                rocks.append(dict(
                    x=ox,
                    y=oy,
                    vx=dx / flight_time,
                    vy=dy / flight_time - 0.5 * ROCK_GRAVITY * flight_time,
                    life=ROCK_LIFE,
                    damage=BOSS_ROCK_DAMAGE,
                ))
                boss.cooldown = BOSS_ROCK_COOLDOWN * (1.5 if family_bird_count > 1 else 1.0)

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
            boss_hit = None
            for p in people:
                if p.dead > 0 or p.stun > 0:
                    continue
                if p.umbrella and segment_hits_rect(
                        previous_x, previous_y, poop["x"], poop["y"],
                        p.x - 1.0, gl - 5.5, p.x + 4.0, gl - 4.0):
                    hit = "umbrella"
                    break
                # Include the head, torso, and legs.  Keep the horizontal
                # bounds at the actual three-column body so neighbors do not
                # share hitboxes.
                if segment_hits_rect(
                        previous_x, previous_y, poop["x"], poop["y"],
                        p.x, gl - 3.0 - PERSON_HIT_VERTICAL_MARGIN,
                        p.x + 3.0, gl + PERSON_HIT_VERTICAL_MARGIN):
                    hit = p
                    break
            if hit is None and boss is not None and segment_hits_rect(
                    previous_x, previous_y, poop["x"], poop["y"],
                    boss.x, gl - 6.0, boss.x + 7.0, gl - 3.0):
                boss_hit = boss
            if hit or boss_hit or poop["y"] >= gl - 1:
                poops.remove(poop)
                for _ in range(4 + 3 * poop["size"]):
                    particles.append([poop["x"], min(poop["y"], gl - 2), random.uniform(-12, 12),
                                      random.uniform(-14, -3), 0.5, random.choice(".,*'`")])
                if hit == "umbrella":
                    splats.append([poop["x"], "UMBRELLA!", 0.8])
                    continue
                if boss_hit:
                    boss_hit.hp -= 1 + poop["size"] * 2
                    floaters.append([boss_hit.x + 2, gl - 8.0, "BOSS HIT!", 0.8])
                    if boss_hit.hp <= 0:
                        boss_defeated = True
                        boss = None
                        score += 500
                        wallet["money"] += 250
                        write_wallet(wallet["money"])
                        announcement = "THE MAYOR IS DOWN! +$250"
                        announcement_time = 3.0
                    continue
                if hit:
                    # One person cannot pad the same combo twice in one frame.
                    if id(hit) not in direct_hit_people:
                        direct_hit_people.add(id(hit))
                        direct_hits_this_moment += 1
                    if id(hit) not in respect_combo_people:
                        respect_combo_people.add(id(hit))
                        respect_combo_hits += 1
                        respect_combo_timer = 0.45
                    # Group membership does not turn a miss into a hit.
                    victims = (hit,)
                    for victim in victims:
                        distance = min(abs((victim.x + 1.5) - (px + 2.5)),
                                       w - abs((victim.x + 1.5) - (px + 2.5)))
                        proximity_mult = 2 if distance <= NEAR_PERSON_DISTANCE else 1
                        gained = PERSON_HIT_POINTS * Person.KINDS[victim.kind]["mult"] * proximity_mult
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

        if respect_combo_hits >= 5:
            save["respect_plus"] += 1
            write_save(save)
            announcement = "AMAZING! FIVE HIT! RESPECT+ +1"
            announcement_time = 2.5
            respect_combo_hits = 0
            respect_combo_people.clear()
            respect_combo_timer = 0.0
        elif respect_combo_hits >= 3:
            save["respect_plus"] += 1
            write_save(save)
            announcement = "GOOD JOB! TRIPLE HIT! RESPECT+ +1"
            announcement_time = 2.5
            respect_combo_hits = 0
            respect_combo_people.clear()
            respect_combo_timer = 0.0

        if rock_salvo_pending and rock_salvo_remaining == 0 and rock_salvo_cooldown <= 0:
            if rock_throw_queue:
                thrower = rock_throw_queue[0]
                if thrower in people and thrower.dead <= 0 and thrower.stun <= 0:
                    rock_throw_queue.pop(0)
                    rock_salvo_thrower = thrower
                    salvo_size = ROCK_SALVO_SIZES[difficulty_tier]
                    if family_bird_count > 1:
                        salvo_size = max(1, int(math.ceil(salvo_size * 0.5)))
                    rock_salvo_remaining = salvo_size
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
            rock_salvo_remaining -= 1
            rock_rate = 1.0
            rock_rate += difficulty_tier * POST_SCORE_ROCK_RATE_STEP
            throw_min, throw_max = ROCK_THROW_RANGES[difficulty_tier]
            family_rock_delay = 1.5 if family_bird_count > 1 else 1.0
            next_rock_throw = (random.uniform(throw_min, throw_max) * family_rock_delay) / (difficulty * rock_rate)
            if rock_salvo_remaining == 0:
                rock_salvo_thrower = None
                rock_salvo_pending = bool(rock_throw_queue)
                rock_salvo_cooldown = random.uniform(
                    ROCK_SALVO_COOLDOWN_MIN, ROCK_SALVO_COOLDOWN_MAX
                ) * family_rock_delay / rock_rate

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
            # A rock can hit any active family bird. One shared flock HP bar
            # keeps the result fair while still making companions vulnerable.
            bird_targets = [(px, py)]
            if family_option:
                x_limit = max(1, w - 6)
                bird_targets.append(((px - face * 7) % x_limit, py + 1.0))
                if family_option["birds"] == 3:
                    bird_targets.append(((px - face * 4) % x_limit, py + 3.0))
            rock_hits_player = False
            for bird_x, bird_y in bird_targets:
                low_altitude = max(0.0, min(1.0, (bird_y - (gl - 8 - LOW_ALTITUDE_BAND)) / LOW_ALTITUDE_BAND))
                hitbox_x = LOW_ALTITUDE_HITBOX_X * low_altitude
                hitbox_y = LOW_ALTITUDE_HITBOX_Y * low_altitude
                if segment_hits_rect(
                        previous_x, previous_y, rock["x"], rock["y"],
                        bird_x - 0.5 - hitbox_x, bird_y - 0.5 - hitbox_y,
                        bird_x + 5.5 + hitbox_x, bird_y + 2.5 + hitbox_y):
                    rock_hits_player = True
                    break
            if rock_hits_player and shield_charges > 0:
                rocks.remove(rock)
                shield_charges -= 1
                announcement = "SHIELD BLOCKED ROCK! %d LEFT" % shield_charges
                announcement_time = 1.2
                continue
            if ((not reloading) and hurt_iframes <= 0 and
                    rock_hits_player):
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
            if p.umbrella:
                put(stdscr, gl - 5, int(p.x) - 1, "___", COL["cyan"] | curses.A_BOLD)
            put_sprite(stdscr, gl - 3, int(p.x), p.rows(), attr)
            if (p.dead > 0 or p.stun > 0) and p.shout:
                put(stdscr, gl - 4, int(p.x + 1.5 - len(p.shout) / 2), p.shout, COL["red"] | curses.A_BOLD)
        if family_unlocked:
            x_limit = max(1, w - 6)
            partner_x = (px - face * 7) % x_limit
            baby_x = (px - face * 4) % x_limit
            partner_frames = PIGEON_R if face > 0 else PIGEON_L
            if family_type == "lesbian":
                main_color, partner_color = COL["magenta"], COL["magenta"]
            elif family_type == "gay":
                main_color, partner_color = COL["white"], COL["white"]
            else:
                main_color, partner_color = COL["white"], COL["magenta"]
            put_sprite(stdscr, int(py) + 1, int(partner_x), partner_frames[int(flap) % 2], partner_color | curses.A_BOLD)
            if family_option["baby"]:
                baby_frames = PIGEON_BABY_R if face > 0 else PIGEON_BABY_L
                put_sprite(stdscr, int(py) + 3, int(baby_x), baby_frames, COL["cyan"] | curses.A_BOLD)
        if boss is not None:
            put_sprite(stdscr, gl - 6, int(boss.x), boss.rows(), COL["red"] | curses.A_BOLD)
            put(stdscr, gl - 7, int(boss.x), "HP %02d" % boss.hp, COL["red"] | curses.A_BOLD)
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
        main_color = COL["white"]
        if family_unlocked and family_type == "lesbian":
            main_color = COL["magenta"]
        put_sprite(stdscr, int(py), int(px), frames[int(flap) % 2], main_color | curses.A_BOLD)
        if hit_notice > 0:
            put(stdscr, max(2, int(py) - 1), int(px) - 2, "-10 HP  -10 SCORE", COL["red"] | curses.A_BOLD)

        put(stdscr, 0, 1, "SCORE %05d" % score, COL["yellow"] | curses.A_BOLD)
        put(stdscr, 0, 16, "LV %d" % (difficulty_tier + 1), COL["magenta"] | curses.A_BOLD)
        put(stdscr, 0, 24, difficulty_name[:14], COL["magenta"] | curses.A_BOLD)
        hp_attr = (COL["red"] | curses.A_BOLD) if player_hp <= ROCK_HIT_DAMAGE else (COL["green"] | curses.A_BOLD)
        put(stdscr, 0, 41, "HP %03d" % player_hp, hp_attr)
        time_text = "TIME INF" if game_mode == "endless" else "TIME %03d" % math.ceil(left)
        put(stdscr, 0, 51, time_text, COL["white"] | curses.A_BOLD)
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
        put(stdscr, 1, 34, "RESPECT+ %d" % save["respect_plus"], COL["red"] | curses.A_BOLD)
        if shield_charges:
            put(stdscr, 1, 52, "SHIELD %d" % shield_charges, COL["cyan"] | curses.A_BOLD)
        put(stdscr, h - 1, 1, "arrows/WASD fly   SPACE poop   Q menu", curses.A_DIM)
        stdscr.refresh()

        time.sleep(max(0.0, 1 / 30 - (time.perf_counter() - now)))

    audio.stop_background_music()

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
    audio.start_menu_music()
    return score

# --------------------------------------------------------------------------- menus

def enter_code(stdscr, save, wallet):
    buf, msg, ok = "", "", False
    cursor(1)
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
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
    market_msg = ""
    size_i, sound_i = size_index(save), sound_index(save)
    upgrade_i = 0
    family_i = next(
        (i for i, option in enumerate(FAMILY_OPTIONS) if option["key"] == save["family_type"]),
        0,
    )
    amount_i = next(
        (i for i, mode in enumerate(POOP_MODES) if mode["key"] == save["poop_mode"]),
        0,
    )
    while True:
        stdscr.erase()
        h, _ = stdscr.getmaxyx()
        cy = h // 2 - 8
        amount = POOP_MODES[amount_i]
        family_option = FAMILY_OPTIONS[family_i]
        center(stdscr, cy, "MARKET", COL["yellow"] | curses.A_BOLD)
        center(stdscr, cy + 1, "Wallet: %s" % wallet_display(save, wallet),
               COL["green"] | curses.A_BOLD)
        rows = [
            ("SIZE", SIZES[size_i]["name"], size_i in owned_sizes(save), SIZE_PRICES[SIZES[size_i]["key"]]),
            ("SOUND", SOUNDS[sound_i]["name"], sound_i in owned_sounds(save), SOUND_PRICES[SOUNDS[sound_i]["key"]]),
            ("AMOUNT", amount["name"], amount["key"] in save["poop_modes"], amount["cost"]),
            ("UPGRADE", UPGRADES[upgrade_i]["name"], UPGRADES[upgrade_i]["key"] in save["upgrades"], UPGRADES[upgrade_i]["price"]),
            ("RESPECT+", "Random Reward", save["respect_plus"] > 0, 1),
            ("FAMILY", family_display_name(family_option), family_option["key"] in save["family_unlocks"], family_option["price"]),
        ]
        for i, (kind, value, owned, price) in enumerate(rows):
            selectable_value = i < 6
            displayed_value = "< %s >" % value if selectable_value else value
            if kind == "RESPECT+":
                status = "AVAILABLE" if owned else "NEED RESPECT+"
            elif kind == "FAMILY":
                if family_option.get("action") == "divorce":
                    status = "ACTION"
                else:
                    status = "EQUIPPED" if owned and family_option["key"] == save["family_type"] else ("OWNED" if owned else "$%d" % price)
            elif owned:
                if kind == "SIZE":
                    equipped = save["size"] == SIZES[size_i]["key"]
                elif kind == "SOUND":
                    equipped = save["sound"] == SOUNDS[sound_i]["key"]
                elif kind == "AMOUNT":
                    equipped = save["poop_mode"] == POOP_MODES[amount_i]["key"]
                else:
                    equipped = UPGRADES[upgrade_i]["key"] in save["equipped_upgrades"]
                status = "EQUIPPED" if equipped else "OWNED"
            else:
                status = "$%d" % price
            label_text = "%s %s: %s - %s" % (
                ">" if i == row else " ", kind, displayed_value, status)
            center(stdscr, cy + 3 + i, label_text, curses.A_BOLD if i == row else 0)
        if market_msg:
            center(stdscr, cy + 9, market_msg, COL["green"] | curses.A_BOLD)
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
                audio.play(sound_i, size_i)
            elif row == 2:
                amount_i = (amount_i + step) % len(POOP_MODES)
            elif row == 3:
                upgrade_i = (upgrade_i + step) % len(UPGRADES)
            elif row == 5:
                family_i = (family_i + step) % len(FAMILY_OPTIONS)
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
            elif row == 3:
                selected = UPGRADES[upgrade_i]
                key = selected["key"]
                if key not in save["upgrades"]:
                    if can_afford(save, wallet, selected["price"]):
                        spend_wallet(save, wallet, selected["price"])
                        save["upgrades"].append(key)
                        save["upgrades"] = sorted(set(save["upgrades"]))
                        save["equipped_upgrades"] = [key]
                        market_msg = selected["name"] + " purchased and equipped."
                elif key in save["equipped_upgrades"]:
                    save["equipped_upgrades"] = []
                    market_msg = selected["name"] + " unequipped."
                else:
                    save["equipped_upgrades"] = [key]
                    market_msg = selected["name"] + " equipped."
                write_save(save)
            elif row == 4:
                market_msg = redeem_random_respect_reward(save)
            elif row == 5:
                selected = FAMILY_OPTIONS[family_i]
                key = selected["key"]
                if selected.get("action") == "divorce":
                    if not save.get("family_unlocked"):
                        market_msg = "NO FAMILY TO DIVORCE"
                    else:
                        lost_points = save["best"] // 2
                        save["best"] -= lost_points
                        write_save(save)
                        market_msg = "DIVORCED! -%d POINTS" % lost_points
                elif key not in save["family_unlocks"]:
                    if can_afford(save, wallet, selected["price"]):
                        spend_wallet(save, wallet, selected["price"])
                        save["family_unlocks"].append(key)
                        save["family_unlocks"] = sorted(set(save["family_unlocks"]))
                        save["family_unlocked"] = True
                        save["family_type"] = key
                        write_save(save)
                        family_animation(stdscr, audio, save, wallet, selected)
                else:
                    save["family_unlocked"] = True
                    save["family_type"] = key
                    write_save(save)
                    family_animation(stdscr, audio, save, wallet, selected)
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
    items = ["PLAY", "MARKET", "AUDIO", "MODE", "CLEAR USER DATA", "QUIT"]
    sel, msg = 0, ""
    audio.start_menu_music()
    while True:
        stdscr.nodelay(False)
        stdscr.timeout(-1)
        cursor(0)
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        # Keep the menu compact enough for the game's minimum 20-line terminal.
        top = max(0, h // 2 - 9)
        for i, line in enumerate(TITLE):
            center(stdscr, top + i, line, COL["white"] | curses.A_BOLD)
        center(stdscr, top + len(TITLE) + 1, "shit on people.", curses.A_DIM)
        labels = items[:]
        labels[2] = "AUDIO: MUTED" if audio.menu_muted else "AUDIO: %d%%" % round(audio.menu_volume * 100)
        labels[3] = "MODE: ENDLESS" if save["game_mode"] == "endless" else "MODE: TIME LIMIT"
        for i in range(2):
            if i == 0:
                text = "[>>> PLAY <<<]" if i == sel else "[   PLAY   ]"
            else:
                text = ("> %s <" % labels[i]) if i == sel else labels[i]
            center(stdscr, top + 8 + i, text, (COL["yellow"] | curses.A_BOLD) if i == sel else 0)
        row_labels = []
        for i in range(2, 6):
            text = ("> %s <" % labels[i]) if i == sel else labels[i]
            row_labels.append(text)
        # Keep the four controls on one line even when a long label is selected.
        row_gap = 2
        row_width = sum(len(text) for text in row_labels) + row_gap * (len(row_labels) - 1)
        row_x = max(0, (w - row_width) // 2)
        for text in row_labels:
            put(stdscr, top + 12, row_x, text,
                (COL["yellow"] | curses.A_BOLD) if text.startswith("> ") else 0)
            row_x += len(text) + row_gap
        if msg:
            center(stdscr, top + 15, msg, COL["red"] | curses.A_BOLD)
        elif sel == 2:
            center(stdscr, top + 15, "Left/Right: volume   Enter: mute/unmute", curses.A_DIM)
        elif sel == 3:
            center(stdscr, top + 15, "Left/Right or Enter: switch mode", curses.A_DIM)
        else:
            center(stdscr, top + 15, "Best: %d   Wallet: %s" % (save["best"], wallet_display(save, wallet)), COL["magenta"])
        stdscr.refresh()

        k = stdscr.getch()
        act = None
        if k in (curses.KEY_UP, ord("k")):
            sel = (sel - 1) % len(items)
        elif k in (curses.KEY_DOWN, ord("j")):
            sel = (sel + 1) % len(items)
        elif sel == 2 and k in (curses.KEY_LEFT, ord("-")):
            audio.adjust_menu_volume(-0.05)
        elif sel == 2 and k in (curses.KEY_RIGHT, ord("+"), ord("=")):
            audio.adjust_menu_volume(0.05)
        elif sel == 3 and k in (curses.KEY_LEFT, curses.KEY_RIGHT, ord("-"), ord("+"), ord("=")):
            save["game_mode"] = "endless" if save["game_mode"] == "timed" else "timed"
            write_save(save)
        elif k in (10, 13, curses.KEY_ENTER):
            act = sel
        elif ord("1") <= k <= ord("6"):
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
            audio.toggle_menu_mute()
        elif act == 3:
            save["game_mode"] = "endless" if save["game_mode"] == "timed" else "timed"
            write_save(save)
        elif act == 4:
            msg = confirm_clear_user_data(stdscr, save, wallet)
        elif act == 5:
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
