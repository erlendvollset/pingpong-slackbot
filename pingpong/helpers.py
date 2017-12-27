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

def calculate_new_elo_ratings(rating1, rating2, player1_win):
    t1 = 10 ** (rating1 / 400)
    t2 = 10 ** (rating2 / 400)
    e1 = (t1 / (t1 + t2))
    e2 = (t2 / (t1 + t2))
    s1 = 1 if player1_win else 0
    s2 = 0 if player1_win else 1
    new_rating1 = rating1 + int(round(32 * (s1 - e1)))
    new_rating2 = rating2 + int(round(32 * (s2 - e2)))
    return new_rating1, new_rating2





