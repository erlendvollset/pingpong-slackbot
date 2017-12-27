def update_scoreboard(winner, loser, scoreboard):
    for row in scoreboard:
        if row['name'] == winner:
            row[loser] += 1
            break
    return scoreboard

def update_leaderboard(winner, loser, leaderboard):
    for player in leaderboard:
        if player['Name'] == winner:
            player['Wins'] += 1
        elif player['Name'] == loser:
            player['Losses'] += 1
    return leaderboard