#!/usr/bin/env python3
"""
Pickleball League HTML Page Generator

Reads rankings.json and config.json to generate a beautiful HTML page displaying the rankings.
"""

import json
from pathlib import Path
from datetime import datetime


def load_config(base_dir):
    """Load configuration file."""
    config_path = base_dir / "config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        # Default config
        return {
            "league_name": "Pickleball League",
            "league_description": "Competitive Pickleball League",
            "ranking_methods": ["ELO Rating System", "Points Difference", "Win/Loss Record"],
            "colors": {"primary": "#082946", "accent": "#e0672b"}
        }


def generate_rankings_table(rankings, table_type='singles'):
    """Generate HTML table for rankings."""
    if not rankings:
        return '<p class="no-data">No matches recorded yet.</p>'

    header_label = 'Player' if table_type != 'doubles_teams' else 'Team'

    html = '''
    <div class="table-responsive">
        <table class="rankings-table">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>{}</th>
                    <th>Rating</th>
                    <th>Record</th>
                    <th>Win %</th>
                    <th>Games</th>
                    <th>Matches</th>
                </tr>
            </thead>
            <tbody>
    '''.format(header_label)

    for entry in rankings:
        name = entry.get('player') or entry.get('team')
        wl_record = f"{entry['wins']}-{entry['losses']}"
        games_record = f"{entry['games_won']}-{entry['games_lost']}"

        # Add medal emoji for top 3
        rank_display = entry['rank']
        if entry['rank'] == 1:
            rank_display = '🥇'
        elif entry['rank'] == 2:
            rank_display = '🥈'
        elif entry['rank'] == 3:
            rank_display = '🥉'

        html += f'''
                <tr>
                    <td class="rank-cell">{rank_display}</td>
                    <td class="player-cell">{name}</td>
                    <td class="rating-cell">{entry['rating']}</td>
                    <td>{wl_record}</td>
                    <td>{entry['win_pct']}%</td>
                    <td>{games_record}</td>
                    <td>{entry['matches_played']}</td>
                </tr>
        '''

    html += '''
            </tbody>
        </table>
    </div>
    '''

    return html


