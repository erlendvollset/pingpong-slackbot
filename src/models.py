class Player():
    def __init__(self, id, name, elo_rating=1000):
        self.id = id
        self.name = name
        self.elo_rating = elo_rating

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_rating(self):
        return self.elo_rating

    def set_id(self, id):
        self.id = id

    def set_name(self, name):
        self.name = name

    def set_rating(self, elo_rating):
        self.elo_rating = elo_rating

class Match():
    def __init__(self, id, player1_id, player2_id, player1_score, player2_score, player1_rating, player2_rating):
        self.id = id
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.player1_score = player1_score
        self.player2_score = player2_score
        self.player1_rating = player1_rating
        self.player2_rating = player2_rating