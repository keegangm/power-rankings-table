# nba_teams.py

# DONE: modules
import csv

# DONE: import 'NBA_Teams.csv' file
teams_filename = 'Reference/NBA_Teams.csv'

with open(teams_filename, mode = 'r') as file:
    csv_reader = csv.DictReader(file)

    team_list = []

    # Iterate through each row in the CSV file
    for row in csv_reader:
        # Append each row (as a dictionary) to the list
        team_list.append(row)


# DONE: import 'NBA_TeamColors.csv' file
colors_filename = 'Reference/NBA_TeamColors.csv'
with open(colors_filename, mode='r') as file:
    csv_reader = csv.DictReader(file)

    team_colors = []

    for row in csv_reader:
        team_colors.append(row)


# define find_team() method for agnostic search term
def find_team(query, property_name):
    """ Return desired property_name for teamname query in almost any form. """
    query = query.lower()
    for t in team_list:
        if (
            query in t['aliases'].lower() or 
            query in t['teamname'].lower() or 
            query in t['abbrev'].lower()
        ):
            return t[property_name]
    return "None"

def find_team_colors(team, color_rank):
    """ Match full team name input to team color scheme. """
    for t in team_colors:
        if team in t['teamname']:
            if color_rank == 1:
                color_1 = t['color_1']
                return color_1
            if color_rank == 2:
                color_2 = t['color_2']
                return color_2
            if color_rank == 3:
                color_3 = t['color_3']
                return color_3
            else:
                return "No corresponding color value found."
    else:
        return "No team match"

# DONE: define nba_tmname()
# derive team name (e.g. 'Utah Jazz') from inputs including abbreviation ('UTA') or aliases ('Utah', 'Jazz')
def nba_tmname(query):
    """ Find full team name for NBA team. """
    return find_team(query, 'teamname')

# DONE: define nba_abbrname()
# derive team abbreviation (e.g. 'UTA') from inputs team name ('Utah Jazz') or aliases ('Utah', 'Jazz')
def nba_abbrname(query):
    """ Find abbreviation for NBA team. """
    return find_team(query, 'abbrev')


def nba_conf(query):
    """ Find Conference for NBA team. """
    return find_team(query, 'conference')

def nba_div(query):
    """ Find Division for NBA team. """
    return find_team(query, 'division')

def team_color1(query):
    """ Find primary color for NBA team. """
    team = find_team(query, 'teamname')
    return find_team_colors(team, 1)

def team_color2(query):
    """ Find secondary color for NBA team. """
    team = find_team(query, 'teamname')
    return find_team_colors(team, 2)

def team_color3(query):
    """ Find tertiary color for NBA team. """
    team = find_team(query, 'teamname')
    return find_team_colors(team, 3)

def team_color_any(query, color_rank):
    """ Find any color (1, 2, 3) for NBA team. """
    team = find_team(query, 'teamname')
    return find_team_colors(team, color_rank)