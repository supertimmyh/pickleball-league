# Pickleball League Management System

A simple, YAML-based league management system for tracking pickleball matches and rankings.

## Features

- **Simple Match Recording**: HTML form to record matches (no backend required)
- **ELO Rating System**: Automatic ranking calculation using ELO (K=32)
- **Singles & Doubles Support**: Track both singles and doubles matches
- **Beautiful Rankings Display**: Auto-generated HTML page with responsive design
- **Version Control Friendly**: All match data stored in YAML files (perfect for Git)

## Quick Start

### 1. Record a Match

Open `match-form.html` in your browser and fill in the match details:
- Select match type (Singles or Doubles)
- Enter match date
- Enter player names
- Enter final score (games to X format)

The form will generate YAML content for you to save.

### 2. Save Match Data

Create a YAML file in the appropriate directory:
- Singles: `matches/singles/YYYY-MM-DD-description.yml`
- Doubles: `matches/doubles/YYYY-MM-DD-description.yml`

Copy the generated YAML content into the file.

### 3. Generate Rankings

Run the ranking generation script:

```bash
python3 scripts/generate_rankings.py
```

This will:
- Process all match files
- Calculate ELO ratings
- Generate `rankings.json`

### 4. Build HTML Page

Generate the rankings webpage:

```bash
python3 scripts/build_pages.py
```

This creates `index.html` with beautiful rankings tables.

### 5. View Rankings

Open `index.html` in your browser to see the current standings!

## Match File Format

### Singles Match

```yaml
date: '2025-10-22'
players:
  - Alice Johnson
  - Bob Smith
score:
  player1_games: 11
  player2_games: 7
winner: Alice Johnson
```

### Doubles Match

```yaml
date: '2025-10-22'
team1:
  - Alice Johnson
  - Carol White
team2:
  - Bob Smith
  - Dave Brown
score:
  team1_games: 11
  team2_games: 9
winner_team: 1
```

## Directory Structure

```
pickleball-league/
├── matches/
│   ├── singles/           # Singles match YAML files
│   └── doubles/           # Doubles match YAML files
├── scripts/
│   ├── generate_rankings.py   # Calculate rankings
│   └── build_pages.py         # Generate HTML
├── match-form.html        # Match recording form
├── index.html             # Rankings display (generated)
├── rankings.json          # Rankings data (generated)
└── README.md             # This file
```

## Ranking System

- **Algorithm**: ELO rating system
- **K-Factor**: 32 (moderate volatility)
- **Default Rating**: 1200 (starting point for all players)
- **Calculations**: Rating updated after each match based on opponent strength

### Statistics Tracked

- **Rating**: ELO rating
- **W-L Record**: Wins and losses
- **Win %**: Win percentage
- **Games W-L**: Total games won and lost
- **Matches Played**: Total matches

## Migration to Backend (Phase 2)

When you're ready to add more features:

1. **Import existing data**: Use `league-app-new` backend with import script
2. **Activate API**: Your backend is already built in `../league-app-new/`
3. **Add features**: User authentication, real-time updates, etc.

The migration path preserves all your YAML data!

## Requirements

- Python 3.7+
- PyYAML library (`pip install pyyaml`)
- Modern web browser (for viewing HTML pages)

## Tips

- Commit YAML files to Git for full match history tracking
- Keep consistent player names (case-sensitive)
- Date format in filenames helps with chronological sorting
- Run ranking scripts after adding new matches

## License

Open source - use freely for your league!
