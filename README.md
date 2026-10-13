<p align="center">
  <img src="docs/screenshots/title-art.png" alt="PIGEON rendered in ASCII characters" width="760" />
</p>

<h1 align="center">PIGEON</h1>

<p align="center">
  <strong>Terminal arcade. Questionable aerial tactics.</strong><br />
  A real-time ASCII game built with Python, <code>curses</code>, and Pygame.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white" alt="Python 3.9 or newer recommended" />
  <img src="https://img.shields.io/badge/interface-terminal-242424?logo=gnometerminal&logoColor=white" alt="Terminal interface" />
  <img src="https://img.shields.io/badge/rendering-ASCII-6C5CE7" alt="ASCII rendering" />
  <img src="https://img.shields.io/badge/audio-Pygame-25A55F" alt="Pygame audio" />
</p>

---

## The idea

Take control of a pigeon, navigate a tiny city made from terminal characters, and aim your payload at pedestrians. Hits earn points and cash; the people you hit may throw rocks back. Stay airborne, watch your health, and make the most of a round before the clock runs out.

PIGEON keeps the presentation deliberately low-resolution: colored text, ASCII sprites, a scrolling-feeling city scene, sound effects, and a compact in-game market. No graphical window is required for the game view—just a terminal big enough to fly in.

## Screenshots

<p align="center">
  <img src="docs/screenshots/main-menu.png" alt="PIGEON main menu showing Play, Market, Clear User Data, and Quit" width="680" />
</p>

<p align="center">
  <img src="docs/screenshots/gameplay.png" alt="Gameplay view with the pigeon, city skyline, pedestrians, score, health, timer, and ammo display" width="860" />
</p>

<p align="center">
  <img src="docs/screenshots/market.png" alt="Market menu showing wallet balance and selectable size, sound, and drop-amount upgrades" width="680" />
</p>

## Features

- **Live terminal action** — fly in four directions while the city and pedestrians keep moving.
- **A 120-second round** — the countdown starts on your first successful drop, so you can line up before committing.
- **Four payload sizes** — Small, Medium, Large, and MEGA, each with a different ammo cost and base score.
- **Four drop modes** — Single, Double, Triple, and Shower. Bigger bursts use more ammo and raise the difficulty pressure.
- **Three pedestrian types** — normal, chunky, and VIP. VIPs are worth triple base points.
- **Close-range bonus** — hits made near the pigeon are worth double points.
- **Retaliation and health** — people you hit can throw rocks. Rocks cost health and score, so movement matters.
- **Progression and rewards** — score earns wallet cash in $5 steps for every 30 points reached; spend it in the market.
- **Redeemable unlock codes** — unlock selected sizes and sounds through the market.
- **Audio controls** — menu music volume and mute toggle, background music, and drop sound effects.
- **Local persistence** — best score, wallet, unlocked items, and selected loadout survive between runs.
- **Clear User Data option** — reset local progress after an explicit confirmation.

## Get it running

### Requirements

