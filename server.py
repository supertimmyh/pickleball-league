#!/usr/bin/env python3
"""
Pickleball League Flask Server

Simple web server for managing pickleball league matches and rankings.
Supports both local filesystem and Google Cloud Storage backends.
"""

import os
import sys
import yaml
import csv
import subprocess
import tempfile
import io
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file

# Load environment variables from .env.development if it exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env.development'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded environment variables from {env_file}")
except ImportError:
    pass

# Google Cloud Storage imports
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

# Configuration
BASE_DIR = Path(__file__).parent
MATCHES_DIR = BASE_DIR / "matches"
SINGLES_DIR = MATCHES_DIR / "singles"
DOUBLES_DIR = MATCHES_DIR / "doubles"
PLAYERS_FILE = BASE_DIR / "players.csv"
RANKINGS_FILE = BASE_DIR / "rankings.json"
INDEX_FILE = BASE_DIR / "index.html"

# Google Cloud Storage configuration
USE_GCS = os.getenv('USE_GCS', 'false').lower() == 'true'
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
GCS_MATCHES_BUCKET = os.getenv('GCS_MATCHES_BUCKET', 'pickleball-matches-data')
GCS_CONFIG_BUCKET = os.getenv('GCS_CONFIG_BUCKET', 'pickleball-config-data')

# Initialize storage client
storage_client = None
if USE_GCS and GCS_AVAILABLE:
    try:
        storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
        print(f"✓ Connected to Google Cloud Storage")
        print(f"  Project: {GOOGLE_CLOUD_PROJECT}")
        print(f"  Matches bucket: {GCS_MATCHES_BUCKET}")
        print(f"  Config bucket: {GCS_CONFIG_BUCKET}")
    except Exception as e:
        print(f"Warning: Could not connect to GCS: {e}")
        USE_GCS = False

# Initialize Flask app
app = Flask(__name__, static_folder=str(BASE_DIR / 'static'))

# Helper functions for Cloud Storage operations
def read_file_from_gcs(bucket_name, file_path):
    """Read a file from Google Cloud Storage."""
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        return blob.download_as_string()
    except Exception as e:
        print(f"Error reading {file_path} from GCS: {e}")
        return None


def write_file_to_gcs(bucket_name, file_path, content):
    """Write a file to Google Cloud Storage."""
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        if isinstance(content, str):
            blob.upload_from_string(content)
        else:
            blob.upload_from_string(content)
        print(f"✓ Saved to GCS: gs://{bucket_name}/{file_path}")
        return True
    except Exception as e:
        print(f"Error writing {file_path} to GCS: {e}")
        return False


# Cache for players (reload on each request to pick up changes)
def load_players():
    """Load players from CSV file (local or GCS)."""
    if USE_GCS:
        csv_data = read_file_from_gcs(GCS_CONFIG_BUCKET, 'players.csv')
        if csv_data is None:
            return []
        csv_text = csv_data.decode('utf-8') if isinstance(csv_data, bytes) else csv_data
        players = []
        for line in csv_text.strip().split('\n'):
            line = line.strip()
            if line:
                players.append(line)
        return players
    else:
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
    """Mark rankings as needing update (called via Cloud Scheduler).

    Note: Match submission no longer directly regenerates rankings.
    Rankings are updated periodically by Cloud Scheduler job to prevent
    race conditions in multi-instance environments.
    """
    print("✓ Match saved. Rankings will be updated by scheduled job.")
    return True


