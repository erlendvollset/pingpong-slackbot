from typing import Optional

from pingpong.cdf_backend import CDFBackend
from pingpong.data_classes import Hand, Match, Player, Sport


class PlayerDoesNotExist(Exception):
    pass


class InvalidMatchRegistration(Exception):
    pass


class PingPongService:
    def __init__(self, cdf_backend: CDFBackend) -> None:
        self.cdf_backend = cdf_backend

    def add_new_player(self, id: str) -> None:
        player = Player(id, id)
        self.cdf_backend.create_player(player)

    def get_player(self, player_id: str) -> Player:
        players = self.cdf_backend.get_players(ids=[player_id])
        if players:
            return players[0]
        raise PlayerDoesNotExist()

    def update_display_name(self, player: Player, new_name: str) -> bool:
        players = self.cdf_backend.list_players()
        names = [p.name.lower() for p in players]
        if new_name.lower() in names:
            return False
        self.cdf_backend.update_player(player.id, new_name=new_name)
        return True

    def add_match(
        self, p1_id: str, nd1: bool, p2_id: str, nd2: bool, score_p1: int, score_p2: int
    ) -> tuple[Player, int, Player, int]:
        if p1_id == p2_id or int(score_p1) == int(score_p2):
            raise InvalidMatchRegistration()

        p1_hand = Hand.NON_DOMINANT if nd1 else Hand.DOMINANT
        p2_hand = Hand.NON_DOMINANT if nd2 else Hand.DOMINANT
        p1 = self.get_player(p1_id)
        p2 = self.get_player(p2_id)

        if p1 and p2:
            match = Match(
                p1_id,
                p2_id,
                score_p1,
                score_p2,
                p1.get_rating(sport=Sport.PING_PONG),
                p2.get_rating(sport=Sport.PING_PONG),
                sport=Sport.PING_PONG,
                player1_hand=p1_hand,
                player2_hand=p2_hand,
            )
            self.cdf_backend.create_match(match)

            new_rating1, new_rating2 = self.calculate_new_elo_ratings(
                rating1=p1.get_rating(Sport.PING_PONG, p1_hand),
                rating2=p2.get_rating(Sport.PING_PONG, p2_hand),
                player1_win=int(match.player1_score) > int(match.player2_score),
            )
            new_p1 = self.cdf_backend.update_player(p1.id, new_rating=new_rating1, hand=p1_hand)
            new_p2 = self.cdf_backend.update_player(p2.id, new_rating=new_rating2, hand=p2_hand)

            updated_players = (
                new_p1,
                new_p1.get_rating(Sport.PING_PONG, p1_hand) - p1.get_rating(Sport.PING_PONG, p1_hand),
                new_p2,
                new_p2.get_rating(Sport.PING_PONG, p2_hand) - p2.get_rating(Sport.PING_PONG, p2_hand),
            )
            return updated_players
        raise PlayerDoesNotExist()

    def undo_last_match(self) -> tuple[Optional[str], Optional[int], Optional[str], Optional[int]]:
        matches = self.cdf_backend.get_matches()

        if not matches or True:  # Todo: fix undo
            return None, None, None, None

        latest_match = matches[0]

        if latest_match.player1_score > latest_match.player2_score:
            winner = self.get_player(player_id=latest_match.player1_id)
            winner_prev_rating = latest_match.player1_rating
            loser = self.get_player(player_id=latest_match.player2_id)
            loser_prev_rating = latest_match.player2_rating
        else:
            winner = self.get_player(player_id=latest_match.player2_id)
            winner_prev_rating = latest_match.player2_rating
            loser = self.get_player(player_id=latest_match.player1_id)
            loser_prev_rating = latest_match.player1_rating

        # CDF_BACKEND.delete_matches(ids=[latest_match.id])
        self.cdf_backend.update_player(winner.id, new_rating=winner_prev_rating)
        self.cdf_backend.update_player(loser.id, new_rating=loser_prev_rating)
        return winner.name, winner_prev_rating, loser.name, loser_prev_rating

    def get_leaderboard(self) -> str:
        players = self.cdf_backend.list_players()
        matches = self.cdf_backend.get_matches()
        active_players = [p for p in players if self.__has_played_match(matches, p)]
        active_players = sorted(active_players, key=lambda p: p.get_rating(Sport.PING_PONG), reverse=True)
        printable_leaderboard = "\n".join(
            ["{}. {} ({})".format(i + 1, p.name, p.get_rating(Sport.PING_PONG)) for i, p in enumerate(active_players)]
        )
        return printable_leaderboard

    @staticmethod
    def __has_played_match(matches: list[Match], player: Player) -> bool:
        for match in matches:
            if match.player1_id == player.id or match.player2_id == player.id:
                return True
        return False

    def get_total_matches(self) -> int:
        matches = self.cdf_backend.get_matches()
        return len(matches)

    def get_player_stats(self, name: str) -> tuple[int, int, int, str]:
        players = self.cdf_backend.get_players([name])
        try:
            player = next(player for player in players if player.name == name)
        except StopIteration:
            raise PlayerDoesNotExist()
        wins = 0
        losses = 0
        matches = self.cdf_backend.get_matches()
        for match in matches:
            if match.player1_id == player.id:
                if match.player1_score > match.player2_score:
                    wins += 1
                else:
                    losses += 1
            elif match.player2_id == player.id:
                if match.player2_score > match.player1_score:
                    wins += 1
                else:
                    losses += 1
        wl_ratio = "{:.2f}".format(wins / losses) if losses > 0 else "∞"
        return player.get_rating(Sport.PING_PONG), wins, losses, wl_ratio

    @staticmethod
    def calculate_new_elo_ratings(rating1: int, rating2: int, player1_win: bool) -> tuple[int, int]:
        t1 = 10 ** (rating1 / 400)
        t2 = 10 ** (rating2 / 400)
        e1 = t1 / (t1 + t2)
        e2 = t2 / (t1 + t2)
        s1 = 1 if player1_win else 0
        s2 = 0 if player1_win else 1
        new_rating1 = rating1 + int(round(32 * (s1 - e1)))
        new_rating2 = rating2 + int(round(32 * (s2 - e2)))
        return new_rating1, new_rating2
