import random
import string


def generate_game_id() -> str:
    """
    Генерирует уникальный идентификатор игры длиной 6 символов,
    состоящий из заглавных букв латинского алфавита и цифр.

    :return: Строка сгенерированного ID игры.
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
