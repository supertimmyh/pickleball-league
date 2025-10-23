#!/usr/bin/env python3
"""
Pickleball League Flask Server

Simple web server for managing pickleball league matches and rankings.
"""

import os
import sys
import yaml
import csv
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file

# Configuration
BASE_DIR = Path(__file__).parent
MATCHES_DIR = BASE_DIR / "matches"
SINGLES_DIR = MATCHES_DIR / "singles"
DOUBLES_DIR = MATCHES_DIR / "doubles"
PLAYERS_FILE = BASE_DIR / "players.csv"
RANKINGS_FILE = BASE_DIR / "rankings.json"
INDEX_FILE = BASE_DIR / "index.html"

# Initialize Flask app
app = Flask(__name__, static_folder=str(BASE_DIR))

# Cache for players (reload on each request to pick up changes)
def load_players():
    """Load players from CSV file."""
    if not PLAYERS_FILE.exists():
        return []

    players = []
    with open(PLAYERS_FILE, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip():  # Skip empty lines
                players.append(row[0].strip())
    return players


def regenerate_rankings():
    """Run the ranking generation and page building scripts."""
    try:
        # Generate rankings
        result1 = subprocess.run(
            [sys.executable, str(BASE_DIR / "scripts" / "generate_rankings.py")],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result1.returncode != 0:
            print(f"Error generating rankings: {result1.stderr}")
            return False

        # Build HTML pages
        result2 = subprocess.run(
            [sys.executable, str(BASE_DIR / "scripts" / "build_pages.py")],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result2.returncode != 0:
            print(f"Error building pages: {result2.stderr}")
            return False

        print("✓ Rankings regenerated successfully")
        return True

    except Exception as e:
        print(f"Error regenerating rankings: {e}")
        return False


# Routes
@app.route('/')
def index():
    """Serve the rankings page."""
    if INDEX_FILE.exists():
        return send_file(INDEX_FILE)
    else:
        return jsonify({"error": "Rankings not generated yet. Please add some matches first."}), 404


@app.route('/record')
def record_match():
    """Serve the match recording form."""
    form_file = BASE_DIR / "match-form.html"
    if form_file.exists():
        return send_file(form_file)
    else:
        return jsonify({"error": "Match form not found"}), 404


@app.route('/rankings.json')
def get_rankings_json():
    """Serve the rankings JSON file."""
    if RANKINGS_FILE.exists():
        return send_file(RANKINGS_FILE)
    else:
        return jsonify({"error": "No rankings available"}), 404


@app.route('/api/players', methods=['GET'])
def get_players():
    """Get list of all players."""
    players = load_players()
    return jsonify(players)


@app.route('/api/matches', methods=['POST'])
def submit_match():
    """Submit a new match result."""
    try:
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        match_type = data.get('type')
        match_date = data.get('date')

        if not match_type or not match_date:
            return jsonify({"error": "Missing match type or date"}), 400

        # Validate match type
        if match_type not in ['singles', 'doubles']:
            return jsonify({"error": "Invalid match type"}), 400

        # Generate filename
        timestamp = datetime.now().strftime("%H%M%S")
        if match_type == 'singles':
            player1 = data.get('players', [])[0] if data.get('players') else "unknown"
            player2 = data.get('players', [])[1] if len(data.get('players', [])) > 1 else "unknown"
            filename = f"{match_date}-{player1.replace(' ', '-')}-vs-{player2.replace(' ', '-')}-{timestamp}.yml"
            save_dir = SINGLES_DIR
        else:
            filename = f"{match_date}-doubles-{timestamp}.yml"
            save_dir = DOUBLES_DIR

        # Ensure directory exists
        save_dir.mkdir(parents=True, exist_ok=True)

        # Prepare YAML data
        yaml_data = {
            'date': match_date
        }

        if match_type == 'singles':
            yaml_data['players'] = data.get('players', [])
            yaml_data['games'] = data.get('games', [])
            yaml_data['winner'] = data.get('winner')
        else:
            yaml_data['team1'] = data.get('team1', [])
            yaml_data['team2'] = data.get('team2', [])
            yaml_data['games'] = data.get('games', [])
            yaml_data['winner_team'] = data.get('winner_team')

        # Save YAML file
        filepath = save_dir / filename
        with open(filepath, 'w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Saved match: {filepath}")

        # Regenerate rankings
        if regenerate_rankings():
            return jsonify({
                "message": "Match recorded successfully!",
                "filename": filename
            }), 200
        else:
            return jsonify({
                "message": "Match saved but rankings update failed. Please check server logs.",
                "filename": filename
            }), 500

    except Exception as e:
        print(f"Error submitting match: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory(BASE_DIR, path)


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


def main():
    """Run the Flask development server."""
    print("=" * 60)
    print("Pickleball League Server")
    print("=" * 60)
    print(f"Base directory: {BASE_DIR}")
    print(f"Players file: {PLAYERS_FILE}")
    print()

    # Check for required files
    if not PLAYERS_FILE.exists():
        print("WARNING: players.csv not found. Creating empty file...")
        PLAYERS_FILE.touch()

    # Load initial player list
    players = load_players()
    print(f"Loaded {len(players)} players from {PLAYERS_FILE}")
    if players:
        print(f"  Players: {', '.join(players[:5])}")
        if len(players) > 5:
            print(f"  ... and {len(players) - 5} more")
    print()

    # Ensure match directories exist
    SINGLES_DIR.mkdir(parents=True, exist_ok=True)
    DOUBLES_DIR.mkdir(parents=True, exist_ok=True)

    print("Server starting...")
    print("=" * 60)
    print()
    print("Open in your browser:")
    print("  Rankings: http://localhost:8000/")
    print("  Record Match: http://localhost:8000/record")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    # Run the Flask app
    app.run(host='0.0.0.0', port=8000, debug=True)


if __name__ == '__main__':
    main()
