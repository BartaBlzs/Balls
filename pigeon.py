import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
import time

try:
    import curses
except ImportError:
    sys.exit("curses not found. On Windows run: pip install windows-curses")

SAVE_PATH = os.path.join(os.path.expanduser("~"), ".pigeon_save.json")
WALLET_PATH = os.path.join(os.path.expanduser("~"), ".pigeon_wallet.json")
WALLET_SALT = "PIGEON_WALLET_V1"
ROUND_SECS = 120
MIN_W, MIN_H = 70, 20
PLAYER_HP_MAX = 100
PEOPLE_PER_DIFFICULTY = 3
MAX_PEOPLE = 10
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
POOP_HIT_LOCKOUT = 1.0
ROCK_SALVO_COOLDOWN_MIN = 1.0
ROCK_SALVO_COOLDOWN_MAX = 3.0
POOP_GRAVITY = 52.0
POOP_MAX_SPEED = 42.0
POOP_AIR_DRAG = 0.08
PERSON_DEATH_TIME = 0.85

# --------------------------------------------------------------------------- content

# cost = ammo per poop, pts = base score, hw = extra hit-box half width
SIZES = [
    dict(key="small",  name="Small",  glyph=".",      splat=",",          cost=1, pts=10,  hw=0),
    dict(key="medium", name="Medium", glyph="o",      splat="-o-",        cost=2, pts=25,  hw=1),
    dict(key="large",  name="Large",  glyph="(@)",    splat="~(@)~",      cost=4, pts=60,  hw=2),
    dict(key="mega",   name="MEGA",   glyph="(@@@)",  splat="~~(@@@)~~",  cost=8, pts=150, hw=3),
]
SOUNDS = [
    dict(key="poop",    name="Poop"),
    dict(key="splat",   name="Splat"),
    dict(key="squelch", name="Squelch"),
    dict(key="boing",   name="Boing"),
    dict(key="bomb",    name="Bomb"),
]
POOP_MODES = [
    dict(key="single", name="Single", count=1, cost=0, sound="poop"),
    dict(key="double", name="Double", count=2, cost=40, sound="splat"),
    dict(key="triple", name="Triple", count=3, cost=75, sound="squelch"),
    dict(key="shower", name="Shower", count=5, cost=120, sound="bomb"),
]
FREE = {"size:small", "sound:poop"}
CODE_REDEEM_COST = 10
FREE = {"size:small", "sound:poop"}

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
 ___ ___ ___ ___ ___  _  _
