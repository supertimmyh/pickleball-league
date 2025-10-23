#!/usr/bin/env python3
"""
Migration Script: YAML to SQLite Database

This script imports all YAML match files into the league-app-new SQLite database.
Use this when transitioning from Phase 1 (YAML) to Phase 2 (Backend).

Usage:
    python3 import_to_database.py [yaml_base_dir] [database_path]
"""

import os
import sys
import yaml
import sqlite3
from pathlib import Path
from datetime import datetime


class YAMLToDBImporter:
    def __init__(self, yaml_base_dir, db_path):
        self.yaml_base_dir = Path(yaml_base_dir)
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None

        # Cache for player and league IDs
        self.player_ids = {}
        self.league_id = None

    def connect_db(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print(f"✓ Connected to database: {self.db_path}")

    def ensure_league_exists(self, league_name="Pickleball League", sport="Pickleball"):
        """Ensure a league exists in the database."""
        self.cursor.execute(
            "SELECT id FROM Leagues WHERE name = ? AND sport = ?",
            (league_name, sport)
        )
        result = self.cursor.fetchone()

        if result:
            self.league_id = result[0]
            print(f"✓ Using existing league: {league_name} (ID: {self.league_id})")
        else:
            self.cursor.execute(
                "INSERT INTO Leagues (name, sport, status) VALUES (?, ?, ?)",
                (league_name, sport, 'active')
            )
            self.league_id = self.cursor.lastrowid
            self.conn.commit()
            print(f"✓ Created new league: {league_name} (ID: {self.league_id})")

    def get_or_create_player(self, player_name):
        """Get player ID or create new player."""
        if player_name in self.player_ids:
            return self.player_ids[player_name]

        self.cursor.execute("SELECT id FROM Players WHERE name = ?", (player_name,))
        result = self.cursor.fetchone()

        if result:
            player_id = result[0]
        else:
            self.cursor.execute(
                "INSERT INTO Players (name, email) VALUES (?, ?)",
                (player_name, None)
            )
            player_id = self.cursor.lastrowid
            self.conn.commit()
            print(f"  Created player: {player_name} (ID: {player_id})")

        self.player_ids[player_name] = player_id
        return player_id

    def import_singles_match(self, match_data):
        """Import a singles match."""
        try:
            player1_name = match_data['players'][0]
            player2_name = match_data['players'][1]
            p1_games = match_data['score']['player1_games']
            p2_games = match_data['score']['player2_games']
            winner_name = match_data['winner']
            date = match_data['date']

            # Get or create players
            player1_id = self.get_or_create_player(player1_name)
            player2_id = self.get_or_create_player(player2_name)
            winner_id = self.get_or_create_player(winner_name)
            loser_id = player1_id if winner_id == player2_id else player2_id

            # Insert match
            self.cursor.execute('''
                INSERT INTO Matches (
                    league_id, date, type,
                    player1_id, player2_id,
                    score_player1, score_player2,
                    winner_id, loser_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.league_id, date, 'singles',
                player1_id, player2_id,
                p1_games, p2_games,
                winner_id, loser_id
            ))

            return True

        except Exception as e:
            print(f"  Error importing singles match: {e}")
            return False

    def import_doubles_match(self, match_data):
        """Import a doubles match."""
        try:
            team1_players = match_data['team1']
            team2_players = match_data['team2']
            team1_games = match_data['score']['team1_games']
            team2_games = match_data['score']['team2_games']
            winner_team_num = match_data['winner_team']
            date = match_data['date']

            # Get or create all players
            team1_ids = [self.get_or_create_player(p) for p in team1_players]
            team2_ids = [self.get_or_create_player(p) for p in team2_players]

            # Create team identifiers (sorted names for consistency)
            team1_name = " & ".join(sorted(team1_players))
            team2_name = " & ".join(sorted(team2_players))

            # Get or create teams
            team1_id = self.get_or_create_team(team1_name, team1_ids)
            team2_id = self.get_or_create_team(team2_name, team2_ids)

            # Determine winner/loser
            winner_team_id = team1_id if winner_team_num == 1 else team2_id
            loser_team_id = team2_id if winner_team_num == 1 else team1_id

            # Insert match
            self.cursor.execute('''
                INSERT INTO Matches (
                    league_id, date, type,
                    team1_id, team2_id,
                    score_team1, score_team2,
                    winner_team_id, loser_team_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.league_id, date, 'doubles',
                team1_id, team2_id,
                team1_games, team2_games,
                winner_team_id, loser_team_id
            ))

            return True

        except Exception as e:
            print(f"  Error importing doubles match: {e}")
            return False

    def get_or_create_team(self, team_name, player_ids):
        """Get team ID or create new team."""
        self.cursor.execute(
            "SELECT id FROM Teams WHERE name = ? AND league_id = ?",
            (team_name, self.league_id)
        )
        result = self.cursor.fetchone()

        if result:
            return result[0]

        self.cursor.execute(
            "INSERT INTO Teams (name, league_id, player1_id, player2_id) VALUES (?, ?, ?, ?)",
            (team_name, self.league_id, player_ids[0], player_ids[1] if len(player_ids) > 1 else None)
        )
        team_id = self.cursor.lastrowid
        self.conn.commit()
        print(f"  Created team: {team_name} (ID: {team_id})")
        return team_id

    def load_yaml_file(self, filepath):
        """Load a YAML match file."""
        try:
            with open(filepath, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"  Error loading {filepath}: {e}")
            return None

    def import_all_matches(self):
        """Import all singles and doubles matches."""
        singles_dir = self.yaml_base_dir / "matches" / "singles"
        doubles_dir = self.yaml_base_dir / "matches" / "doubles"

        singles_count = 0
        doubles_count = 0

        # Import singles matches
        print("\n📊 Importing Singles Matches...")
        if singles_dir.exists():
            for yaml_file in sorted(singles_dir.glob("*.yml")) + sorted(singles_dir.glob("*.yaml")):
                match_data = self.load_yaml_file(yaml_file)
                if match_data and self.import_singles_match(match_data):
                    singles_count += 1
                    print(f"  ✓ Imported: {yaml_file.name}")

        # Import doubles matches
        print("\n🏐 Importing Doubles Matches...")
        if doubles_dir.exists():
            for yaml_file in sorted(doubles_dir.glob("*.yml")) + sorted(doubles_dir.glob("*.yaml")):
                match_data = self.load_yaml_file(yaml_file)
                if match_data and self.import_doubles_match(match_data):
                    doubles_count += 1
                    print(f"  ✓ Imported: {yaml_file.name}")

        self.conn.commit()

        print(f"\n✓ Import Complete!")
        print(f"  Singles matches imported: {singles_count}")
        print(f"  Doubles matches imported: {doubles_count}")
        print(f"  Total players: {len(self.player_ids)}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("\n✓ Database connection closed")


def main():
    # Default paths
    yaml_base_dir = Path(__file__).parent.parent
    db_path = Path(__file__).parent.parent.parent / "league-app-new" / "backend" / "data" / "database.sqlite"

    # Allow override via command line
    if len(sys.argv) > 1:
        yaml_base_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        db_path = Path(sys.argv[2])

    print("=" * 60)
    print("YAML to Database Migration Tool")
    print("=" * 60)
    print(f"YAML source: {yaml_base_dir}")
    print(f"Database: {db_path}")
    print()

    if not yaml_base_dir.exists():
        print(f"❌ Error: YAML directory not found: {yaml_base_dir}")
        sys.exit(1)

    if not db_path.exists():
        print(f"❌ Error: Database not found: {db_path}")
        print("Please create the database first using the backend initialization script.")
        sys.exit(1)

    # Perform import
    importer = YAMLToDBImporter(yaml_base_dir, db_path)
    try:
        importer.connect_db()
        importer.ensure_league_exists()
        importer.import_all_matches()
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        sys.exit(1)
    finally:
        importer.close()

    print("\n" + "=" * 60)
    print("Migration complete! You can now use the backend API.")
    print("=" * 60)


if __name__ == "__main__":
    main()