def generate_index_page(rankings_data, config, output_path):
    """Generate the main index.html page."""

    generated_time = datetime.fromisoformat(rankings_data['generated_at']).strftime('%B %d, %Y at %I:%M %p')

    singles_table = generate_rankings_table(rankings_data.get('singles', []), 'singles')
    doubles_teams_table = generate_rankings_table(rankings_data.get('doubles_teams', []), 'doubles_teams')
    doubles_individual_table = generate_rankings_table(rankings_data.get('doubles_individual', []), 'doubles_individual')

    # Extract config values
    league_name = config.get('league_name', 'Pickleball League')
    league_desc = config.get('league_description', 'Competitive Pickleball League')
    ranking_methods = config.get('ranking_methods', [])
    ranking_methods_str = ' | '.join(ranking_methods) if ranking_methods else 'ELO Rating System'
    primary_color = config.get('colors', {}).get('primary', '#082946')
    accent_color = config.get('colors', {}).get('accent', '#e0672b')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{league_name} Rankings</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, {primary_color} 0%, {primary_color}dd 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}

        .logo-placeholder {{
            width: 100px;
            height: 100px;
            margin: 0 auto 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: rgba(255,255,255,0.5);
            font-size: 14px;
            border: 3px dashed rgba(255,255,255,0.3);
        }}

        .header h1 {{
            font-size: 48px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header .subtitle {{
            font-size: 18px;
            opacity: 0.9;
        }}

        .header .updated {{
            font-size: 14px;
            opacity: 0.8;
            margin-top: 10px;
        }}

        .tabs {{
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}

        .tab-btn {{
            flex: 1;
            min-width: 200px;
            padding: 16px 24px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            backdrop-filter: blur(10px);
        }}

        .tab-btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }}

        .tab-btn.active {{
            background: white;
            color: {primary_color};
            border-color: white;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .card {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            margin-bottom: 20px;
        }}

        .card h2 {{
            color: {primary_color};
            margin-bottom: 24px;
            font-size: 28px;
            border-bottom: 3px solid {accent_color};
            padding-bottom: 12px;
        }}

        .table-responsive {{
            overflow-x: auto;
        }}

        .rankings-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .rankings-table thead {{
            background: {primary_color};
            color: white;
        }}

        .rankings-table th {{
            padding: 16px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .rankings-table tbody tr {{
            border-bottom: 1px solid #e0e0e0;
            transition: background-color 0.2s;
        }}

        .rankings-table tbody tr:hover {{
            background-color: #f8f9fa;
        }}

        .rankings-table tbody tr:nth-child(odd) {{
            background-color: #fafbfc;
        }}

        .rankings-table tbody tr:nth-child(odd):hover {{
            background-color: #f1f3f5;
        }}

        .rankings-table td {{
            padding: 16px;
            font-size: 15px;
        }}

        .rank-cell {{
            font-weight: 700;
            font-size: 20px;
            text-align: center;
            width: 80px;
        }}

        .player-cell {{
            font-weight: 600;
            color: #333;
        }}

        .rating-cell {{
            font-weight: 700;
            color: {accent_color};
            font-size: 18px;
        }}

        .no-data {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 16px;
        }}

        .actions {{
            display: flex;
            gap: 12px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}

        .btn {{
            padding: 12px 24px;
            background: {primary_color};
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s;
        }}

        .btn:hover {{
            background: {accent_color};
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(224, 103, 43, 0.4);
        }}

        .btn-secondary {{
            background: {accent_color};
        }}

        .btn-secondary:hover {{
            background: {primary_color};
        }}

        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            padding: 20px;
            opacity: 0.9;
        }}

        .footer .league-info {{
            font-size: 16px;
            margin-bottom: 10px;
            font-weight: 500;
        }}

        .footer .ranking-methods {{
            font-size: 13px;
            opacity: 0.8;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 32px;
            }}

            .card {{
                padding: 24px;
            }}

            .rankings-table {{
                font-size: 13px;
            }}

            .rankings-table th,
            .rankings-table td {{
                padding: 10px 8px;
            }}

            .tab-btn {{
                min-width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo-placeholder">[LOGO]</div>
            <h1>{league_name}</h1>
            <div class="subtitle">{league_desc}</div>
            <div class="updated">Last updated: {generated_time}</div>
        </div>

        <div class="tabs">
            <button class="tab-btn active" onclick="showTab('singles')">Singles Rankings</button>
            <button class="tab-btn" onclick="showTab('doubles-teams')">Doubles Teams</button>
            <button class="tab-btn" onclick="showTab('doubles-individual')">Doubles Individual</button>
        </div>

        <div id="singles" class="tab-content active">
            <div class="card">
                <h2>Singles Rankings</h2>
                {singles_table}
            </div>
        </div>

        <div id="doubles-teams" class="tab-content">
            <div class="card">
                <h2>Doubles Rankings - Teams</h2>
                {doubles_teams_table}
            </div>
        </div>

        <div id="doubles-individual" class="tab-content">
            <div class="card">
                <h2>Doubles Rankings - Individual Players</h2>
                {doubles_individual_table}
            </div>
        </div>

        <div class="actions">
            <a href="/record" class="btn">Record New Match</a>
            <a href="/rankings.json" class="btn btn-secondary" download>Download Data (JSON)</a>
        </div>

        <div class="footer">
            <div class="league-info">{league_name} - {league_desc}</div>
            <div class="ranking-methods">Ranking Methods: {ranking_methods_str}</div>
        </div>
    </div>

    <script>
        function showTab(tabId) {{
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {{
                content.classList.remove('active');
            }});

            // Deactivate all tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});

            // Show selected tab content
            document.getElementById(tabId).classList.add('active');

            // Activate clicked tab button
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>
'''

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✓ Generated: {output_path}")


def main():
    import sys

    # Get base directory (default to parent of script location)
    if len(sys.argv) > 1:
        base_dir = Path(sys.argv[1])
    else:
        base_dir = Path(__file__).parent.parent

    # Load config
    config = load_config(base_dir)

    # Load rankings data
    rankings_file = base_dir / "rankings.json"

    if not rankings_file.exists():
        print(f"Error: Rankings file not found at {rankings_file}")
        print("Please run generate_rankings.py first.")
        return

    with open(rankings_file, 'r') as f:
        rankings_data = json.load(f)

    # Generate index.html
    output_path = base_dir / "index.html"
    generate_index_page(rankings_data, config, output_path)

    print(f"\n✓ HTML pages generated successfully!")
    print(f"  Open {output_path} in your browser to view rankings.")


if __name__ == "__main__":
    main()
