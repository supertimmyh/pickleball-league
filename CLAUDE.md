# Pickleball League - Project Memory & Implementation Guide

**Last Updated:** October 27, 2025
**Current Phase:** Phase 1.5 (Automated YAML-based with Web Server + Cloud Scheduler)
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
- ✅ Auto-save YAML files to GCS or local filesystem
- ✅ Scheduled ranking regeneration via Cloud Scheduler (prevents race conditions)
- ✅ Manual ranking regeneration via `/api/regenerate-rankings` endpoint
- ✅ File-based locking mechanism for concurrent instance safety
- ✅ Smart timestamp detection (skips regeneration if no new matches)
- ✅ Custom theme (Dark Blue #082946 & Orange #e0672b)
- ✅ Logo file serving from GCS
- ✅ Configurable league info via `config.json`
- ✅ Backward compatible with old single-score YAML format
- ✅ Comprehensive error logging and debug endpoints

---

## 📁 Project Structure

```
pickleball-league/
├── server.py                           # Flask web server (port 8000)
├── players.csv                         # Player registry (edit directly)
├── config.json                         # League configuration
├── match-form.html                     # Match recording form
├── index.html                          # Rankings display (auto-generated)
├── rankings.json                       # Rankings data (auto-generated)
├── last_generation.timestamp           # Timestamp of last ranking generation
├── rankings.lock                       # Lock file for concurrent safety
├── requirements.txt                    # Phase 1 dependencies (pyyaml)
├── requirements-server.txt             # Phase 1.5 dependencies (flask, pyyaml)
├── update_rankings.sh                  # Convenience script for manual updates
├── scheduled_ranking_update.sh         # Cloud Scheduler execution script
├── matches/
│   ├── singles/                        # Singles match YAML files
│   └── doubles/                        # Doubles match YAML files
├── scripts/
│   ├── generate_rankings.py           # Ranking calculator with locking & timestamps
│   ├── build_pages.py                 # HTML generator (themed)
│   └── import_to_database.py          # Migration script for Phase 2
├── static/
│   └── picktopia_logo.png             # Logo (served from container filesystem)
├── Dockerfile                          # Container image definition (copies static/ files)
├── README.md                           # Original Phase 1 documentation
├── README-SERVER.md                    # Phase 1.5 complete documentation
├── CLOUD-SCHEDULER-SETUP.md            # Cloud Scheduler setup guide
├── QUICKSTART.md                       # 5-minute setup guide
└── CLAUDE.md                           # This project memory file
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

### 7. Ranking Generation (Updated October 27, 2025)

**Previous Behavior (before optimization):**
- Match submitted → Rankings regenerated immediately → Page rebuilt
- Simple but causes race conditions on multi-instance Cloud Run

**Current Behavior (with Cloud Scheduler):**

**Match Submission Flow:**
1. User submits match via `/api/matches` endpoint
2. Server saves match YAML file to GCS (or local filesystem)
3. Returns immediately to user (no ranking update)
4. User sees match recorded instantly ✅

**Ranking Generation (Scheduled):**
1. **Cloud Scheduler** triggers daily at configured time (default: 2 AM UTC)
2. Calls POST `/api/regenerate-rankings` endpoint
3. `generate_rankings.py` executes with:
   - **Locking mechanism** - Acquires `rankings.lock` (prevents concurrent execution)
   - **Timestamp check** - Compares newest match vs last generation time
   - **Smart decision:**
     - If new matches exist → Regenerate rankings
     - If no new matches → Skip (efficient!)
   - **Timestamp save** - Records when generation happened
   - **Lock release** - Allows next job to run

**Manual Regeneration (Optional):**
Users can manually trigger ranking updates via:
```bash
curl -X POST https://your-cloud-run-url/api/regenerate-rankings
```

**Files Used:**
- `scripts/generate_rankings.py` - Contains locking and timestamp logic
- `scheduled_ranking_update.sh` - Shell script for Cloud Scheduler
- `last_generation.timestamp` - Records when rankings were last generated
- `rankings.lock` - Lock file for concurrent safety

**Benefits:**
- ✅ Eliminates race conditions (only one process at a time)
- ✅ Efficient (skips regeneration if no new matches)
- ✅ Scalable (works with multiple Cloud Run instances)
- ✅ User-friendly (match submission is instant)
- ✅ Logging (detailed error messages and debug endpoint at `/api/debug-gcs`)

**Setup:**
See `CLOUD-SCHEDULER-SETUP.md` for complete Cloud Scheduler configuration instructions.

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
- API (ranking regeneration): POST http://localhost:8000/api/regenerate-rankings

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
**Check (with Cloud Scheduler):**
1. Cloud Scheduler job is enabled and running
2. Check Cloud Run logs for `/api/regenerate-rankings` requests
3. Verify locking mechanism is working (no deadlocks)
4. See `CLOUD-SCHEDULER-SETUP.md` for troubleshooting

**Check (manual):**
1. Console output for Python script errors
2. `matches/` directory permissions
3. PyYAML is installed: `pip3 install pyyaml`
4. Lock file not stuck: `rm rankings.lock` if needed

### Issue 5: Static Files (Logo, etc.) Not Loading
**Architecture:** Static files are served from the **local container filesystem** (not GCS)
**How it works:**
1. Static files are copied into the Docker image via `Dockerfile` (line 17: `COPY static/ static/`)
2. Server serves files from the local `static/` directory
3. Fallback to GCS available if `USE_GCS=true` and local file not found

**Solution if files return 404:**
1. Ensure file exists locally: `ls -la static/picktopia_logo.png`
2. Verify `Dockerfile` includes `COPY static/ static/` (line 17)
3. Ensure Docker image was rebuilt after adding files
4. For Cloud Run: redeploy with `gcloud run deploy` to rebuild the container

**Example - Adding a new static file:**
```bash
# 1. Add file to local static/ directory
cp logo.png static/

# 2. Commit to git
git add static/
git commit -m "Add logo to static files"

# 3. Redeploy to Cloud Run
gcloud run deploy pickleball-league-app --source .

# 4. Access at /static/logo.png
```

**Debugging:** Check server console logs for "Serving static file from local filesystem:"

### Issue 6: Lock File Stuck (Rankings Not Updating)
**Cause:** Previous ranking generation crashed without releasing lock
**Solution:**
```bash
# Remove stuck lock file (safe if no other process is running)
rm rankings.lock

# Or on GCS:
gsutil rm gs://pickleball-config-data/rankings.lock
```

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

### Normal Operation (Match Submission)
1. User visits `/record`
2. Selects match type (defaults to Doubles)
3. Selects players from dropdowns
4. Enters game scores (1-3 games)
5. Clicks "Submit Match"
6. **Backend immediately:**
   - Validates data
   - Creates YAML file (saves to GCS or local filesystem)
   - Returns success to user ✅
   - **Does NOT regenerate rankings** (prevents race conditions)

### Ranking Generation (Scheduled or Manual)

**Automatic (Cloud Scheduler - Recommended):**
1. Cloud Scheduler triggers at configured time (default: 2 AM UTC)
2. Calls POST `/api/regenerate-rankings`
3. `generate_rankings.py` runs with locking and smart timestamp detection
4. Only regenerates if new matches exist (efficient!)
5. Saves new rankings to GCS or local filesystem

**Manual Trigger:**
```bash
# Trigger via curl
curl -X POST https://your-cloud-run-url/api/regenerate-rankings

# Or run locally
python3 scripts/generate_rankings.py
python3 scripts/build_pages.py
```

### Manual Operations
```bash
# Add players
nano players.csv

# Regenerate rankings and pages manually
python3 scripts/generate_rankings.py
python3 scripts/build_pages.py

# Or use convenience script
./update_rankings.sh

# Debug GCS connectivity
curl https://your-cloud-run-url/api/debug-gcs

# View logs (local development)
tail -f scheduled_update.log
```

### Key Differences from Previous Version
| Aspect | Before | Now |
|--------|--------|-----|
| **Match Submission** | Slow (waits for ranking update) | Fast (returns immediately) |
| **Ranking Update** | Immediate (on every match) | Scheduled (once daily or manual) |
| **Race Conditions** | Possible on multi-instance | Prevented by locking |
| **Efficiency** | Regenerates every time | Skips if no new matches |
| **User Experience** | Wait for response | Instant response |

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

### Add or Update Static Files (Logo, Images, etc.)

**How static files work:**
- All files in the `static/` directory are served at `/static/filename`
- Files are **included in the Docker image** via `Dockerfile` line 17
- Changes require redeploying to Cloud Run

**Steps to add/update a static file:**

1. **Add the file locally:**
   ```bash
   # Example: add a new logo
   cp your-logo.png static/picktopia_logo.png
   ```

2. **HTML files already reference the correct path:**
   ```html
   <!-- match-form.html and generated index.html -->
   <img src="/static/picktopia_logo.png" alt="Logo">
   ```
   No HTML edits needed if you keep the same filename!

3. **For a different filename, edit HTML references:**
   - `match-form.html` (line ~315)
   - `scripts/build_pages.py` (update the img src in the template)

4. **Deploy to Cloud Run:**
   ```bash
   git add static/
   git commit -m "Update logo"
   gcloud run deploy pickleball-league-app --source .
   ```

**Local testing:**
```bash
# Start server
python3 server.py

# Test static file
curl http://localhost:8000/static/picktopia_logo.png
```

**Verify in Cloud Run:**
```bash
curl https://pickleball-league-app-415494410673.us-central1.run.app/static/picktopia_logo.png
```

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
GET  /                           # Rankings page
GET  /record                     # Match form
GET  /api/players                # Player list (JSON)
POST /api/matches                # Submit match (JSON) - saves match only
POST /api/regenerate-rankings    # Manually trigger ranking generation
GET  /api/debug-gcs              # Debug GCS connectivity (testing only)
GET  /rankings.json              # Rankings data
GET  /static/<path:path>         # Serve static files (from container filesystem or GCS fallback)
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

### October 28, 2025 - Static File Serving Fix
- ✅ Fixed logo and static file serving from container filesystem instead of GCS
- ✅ Updated `Dockerfile` to include `COPY static/ static/` (line 17)
- ✅ Modified `serve_static()` function to prioritize local filesystem with GCS fallback
- ✅ Tested logo serving locally (HTTP 200 OK)
- ✅ Updated CLAUDE.md documentation for static files
- ✅ Created comprehensive static file handling guide

### October 27, 2025 - Race Condition Optimization
- ✅ Implemented Cloud Scheduler integration for scheduled ranking generation
- ✅ Added file-based locking mechanism (prevents concurrent execution)
- ✅ Implemented timestamp detection (skips regeneration if no new matches)
- ✅ Separated match submission from ranking generation
- ✅ Created `/api/regenerate-rankings` POST endpoint for manual triggering
- ✅ Created `/api/debug-gcs` endpoint for GCS connectivity troubleshooting
- ✅ Enhanced error logging in GCS file operations
- ✅ Fixed Flask static_folder configuration for GCS file serving
- ✅ Created `scheduled_ranking_update.sh` for Cloud Scheduler
- ✅ Created comprehensive `CLOUD-SCHEDULER-SETUP.md` guide
- ✅ Updated project memory with new workflow documentation

### October 22, 2025 - Initial Phase 1.5 Release
- ✅ Implemented Phase 1.5 with Flask server
- ✅ Added multi-game support (best of 3)
- ✅ Implemented player dropdowns from CSV
- ✅ Applied custom theme (dark blue & orange)
- ✅ Changed default to doubles match
- ✅ Added column headers for game scores
- ✅ Fixed form validation (removed HTML required from singles)
- ✅ Changed server port to 8000
- ✅ Created comprehensive documentation

---

## 🎯 Success Metrics

Current system successfully handles:
- ✅ Automatic match recording (instant, no wait)
- ✅ Scheduled ranking updates (daily via Cloud Scheduler)
- ✅ Manual ranking regeneration (on-demand via API)
- ✅ Concurrent instance safety (file-based locking)
- ✅ Efficient processing (smart timestamp detection)
- ✅ Multi-device access
- ✅ Player management
- ✅ Data persistence (YAML + GCS)
- ✅ Professional UI/UX with logo support
- ✅ Comprehensive error logging and debugging
- ✅ GCS integration with fallback to local filesystem

**System is production-ready for cloud deployment with multi-instance safety!**
**Optimized for race condition prevention and efficient resource usage.**

---

**Remember:** This is Phase 1.5 - simple but functional. When you need more features (user accounts, mobile app, etc.), migrate to Phase 2 using the existing `league-app-new/` backend. All your data migrates seamlessly via `scripts/import_to_database.py`.

**Enjoy your league!** 🏓
