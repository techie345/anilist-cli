# anilist-cli

A small command-line tool for checking new anime/manga releases and your
AniList lists, with colorful `rich`-rendered tables.

- **Anime data & user lists** come from the [AniList GraphQL API](https://docs.anilist.co/) (no API key needed for public data).
- **Manga chapter releases** come from the [MangaDex API](https://api.mangadex.org/docs/), since AniList doesn't track individual chapter drops.

## Installation

Requires Python 3.8+. This is a pure-Python package, so the same install
methods work on Linux, macOS, and Windows.

### Linux (CachyOS / Arch, fish shell)

**pipx (recommended)** — installs into its own isolated environment and puts
`anilist-cli` on your PATH:

```fish
sudo pacman -S python-pipx
pipx ensurepath   # restart your shell after this

cd anilist-cli
pipx install .

anilist-cli --help
```

Upgrade after changes: `pipx install --force .`
Remove: `pipx uninstall anilist-cli`

**Or a regular venv:**

```fish
cd anilist-cli
python -m venv anilist-venv
source anilist-venv/bin/activate.fish
pip install -r requirements.txt
pip install .

anilist-cli --help
```

### Windows (PowerShell)

**pipx (recommended)**:

```powershell
# requires Python from python.org or the Microsoft Store, with "Add to PATH" enabled
python -m pip install --user pipx
python -m pipx ensurepath   # then open a new PowerShell window

cd anilist-cli
pipx install .

anilist-cli --help
```

Upgrade after changes: `pipx install --force .`
Remove: `pipx uninstall anilist-cli`

**Or a regular venv:**

```powershell
cd anilist-cli
python -m venv anilist-venv
.\anilist-venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install .

anilist-cli --help
```

If `anilist-cli` isn't found after a venv install, use `python -m anilist_cli.main ...`
instead — same commands, just prefixed.

### Run without installing (any OS)

```bash
cd anilist-cli
pip install -r requirements.txt
python -m anilist_cli.main --help
```

## Commands

### New releases

**Recently aired anime episodes** (last 24h by default):

```bash
anilist-cli releases anime
anilist-cli releases anime --hours 12 --limit 30
```

Only show episodes for anime you're actively watching/rewatching
(`CURRENT`/`REPEATING` on your AniList list):

```bash
anilist-cli releases anime --following
anilist-cli releases anime --following --username YourAniListUsername
```

**Upcoming anime episodes**:

```bash
anilist-cli releases anime --upcoming --hours 48
anilist-cli releases anime --upcoming --following
```

**Recently released manga chapters** (via MangaDex, default source):

```bash
anilist-cli releases manga
anilist-cli releases manga --lang en --limit 25
```

Only show chapters for manga you're actively reading/rereading. This
matches via the AniList↔MangaDex link on each series where available,
falling back to a title match:

```bash
anilist-cli releases manga --following
```

**Newly added / currently releasing manga series** (via AniList instead):

```bash
anilist-cli releases manga --source anilist
anilist-cli releases manga --source anilist --following
```

### Your list (watching / reading / planning / etc.)

By default this shows your AniList **anime** list. The AniList list must be
public (this is the default for most accounts).

```bash
anilist-cli list YourAniListUsername
anilist-cli list YourAniListUsername --type MANGA
anilist-cli list YourAniListUsername --status CURRENT
anilist-cli list YourAniListUsername --type MANGA --status PLANNING
```

Valid `--status` values: `CURRENT` (watching/reading), `PLANNING`,
`COMPLETED`, `DROPPED`, `PAUSED`, `REPEATING`.

### Save a default username

So you don't have to type your username every time:

```bash
anilist-cli config set-username YourAniListUsername
anilist-cli config show

# now this works:
anilist-cli list
anilist-cli list --type MANGA --status CURRENT
```

Config is stored as JSON at `~/.config/anilist-cli/config.json` (on Windows
this resolves to `C:\Users\<you>\.config\anilist-cli\config.json`).

## Project layout

```
anilist-cli/
├── anilist_cli/
│   ├── __init__.py
│   ├── main.py          # CLI commands (click)
│   ├── anilist_api.py   # AniList GraphQL queries
│   ├── mangadex_api.py  # MangaDex chapter feed
│   ├── display.py       # rich tables / TUI rendering
│   └── config.py        # local config (default username)
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Notes / possible extensions

- Listing private lists isn't supported since that requires OAuth; only
  public AniList lists can be queried by username.
- `--following` considers anything in your `CURRENT` or `REPEATING` status
  as "followed".
- For manga `--following`, MangaDex/AniList matching relies on the
  `links.al` field MangaDex stores on a manga (when present), with a
  title-match fallback. A small number of series may not match if MangaDex
  has no AniList link and the titles differ between the two sites.
- `releases manga --source mangadex` filters to English chapters by default;
  change with `--lang` (e.g. `--lang es`, `--lang ja`).
- This intentionally keeps things to non-interactive, colorized table output
  (a "simple TUI"). It could be extended into a full interactive app (e.g.
  with `textual`) for scrolling/paging/search if desired.
