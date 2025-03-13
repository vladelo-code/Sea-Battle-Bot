import random
import string


# Функция для генерации ключа игры
def generate_game_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
