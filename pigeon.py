#!/usr/bin/env python3
"""
PIGEON - an ASCII terminal game. You are a pigeon. People are walking below.
You know what to do.

Run:   python3 pigeon.py
Needs: Python 3.8+ and curses (built in on Linux/macOS; Windows: pip install windows-curses)
Sound: generated on the fly (no asset files). Uses afplay / paplay / aplay / pw-play /
       ffplay / play if found, winsound on Windows, otherwise the terminal bell.

Adding codes:  python3 pigeon.py --hash MY-NEW-CODE   -> paste the hash into CODES below.
"""
import hashlib
import json
import math
import os
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave

try:
    import curses
except ImportError:
    sys.exit("curses not found. On Windows run: pip install windows-curses")

SAVE_PATH = os.path.join(os.path.expanduser("~"), ".pigeon_save.json")
ROUND_SECS = 90
MIN_W, MIN_H = 70, 20

# --------------------------------------------------------------------------- content

# cost = ammo per poop, pts = base score, hw = extra hit-box half width
SIZES = [
    dict(key="small",  name="Small",  glyph=".",      splat=",",          cost=1, pts=10,  hw=0),
    dict(key="medium", name="Medium", glyph="o",      splat="-o-",        cost=2, pts=25,  hw=1),
    dict(key="large",  name="Large",  glyph="(@)",    splat="~(@)~",      cost=4, pts=60,  hw=2),
    dict(key="mega",   name="MEGA",   glyph="(@@@)",  splat="~~(@@@)~~",  cost=8, pts=150, hw=3),
]
SOUNDS = [
    dict(key="plop",    name="Plop"),
    dict(key="splat",   name="Splat"),
    dict(key="squelch", name="Squelch"),
    dict(key="boing",   name="Boing"),
    dict(key="bomb",    name="Bomb"),
]
FREE = {"size:small", "sound:plop"}

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
    data = {"unlocked": [], "size": "small", "sound": "plop", "best": 0}
    try:
        with open(SAVE_PATH) as f:
            data.update(json.load(f))
    except (OSError, ValueError):
        pass
    data["unlocked"] = sorted(set(data["unlocked"]) | FREE)
    return data


def write_save(save):
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(save, f)
    except OSError:
        pass


def label(unlock_id):
    kind, key = unlock_id.split(":")
    if kind == "size":
        return next(s["name"] for s in SIZES if s["key"] == key) + " poop"
    return next(s["name"] for s in SOUNDS if s["key"] == key) + " sound"


def redeem(save, raw):
    unlocks = CODES.get(code_hash(raw))
    if not unlocks:
        return False, "Invalid code."
    new = [u for u in unlocks if u not in save["unlocked"]]
    if not new:
        return False, "You already redeemed that code."
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

SR = 22050
PITCH = [1.35, 1.0, 0.72, 0.5]    # bigger poop = lower pitch
LENGTH = [1.0, 1.2, 1.5, 2.0]     # ...and longer sound


def synth(pack, size_i):
    k, L = PITCH[size_i], LENGTH[size_i]
    rnd = random.Random(size_i * 31 + 7)
    out = []
    if pack == "plop":
        n = int(SR * 0.18 * L)
        ph = 0.0
        for i in range(n):
            t = i / n
            ph += 2 * math.pi * (700 - 550 * t) * k / SR
            out.append(math.sin(ph) * (1 - t) ** 2)
    elif pack == "splat":
        n = int(SR * 0.28 * L)
        lp = ph = 0.0
        for i in range(n):
            t = i / n
            lp += (rnd.uniform(-1, 1) - lp) * 0.3 * k
            ph += 2 * math.pi * 110 * k / SR
            out.append(lp * 3.0 * (1 - t) ** 1.5 + 0.8 * math.sin(ph) * (1 - t) ** 3)
    elif pack == "squelch":
        n = int(SR * 0.35 * L)
        ph = 0.0
        for i in range(n):
            t = i / n
            ph += 2 * math.pi * (420 - 260 * t) * k / SR
            wob = 4 * math.sin(2 * math.pi * 35 * i / SR)
            out.append(math.sin(ph + wob) * (1 - t))
    elif pack == "boing":
        n = int(SR * 0.4 * L)
        ph = 0.0
        for i in range(n):
            t = i / n
            f = (250 + 300 * t) * k + 40 * math.sin(2 * math.pi * 14 * i / SR)
            ph += 2 * math.pi * f / SR
            out.append(math.sin(ph) * (1 - t) ** 1.2)
    else:  # bomb
        n = int(SR * 0.7 * L)
        lp = ph = 0.0
        for i in range(n):
            t = i / n
            lp += (rnd.uniform(-1, 1) - lp) * 0.05
            ph += 2 * math.pi * (140 - 100 * t) * k / SR
            out.append((lp * 6.0 + math.sin(ph)) * (1 - t) ** 2)
    peak = max(0.001, max(abs(s) for s in out))
    return [max(-1.0, min(1.0, s / peak * 0.8)) for s in out]