- Python **3.9 or newer recommended**
- A terminal that supports `curses` and Unicode characters
- Pygame for audio
- The audio files listed under [Audio assets](#audio-assets)

### 1. Install dependencies

**macOS / Linux**

`curses` is normally included with Python on these systems. Install Pygame:

```bash
python3 -m pip install pygame
```

**Windows**

Install the Windows-compatible curses package and Pygame:

```powershell
py -m pip install windows-curses pygame
```

### 2. Arrange the files

Keep the game script and `audio/` folder together. The game looks for audio relative to `pigeon.py`.

```text
pigeon/
├── pigeon.py
├── audio/
│   ├── fart.mp3
│   ├── fart1.mp3
│   ├── fart2.mp3
│   ├── Star Wars Main Theme Cover (Handfarts).mp3
│   └── 🌿 Nature Soundscape Relaxing Bird Songs for Study & Meditation 10 Min Mix 🎶.mp3
└── docs/
    └── screenshots/
```

### 3. Launch

From the project directory:

```bash
python pigeon.py
```

On systems where Python 3 is invoked as `python3` or `py`, use that command instead. A terminal size of at least **70 columns × 20 rows** is required; a larger window is more comfortable.

## How to play

### In-game controls

| Key | Action |
|---|---|
| `←` / `A` | Fly left |
| `→` / `D` | Fly right |
| `↑` / `W` | Fly up |
| `↓` / `S` | Fly down |
| `Space` | Drop payload |
| `Q` or `Esc` | Return to the menu |

### Menu controls

| Key | Action |
|---|---|
| `↑` / `K`, `↓` / `J` | Move through menu options |
| `Enter` or `1`–`5` | Select a menu item |
| `←` / `→` while Audio is selected | Lower / raise menu music volume |
| `Enter` while Audio is selected | Toggle mute |

### Market controls

| Key | Action |
|---|---|
| `↑` / `K`, `↓` / `J` | Choose size, sound, or drop amount |
| `←` / `→` or `H` / `L` | Browse the available option in that row |
| `Enter` or `Space` | Buy or equip the selected item |
| `C` | Enter a redeem code |
| `Esc` or `Q` | Return to the menu |

In the code-entry screen, type the code and press `Enter` to redeem it. Use `Backspace` to edit or `Esc` to cancel.

## Progression and market

All prices below are paid from the in-game wallet.

### Payload sizes

| Size | Base points per hit | Ammo units per payload | Market price |
|---|---:|---:|---:|
| Small | 10 | 1 | Free |
| Medium | 25 | 2 | $2,200 |
| Large | 60 | 4 | $3,500 |
| MEGA | 150 | 8 | $6,000 |

### Sounds

| Sound | Market price |
|---|---:|
| Fart | Free |
| Fart 1 | $1,800 |
| Fart 2 | $2,600 |

### Drop amounts

| Mode | Payloads per press | Market price |
|---|---:|---:|
| Single | 1 | Free |
| Double | 2 | $1,500 |
| Triple | 3 | $2,500 |
| Shower | 5 | $5,000 |

The ammo cost of a press is the selected size's ammo cost multiplied by the number of payloads in the selected mode. The game starts with enough ammo for one burst and reloads automatically when needed.

### Redeem codes

Enter these from **Market → `C`**. A successful new code redemption costs **$1,000** in-game. Codes are normalized to uppercase and spaces are ignored.

| Code | Unlocks |
|---|---|
| `PIGEON-PLUS` | Medium payload + Fart 1 sound |
| `SQUELCH-ME` | Fart 2 sound |
| `BIG-ONE` | Large payload |
| `BOMBS-AWAY` | MEGA payload + Fart 2 sound |

Codes can only grant items that are not already unlocked. Redeeming an already-used code does not charge the wallet again.

## Saves and privacy

Progress is stored locally in your home directory:

- `.pigeon_save.json` — unlocks, selected loadout, drop mode, respect bonus counter, and best score.
- `.pigeon_wallet.json` — wallet balance and a SHA-256 consistency hash.

There are no online accounts or server-side saves in the supplied code. The wallet hash is a basic consistency check, **not encryption or tamper-proof security**; local save data should not be treated as protected against someone who can edit the game or its files.

To reset progress, select **Clear User Data** from the main menu and press `Y` to confirm. This resets the wallet, best score, unlocks, and selected loadout. Any other key cancels the reset.

## Audio assets

The current script expects these files inside `audio/` using the exact filenames below:

**Required for the game to start**

- `Star Wars Main Theme Cover (Handfarts).mp3` — menu music
- `🌿 Nature Soundscape Relaxing Bird Songs for Study & Meditation 10 Min Mix 🎶.mp3` — gameplay music

**Sound effects**

- `fart.mp3`
- `fart1.mp3`
- `fart2.mp3`

The three effect files are optional in the current implementation; if one is missing, the game falls back to a terminal beep for that sound. The two music files are checked at startup and missing files will stop initialization with an error.

Before publishing or distributing a repository, make sure you have permission to redistribute every audio track. If not, replace the tracks with audio you are licensed to use and update the filenames/constants in `pigeon.py`.

## Developer notes

The project is currently organized as a single Python file, with sections for save handling, audio, drawing helpers, the game loop, and menus. That keeps the prototype easy to run and modify without a package build step.

A few useful extension points:

- **Balancing:** constants near the top of `pigeon.py` control round duration, movement, collision sizes, scoring pressure, rock behavior, and cooldowns.
- **Content:** `SIZES`, `SOUNDS`, `POOP_MODES`, and the associated price dictionaries define market inventory.
- **Pedestrians:** `Person.KINDS` defines archetypes, colors, speed ranges, and score multipliers.
- **Unlock codes:** `CODES` maps normalized SHA-256 hashes to unlock IDs. The helper below prints the hash for a code string:

  ```bash
  python pigeon.py --hash "YOUR-CODE"
  ```

  Add the resulting hash and the intended unlock IDs to `CODES`. Unlock IDs follow forms such as `size:large` and `sound:fart2`; make sure the item exists in the inventory definitions and is accepted by save validation.

For changes to collision or scoring, test single hits, overlapping targets, bursts, and retaliation separately. The code intentionally counts direct hits per frame rather than assuming every person in a group was hit.

## Troubleshooting

**The game says the terminal is too small.**  
Resize the terminal to at least 70 × 20 characters. A wide terminal makes the scene easier to read.

**Windows says `curses` is missing.**  
Run `py -m pip install windows-curses pygame`, then launch the script again.

**The game cannot find music.**  
Confirm both required tracks are inside `audio/` next to the script and their filenames match exactly, including spaces and emoji. Alternatively, change `MENU_MUSIC_FILE` or `BACKGROUND_MUSIC_FILE` in `pigeon.py` to match your own files.

**Audio fails to initialize.**  
Check that your system has an available audio output device and that Pygame can initialize its mixer.

**The screen looks cramped or colors are missing.**  
Use a larger terminal and a terminal emulator with color support. The game can fall back when color support is unavailable, but the display is designed around colored terminal text.

## License

No license file was provided with the supplied project. Until a `LICENSE` file is added, do not assume that the code or bundled assets are available for reuse or redistribution. Choose a license and add its full text before publishing the repository for outside contributions.

---

<p align="center">
  <sub>Made for the terminal. Best played with a little room to maneuver.</sub>
</p>
