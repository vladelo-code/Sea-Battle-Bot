def calculate_elo(winner_rating: int, loser_rating: int, k: int = 32, winner_is_donor: bool = False) -> tuple[int, int]:
    """
    Вычисляет новые рейтинги игроков по системе Elo после завершения матча.
    Для доноров применяется бонус +20% к приросту рейтинга.

    :param winner_rating: Текущий рейтинг победителя.
    :param loser_rating: Текущий рейтинг проигравшего.
    :param k: Коэффициент чувствительности рейтинга (по умолчанию 32).
    :param winner_is_donor: Является ли победитель донором.
    :return: Кортеж из новых рейтингов (победителя, проигравшего).
    """
    expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    expected_loser = 1 / (1 + 10 ** ((winner_rating - loser_rating) / 400))

    # Базовый прирост рейтинга
    winner_change = k * (1 - expected_winner)
    loser_change = k * (0 - expected_loser)

    # Применяем бонус +20% для доноров при победе
    if winner_is_donor:
        winner_change *= 1.2

    new_winner_rating = round(winner_rating + winner_change)
    new_loser_rating = round(loser_rating + loser_change)

    return new_winner_rating, new_loser_rating
