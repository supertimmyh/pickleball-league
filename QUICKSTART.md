# Quick Start Guide

Get your pickleball league running in 5 minutes!

## Step 1: Install Dependencies (1 minute)

```bash
cd pickleball-league
pip3 install -r requirements-server.txt
```

## Step 2: Add Your Players (1 minute)

Edit `players.csv`:

```bash
nano players.csv
```

Add your players (one per line):
```
Alice Johnson
Bob Smith
Carol White
Dave Brown
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

## Step 3: Start the Server (30 seconds)

```bash
python3 server.py
```

You should see:
```
====================================
Open in your browser:
  Rankings: http://localhost:5000/
  Record Match: http://localhost:5000/record
====================================
```

## Step 4: Record Your First Match (2 minutes)

1. Open `http://localhost:5000/record` in your browser
2. Select "Singles Match" or "Doubles Match"
3. Choose players from dropdowns
4. Enter game scores:
   - Game 1: 11 - 7
   - Game 2: 9 - 11  (optional)
   - Game 3: 11 - 5  (optional)
5. Click "Submit Match"
6. You'll be redirected to rankings automatically!

## Step 5: View Rankings (30 seconds)

Visit `http://localhost:5000/` to see:
- Singles Rankings
- Doubles Team Rankings
- Doubles Individual Rankings

## That's It!

Your league is now running. Record more matches and watch the rankings update automatically!

## Customization (Optional)

### Change League Name & Colors

Edit `config.json`:

```json
{
  "league_name": "My Pickleball League",
  "league_description": "Monday Night League",
  "colors": {
    "primary": "#082946",
    "accent": "#e0672b"
  }
}
```

Then regenerate pages:
```bash
python3 scripts/build_pages.py
```

### Access from Phone/Tablet

Find your computer's IP address:
```bash
ifconfig | grep "inet "
```

Then on your phone, visit:
```
http://YOUR_IP_ADDRESS:5000/
```

For example:
```
http://192.168.1.100:5000/
```

## Next Steps

- Add more players to `players.csv`
- Record more matches
- Share the URL with league members
- Backup your `matches/` folder regularly

## Need Help?

Check `README-SERVER.md` for detailed documentation.

## Common Issues

**Can't access from another device?**
- Make sure devices are on same WiFi network
- Use computer's IP address, not `localhost`

**Players not showing in dropdown?**
- Check `players.csv` has one name per line
- Refresh the page

**Port 5000 in use?**
- Change port in `server.py` to 5001 or another port

Enjoy your league! 🏓
