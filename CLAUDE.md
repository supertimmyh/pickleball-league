# Pickleball League - Project Memory & Implementation Guide

**Last Updated:** October 22, 2025
**Current Phase:** Phase 1.5 (Automated YAML-based with Web Server)
**Status:** ✅ Fully Functional

---

## 🎯 Project Overview

A pickleball league management system that evolved from a simple YAML-based approach to an automated web application, with a clear migration path to a full backend database system.

### Evolution Path
1. **Phase 1** (Initial): Pure YAML files, manual HTML generation
2. **Phase 1.5** (Current): Flask web server with YAML backend - AUTOMATED
3. **Phase 2** (Future): Full backend with SQLite database (already built in `league-app-new/`)

---

## 🏗️ Current Architecture (Phase 1.5)

### Technology Stack
- **Backend:** Python Flask web server
- **Data Storage:** YAML files (Git-trackable, human-readable)
- **Player Registry:** CSV file (`players.csv`)
- **Ranking Algorithm:** ELO rating system (K=32, default 1200)
- **Frontend:** Vanilla HTML/CSS/JavaScript (no build step needed)

### Key Features Implemented
- ✅ Web-based match recording with auto-submit
- ✅ Player dropdowns (populated from CSV)
- ✅ Multi-game support (best of 3, blank games ignored)
- ✅ Auto-calculate winner based on games won
- ✅ Auto-save YAML files
- ✅ Auto-regenerate rankings after each match
- ✅ Custom theme (Dark Blue #082946 & Orange #e0672b)
- ✅ Logo placeholder for club branding
- ✅ Configurable league info via `config.json`
- ✅ Backward compatible with old single-score YAML format

---

## 📁 Project Structure

```
pickleball-league/
├── server.py                    # Flask web server (port 8000)
├── players.csv                  # Player registry (edit directly)
├── config.json                  # League configuration
├── match-form.html              # Match recording form
├── index.html                   # Rankings display (auto-generated)
├── rankings.json                # Rankings data (auto-generated)
├── requirements.txt             # Phase 1 dependencies (pyyaml)
├── requirements-server.txt      # Phase 1.5 dependencies (flask, pyyaml)
├── update_rankings.sh           # Convenience script for manual updates
├── matches/
│   ├── singles/                 # Singles match YAML files
│   └── doubles/                 # Doubles match YAML files
├── scripts/
│   ├── generate_rankings.py    # Ranking calculator (multi-game support)
│   ├── build_pages.py          # HTML generator (themed)
│   └── import_to_database.py   # Migration script for Phase 2
├── README.md                    # Original Phase 1 documentation
├── README-SERVER.md             # Phase 1.5 complete documentation
├── QUICKSTART.md               # 5-minute setup guide
└── PROJECT_MEMORY.md           # This file
```

---

## 🔧 Critical Implementation Details

### 1. Server Port Configuration
**Current:** Port 8000 (changed from 5000 due to conflict)
**Location:** `server.py` line 243
```python
app.run(host='0.0.0.0', port=8000, debug=True)
```

### 2. Match Form Defaults
- **Default Match Type:** Doubles (changed from Singles per user request)
- **Default Visible Section:** Doubles section shown, Singles hidden
- **Form Validation:** JavaScript-based (removed HTML `required` from Singles to avoid conflict)

### 3. Game Score Layout
**Header row structure:**
```
         [Player/Team Name]  [Player/Team Name]  ← Headers (bold, colored)
Game 1:       [11]               [7]
Game 2:       [9]                [11]
Game 3:       [11]               [5]
```

**Implementation:**
- Singles: Headers update dynamically when players selected
- Doubles: Static "Team 1" / "Team 2" headers
- CSS classes: `.score-header` and `.game-header`

### 4. YAML Format (Multi-Game)

**Singles:**
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
winner: Alice Johnson
```

**Doubles:**
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
winner_team: 1
```

### 5. Theme Colors
**Primary:** #082946 (Dark Blue)
**Accent:** #e0672b (Orange)

Applied in:
- `match-form.html` CSS
- `scripts/build_pages.py` (reads from `config.json`)

### 6. Player Management
- **File:** `players.csv` (one name per line)
- **Edit:** Directly with text editor (nano, vim, VS Code)
- **Auto-reload:** Server reads CSV on each `/api/players` request
- **No restart needed** when adding/removing players

---

## 🚀 How to Run

### Quick Start
```bash
cd pickleball-league
pip3 install -r requirements-server.txt
python3 server.py
```

### Access URLs
- Rankings: http://localhost:8000/
- Record Match: http://localhost:8000/record
- API (players): http://localhost:8000/api/players
- API (submit match): POST http://localhost:8000/api/matches

### From Other Devices
1. Find your computer's IP: `ifconfig | grep "inet "`
2. Use: `http://YOUR_IP:8000/`

---

## 🐛 Known Issues & Solutions

### Issue 1: Port 8000 Already in Use
**Solution:** Change port in `server.py` line 243
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # Or any other port
```
Also update line 235 to match new port in the console message.

### Issue 2: Form Won't Submit (Validation Error)
**Cause:** HTML5 `required` attribute on hidden fields
**Solution:** Already fixed - removed `required` from Singles fields (line 330, 337)
**Validation:** Now handled by JavaScript based on active match type

### Issue 3: Players Not Loading
**Check:**
1. `players.csv` exists
2. Format is correct (one name per line, no commas)
3. No empty lines
4. Server is running

### Issue 4: Rankings Not Updating
**Check:**
1. Console output for Python script errors
2. `matches/` directory permissions
3. PyYAML is installed: `pip3 install pyyaml`

---

## 📝 Configuration Files

### config.json
```json
{
  "league_name": "Pickleball League",
  "league_description": "Competitive Pickleball League",
  "ranking_methods": [
    "ELO Rating System",
    "Points Difference",
    "Win/Loss Record"
  ],
  "colors": {
    "primary": "#082946",
    "accent": "#e0672b"
  },
  "elo_k_factor": 32,
  "default_rating": 1200
}
```

**What it controls:**
- League name in header
- League description in footer
- Ranking methods displayed in footer
- Theme colors throughout the app
- ELO algorithm parameters

### players.csv
```csv
Alice Johnson
Bob Smith
Carol White
Dave Brown
Eve Martinez
Frank Chen
```

**Rules:**
- One player name per line
- No headers
- No commas
- Consistent naming (case-sensitive)

---

## 🔄 Workflow

### Normal Operation
1. User visits `/record`
2. Selects match type (defaults to Doubles)
3. Selects players from dropdowns
4. Enters game scores (1-3 games)
5. Clicks "Submit Match"
6. **Backend automatically:**
   - Validates data
   - Creates YAML file
   - Runs `generate_rankings.py`
   - Runs `build_pages.py`
   - Redirects to updated rankings

### Manual Operations
```bash
# Add players
nano players.csv

# Regenerate rankings manually
python3 scripts/generate_rankings.py
python3 scripts/build_pages.py

# Or use convenience script
./update_rankings.sh

# View logs
# Check server console for errors
```

---

## 🛣️ Future Roadmap

### Phase 2: Full Backend Migration (When Needed)

**Already Built:** `league-app-new/` directory contains:
- Express.js REST API
- SQLite database with schema
- React TypeScript frontend
- Admin dashboard
- Full CRUD operations

**Migration Steps:**
1. Run import script:
   ```bash
   python3 scripts/import_to_database.py
   ```
2. Start backend:
   ```bash
   cd ../league-app-new/backend
   node app.js
   ```
3. Start frontend:
   ```bash
   cd ../frontend
   npm start
   ```

**What You Gain:**
- User authentication
- Multiple leagues support
- Real-time updates
- Advanced analytics
- Mobile-friendly React app
- API for external integrations

**What You Keep:**
- All match history (imported from YAML)
- All player data
- Same ranking algorithm
- Same theme colors

### Potential Enhancements (Phase 1.5)

**Easy Wins:**
1. **Add logo image:**
   - Replace `[LOGO]` placeholder with `<img src="/static/logo.png">`
   - Save logo as `static/logo.png`

2. **Match history page:**
   - Create `match-history.html`
   - Display all YAML files in reverse chronological order
   - Link from rankings page

3. **Player statistics page:**
   - Individual player stats
   - Head-to-head records
   - Recent match history

4. **Export rankings to PDF:**
   - Add Python library (ReportLab)
   - Generate PDF button on rankings page

5. **Email notifications:**
   - Send rankings to league members
   - Match result confirmations

**Medium Effort:**
1. **Undo last match:**
   - Delete most recent YAML file
   - Regenerate rankings
   - Admin authentication needed

2. **Edit match results:**
   - Web form to modify existing YAML files
   - Require admin password

3. **Scheduling system:**
   - Future matches
   - Calendar view
   - Email reminders

4. **Multiple leagues:**
   - Separate directories for each league
   - League selector on homepage

**Big Features (Consider Phase 2 Instead):**
- User accounts with login
- Real-time leaderboard updates
- Mobile app
- Tournament bracket generation
- Payment integration
- Social features (comments, reactions)

---

## 📚 Dependencies

### Python Packages
```
flask>=3.0.0         # Web server
pyyaml>=6.0          # YAML file handling
```

### System Requirements
- Python 3.7+
- Modern web browser
- Network access (for multi-device use)

### Optional
- Git (for version control of matches)
- Text editor (nano, vim, VS Code) for config files

---

## 🔐 Security Considerations

### Current (Phase 1.5)
- **No authentication** - anyone can submit matches
- **No user accounts** - open access
- **No input sanitization** - trusts player names from CSV
- **Local network only** - not exposed to internet

### For Production Use
If deploying publicly:
1. Add authentication (admin password for match submission)
2. Validate/sanitize player names
3. Rate limiting on API endpoints
4. HTTPS with SSL certificate
5. Consider migrating to Phase 2 for proper user management

### Current Recommendation
**Best for:** Private local network use (home league, club)
**Not recommended for:** Public internet deployment without modifications

---

## 🎨 Customization Guide

### Change League Name
Edit `config.json`:
```json
{
  "league_name": "Your League Name Here",
  "league_description": "Your Description Here"
}
```
Then regenerate pages: `python3 scripts/build_pages.py`

### Change Colors
Edit `config.json`:
```json
{
  "colors": {
    "primary": "#YourColorHere",
    "accent": "#YourColorHere"
  }
}
```
Then regenerate pages.

### Change ELO Parameters
Edit `config.json`:
```json
{
  "elo_k_factor": 32,      // Higher = more volatile ratings
  "default_rating": 1200   // Starting rating for new players
}
```
Then regenerate rankings: `python3 scripts/generate_rankings.py`

### Change Server Port
Edit `server.py` line 243:
```python
app.run(host='0.0.0.0', port=YOUR_PORT, debug=True)
```
Also update line 235 console message.

### Add Logo
1. Save logo as `static/logo.png`
2. Edit `match-form.html` line 296:
   ```html
   <img src="/static/logo.png" alt="Logo" style="width: 80px; height: 80px; border-radius: 50%;">
   ```
3. Edit `scripts/build_pages.py` logo placeholder section similarly

---

## 📊 Data Management

### Backup Strategy
**Important:** Regularly backup these directories:
```
matches/         # All match history
players.csv      # Player roster
config.json      # League settings
```

**Recommended:**
```bash
# Git-based backup
git init
git add matches/ players.csv config.json
git commit -m "Backup matches and players"
git push origin main

# Or manual backup
tar -czf backup-$(date +%Y%m%d).tar.gz matches/ players.csv config.json
```

### Data Recovery
If rankings get corrupted:
1. Delete `rankings.json` and `index.html`
2. Run `python3 scripts/generate_rankings.py`
3. Run `python3 scripts/build_pages.py`
4. All data reconstructed from YAML files

---

## 🧪 Testing

### Manual Testing Checklist
- [ ] Start server successfully
- [ ] Load rankings page
- [ ] Load match form
- [ ] Player dropdowns populated
- [ ] Submit singles match
- [ ] Submit doubles match
- [ ] Rankings update automatically
- [ ] Match appears in YAML files
- [ ] Access from another device
- [ ] Add new player to CSV
- [ ] New player appears in dropdowns

### Test Data
Sample players already in `players.csv`:
- Alice Johnson
- Bob Smith
- Carol White
- Dave Brown
- Eve Martinez
- Frank Chen

Sample matches already exist in `matches/` for testing rankings.

---

## 🆘 Troubleshooting

### Server Won't Start
1. Check port not in use: `lsof -i :8000`
2. Kill conflicting process or change port
3. Check Python version: `python3 --version` (need 3.7+)
4. Reinstall dependencies: `pip3 install -r requirements-server.txt`

### Matches Not Saving
1. Check console for Python errors
2. Verify `matches/` directory exists and is writable
3. Check YAML syntax in error message
4. Ensure players exist in `players.csv`

### Rankings Not Calculating
1. Check `scripts/generate_rankings.py` runs: `python3 scripts/generate_rankings.py`
2. Look for YAML parsing errors
3. Verify all YAML files are valid
4. Check Python packages installed: `pip3 list | grep yaml`

### Browser Shows Old Rankings
1. Hard refresh: Ctrl+F5 (or Cmd+Shift+R on Mac)
2. Clear browser cache
3. Check `index.html` timestamp to verify it was regenerated
4. Check server console for script execution confirmation

---

## 📞 Quick Reference

### Important Files
| File | Purpose | Edit? |
|------|---------|-------|
| `server.py` | Web server | Only for port changes |
| `players.csv` | Player list | Yes - frequently |
| `config.json` | Settings | Yes - for customization |
| `match-form.html` | Match form | Only for UI changes |
| `scripts/generate_rankings.py` | Rankings | Only for algorithm changes |
| `scripts/build_pages.py` | HTML gen | Only for theme changes |

### Common Commands
```bash
# Start server
python3 server.py

# Add player
echo "New Player Name" >> players.csv

# Manual ranking update
python3 scripts/generate_rankings.py && python3 scripts/build_pages.py

# View recent matches
ls -lt matches/singles/ | head -5
ls -lt matches/doubles/ | head -5

# Check server logs
# (visible in terminal where server.py is running)
```

### API Endpoints
```
GET  /                      # Rankings page
GET  /record                # Match form
GET  /api/players           # Player list (JSON)
POST /api/matches           # Submit match (JSON)
GET  /rankings.json         # Rankings data
```

---

## 🎓 Learning Resources

If you need to modify the code later:

**Flask (Python web framework):**
- Official docs: https://flask.palletsprojects.com/
- Tutorial: https://flask.palletsprojects.com/tutorial/

**YAML:**
- Syntax guide: https://yaml.org/
- Python PyYAML: https://pyyaml.org/wiki/PyYAMLDocumentation

**ELO Rating System:**
- Wikipedia: https://en.wikipedia.org/wiki/Elo_rating_system
- Implementation in `scripts/generate_rankings.py` lines 11-19

**Frontend:**
- Vanilla JavaScript (no framework)
- Bootstrap-inspired CSS (custom, no library)
- Fetch API for server communication

---

## ✅ Final Checklist for Deployment

Before giving to league members:

- [ ] Add your league name to `config.json`
- [ ] Add all players to `players.csv`
- [ ] Test match submission (singles and doubles)
- [ ] Verify rankings calculate correctly
- [ ] Add your logo (optional)
- [ ] Change theme colors if desired (optional)
- [ ] Set up regular backups (Git or manual)
- [ ] Note your server's IP address for sharing
- [ ] Create simple instructions for users
- [ ] Test from multiple devices

---

## 📝 Change Log

### October 22, 2025
- ✅ Implemented Phase 1.5 with Flask server
- ✅ Added multi-game support (best of 3)
- ✅ Implemented player dropdowns from CSV
- ✅ Applied custom theme (dark blue & orange)
- ✅ Changed default to doubles match
- ✅ Added column headers for game scores
- ✅ Fixed form validation (removed HTML required from singles)
- ✅ Changed server port to 8000
- ✅ Created comprehensive documentation

### Future Changes
- Log any modifications here for reference

---

## 🎯 Success Metrics

Current system successfully handles:
- ✅ Automatic match recording
- ✅ Real-time ranking updates
- ✅ Multi-device access
- ✅ Player management
- ✅ Data persistence
- ✅ Professional UI/UX

**System is production-ready for local league use!**

---

**Remember:** This is Phase 1.5 - simple but functional. When you need more features (user accounts, mobile app, etc.), migrate to Phase 2 using the existing `league-app-new/` backend. All your data migrates seamlessly via `scripts/import_to_database.py`.

**Enjoy your league!** 🏓
