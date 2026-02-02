# Yaque

Yet Another Queens Game - A puzzle game for Android where you place queens on a board so that no two queens attack each other or are adjacent.

## Features

- Daily puzzles in 3 sizes (6x6, 7x7, 8x8)
- Random puzzle generation with selectable size
- Calendar view with completion tracking (gold queens for completed puzzles)
- Game state persistence - resume where you left off
- Share puzzles via QR code or custom URL scheme (`yaque://start?game=CODE`)
- Local database tracking play history and best times
- Undo/redo support
- Victory celebration with golden rotating queens
- Works offline - no network required

## Building

### Requirements

- Python 3.11+
- Kivy
- Buildozer (for Android builds)

### Run locally

```bash
pip install kivy pillow qrcode
python src/main.py
```

### Build Android APK

```bash
buildozer android debug
```

Or push to GitHub - the CI workflow builds APKs automatically.

## Development

### Run tests

```bash
pip install pytest pytest-xdist
python -m pytest tests/ -n auto -v
```

### Project structure

```
src/
  app.py          - Main application
  game.py         - Puzzle generation and solving
  game_encoding.py - Compact puzzle encoding/decoding
  database.py     - Local SQLite for play history
  board_widget.py - Game board UI
  screens/        - App screens (menu, game, calendar)
  popups.py       - Dialogs and popups
  assets/         - Images, fonts, icons
tests/            - Unit tests
```

## TODO

- [x] APK build process on GitHub
- [x] Game repeatability via random seed
- [x] SQLite database of played games
- [x] Main screen: 3 daily challenges, calendar, random game, exit
- [x] Before time starts show only gray game field
- [x] Play/pause button to show/hide the game and control clock
- [x] Share button with QR code and custom URL scheme
- [x] Icon buttons (play, pause, undo, redo, share)
- [x] Rounded green buttons
- [x] Victory celebration effect
- [x] Adaptive icon for Android
- [x] Click on hidden board to start
- [x] Game size selection for random puzzles
- [x] Calendar view with completion tracking
- [x] Game state persistence (resume daily puzzles)
- [ ] Streak counter
- [ ] Fun rating after completion
- [ ] Pick a license
