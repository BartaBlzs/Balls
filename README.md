<p align="center">
  <img src="docs/screenshots/title-art.png" alt="PIGEON ASCII title art" width="760" />
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
  <img src="https://img.shields.io/badge/modes-Timed%20%2B%20Endless-E1B12C" alt="Timed and Endless modes" />
</p>

---

## What is PIGEON?

PIGEON is a small, chaotic terminal arcade game about flying a pigeon over an ASCII city, landing hits, building a wallet, and trying not to get pelted with rocks in return.

The entire game scene is rendered as terminal characters. Fly through the skyline, choose your payload, unlock upgrades, and see how long you last once the city starts fighting back. It needs no graphical game window—just Python, a terminal, and the required audio files.

> **The pitch:** old-school terminal visuals, arcade pacing, a suspiciously detailed upgrade economy, and a boss called **The Mayor**.

## Screenshots

<p align="center">
  <img src="docs/screenshots/main-menu.png" alt="PIGEON main-menu terminal art" width="720" />
</p>

<p align="center">
  <img src="docs/screenshots/gameplay.png" alt="Gameplay with the pigeon, ASCII city, pedestrians, score, health, timer, and ammo" width="900" />
</p>

<p align="center">
  <img src="docs/screenshots/market.png" alt="PIGEON market showing wallet balance and item selection" width="720" />
</p>

<sub>These screenshots show the visual style from an earlier build. The current market also includes upgrades, Respect+ rewards, and family options; the menu includes the game-mode switch.</sub>

## Features

### The run

- **Two game modes:** play a 120-second round or switch to **Endless** and keep going until you run out of health.
- **Four-direction flight:** move with the arrow keys or WASD while pedestrians move across the city.
- **Arcade-style scoring:** Small, Medium, Large, and MEGA payloads have different costs and base scores.
- **Crowd proximity bonus:** hits made near the pigeon are worth double points.
- **Three pedestrian types:** normal, chunky, and VIP. VIPs are worth three times the base hit score.
- **Retaliation:** hit pedestrians can throw rocks back. Rocks can damage health, reduce score, and temporarily prevent dropping another payload.
- **Escalating difficulty:** score thresholds bring faster pressure, larger rock salvos, umbrellas, and eventually a boss fight.
- **The Mayor boss fight:** deal enough damage to defeat the Mayor for a **500-point bonus** and **$250**.

### Progression and customization

- **Four payload sizes** and **four drop modes**: Single, Double, Triple, and Shower.
- **Three sound-effect choices**, plus menu, gameplay, and family-scene music.
- **Four purchasable upgrades:** Shield, Rapid-fire Laxative, Faster Pigeon Movement, and Faster Reload. Only one upgrade can be equipped at a time.
- **Family options:** unlock a companion setup. Depending on the option, the pigeon flies with a partner or a small family—including a baby bird—and launches payloads from multiple birds.
- **Respect+ rewards:** earn Respect+ through multi-target hits and spend it on one random item you have not unlocked yet.
- **Redeem codes:** selected codes unlock payload sizes or sounds for an in-game fee.
- **Persistent progress:** best score, wallet, unlocks, modes, upgrades, family choice, and related progression are saved locally.
- **Clear User Data:** reset local progress and wallet after confirming the action.

## Get it running

### Requirements