def write_wav(path, samples):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(b"".join(struct.pack("<h", int(s * 32767)) for s in samples))


class Audio:
    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="pigeon_")
        self.cache = {}
        self.procs = []
        self.cmd = self._find_player()

    @staticmethod
    def _find_player():
        if sys.platform.startswith("win"):
            return "winsound"
        for cmd in (["afplay"], ["paplay"], ["pw-play"], ["aplay", "-q"],
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"], ["play", "-q"]):
            if shutil.which(cmd[0]):
                return cmd
        return None

    def _path(self, pack, size_i):
        key = (pack, size_i)
        if key not in self.cache:
            p = os.path.join(self.dir, "%s_%d.wav" % key)
            write_wav(p, synth(pack, size_i))
            self.cache[key] = p
        return self.cache[key]

    def play(self, pack_i, size_i):
        pack = SOUNDS[pack_i]["key"]
        if self.cmd is None:
            curses.beep()
            return
        path = self._path(pack, size_i)
        if self.cmd == "winsound":
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
        self.procs = [p for p in self.procs if p.poll() is None]   # reap finished players
        if len(self.procs) >= 6:
            return
        try:
            self.procs.append(subprocess.Popen(self.cmd + [path], stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL))
        except OSError:
            self.cmd = None

    def cleanup(self):
        for p in self.procs:
            try:
                p.terminate()
            except OSError:
                pass
        shutil.rmtree(self.dir, ignore_errors=True)

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
        self.shout = ""
        self.anim = random.random() * 10

    def rows(self):
        k = self.KINDS[self.kind]
        if self.stun > 0:
            return [" x ", "\\|/", "/ \\"]
        legs = "/ \\" if int(self.anim * 2) % 2 == 0 else " | "
        return [" " + k["head"] + " ", "/|\\", legs]


def play(stdscr, save, audio):
    cursor(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)
    h, w = stdscr.getmaxyx()
    if w < MIN_W or h < MIN_H:
        return None
    size_i, sound_i = size_index(save), sound_index(save)
    G, MAX_AMMO, REGEN = 35.0, 12.0, 2.2

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
    poops, particles, splats, floaters = [], [], [], []
    px, py, vx, vy, face, flap = w / 2, 4.0, 0.0, 0.0, 1, 0.0
    ammo, cooldown, score, streak = MAX_AMMO, 0.0, 0, 0
    no_ammo_flash = 0.0
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
            elif ord("1") <= k <= ord("4"):
                if k - ord("1") in owned_sizes(save):
                    size_i = k - ord("1")
            elif k in (ord("m"), ord("M")):
                o = owned_sounds(save)
                sound_i = o[(o.index(sound_i) + 1) % len(o)]
            elif k in (ord("q"), ord("Q"), 27):
                return score

        # ---- pigeon
        drag = math.exp(-3.0 * dt)
        vx, vy = vx * drag, vy * drag
        px = min(max(0, px + vx * dt), w - 6)
        py = min(max(3, py + vy * dt), gl - 8)
        flap += dt * (8 + abs(vx) * 0.3)
        ammo = min(MAX_AMMO, ammo + REGEN * dt)
        cooldown = max(0.0, cooldown - dt)
        no_ammo_flash = max(0.0, no_ammo_flash - dt)

        if want_drop and cooldown <= 0:
            s = SIZES[size_i]
            if ammo >= s["cost"]:
                ammo -= s["cost"]
                cooldown = 0.1
                poops.append(dict(x=px + (2.5 if face > 0 else 3.5), y=py + 2.0, vy=2.0, size=size_i))
            else:
                no_ammo_flash = 0.6

        # ---- people
        for p in people:
            p.anim += dt * p.speed
            if p.stun > 0:
                p.stun -= dt
                continue
            p.x += p.dir * p.speed * dt
            if p.x > w + 1 or p.x < -4:
                p.respawn(w, edge=-p.dir)

        # ---- poops
        for poop in poops[:]:
            poop["vy"] += G * dt
            poop["y"] += poop["vy"] * dt
            s = SIZES[poop["size"]]
            hit = None
            for p in people:
                if gl - 3 <= poop["y"] <= gl and abs(poop["x"] - (p.x + 1.5)) <= 1.5 + s["hw"]:
                    hit = p
                    break
            if hit or poop["y"] >= gl - 1:
                poops.remove(poop)
                audio.play(sound_i, poop["size"])
                for _ in range(4 + 3 * poop["size"]):
                    particles.append([poop["x"], min(poop["y"], gl - 2), random.uniform(-12, 12),
                                      random.uniform(-14, -3), 0.5, random.choice(".,*'`")])
                if hit:
                    if hit.stun <= 0:
                        streak += 1
                        mult = min(5, 1 + streak // 2)
                        gained = s["pts"] * mult * Person.KINDS[hit.kind]["mult"]
                        score += gained
                        floaters.append([hit.x + 1, gl - 5.0, "+%d" % gained, 1.0])
                        hit.shout = random.choice(VIP_SHOUTS if hit.kind == "vip" else SHOUTS)
                    hit.stun = 1.3
                else:
                    streak = 0
                    splats.append([poop["x"], s["splat"], 4.0])

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
            if p.stun > 0 and p.shout:
                put(stdscr, gl - 4, int(p.x + 1.5 - len(p.shout) / 2), p.shout, COL["red"] | curses.A_BOLD)
        for poop in poops:
            g = SIZES[poop["size"]]["glyph"]
            put(stdscr, int(poop["y"]), int(poop["x"] - len(g) / 2), g, COL["yellow"] | curses.A_BOLD)
        for pt in particles:
            put(stdscr, int(pt[1]), int(pt[0]), pt[5], COL["yellow"])
        for f in floaters:
            put(stdscr, int(f[1]), int(f[0]), f[2], COL["yellow"] | curses.A_BOLD)
        frames = PIGEON_R if face > 0 else PIGEON_L
        put_sprite(stdscr, int(py), int(px), frames[int(flap) % 2], COL["white"] | curses.A_BOLD)

        mult = min(5, 1 + streak // 2)
        put(stdscr, 0, 1, "SCORE %05d" % score, COL["yellow"] | curses.A_BOLD)
        put(stdscr, 0, 16, "STREAK %d (x%d)" % (streak, mult), COL["magenta"] | curses.A_BOLD)
        put(stdscr, 0, w - 12, "TIME %3d" % math.ceil(left), COL["white"] | curses.A_BOLD)
        bar = int(ammo / MAX_AMMO * 12)
        ammo_attr = COL["red"] | curses.A_BOLD if no_ammo_flash > 0 else COL["cyan"]
        put(stdscr, 1, 1, "AMMO [%s%s]" % ("#" * bar, "-" * (12 - bar)), ammo_attr)
        put(stdscr, 1, 21, "SIZE %s (cost %d)" % (SIZES[size_i]["name"], SIZES[size_i]["cost"]), COL["white"])
        put(stdscr, 1, 44, "SOUND %s" % SOUNDS[sound_i]["name"], COL["white"])
        put(stdscr, h - 1, 1, "arrows/WASD fly   SPACE poop   1-4 size   M sound   Q menu", curses.A_DIM)
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
    center(stdscr, cy, "TIME'S UP!", COL["yellow"] | curses.A_BOLD)
    center(stdscr, cy + 2, "You hit people for %d points" % score, COL["white"])
    center(stdscr, cy + 3, "NEW BEST!" if new_best else "Best: %d" % save["best"], COL["magenta"] | curses.A_BOLD)
    center(stdscr, cy + 5, "press any key", curses.A_DIM)
    stdscr.refresh()
    time.sleep(0.6)
    curses.flushinp()
    stdscr.getch()
    return score

# --------------------------------------------------------------------------- menus

def enter_code(stdscr, save):
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
                ok, msg = redeem(save, buf)
            buf = ""
        elif k == 27:
            break
        elif k in (127, 8, curses.KEY_BACKSPACE):
            buf = buf[:-1]
        elif 32 <= k < 127 and len(buf) < 32:
            buf += chr(k)
    cursor(0)


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


def menu(stdscr, save, audio):
    items = ["PLAY", "ENTER CODE", "LOADOUT", "QUIT"]
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
        center(stdscr, top + len(TITLE) + 1, "poop on people. sell codes. profit.", curses.A_DIM)
        for i, it in enumerate(items):
            text = ("> %s <" % it) if i == sel else it
            center(stdscr, top + 8 + i * 2, text, (COL["yellow"] | curses.A_BOLD) if i == sel else 0)
        if msg:
            center(stdscr, top + 17, msg, COL["red"] | curses.A_BOLD)
        center(stdscr, top + 19, "Best: %d" % save["best"], COL["magenta"])
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
            if play(stdscr, save, audio) is None:
                msg = "Terminal too small - need at least %dx%d" % (MIN_W, MIN_H)
        elif act == 1:
            enter_code(stdscr, save)
        elif act == 2:
            loadout(stdscr, save, audio)
        elif act == 3:
            return


def main(stdscr):
    init_colors()
    save = load_save()
    audio = Audio()
    try:
        menu(stdscr, save, audio)
    finally:
        audio.cleanup()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--hash":
        print(code_hash(sys.argv[2]))
        sys.exit(0)
    os.environ.setdefault("ESCDELAY", "25")
    curses.wrapper(main)