# Routes
@app.route('/')
def index():
    """Serve the rankings page."""
    if USE_GCS:
        html_data = read_file_from_gcs(GCS_CONFIG_BUCKET, 'index.html')
        if html_data:
            html_text = html_data.decode('utf-8') if isinstance(html_data, bytes) else html_data
            return html_text, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            return jsonify({"error": "Rankings not generated yet. Please add some matches first."}), 404
    else:
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
    if USE_GCS:
        json_data = read_file_from_gcs(GCS_CONFIG_BUCKET, 'rankings.json')
        if json_data:
            json_text = json_data.decode('utf-8') if isinstance(json_data, bytes) else json_data
            return json_text, 200, {'Content-Type': 'application/json'}
        else:
            return jsonify({"error": "No rankings available"}), 404
    else:
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
            match_type_dir = 'singles'
        else:
            filename = f"{match_date}-doubles-{timestamp}.yml"
            match_type_dir = 'doubles'

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
        yaml_content = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)

        if USE_GCS:
            gcs_path = f"{match_type_dir}/{filename}"
            success = write_file_to_gcs(GCS_MATCHES_BUCKET, gcs_path, yaml_content)
            if not success:
                return jsonify({"error": "Failed to save match to Cloud Storage"}), 500
        else:
            save_dir = SINGLES_DIR if match_type == 'singles' else DOUBLES_DIR
            save_dir.mkdir(parents=True, exist_ok=True)
            filepath = save_dir / filename
            with open(filepath, 'w') as f:
                f.write(yaml_content)
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
    """Serve static files from local filesystem or GCS."""
    if USE_GCS:
        # Serve from GCS
        file_data = read_file_from_gcs(GCS_CONFIG_BUCKET, f'static/{path}')
        if file_data is None:
            return jsonify({"error": "Static file not found"}), 404

        # Determine content type based on file extension
        import mimetypes
        content_type, _ = mimetypes.guess_type(path)
        if content_type is None:
            content_type = 'application/octet-stream'

        return file_data, 200, {'Content-Type': content_type}
    else:
        # Serve from local filesystem
        return send_from_directory(app.static_folder, path)


@app.route('/api/regenerate-rankings', methods=['POST'])
def api_regenerate_rankings():
    """Manually trigger ranking regeneration (admin endpoint).

    This endpoint runs the full ranking generation and page building
    process. It should be protected by authentication in production.
    """
    try:
        # Set environment variables for subprocess
        env = os.environ.copy()
        env['USE_GCS'] = str(USE_GCS).lower()
        if USE_GCS:
            env['GOOGLE_CLOUD_PROJECT'] = GOOGLE_CLOUD_PROJECT
            env['GCS_MATCHES_BUCKET'] = GCS_MATCHES_BUCKET
            env['GCS_CONFIG_BUCKET'] = GCS_CONFIG_BUCKET

        # Run generate_rankings.py (now with locking and smart detection)
        result1 = subprocess.run(
            [sys.executable, str(BASE_DIR / "scripts" / "generate_rankings.py")],
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )

        if result1.returncode != 0:
            print(f"Error generating rankings: {result1.stderr}")
            return jsonify({
                "error": "Failed to generate rankings",
                "details": result1.stderr
            }), 500

        # Build HTML pages
        result2 = subprocess.run(
            [sys.executable, str(BASE_DIR / "scripts" / "build_pages.py")],
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )

        if result2.returncode != 0:
            print(f"Error building pages: {result2.stderr}")
            return jsonify({
                "error": "Failed to build pages",
                "details": result2.stderr
            }), 500

        print("✓ Manual rankings regeneration completed successfully")
        return jsonify({
            "message": "Rankings regenerated successfully",
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        print(f"Error regenerating rankings: {e}")
        return jsonify({"error": str(e)}), 500


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

    # Determine storage backend
    storage_mode = "Google Cloud Storage" if USE_GCS else "Local Filesystem"
    print(f"Storage Mode: {storage_mode}")

    if not USE_GCS:
        print(f"Base directory: {BASE_DIR}")
        print(f"Players file: {PLAYERS_FILE}")
    print()

    # Check for required files (only if using local storage)
    if not USE_GCS and not PLAYERS_FILE.exists():
        print("WARNING: players.csv not found. Creating empty file...")
        PLAYERS_FILE.touch()

    # Load initial player list
    players = load_players()
    print(f"Loaded {len(players)} players")
    if players:
        print(f"  Players: {', '.join(players[:5])}")
        if len(players) > 5:
            print(f"  ... and {len(players) - 5} more")
    print()

    # Ensure match directories exist (only if using local storage)
    if not USE_GCS:
        SINGLES_DIR.mkdir(parents=True, exist_ok=True)
        DOUBLES_DIR.mkdir(parents=True, exist_ok=True)

    print("Server starting...")
    print("=" * 60)
    print()
    print("Open in your browser:")

    # Determine port (Cloud Run uses PORT env var)
    port = int(os.getenv('PORT', '8000'))

    if port == 8000:
        print(f"  Rankings: http://localhost:{port}/")
        print(f"  Record Match: http://localhost:{port}/record")
        print()
        print("Press Ctrl+C to stop the server")
    else:
        print(f"  Listening on port {port}")

    print("=" * 60)
    print()

    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=(port == 8000))


if __name__ == '__main__':
    main()