- Python **3.9 or newer recommended**
- A terminal that supports `curses` and color output (color support can fall back if unavailable)
- Pygame for audio
- The three required music files listed under [Audio assets](#audio-assets)
- A terminal at least **70 columns × 20 rows**. Bigger is better for the city view.

### 1. Install dependencies

**macOS / Linux**

`curses` is normally included with Python on these systems. Install Pygame:

```bash
python3 -m pip install pygame
```

**Windows**

Install `windows-curses` and Pygame:

```powershell
py -m pip install windows-curses pygame
```

### 2. Arrange the files

Keep `pigeon.py` and the `audio/` directory together. The game loads audio relative to the script location.

```text
pigeon/
├── pigeon.py
├── audio/
│   ├── fart.mp3
│   ├── fart1.mp3
│   ├── fart2.mp3
│   ├── Star Wars Main Theme Cover (Handfarts).mp3
│   ├── 🌿 Nature Soundscape Relaxing Bird Songs for Study & Meditation 10 Min Mix 🎶.mp3
│   └── Romantic music sound effect.mp3
└── README.md
```

The screenshot directory in this repository is only for README images; it is not required to run the game. Audio tracks are not included in the README screenshot bundle.

### 3. Launch

From the project directory:

```bash
python pigeon.py
```

Use `python3 pigeon.py` or `py pigeon.py` if that is how Python is installed on your system.

## How to play

### In-game controls

| Key | Action |
|---|---|
| `←` / `A` | Fly left |
| `→` / `D` | Fly right |
| `↑` / `W` | Fly up |
| `↓` / `S` | Fly down |
| `Space` | Drop payload |
| `Q` or `Esc` | Leave the run and return to the menu |

The timer begins on the first successful drop in Timed mode, so you can reposition before starting the clock. **Endless** mode has no countdown, but your health still matters.

### Main-menu controls

| Key | Action |
|---|---|
| `↑` / `K`, `↓` / `J` | Move the selection |
| `Enter` or `1`–`6` | Choose a menu item |
| `←` / `→` while **Audio** is selected | Lower / raise menu music volume |
| `Enter` while **Audio** is selected | Mute / unmute menu music |
| `←` / `→` or `Enter` while **Mode** is selected | Switch Timed / Endless |
| `Q` or `Esc` | Exit the menu loop |

### Market controls

| Key | Action |
|---|---|
| `↑` / `K`, `↓` / `J` | Select a market category |
| `←` / `→` or `H` / `L` | Browse options in the selected category |
| `Enter` or `Space` | Buy, equip, use, or claim the selected item |
| `C` | Enter a redeem code |
| `Esc` or `Q` | Return to the menu |

The market has six rows: **Size**, **Sound**, **Amount**, **Upgrade**, **Respect+**, and **Family**. The Respect+ row claims a random eligible reward; family options play a short animated scene when selected or unlocked.

In the code-entry screen, type a code and press `Enter` to redeem it. Use `Backspace` to edit or `Esc` to cancel.

## Game systems

### Difficulty and the Mayor

Difficulty is driven by score, not by the selected drop mode:

| Score | Level |
|---:|---|
| 0–49 | EASY |
| 50–149 | MEDIUM |
| 150–250 | HARDCORE |
| 251+ | U ARE FUCKED — the Mayor arrives |

As difficulty rises, pedestrians move faster and rock attacks become more intense. At the highest tier, some pedestrians carry umbrellas that can block a payload. The Mayor moves across the street and fires aimed rocks. Hit the boss with payloads to reduce its **12 HP**; larger payloads deal more boss damage. Defeating it awards **+500 score** and **+$250**.

### Payload sizes

| Size | Base score per pedestrian hit | Ammo cost per payload | Market price |
|---|---:|---:|---:|
| Small | 10 | 1 | Free |
| Medium | 25 | 2 | $2,200 |
| Large | 60 | 4 | $3,500 |
| MEGA | 150 | 8 | $6,000 |

### Drop modes

| Mode | Payloads per bird per press | Market price |
|---|---:|---:|
| Single | 1 | Free |
| Double | 2 | $1,500 |
| Triple | 3 | $2,500 |
| Shower | 5 | $5,000 |

Ammo use is based on **payload size × drop count × number of active birds**. Family options can therefore make a press more expensive in ammo, but also put more payloads in the air. The game begins with enough ammo for one full selected burst and reloads automatically.

### Sounds

| Sound | Market price |
|---|---:|
| Fart | Free |
| Fart 1 | $1,800 |
| Fart 2 | $2,600 |

### Upgrades

Only one upgrade can be equipped at a time. Buy an upgrade in the market, then select it again to equip or unequip it.

| Upgrade | Price | Effect |
|---|---:|---|
| Shield | $5,000 | Blocks the first **3 incoming rocks** in a run |
| Rapid-fire Laxative | $6,500 | Reduces the drop cooldown from 0.28s to 0.14s |
| Faster Pigeon Movement | $4,500 | Raises movement acceleration and speed cap |
| Faster Reload | $4,500 | Reduces reload time from 2.0s to 0.9s |

### Family options

Family options add companion birds to the flight. They also change the ammo cost because multiple birds drop payloads on each press.

| Option | Price | Birds | What changes |
|---|---:|---:|---|
| Impress a Partner | $10,000 | 3 | Partner plus a baby bird |
| Impress a Partner + Condoms | $15,000 | 2 | Partner; no baby bird |
| Lesbian Partners | $15,000 | 2 | Partner configuration with its own color treatment |
| Gay Partners | $15,000 | 2 | Partner configuration with its own color treatment |

These options are available regardless of the selected character-gender setting. The family setup is saved, and you can switch between family options you have unlocked from the market.

### Cash and Respect+

- **Wallet cash:** reaching each new 30-point score milestone awards $5.
- **VIP hits:** VIP pedestrians multiply the payload's base score by 3.
- **Close-range hits:** hitting while near a pedestrian doubles that hit's score.
- **Rock hits:** an unblocked rock normally removes 10 HP and 10 score, and briefly locks payload drops.
- **Respect+:** hitting at least 3 distinct pedestrians in the same update awards +1 Respect+. A five-hit moment gets its own announcement but still awards +1 for that event.
- **Random reward:** spend 1 Respect+ to unlock one random item you do not yet own. Eligible rewards include payload sizes, sounds, drop modes, and upgrades.

### Redeem codes

Enter a code from **Market → `C`**. A successful new redemption costs **$1,000** in-game. Codes are converted to uppercase and spaces are ignored.

| Code | Unlocks |
|---|---|
| `PIGEON-PLUS` | Medium payload + Fart 1 sound |
| `SQUELCH-ME` | Fart 2 sound |
| `BIG-ONE` | Large payload |
| `BOMBS-AWAY` | MEGA payload + Fart 2 sound |

Codes can grant only items that are not already unlocked. Trying an invalid or already-redeemed code does not charge the wallet.

## Saves and privacy

Progress is stored locally in your home directory:

- `~/.pigeon_save.json` — best score, unlocks, selected payload, sound, drop mode, upgrades, Respect+, game mode, family configuration, and related progression.
- `~/.pigeon_wallet.json` — wallet balance plus a SHA-256 consistency hash.

There are no online accounts or server-side saves in the supplied code. The wallet hash is a basic consistency check, **not encryption or tamper-proof security**; anyone who can edit the local game files or save data can still change their local experience.

To reset your progress, choose **Clear User Data** in the main menu and press `Y` to confirm. This permanently resets the wallet, best score, unlocks, upgrades, Respect+, family setup, and selected game mode. Any other key cancels the reset.

## Audio assets

The current code expects these three music files inside `audio/` and checks for all three during startup. Filenames must match exactly, including spaces and emoji.

| File | Used for | Required? |
|---|---|---|
| `Star Wars Main Theme Cover (Handfarts).mp3` | Main-menu music | Yes |
| `🌿 Nature Soundscape Relaxing Bird Songs for Study & Meditation 10 Min Mix 🎶.mp3` | Gameplay music | Yes |
| `Romantic music sound effect.mp3` | Family animation scene | Yes |
| `fart.mp3` | Fart sound | Optional |
| `fart1.mp3` | Fart 1 sound | Optional |
| `fart2.mp3` | Fart 2 sound | Optional |

If a sound-effect file is missing, the game falls back to a terminal beep for that effect. Missing music files stop initialization with an error. Before publishing or distributing the project, confirm you have permission to redistribute each audio track. Replace tracks you are not licensed to share and update the filename constants in `pigeon.py`.

## Developer notes

PIGEON currently lives in one Python file. Its sections are separated by purpose—save/codes, audio, drawing helpers, game entities, game loop, and menus—so it can be run without a package build step.

### Useful extension points

- **Game balance:** constants near the top of `pigeon.py` tune round length, HP, movement, projectile physics, rock behavior, boss stats, and cooldowns.
- **Market inventory:** `SIZES`, `SOUNDS`, `POOP_MODES`, `UPGRADES`, and `FAMILY_OPTIONS` define the purchasable content; price dictionaries/constants define costs.
- **Pedestrian behavior:** `Person.KINDS` controls pedestrian archetypes, colors, movement ranges, and score multipliers.
- **Boss behavior:** the `Boss` class and `BOSS_*` constants govern The Mayor.
- **Progress validation:** `load_save()` normalizes save values and filters unlocks against the current item definitions. Update validation when introducing new saved items.
- **Redeem codes:** `CODES` maps SHA-256 hashes to unlock IDs. The helper below prints the normalized hash for a code:

  ```bash
  python pigeon.py --hash "YOUR-CODE"
  ```

  Add that hash and the intended unlock IDs to `CODES`. IDs follow patterns such as `size:large` and `sound:fart2`; ensure the item exists and save validation accepts it.

### Suggested test checklist

When changing progression or collision logic, test these paths independently:

- Timed mode starts its clock only after the first successful drop; Endless does not count down.
- Repeated pellets do not count the same pedestrian twice toward a combo in one update.
- Single, Double, Triple, and Shower use the expected amount of ammo with and without family companions.
- Buying, equipping, unequipping, and resetting each upgrade behaves consistently.
- Boss spawn threshold, boss hits, defeat reward, and umbrella blocks behave as intended.
- Respect+ is awarded for multi-target hits and cannot be spent when no eligible rewards remain.
- Clear User Data resets both progress and wallet, while cancelling leaves them untouched.
- Missing optional sound effects fall back cleanly; missing required music files produce a useful error.

## Troubleshooting

**The game says the terminal is too small.**  
Resize the terminal to at least **70 × 20** characters. A wider terminal makes the city and HUD easier to read.

**Windows says `curses` is missing.**  
Run `py -m pip install windows-curses pygame`, then launch again.

**The game cannot find music.**  
Confirm all three required music files are inside `audio/` beside `pigeon.py`. Check spelling, spaces, punctuation, and emoji. You can alternatively rename your files and update `MENU_MUSIC_FILE`, `BACKGROUND_MUSIC_FILE`, or `ROMANTIC_MUSIC_FILE` in the script.

**Audio fails to initialize.**  
Check that the system has an available audio output device and that Pygame can initialize its mixer.

**Colors are missing or the display is cramped.**  
Use a terminal emulator with color support and a larger window. The game attempts to fall back if terminal color support is unavailable.

## License

No license file was provided with the supplied project. Until a `LICENSE` file is added, do not assume that the code or bundled assets are available for reuse or redistribution. Choose a license and add its full text before inviting outside contributions.

---

<p align="center">
  <sub>Made for terminals. Best enjoyed with a little space, a working audio device, and absolutely no respect for city planning.</sub>
</p>
