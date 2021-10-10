from typing import Optional

from src.backend.backend import Backend
from src.backend.data_classes import Hand, Match, Player, Sport
from src.backend.rating import RatingCalculator, Ratings


class PlayerDoesNotExist(Exception):
    pass


class InvalidMatchRegistration(Exception):
    pass


class PingPongService:
    def __init__(self, backend: Backend) -> None:
        self._backend = backend

    def add_new_player(self, id: str) -> Player:
        player = Player(id, id, Ratings())
        return self._backend.create_player(player)

    def get_player(self, player_id: str) -> Player:
        players = self._backend.get_players(ids=[player_id])
        if players:
            return players[0]
        raise PlayerDoesNotExist()

    def update_display_name(self, player: Player, new_name: str) -> bool:
        players = self._backend.list_players()
        names = [p.name.lower() for p in players]
        if new_name.lower() in names:
            return False
        self._backend.update_player(player.id, name=new_name)
        return True

    def add_match(
        self, p1_id: str, p1_hand: Hand, p2_id: str, p2_hand: Hand, score_p1: int, score_p2: int
    ) -> tuple[Player, int, Player, int]:
        if p1_id == p2_id or int(score_p1) == int(score_p2):
            raise InvalidMatchRegistration()

        p1 = self.get_player(p1_id)
        p2 = self.get_player(p2_id)

        if p1 and p2:
            match = Match(
                p1_id,
                p2_id,
                score_p1,
                score_p2,
                p1.ratings.get(p1_hand, Sport.PING_PONG),
                p2.ratings.get(p2_hand, Sport.PING_PONG),
                sport=Sport.PING_PONG,
                player1_hand=p1_hand,
                player2_hand=p2_hand,
            )
            self._backend.create_match(match)

            new_rating1, new_rating2 = RatingCalculator.calculate_new_elo_ratings(
                rating1=p1.ratings.get(p1_hand, Sport.PING_PONG),
                rating2=p2.ratings.get(p2_hand, Sport.PING_PONG),
                player1_win=int(match.player1_score) > int(match.player2_score),
            )
            new_p1 = self._backend.update_player(
                p1.id, ratings=p1.ratings.update(p1_hand, Sport.PING_PONG, new_rating1)
            )
            new_p2 = self._backend.update_player(
                p2.id, ratings=p2.ratings.update(p2_hand, Sport.PING_PONG, new_rating2)
            )

            updated_players = (
                new_p1,
                new_p1.ratings.get(p1_hand, Sport.PING_PONG) - p1.ratings.get(p1_hand, Sport.PING_PONG),
                new_p2,
                new_p2.ratings.get(p2_hand, Sport.PING_PONG) - p2.ratings.get(p2_hand, Sport.PING_PONG),
            )
            return updated_players
        raise PlayerDoesNotExist()

    def undo_last_match(self) -> tuple[Optional[str], Optional[int], Optional[str], Optional[int]]:
        matches = self._backend.get_matches(sport=Sport.PING_PONG)

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
        self._backend.update_player(winner.id, sport=Sport.PING_PONG, new_rating=winner_prev_rating)
        self._backend.update_player(loser.id, sport=Sport.PING_PONG, new_rating=loser_prev_rating)
        return winner.name, winner_prev_rating, loser.name, loser_prev_rating

    def get_leaderboard(self) -> str:
        players = self._backend.list_players()
        matches = self._backend.get_matches(sport=Sport.PING_PONG)
        active_players = [p for p in players if self.__has_played_match(matches, p)]
        active_players = sorted(
            active_players, key=lambda p: p.ratings.get(Hand.DOMINANT, Sport.PING_PONG), reverse=True
        )
        printable_leaderboard = "\n".join(
            [
                "{}. {} ({})".format(i + 1, p.name, p.ratings.get(Hand.DOMINANT, Sport.PING_PONG))
                for i, p in enumerate(active_players)
            ]
        )
        return printable_leaderboard

    @staticmethod
    def __has_played_match(matches: list[Match], player: Player) -> bool:
        for match in matches:
            if match.player1_id == player.id or match.player2_id == player.id:
                return True
        return False

    def get_total_matches(self) -> int:
        matches = self._backend.get_matches(sport=Sport.PING_PONG)
        return len(matches)

    def get_player_stats(self, name: str) -> tuple[int, int, int, str]:
        players = self._backend.list_players()
        try:
            player = next(player for player in players if player.name == name)
        except StopIteration:
            raise PlayerDoesNotExist()
        wins = 0
        losses = 0
        matches = self._backend.get_matches(sport=Sport.PING_PONG)
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
        return player.ratings.get(Hand.DOMINANT, Sport.PING_PONG), wins, losses, wl_ratio