| _ \_ _/ __| __/ _ \| \| |
|  _/| | (_ | _| (_) | .` |
|_| |___\___|___\___/|_|\_|
""".strip("\n").splitlines()

PIGEON_R = [["  \\\\  ", "==(o> "], ["  --  ", "==(o> "]]
PIGEON_L = [["  //  ", " <o)=="], ["  --  ", " <o)=="]]

# --------------------------------------------------------------------------- save / codes

def code_hash(raw):
    return hashlib.sha256(raw.strip().upper().replace(" ", "").encode()).hexdigest()


def load_save():
    data = {
        "unlocked": [], "size": "small", "sound": "plop",
        "poop_mode": "single", "poop_modes": ["single"], "best": 0,
    }
    try:
        with open(SAVE_PATH) as f:
            data.update(json.load(f))
    except (OSError, ValueError):
        pass
    if data["sound"] == "plop":
        data["sound"] = "poop"
        data["unlocked"] = ["sound:poop" if item == "sound:plop" else item
                            for item in data["unlocked"]]
    data["unlocked"] = sorted(set(data["unlocked"]) | FREE)
    if data["poop_mode"] not in {mode["key"] for mode in POOP_MODES}:
        data["poop_mode"] = "single"
    data["poop_modes"] = sorted(set(data.get("poop_modes", [])) & {mode["key"] for mode in POOP_MODES} | {"single"})
    return data


def write_save(save):
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(save, f)
    except OSError:
        pass


def wallet_hash(money):
    return hashlib.sha256(("%d|%s" % (money, WALLET_SALT)).encode()).hexdigest()


def load_wallet():
    try:
        with open(WALLET_PATH) as f:
            data = json.load(f)
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
        with open(WALLET_PATH, "w") as f:
            json.dump(payload, f)
    except OSError:
        pass


def label(unlock_id):
    kind, key = unlock_id.split(":")
    if kind == "size":
        return next(s["name"] for s in SIZES if s["key"] == key) + " poop"
    return next(s["name"] for s in SOUNDS if s["key"] == key) + " sound"


def redeem(save, wallet, raw):
    unlocks = CODES.get(code_hash(raw))
    if not unlocks:
        return False, "Invalid code."
    new = [u for u in unlocks if u not in save["unlocked"]]
    if not new:
        return False, "You already redeemed that code."
    if wallet["money"] < CODE_REDEEM_COST:
        return False, "Need $%d to redeem a code." % CODE_REDEEM_COST
    wallet["money"] -= CODE_REDEEM_COST
    write_wallet(wallet["money"])
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
        self.procs = []
        self.cmd = self._find_player()

    @staticmethod
    def _find_player():
        players = [["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
                   ["afplay"], ["paplay"], ["pw-play"], ["aplay", "-q"],
                   ["play", "-q"]]
        if sys.platform.startswith("win"):
            players.append([
                "powershell.exe", "-NoProfile", "-STA", "-WindowStyle", "Hidden", "-Command",
                ""
            ])
        for cmd in players:
            if shutil.which(cmd[0]):
                return cmd
        return None

    def play(self, pack_i, size_i):
        pack = SOUNDS[pack_i]["key"]
        if self.cmd is None:
            curses.beep()
            return
        path = os.path.join(self.dir, pack + ".mp3")
        if not os.path.isfile(path):
            curses.beep()
            return
        self.procs = [p for p in self.procs if p.poll() is None]   # reap finished players
        if len(self.procs) >= MAX_SIMULTANEOUS_SOUNDS:
            return
        try:
            self.procs.append(subprocess.Popen(self._play_command(path), stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL))
        except OSError:
            self.cmd = None

    def play_pack(self, pack, size_i):
        pack_i = next(i for i, sound in enumerate(SOUNDS) if sound["key"] == pack)
        self.play(pack_i, size_i)

    def _play_command(self, path):
        player = os.path.basename(self.cmd[0]).lower()
        volume = max(0.0, min(1.0, VOLUME))
        if player == "ffplay":
            return self.cmd + ["-volume", str(int(volume * 100)), path]
        if player == "afplay":
            return self.cmd + ["-v", str(volume), path]
        if player == "paplay":
            return self.cmd + ["--volume", str(int(volume * 65536)), path]
        if player == "pw-play":
            return self.cmd + ["--volume", str(volume), path]
        if player == "aplay":
            return self.cmd + [path]
        if player == "play":
            return self.cmd + ["-v", str(volume), path]
        if player == "powershell.exe":
            safe_path = path.replace("'", "''")
            script = (
                "$done = New-Object Threading.ManualResetEvent($false); "
                "Add-Type -AssemblyName PresentationCore; "
                "$player = New-Object System.Windows.Media.MediaPlayer; "
                "$player.Volume = " + str(volume) + "; "
                "$dispatcher = [System.Windows.Threading.Dispatcher]::CurrentDispatcher; "
                "$timer = New-Object System.Windows.Threading.DispatcherTimer; "
                "$timer.Interval = [TimeSpan]::FromSeconds(10); "
                "$timer.Add_Tick({ $player.Close(); $dispatcher.InvokeShutdown() }); "
                "$player.add_MediaOpened({ $player.Play(); $timer.Start() }); "
                "$player.add_MediaEnded({ $player.Close(); $dispatcher.InvokeShutdown() }); "
                "$player.add_MediaFailed({ $dispatcher.InvokeShutdown() }); "
                "$player.Open([Uri]'" + safe_path + "'); "
                "[System.Windows.Threading.Dispatcher]::Run()"
            )
            return self.cmd[:-1] + [script]
        return self.cmd + [path, str(volume)]

    def cleanup(self):
        for p in self.procs:
            try:
                p.terminate()
            except OSError:
                pass

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


def make_skyline(w, h, gl):
    grid = [[" "] * w for _ in range(h)]
    rng = random.Random(7)
    x = 0
    while x < w:
        bw = rng.randint(7, 14)
        bh = rng.randint(4, max(5, gl - 6))
        for r in range(bh):
            y = gl - 1 - r
            for cx in (x, x + bw - 1):
                if 0 <= cx < w and y >= 0:
                    grid[y][cx] = "|"
            if r == bh - 1:
                for cx in range(x + 1, x + bw - 1):
                    if 0 <= cx < w and y >= 0:
                        grid[y][cx] = "_"
            elif r % 2 == 1:
                for cx in range(x + 2, x + bw - 2, 3):
                    if 0 <= cx < w and y >= 0 and rng.random() < 0.6:
                        grid[y][cx] = "#"
        x += bw + rng.randint(0, 2)
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
    MAX_AMMO, POOP_COOLDOWN, RELOAD_COOLDOWN = 5, 0.28, 2.0

    def layout():
        nonlocal h, w, gl, bg, clouds
        h, w = stdscr.getmaxyx()
        gl = h - 2
        bg = make_skyline(w, h, gl)
        clouds = [[random.uniform(0, w), random.randint(3, max(3, gl // 3)), random.uniform(0.8, 2.0)]
                  for _ in range(max(3, w // 25))]

    gl, bg, clouds = 0, [], []
    layout()
    people = [Person(w) for _ in range(max(4, w // 14))]
    poops, rocks, particles, splats, floaters = [], [], [], [], []
    px, py, vx, vy, face, flap = w / 2, 4.0, 0.0, 0.0, 1, 0.0
    ammo, cooldown, score = MAX_AMMO, 0.0, 0
    poop_lockout = 0.0
    player_hp = PLAYER_HP_MAX
    no_ammo_flash = 0.0
    reloading = False
    retaliation_banner = 0.0
    hurt_iframes = 0.0
    hit_notice = 0.0
    reward_flash = 0.0
    reward_tier = 0
    rock_salvo_remaining = 0
    rock_throw_queue = []
    rock_salvo_thrower = None
    rock_salvo_cooldown = 0.0
    rock_salvo_pending = False
    next_rock_throw = 0.0
    died = False
    start = last = time.perf_counter()

    while True:
        now = time.perf_counter()
        dt = min(0.1, now - last)
        last = now
        left = ROUND_SECS - (now - start)
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
        rock_salvo_cooldown = max(0.0, rock_salvo_cooldown - dt)
        next_rock_throw = max(0.0, next_rock_throw - dt)
        difficulty_name, difficulty_tier = score_difficulty(score)
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

        # ---- poops
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
                if p.dead > 0:
                    continue
                # Expand the whole person sprite by the poop radius and use
                # the previous/current positions to prevent fast-falling hits
                # from passing between terminal rows.
                half_width = max(0.5, len(s["glyph"]) / 2) + 0.5
                if segment_hits_rect(
                        previous_x, previous_y, poop["x"], poop["y"],
                        p.x + 1.5 - half_width, gl - 3.5 - 0.5,
                        p.x + 1.5 + half_width, gl + 0.5):
                    hit = p
                    break
            if hit or poop["y"] >= gl - 1:
                poops.remove(poop)
                for _ in range(4 + 3 * poop["size"]):
                    particles.append([poop["x"], min(poop["y"], gl - 2), random.uniform(-12, 12),
                                      random.uniform(-14, -3), 0.5, random.choice(".,*'`")])
                if hit:
                    gained = s["pts"] * Person.KINDS[hit.kind]["mult"]
                    score += gained
                    new_tier = score // 30
                    if new_tier > reward_tier:
                        bonus = (new_tier - reward_tier) * 5
                        reward_tier = new_tier
                        wallet["money"] += bonus
                        write_wallet(wallet["money"])
                        reward_flash = 1.5
                        floaters.append([px + 1, max(2.0, py - 1.0), "+$%d" % bonus, 1.1])
                    floaters.append([hit.x + 1, gl - 5.0, "+%d" % gained, 1.0])
                    hit.shout = random.choice(VIP_SHOUTS if hit.kind == "vip" else SHOUTS)
                    hit.throws_rocks = True
                    rock_throw_queue.append(hit)
                    rock_salvo_pending = True
                    retaliation_banner = 3.0
                    hit.stun = PERSON_DEATH_TIME
                else:
                    splats.append([poop["x"], s["splat"], 4.0])

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
            if ((not reloading) and hurt_iframes <= 0 and
                    segment_hits_rect(
                        previous_x, previous_y, rock["x"], rock["y"],
                        px - 0.5, py - 0.5, px + 5.5, py + 2.5)):
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
        for rock in rocks:
            put(stdscr, int(rock["y"]), int(rock["x"]), "O", COL["red"] | curses.A_BOLD)
        for f in floaters:
            put(stdscr, int(f[1]), int(f[0]), f[2], COL["yellow"] | curses.A_BOLD)
        frames = PIGEON_R if face > 0 else PIGEON_L
        put_sprite(stdscr, int(py), int(px), frames[int(flap) % 2], COL["white"] | curses.A_BOLD)
        if hit_notice > 0:
            put(stdscr, max(2, int(py) - 1), int(px) - 2, "-10 HP  -10 SCORE", COL["red"] | curses.A_BOLD)

        put(stdscr, 0, 1, "SCORE %05d" % score, COL["yellow"] | curses.A_BOLD)
        put(stdscr, 0, 16, difficulty_name, COL["magenta"] | curses.A_BOLD)
        hp_attr = (COL["red"] | curses.A_BOLD) if player_hp <= ROCK_HIT_DAMAGE else (COL["green"] | curses.A_BOLD)
        put(stdscr, 0, max(1, w // 2 - 5), "HP %03d" % player_hp, hp_attr)
        put(stdscr, 0, max(30, w - 26), "MONEY $%d" % wallet["money"], COL["green"] | curses.A_BOLD)
        put(stdscr, 0, w - 12, "TIME %3d" % math.ceil(left), COL["white"] | curses.A_BOLD)
        if retaliation_banner > 0:
            center(stdscr, 2, "POOPED PEOPLE ARE THROWING ROCKS - DODGE!", COL["red"] | curses.A_BOLD)
        if reward_flash > 0:
            center(stdscr, 3, "+$5 every 30 score!", COL["green"] | curses.A_BOLD)
        bar = int(ammo / MAX_AMMO * 12)
        ammo_attr = COL["red"] | curses.A_BOLD if no_ammo_flash > 0 else COL["cyan"]
        put(stdscr, 1, 1, "SHITTING [%s%s]" % ("#" * bar, "-" * (12 - bar)), ammo_attr)
        cd_attr = (COL["red"] | curses.A_BOLD) if reloading else ((COL["yellow"] | curses.A_BOLD) if cooldown > 0 else (COL["green"] | curses.A_BOLD))
        cd_text = "RELOAD %.1fs" % cooldown if reloading else ("CD %.1fs" % cooldown if cooldown > 0 else "CD READY")
        put(stdscr, 1, 24, cd_text, cd_attr)
        mode_cost = SIZES[size_i]["cost"] * mode["count"]
        put(stdscr, 1, 38, "%s (cost %d)" % (mode["name"], mode_cost), COL["white"])
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
    center(stdscr, cy + 4, "Wallet: $%d" % wallet["money"], COL["green"] | curses.A_BOLD)
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
    while True:
        stdscr.erase()
        h, _ = stdscr.getmaxyx()
        cy = h // 2 - 7
        current = next(m for m in POOP_MODES if m["key"] == save["poop_mode"])
        center(stdscr, cy, "MARKET", COL["yellow"] | curses.A_BOLD)
        center(stdscr, cy + 1, "Wallet: $%d" % wallet["money"], COL["green"] | curses.A_BOLD)
        for i, mode in enumerate(POOP_MODES):
            owned = mode["key"] in save["poop_modes"]
            label_text = "%s %s poops - $%d - %s" % (
                ">" if i == row else " ", mode["name"], mode["cost"],
                "OWNED" if owned else mode["sound"].upper())
            center(stdscr, cy + 3 + i, label_text, curses.A_BOLD if i == row else 0)
        center(stdscr, cy + 9, "Enter = buy/use   C = redeem code   Esc = back", curses.A_DIM)
        center(stdscr, cy + 10, "Current: %s (%d at a time)" % (current["name"], current["count"]), COL["cyan"])
        stdscr.refresh()
        k = stdscr.getch()
        if k in (curses.KEY_UP, ord("k")):
            row = (row - 1) % len(POOP_MODES)
        elif k in (curses.KEY_DOWN, ord("j")):
            row = (row + 1) % len(POOP_MODES)
        elif k in (10, 13, curses.KEY_ENTER, ord(" ")):
            selected = POOP_MODES[row]
            if selected["key"] in save["poop_modes"]:
                save["poop_mode"] = selected["key"]
                write_save(save)
                audio.play_pack(selected["sound"], size_index(save))
            elif wallet["money"] >= selected["cost"]:
                if selected["cost"]:
                    wallet["money"] -= selected["cost"]
                    write_wallet(wallet["money"])
                save["poop_modes"].append(selected["key"])
                save["poop_mode"] = selected["key"]
                write_save(save)
                audio.play_pack(selected["sound"], size_index(save))
        elif k in (ord("c"), ord("C")):
            enter_code(stdscr, save, wallet)
        elif k in (27, ord("q"), ord("Q")):
            return


def loadout(stdscr, save, audio):
    row = 0
    while True:
        os_, ou = owned_sizes(save), owned_sounds(save)
        si, so = size_index(save), sound_index(save)
        stdscr.erase()
        h, _ = stdscr.getmaxyx()
        cy = h // 2 - 5
        center(stdscr, cy, "LOADOUT", COL["yellow"] | curses.A_BOLD)
        rows = [("Poop size ", SIZES[si]["name"]), ("Poop sound", SOUNDS[so]["name"])]
        for i, (lab, val) in enumerate(rows):
            text = "%s %s: <  %s  >" % (">" if i == row else " ", lab, val)
            center(stdscr, cy + 2 + i * 2, text, curses.A_BOLD if i == row else 0)
        sizes_line = "Sizes:  " + "   ".join(
            s["name"] + ("" if i in os_ else " (locked)") for i, s in enumerate(SIZES))
        sounds_line = "Sounds: " + "   ".join(
            s["name"] + ("" if i in ou else " (locked)") for i, s in enumerate(SOUNDS))
        center(stdscr, cy + 7, sizes_line, curses.A_DIM)
        center(stdscr, cy + 8, sounds_line, curses.A_DIM)
        center(stdscr, cy + 10, "up/down pick   left/right change   Enter = preview sound   Esc = back", curses.A_DIM)
        stdscr.refresh()
        k = stdscr.getch()
        if k in (curses.KEY_UP, curses.KEY_DOWN, ord("k"), ord("j")):
            row = 1 - row
        elif k in (curses.KEY_LEFT, curses.KEY_RIGHT, ord("h"), ord("l")):
            d = -1 if k in (curses.KEY_LEFT, ord("h")) else 1
            if row == 0:
                save["size"] = SIZES[os_[(os_.index(si) + d) % len(os_)]]["key"]
            else:
                save["sound"] = SOUNDS[ou[(ou.index(so) + d) % len(ou)]]["key"]
            write_save(save)
            audio.play(sound_index(save), size_index(save))
        elif k in (10, 13, curses.KEY_ENTER, ord(" ")):
            audio.play(so, si)
        elif k in (27, ord("q")):
            return


def menu(stdscr, save, wallet, audio):
    items = ["PLAY", "MARKET", "LOADOUT", "QUIT"]
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
        center(stdscr, top + 19, "Best: %d   Wallet: $%d" % (save["best"], wallet["money"]), COL["magenta"])
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
            loadout(stdscr, save, audio)
        elif act == 3:
            return


def main(stdscr):
    init_colors()
    save = load_save()
    wallet = {"money": load_wallet()}
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
