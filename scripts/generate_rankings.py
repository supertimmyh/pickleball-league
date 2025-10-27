#!/usr/bin/env python3
"""
Pickleball League Rankings Generator

Generates rankings for both singles and doubles matches using ELO rating system.
Reads YAML match files and outputs rankings data.
Supports both local filesystem and Google Cloud Storage backends.
"""

import os
import yaml
import json
import time
import fcntl
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Google Cloud Storage imports
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False

# ELO Rating Configuration
K_FACTOR = 32  # Rating volatility factor
DEFAULT_RATING = 1200  # Starting rating for all players


def expected(rating_a, rating_b):
    """Calculate expected score for player A against player B."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def update_elo(winner_rating, loser_rating, k=K_FACTOR):
    """Update ELO ratings after a match."""
    expected_win = expected(winner_rating, loser_rating)
    expected_loss = expected(loser_rating, winner_rating)

    new_winner_rating = winner_rating + k * (1 - expected_win)
    new_loser_rating = loser_rating + k * (0 - expected_loss)

    return new_winner_rating, new_loser_rating


class LockManager:
    """Manages file-based locking to prevent concurrent ranking generation."""

    def __init__(self, lock_file_path, timeout=30, wait_interval=0.5):
        """Initialize the lock manager.

        Args:
            lock_file_path: Path to the lock file
            timeout: Maximum time to wait for lock (seconds)
            wait_interval: Time between lock acquisition attempts (seconds)
        """
        self.lock_file_path = Path(lock_file_path)
        self.timeout = timeout
        self.wait_interval = wait_interval
        self.lock_file = None
        self.acquired = False

    def acquire(self):
        """Attempt to acquire the lock."""
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                # Create lock file's parent directory if needed
                self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Try to open and lock the file (non-blocking on some systems)
                self.lock_file = open(self.lock_file_path, 'w')
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.acquired = True
                self.lock_file.write(f"Locked at {datetime.now().isoformat()}\n")
                self.lock_file.flush()
                print(f"✓ Acquired lock: {self.lock_file_path}")
                return True
            except (IOError, OSError) as e:
                # Lock is held by another process
                elapsed = time.time() - start_time
                print(f"⏳ Waiting for lock (elapsed: {elapsed:.1f}s)...")
                time.sleep(self.wait_interval)

        print(f"✗ Failed to acquire lock after {self.timeout} seconds")
        return False

    def release(self):
        """Release the lock."""
        if self.lock_file and self.acquired:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                self.acquired = False
                print(f"✓ Released lock: {self.lock_file_path}")
            except Exception as e:
                print(f"Warning: Error releasing lock: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


def get_newest_match_timestamp(base_dir, use_gcs=False, gcs_client=None, gcs_matches_bucket=None):
    """Get the timestamp of the newest match file.

    Args:
        base_dir: Base directory path
        use_gcs: Whether to use Google Cloud Storage
        gcs_client: GCS client instance (required if use_gcs=True)
        gcs_matches_bucket: GCS bucket name for matches

    Returns:
        Timestamp as float (seconds since epoch), or 0 if no matches exist
    """
    if use_gcs and gcs_client:
        try:
            bucket = gcs_client.bucket(gcs_matches_bucket)
            all_blobs = list(bucket.list_blobs(prefix='singles')) + list(bucket.list_blobs(prefix='doubles'))

            if all_blobs:
                # Get the most recently updated blob
                newest = max(all_blobs, key=lambda b: b.time_updated)
                return newest.time_updated.timestamp()
        except Exception as e:
            print(f"Error getting newest match timestamp from GCS: {e}")
        return 0
    else:
        # Local filesystem
        singles_dir = Path(base_dir) / "matches" / "singles"
        doubles_dir = Path(base_dir) / "matches" / "doubles"

        match_files = []
        if singles_dir.exists():
            match_files.extend(singles_dir.glob("*.yml"))
            match_files.extend(singles_dir.glob("*.yaml"))
        if doubles_dir.exists():
            match_files.extend(doubles_dir.glob("*.yml"))
            match_files.extend(doubles_dir.glob("*.yaml"))

        if match_files:
            return max(f.stat().st_mtime for f in match_files)
        return 0


def get_last_generation_timestamp(base_dir, use_gcs=False, gcs_client=None, gcs_config_bucket=None):
    """Get the timestamp of when rankings were last generated.

    Args:
        base_dir: Base directory path
        use_gcs: Whether to use Google Cloud Storage
        gcs_client: GCS client instance (required if use_gcs=True)
        gcs_config_bucket: GCS bucket name for config

    Returns:
        Timestamp as float (seconds since epoch), or 0 if never generated
    """
    if use_gcs and gcs_client:
        try:
            bucket = gcs_client.bucket(gcs_config_bucket)
            blob = bucket.blob('last_generation.timestamp')
            timestamp_str = blob.download_as_string().decode('utf-8').strip()
            return float(timestamp_str)
        except Exception:
            # File doesn't exist or error reading it
            return 0
    else:
        # Local filesystem
        timestamp_file = Path(base_dir) / "last_generation.timestamp"
        if timestamp_file.exists():
            try:
                with open(timestamp_file, 'r') as f:
                    return float(f.read().strip())
            except Exception:
                return 0
        return 0


def save_generation_timestamp(base_dir, timestamp, use_gcs=False, gcs_client=None, gcs_config_bucket=None):
    """Save the current generation timestamp.

    Args:
        base_dir: Base directory path
        timestamp: Timestamp to save (seconds since epoch)
        use_gcs: Whether to use Google Cloud Storage
        gcs_client: GCS client instance (required if use_gcs=True)
        gcs_config_bucket: GCS bucket name for config
    """
    timestamp_str = str(timestamp)

    if use_gcs and gcs_client:
        try:
            bucket = gcs_client.bucket(gcs_config_bucket)
            blob = bucket.blob('last_generation.timestamp')
            blob.upload_from_string(timestamp_str)
        except Exception as e:
            print(f"Warning: Could not save generation timestamp to GCS: {e}")
    else:
        # Local filesystem
        try:
            timestamp_file = Path(base_dir) / "last_generation.timestamp"
            with open(timestamp_file, 'w') as f:
                f.write(timestamp_str)
        except Exception as e:
            print(f"Warning: Could not save generation timestamp: {e}")


class RankingsGenerator:
    def __init__(self, base_dir, use_gcs=False, gcs_project=None, gcs_matches_bucket=None, gcs_config_bucket=None):
        self.base_dir = Path(base_dir)
        self.singles_dir = self.base_dir / "matches" / "singles"
        self.doubles_dir = self.base_dir / "matches" / "doubles"

        # Cloud Storage configuration
        self.use_gcs = use_gcs
        self.gcs_project = gcs_project
        self.gcs_matches_bucket = gcs_matches_bucket
        self.gcs_config_bucket = gcs_config_bucket
        self.storage_client = None

        if self.use_gcs and GCS_AVAILABLE:
            try:
                self.storage_client = storage.Client(project=self.gcs_project)
            except Exception as e:
                print(f"Warning: Could not connect to GCS: {e}")
                self.use_gcs = False

        # Singles data
        self.singles_ratings = {}
        self.singles_stats = defaultdict(lambda: {
            'wins': 0, 'losses': 0, 'games_won': 0, 'games_lost': 0, 'matches_played': 0
        })

        # Doubles data (team-based)
        self.doubles_ratings = {}
        self.doubles_stats = defaultdict(lambda: {
            'wins': 0, 'losses': 0, 'games_won': 0, 'games_lost': 0, 'matches_played': 0
        })

        # Doubles data (individual player stats in doubles)
        self.doubles_individual_ratings = {}
        self.doubles_individual_stats = defaultdict(lambda: {
            'wins': 0, 'losses': 0, 'games_won': 0, 'games_lost': 0, 'matches_played': 0
        })

    def list_gcs_files(self, bucket_name, prefix):
        """List all files in a GCS bucket with given prefix."""
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blobs = list(bucket.list_blobs(prefix=prefix))
            yaml_files = [blob for blob in blobs if blob.name.endswith(('.yml', '.yaml'))]
            # Sort by name (which includes timestamp)
            yaml_files.sort(key=lambda b: b.name)
            return yaml_files
        except Exception as e:
            print(f"Error listing GCS files: {e}")
            return []

    def load_yaml_file(self, filepath):
        """Load a YAML match file (local or GCS)."""
        if self.use_gcs:
            # filepath is actually a GCS blob
            try:
                yaml_content = filepath.download_as_string()
                yaml_text = yaml_content.decode('utf-8') if isinstance(yaml_content, bytes) else yaml_content
                return yaml.safe_load(yaml_text)
            except Exception as e:
                print(f"Error loading GCS file {filepath.name}: {e}")
                return None
        else:
            try:
                with open(filepath, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                return None

    def process_singles_match(self, match_data):
        """Process a singles match and update ratings/stats."""
        try:
            player1 = match_data['players'][0]
            player2 = match_data['players'][1]
            winner = match_data['winner']
            loser = player1 if winner == player2 else player2

            # Support both old format (single score) and new format (games array)
            if 'games' in match_data:
                # New format: multiple games
                games = match_data['games']
                p1_total_games = sum(g['player1_score'] for g in games)
                p2_total_games = sum(g['player2_score'] for g in games)
            else:
                # Old format: single score
                p1_total_games = match_data['score']['player1_games']
                p2_total_games = match_data['score']['player2_games']

            # Initialize ratings if needed
            if player1 not in self.singles_ratings:
                self.singles_ratings[player1] = DEFAULT_RATING
            if player2 not in self.singles_ratings:
                self.singles_ratings[player2] = DEFAULT_RATING

            # Update ELO ratings (one update per match)
            winner_rating = self.singles_ratings[winner]
            loser_rating = self.singles_ratings[loser]
            new_winner_rating, new_loser_rating = update_elo(winner_rating, loser_rating)

            self.singles_ratings[winner] = new_winner_rating
            self.singles_ratings[loser] = new_loser_rating

            # Update stats
            self.singles_stats[winner]['wins'] += 1
            self.singles_stats[loser]['losses'] += 1
            self.singles_stats[player1]['games_won'] += p1_total_games
            self.singles_stats[player1]['games_lost'] += p2_total_games
            self.singles_stats[player2]['games_won'] += p2_total_games
            self.singles_stats[player2]['games_lost'] += p1_total_games
            self.singles_stats[player1]['matches_played'] += 1
            self.singles_stats[player2]['matches_played'] += 1

        except Exception as e:
            print(f"Error processing singles match: {e}")

    def process_doubles_match(self, match_data):
        """Process a doubles match and update ratings/stats."""
        try:
            team1_players = match_data['team1']
            team2_players = match_data['team2']
            winner_team_num = match_data['winner_team']

            # Support both old format (single score) and new format (games array)
            if 'games' in match_data:
                # New format: multiple games
                games = match_data['games']
                team1_total_games = sum(g['team1_score'] for g in games)
                team2_total_games = sum(g['team2_score'] for g in games)
            else:
                # Old format: single score
                team1_total_games = match_data['score']['team1_games']
                team2_total_games = match_data['score']['team2_games']

            # Create team identifiers (sorted for consistency)
            team1_id = " & ".join(sorted(team1_players))
            team2_id = " & ".join(sorted(team2_players))

            winner_team_id = team1_id if winner_team_num == 1 else team2_id
            loser_team_id = team2_id if winner_team_num == 1 else team1_id
            winner_players = team1_players if winner_team_num == 1 else team2_players
            loser_players = team2_players if winner_team_num == 1 else team1_players
            winner_games = team1_total_games if winner_team_num == 1 else team2_total_games
            loser_games = team2_total_games if winner_team_num == 1 else team1_total_games

            # === Team-based ratings ===
            if team1_id not in self.doubles_ratings:
                self.doubles_ratings[team1_id] = DEFAULT_RATING
            if team2_id not in self.doubles_ratings:
                self.doubles_ratings[team2_id] = DEFAULT_RATING

            winner_rating = self.doubles_ratings[winner_team_id]
            loser_rating = self.doubles_ratings[loser_team_id]
            new_winner_rating, new_loser_rating = update_elo(winner_rating, loser_rating)

            self.doubles_ratings[winner_team_id] = new_winner_rating
            self.doubles_ratings[loser_team_id] = new_loser_rating

            # Update team stats
            self.doubles_stats[winner_team_id]['wins'] += 1
            self.doubles_stats[loser_team_id]['losses'] += 1
            self.doubles_stats[team1_id]['games_won'] += team1_total_games
            self.doubles_stats[team1_id]['games_lost'] += team2_total_games
            self.doubles_stats[team2_id]['games_won'] += team2_total_games
            self.doubles_stats[team2_id]['games_lost'] += team1_total_games
            self.doubles_stats[team1_id]['matches_played'] += 1
            self.doubles_stats[team2_id]['matches_played'] += 1

            # === Individual player ratings in doubles ===
            for player in winner_players + loser_players:
                if player not in self.doubles_individual_ratings:
                    self.doubles_individual_ratings[player] = DEFAULT_RATING

            # Update individual ratings (average of winners vs average of losers)
            avg_winner_rating = sum(self.doubles_individual_ratings[p] for p in winner_players) / len(winner_players)
            avg_loser_rating = sum(self.doubles_individual_ratings[p] for p in loser_players) / len(loser_players)

            new_winner_avg, new_loser_avg = update_elo(avg_winner_rating, avg_loser_rating)

            # Apply rating change to each player
            winner_rating_delta = new_winner_avg - avg_winner_rating
            loser_rating_delta = new_loser_avg - avg_loser_rating

            for player in winner_players:
                self.doubles_individual_ratings[player] += winner_rating_delta
                self.doubles_individual_stats[player]['wins'] += 1
                self.doubles_individual_stats[player]['games_won'] += winner_games
                self.doubles_individual_stats[player]['games_lost'] += loser_games
                self.doubles_individual_stats[player]['matches_played'] += 1

            for player in loser_players:
                self.doubles_individual_ratings[player] += loser_rating_delta
                self.doubles_individual_stats[player]['losses'] += 1
                self.doubles_individual_stats[player]['games_won'] += loser_games
                self.doubles_individual_stats[player]['games_lost'] += winner_games
                self.doubles_individual_stats[player]['matches_played'] += 1

        except Exception as e:
            print(f"Error processing doubles match: {e}")

    def get_sorted_match_files(self, directory, gcs_prefix=None):
        """Get all YAML files sorted by date."""
        if self.use_gcs:
            # Use GCS prefix instead of local directory
            blobs = self.list_gcs_files(self.gcs_matches_bucket, gcs_prefix)
            # Sort by date in filename (assuming format: YYYY-MM-DD-*.yml)
            def get_date(blob):
                try:
                    # Extract date from blob name
                    filename = blob.name.split('/')[-1]  # Get filename from path
                    date_str = filename.split('-')[:3]
                    return datetime.strptime('-'.join(date_str), '%Y-%m-%d')
                except:
                    return datetime.min
            return sorted(blobs, key=get_date)
        else:
            if not directory.exists():
                return []
            yaml_files = list(directory.glob("*.yml")) + list(directory.glob("*.yaml"))
            # Sort by date in filename (assuming format: YYYY-MM-DD-*.yml)
            def get_date(filepath):
                try:
                    date_str = filepath.stem.split('-')[:3]
                    return datetime.strptime('-'.join(date_str), '%Y-%m-%d')
                except:
                    return datetime.min
            return sorted(yaml_files, key=get_date)

    def generate_singles_rankings(self):
        """Generate singles rankings from all singles match files."""
        print("Processing singles matches...")
        match_files = self.get_sorted_match_files(self.singles_dir, 'singles')

        for match_file in match_files:
            match_data = self.load_yaml_file(match_file)
            if match_data:
                self.process_singles_match(match_data)

        # Create rankings list
        rankings = []
        for player in self.singles_ratings:
            stats = self.singles_stats[player]
            win_pct = (stats['wins'] / stats['matches_played'] * 100) if stats['matches_played'] > 0 else 0

            rankings.append({
                'player': player,
                'rating': round(self.singles_ratings[player], 1),
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_pct': round(win_pct, 1),
                'games_won': stats['games_won'],
                'games_lost': stats['games_lost'],
                'matches_played': stats['matches_played']
            })

        # Sort by rating (highest first)
        rankings.sort(key=lambda x: x['rating'], reverse=True)

        # Add rank
        for i, entry in enumerate(rankings):
            entry['rank'] = i + 1

        print(f"Processed {len(match_files)} singles matches, {len(rankings)} players")
        return rankings

    def generate_doubles_rankings(self):
        """Generate doubles rankings (team-based) from all doubles match files."""
        print("Processing doubles matches (team rankings)...")
        match_files = self.get_sorted_match_files(self.doubles_dir, 'doubles')

        for match_file in match_files:
            match_data = self.load_yaml_file(match_file)
            if match_data:
                self.process_doubles_match(match_data)

        # Create team rankings list
        rankings = []
        for team in self.doubles_ratings:
            stats = self.doubles_stats[team]
            win_pct = (stats['wins'] / stats['matches_played'] * 100) if stats['matches_played'] > 0 else 0

            rankings.append({
                'team': team,
                'rating': round(self.doubles_ratings[team], 1),
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_pct': round(win_pct, 1),
                'games_won': stats['games_won'],
                'games_lost': stats['games_lost'],
                'matches_played': stats['matches_played']
            })

        # Sort by rating (highest first)
        rankings.sort(key=lambda x: x['rating'], reverse=True)

        # Add rank
        for i, entry in enumerate(rankings):
            entry['rank'] = i + 1

        print(f"Processed {len(match_files)} doubles matches, {len(rankings)} teams")
        return rankings

    def generate_doubles_individual_rankings(self):
        """Generate doubles rankings (individual player view)."""
        print("Processing doubles matches (individual player rankings)...")

        # Create individual player rankings list
        rankings = []
        for player in self.doubles_individual_ratings:
            stats = self.doubles_individual_stats[player]
            win_pct = (stats['wins'] / stats['matches_played'] * 100) if stats['matches_played'] > 0 else 0

            rankings.append({
                'player': player,
                'rating': round(self.doubles_individual_ratings[player], 1),
                'wins': stats['wins'],
                'losses': stats['losses'],
                'win_pct': round(win_pct, 1),
                'games_won': stats['games_won'],
                'games_lost': stats['games_lost'],
                'matches_played': stats['matches_played']
            })

        # Sort by rating (highest first)
        rankings.sort(key=lambda x: x['rating'], reverse=True)

        # Add rank
        for i, entry in enumerate(rankings):
            entry['rank'] = i + 1

        print(f"{len(rankings)} players in doubles")
        return rankings

    def generate_all_rankings(self):
        """Generate all rankings and save to JSON."""
        singles_rankings = self.generate_singles_rankings()
        doubles_team_rankings = self.generate_doubles_rankings()
        doubles_individual_rankings = self.generate_doubles_individual_rankings()

        output = {
            'generated_at': datetime.now().isoformat(),
            'singles': singles_rankings,
            'doubles_teams': doubles_team_rankings,
            'doubles_individual': doubles_individual_rankings
        }

        # Save to JSON file
        json_content = json.dumps(output, indent=2)

        if self.use_gcs:
            try:
                bucket = self.storage_client.bucket(self.gcs_config_bucket)
                blob = bucket.blob('rankings.json')
                blob.upload_from_string(json_content)
                print(f"\n✓ Rankings saved to: gs://{self.gcs_config_bucket}/rankings.json")
            except Exception as e:
                print(f"Error saving rankings to GCS: {e}")
        else:
            output_file = self.base_dir / "rankings.json"
            with open(output_file, 'w') as f:
                f.write(json_content)
            print(f"\n✓ Rankings saved to: {output_file}")

        # Print summary
        print("\n=== SINGLES RANKINGS ===")
        if singles_rankings:
            print(f"{'Rank':<6} {'Player':<20} {'Rating':<8} {'W-L':<10} {'Win %':<8}")
            print("-" * 60)
            for entry in singles_rankings[:10]:  # Top 10
                wl = f"{entry['wins']}-{entry['losses']}"
                print(f"{entry['rank']:<6} {entry['player']:<20} {entry['rating']:<8} {wl:<10} {entry['win_pct']:<8}")
        else:
            print("No singles matches found.")

        print("\n=== DOUBLES RANKINGS (Teams) ===")
        if doubles_team_rankings:
            print(f"{'Rank':<6} {'Team':<30} {'Rating':<8} {'W-L':<10} {'Win %':<8}")
            print("-" * 70)
            for entry in doubles_team_rankings[:10]:  # Top 10
                wl = f"{entry['wins']}-{entry['losses']}"
                print(f"{entry['rank']:<6} {entry['team']:<30} {entry['rating']:<8} {wl:<10} {entry['win_pct']:<8}")
        else:
            print("No doubles matches found.")

        print("\n=== DOUBLES RANKINGS (Individual) ===")
        if doubles_individual_rankings:
            print(f"{'Rank':<6} {'Player':<20} {'Rating':<8} {'W-L':<10} {'Win %':<8}")
            print("-" * 60)
            for entry in doubles_individual_rankings[:10]:  # Top 10
                wl = f"{entry['wins']}-{entry['losses']}"
                print(f"{entry['rank']:<6} {entry['player']:<20} {entry['rating']:<8} {wl:<10} {entry['win_pct']:<8}")
        else:
            print("No doubles matches found.")

        return output


def main():
    import sys

    # Get base directory (default to parent of script location)
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = Path(__file__).parent.parent

    # Check if using GCS
    use_gcs = os.getenv('USE_GCS', 'false').lower() == 'true'
    gcs_project = os.getenv('GOOGLE_CLOUD_PROJECT')
    gcs_matches_bucket = os.getenv('GCS_MATCHES_BUCKET', 'pickleball-matches-data')
    gcs_config_bucket = os.getenv('GCS_CONFIG_BUCKET', 'pickleball-config-data')

    if use_gcs:
        print(f"Generating rankings from Google Cloud Storage\n")
        print(f"  Project: {gcs_project}")
        print(f"  Matches bucket: {gcs_matches_bucket}")
        print(f"  Config bucket: {gcs_config_bucket}\n")
    else:
        print(f"Generating rankings for: {base_dir}\n")

    # Initialize storage client if using GCS
    storage_client = None
    if use_gcs and GCS_AVAILABLE:
        try:
            storage_client = storage.Client(project=gcs_project)
        except Exception as e:
            print(f"Warning: Could not connect to GCS: {e}")
            use_gcs = False

    # Acquire lock to prevent concurrent ranking generation
    lock_file = Path(base_dir) / "rankings.lock"
    with LockManager(lock_file, timeout=30) as lock_mgr:
        if not lock_mgr.acquired:
            print("✗ Could not acquire lock. Another ranking generation may be in progress.")
            sys.exit(1)

        # Check if there are new matches since last generation
        newest_match_time = get_newest_match_timestamp(
            base_dir,
            use_gcs=use_gcs,
            gcs_client=storage_client,
            gcs_matches_bucket=gcs_matches_bucket
        )
        last_generation_time = get_last_generation_timestamp(
            base_dir,
            use_gcs=use_gcs,
            gcs_client=storage_client,
            gcs_config_bucket=gcs_config_bucket
        )

        # Skip if no new matches
        if newest_match_time > 0 and last_generation_time > 0 and newest_match_time <= last_generation_time:
            print("⏭️  No new matches since last generation. Skipping ranking update.")
            print(f"   Last generation: {datetime.fromtimestamp(last_generation_time).isoformat()}")
            print(f"   Newest match: {datetime.fromtimestamp(newest_match_time).isoformat()}")
            sys.exit(0)

        if newest_match_time == 0:
            print("ℹ️  No matches found. Generating empty rankings.")

        print("🔄 Generating rankings...\n")

        generator = RankingsGenerator(
            base_dir,
            use_gcs=use_gcs,
            gcs_project=gcs_project,
            gcs_matches_bucket=gcs_matches_bucket,
            gcs_config_bucket=gcs_config_bucket
        )
        rankings = generator.generate_all_rankings()

        # Save generation timestamp
        save_generation_timestamp(
            base_dir,
            time.time(),
            use_gcs=use_gcs,
            gcs_client=storage_client,
            gcs_config_bucket=gcs_config_bucket
        )

        print("\n✓ Rankings generation complete!")


if __name__ == "__main__":
    main()
