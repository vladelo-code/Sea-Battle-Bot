def calculate_elo(winner_rating: int, loser_rating: int, k: int = 32) -> tuple[int, int]:
    expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    expected_loser = 1 / (1 + 10 ** ((winner_rating - loser_rating) / 400))

    new_winner_rating = round(winner_rating + k * (1 - expected_winner))
    new_loser_rating = round(loser_rating + k * (0 - expected_loser))

    return new_winner_rating, new_loser_rating
