#!/usr/bin/env python3
"""
Pickleball League Rankings Generator

Generates rankings for both singles and doubles matches using ELO rating system.
Reads YAML match files and outputs rankings data.
"""

import os
import yaml
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

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


class RankingsGenerator:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.singles_dir = self.base_dir / "matches" / "singles"
        self.doubles_dir = self.base_dir / "matches" / "doubles"

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

    def load_yaml_file(self, filepath):
        """Load a YAML match file."""
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

    def get_sorted_match_files(self, directory):
        """Get all YAML files sorted by date."""
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
        match_files = self.get_sorted_match_files(self.singles_dir)

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
        match_files = self.get_sorted_match_files(self.doubles_dir)

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
        output_file = self.base_dir / "rankings.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\nRankings saved to: {output_file}")

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

    print(f"Generating rankings for: {base_dir}\n")

    generator = RankingsGenerator(base_dir)
    rankings = generator.generate_all_rankings()

    print("\n✓ Rankings generation complete!")


if __name__ == "__main__":
    main()
