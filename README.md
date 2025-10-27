# Pickleball League - Phase 1.5 (Automated Web Server)

Complete pickleball league management system with automated match submission and ranking updates.

## Features

- **Web-based Match Recording**: Record matches through a web form
- **Automatic Ranking Updates**: Rankings regenerate automatically after each match
- **Player Management**: Manage players via CSV file
- **Multi-Game Support**: Record up to 3 games per match (best of 3)
- **Beautiful UI**: Custom theme with your league colors
- **No Database Required**: Still uses YAML files (easy migration to Phase 2)

## Deployment Options

### Local Setup (Default)
This guide covers the local setup - perfect for private league use on your computer or local network.

### Cloud Deployment (Optional)
If you want to deploy to Google Cloud Run with Cloud Storage:
- See [CLOUD_RUN_DEPLOYMENT.md](./CLOUD_RUN_DEPLOYMENT.md) for step-by-step instructions
- All features work the same, just hosted in the cloud
- Accessible from anywhere, not just your local network
- Estimated cost: < $5/month

The application supports both modes - you can switch between local and cloud by setting the `USE_GCS` environment variable.

## Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements-server.txt
```

This installs:
- `flask` - Web server
- `pyyaml` - YAML file handling

### 2. Configure Your League

Edit `config.json` to customize:

```json
{
  "league_name": "Your League Name",
  "league_description": "Your League Description",
  "ranking_methods": [
    "ELO Rating System",
    "Points Difference",
    "Win/Loss Record"
  ],
  "colors": {
    "primary": "#082946",  // Dark blue
    "accent": "#e0672b"    // Orange
  }
}
```

### 3. Add Players

Edit `players.csv` (one player name per line):

```
Alice Johnson
Bob Smith
Carol White
Dave Brown
```

**Important**: Edit this file directly - no web interface needed. Changes are picked up immediately.

### 4. Start the Server

```bash
python3 server.py
```

You'll see:

```
====================================
Pickleball League Server
====================================
...
Open in your browser:
  Rankings: http://localhost:8000/
  Record Match: http://localhost:8000/record
====================================
```

### 5. Use the System

1. **View Rankings**: Visit `http://localhost:8000/`
2. **Record Match**: Click "Record New Match" or visit `http://localhost:8000/record`
3. **Fill Form**:
   - Select match type (Singles/Doubles)
   - Choose players from dropdowns
   - Enter scores for up to 3 games
   - Click "Submit Match"
4. **Done!** Rankings update automatically and you're redirected

## Match Recording

### Singles Match

1. Select "Singles Match"
2. Choose Player 1 and Player 2 from dropdowns
3. Enter game scores:
   - Game 1: Required
   - Game 2: Optional
   - Game 3: Optional
4. Winner determined automatically (who wins 2+ games)
5. Submit

### Doubles Match

1. Select "Doubles Match"
2. Choose 2 players for Team 1
3. Choose 2 players for Team 2
4. Enter game scores (1-3 games)
5. Winner determined automatically
6. Submit

### Score Entry

- Always shows 3 game inputs
- Leave blank if game wasn't played
- At least 1 game required
- Winner = who wins most games

## File Structure

```
pickleball-league/
├── server.py                  # Flask web server
├── players.csv                # Player list (edit directly)
├── config.json                # League configuration
├── match-form.html            # Match recording form
├── index.html                 # Rankings display (auto-generated)
├── rankings.json              # Rankings data (auto-generated)
├── requirements-server.txt    # Python dependencies
├── matches/
│   ├── singles/              # Singles match YAML files
│   └── doubles/              # Doubles match YAML files
└── scripts/
    ├── generate_rankings.py  # Ranking calculator
    └── build_pages.py        # HTML generator
```

## YAML File Format

The system automatically creates these files when you submit matches.

### Singles (New Multi-Game Format)

```yaml
date: '2025-10-22'
players:
  - Alice Johnson
  - Bob Smith
games:
  - player1_score: 11
    player2_score: 7
  - player1_score: 9
    player2_score: 11
  - player1_score: 11
    player2_score: 5
winner: Alice Johnson  # Won 2-1
```

### Doubles (New Multi-Game Format)

```yaml
date: '2025-10-22'
team1:
  - Alice Johnson
  - Bob Smith
team2:
  - Carol White
  - Dave Brown
games:
  - team1_score: 11
    team2_score: 8
  - team1_score: 9
    team2_score: 11
  - team1_score: 11
    team2_score: 7
winner_team: 1  # Team 1 won 2-1
```

**Note**: The system is backward compatible with old single-score format.

## Managing Players

### Add Players

Edit `players.csv`:

```bash
nano players.csv
```

Add one name per line:

```
Alice Johnson
Bob Smith
Carol White
```

Save and close. Changes are picked up immediately (no server restart needed).

### Remove Players

Simply delete the line from `players.csv`.

**Warning**: Removing a player doesn't delete their match history. Their past matches remain in the YAML files.

## Customization

### Change Theme Colors

Edit `config.json`:

```json
{
  "colors": {
    "primary": "#082946",   // Your primary color
    "accent": "#e0672b"     // Your accent color
  }
}
```

Then regenerate pages:

```bash
python3 scripts/build_pages.py
```

### Change League Info

Edit `config.json`:

```json
{
  "league_name": "Your League Name",
  "league_description": "Your Description"
}
```

### Add Logo

1. Save your logo as `static/logo.png`
2. Edit `build_pages.py` and `match-form.html`
3. Replace `[LOGO]` placeholder with `<img src="/static/logo.png">`

## Troubleshooting

### Players not showing in dropdown

- Check `players.csv` exists
- Ensure one name per line
- No empty lines
- Restart server if needed

### Matches not saving

- Check console output for errors
- Ensure `matches/singles/` and `matches/doubles/` directories exist
- Check file permissions

### Rankings not updating

- Check if Python scripts run without errors:
  ```bash
  python3 scripts/generate_rankings.py
  python3 scripts/build_pages.py
  ```
- Look for error messages in server console

### Port 8000 already in use

Change port in `server.py` line 243:

```python
app.run(host='0.0.0.0', port=8001, debug=True)  # Use 8001 instead
```

Also update line 235 with the new port in the startup message.

## API Endpoints

If you want to integrate with other tools:

- `GET /` - Rankings HTML page
- `GET /record` - Match recording form
- `GET /api/players` - JSON list of players
- `POST /api/matches` - Submit match (JSON)
- `GET /rankings.json` - Rankings data (JSON)

### Example: Submit Match via API

```bash
curl -X POST http://localhost:8000/api/matches \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-10-22",
    "type": "singles",
    "players": ["Alice Johnson", "Bob Smith"],
    "games": [
      {"player1_score": 11, "player2_score": 7},
      {"player1_score": 9, "player2_score": 11},
      {"player1_score": 11, "player2_score": 5}
    ],
    "winner": "Alice Johnson"
  }'
```

## Migration to Phase 2 (Backend Database)

When you're ready for more features:

1. All YAML files are preserved
2. Use existing `import_to_database.py` script
3. Imports all matches to SQLite
4. Switch to `league-app-new` backend
5. Get features like user auth, APIs, real-time updates

Your data is never lost!

## Tips

- **Backup**: Commit `matches/` directory to Git regularly
- **Player Names**: Be consistent with spelling and capitalization
- **Testing**: Use `players.csv` to add test players first
- **Access from other devices**: Use `http://YOUR_IP:8000/` instead of `localhost`

## Support

- Check server console for error messages
- Validate YAML files if ranking generation fails
- Ensure Python 3.7+ is installed

## License

Open source - use freely for your league!
