import random
from typing import List, Tuple, Optional, Set

# Задаем размер игрового поля
BOARD_SIZE = 10

DIRECTIONS_8 = [(-1, -1), (-1, 0), (-1, 1),  # Верхняя строка
                (0, -1), (0, 1),  # Левая и правая ячейки
                (1, -1), (1, 0), (1, 1)]  # Нижняя строка

Board = List[List[str]]


def create_empty_board() -> Board:
    """
    Создает пустое игровое поле размером BOARD_SIZE x BOARD_SIZE.
    """
    return [["⬜" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def print_board(board: Board, hide_ships: bool = False) -> str:
    """
    Возвращает строку для отображения игрового поля.

    :param board: Игровое поле.
    :param hide_ships: Если True, скрывает корабли на поле.
    """
    letters = "ABCDEFGHIJ"
    header = "  1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟"
    rows = []

    for i, row in enumerate(board):
        line = []
        for cell in row:
            if hide_ships and cell == "🚢":
                line.append("⬜")
            elif cell in {"🚢", "❌", "💥"}:
                line.append(cell)
            else:
                line.append("⬜")
        rows.append(f"{letters[i]} " + " ".join(line))

    # Оборачиваем в моноширный текст, чтобы всё было ровно
    return "<code>\n" + header + "\n" + "\n".join(rows) + "\n</code>"


def place_ship(board: Board, x: int, y: int, size: int, orientation: str) -> bool:
    """
    Пытается разместить корабль на поле.

    :param board: Игровое поле.
    :param x: Начальная координата по X.
    :param y: Начальная координата по Y.
    :param size: Размер корабля.
    :param orientation: Направление ('horizontal' или 'vertical').
    :return: True, если размещение успешно; иначе False.
    """
    if orientation == "horizontal":
        if y + size > BOARD_SIZE:
            return False
        # Проверяем каждую клетку на наличие соседних кораблей
        for i in range(size):
            if board[x][y + i] != "⬜" or not is_valid_position(board, x, y + i):
                return False
        # Размещаем корабль
        for i in range(size):
            board[x][y + i] = "🚢"
    else:
        if x + size > BOARD_SIZE:
            return False
        # Проверяем каждую клетку на наличие соседних кораблей
        for i in range(size):
            if board[x + i][y] != "⬜" or not is_valid_position(board, x + i, y):
                return False
        # Размещаем корабль
        for i in range(size):
            board[x + i][y] = "🚢"
    return True


def place_all_ships(board: Board) -> None:
    """
    Размещает все корабли на поле по заданным размерам.

    :param board: Игровое поле.
    """
    ship_sizes = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
    for size in ship_sizes:
        placed = False
        while not placed:
            x = random.randint(0, BOARD_SIZE - 1)
            y = random.randint(0, BOARD_SIZE - 1)
            orientation = random.choice(["horizontal", "vertical"])
            placed = place_ship(board, x, y, size, orientation)


def is_valid_position(board: Board, x: int, y: int) -> bool:
    """
    Проверяет, нет ли кораблей в соседних клетках (включая диагонали).

    :param board: Игровое поле.
    :param x: Координата X.
    :param y: Координата Y.
    :return: True, если положение валидно; иначе False.
    """
    for dx, dy in DIRECTIONS_8:
        nx, ny = x + dx, y + dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
            if board[nx][ny] == "🚢":
                return False
    return True


def mark_surrounding(board: Board, x: int, y: int) -> None:
    """
    Закрашивает клетки вокруг уничтоженного корабля.

    :param board: Игровое поле.
    :param x: Координата X.
    :param y: Координата Y.
    """
    for dx, dy in DIRECTIONS_8:
        nx, ny = x + dx, y + dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[nx][ny] == "⬜":
            board[nx][ny] = "❌"


def is_ship_destroyed(board: Board, x: int, y: int, visited: Optional[Set[Tuple[int, int]]] = None) -> Tuple[
    bool, List[Tuple[int, int]]]:
    """
    Проверяет, уничтожен ли корабль, начиная с клетки (x, y).

    :param board: Игровое поле.
    :param x: Координата X.
    :param y: Координата Y.
    :param visited: Множество уже проверенных клеток.
    :return: Кортеж (уничтожен ли, список координат всех поврежденных клеток корабля).
    """
    if visited is None:
        visited = set()
    if (x, y) in visited or board[x][y] != "💥":
        return True, []  # Если клетка не повреждена или уже проверена

    visited.add((x, y))
    ship_cells = [(x, y)]
    destroyed = True

    # Проверяем все соседние клетки (вверх, вниз, влево, вправо)
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
            if board[nx][ny] == "🚢":
                return False, []  # Корабль не уничтожен
            if board[nx][ny] == "💥" and (nx, ny) not in visited:
                sub_destroyed, sub_cells = is_ship_destroyed(board, nx, ny, visited)
                destroyed = destroyed and sub_destroyed
                ship_cells.extend(sub_cells)

    return destroyed, ship_cells


def handle_ship_destruction(board: Board, x: int, y: int) -> None:
    """
    Проверяет и обрабатывает полное уничтожение корабля.

    :param board: Игровое поле.
    :param x: Координата попадания X.
    :param y: Координата попадания Y.
    """
    destroyed, ship_cells = is_ship_destroyed(board, x, y)
    if destroyed:
        for sx, sy in ship_cells:
            mark_surrounding(board, sx, sy)


def process_shot(board: Board, x: int, y: int) -> Optional[bool]:
    """
    Обрабатывает выстрел по координатам.

    :param board: Игровое поле.
    :param x: Координата X.
    :param y: Координата Y.
    :return: True — попадание, False — промах, None — недопустимый ход.
    """
    if board[x][y] == "🚢":
        board[x][y] = "💥"
        handle_ship_destruction(board, x, y)  # Проверка и закрашивание
        return True
    elif board[x][y] == "⬜":
        board[x][y] = "❌"
        return False
    return None


def check_victory(board: Board) -> bool:
    """
    Проверяет, остались ли корабли на поле.

    :param board: Игровое поле.
    :return: True, если победа (кораблей не осталось); иначе False.
    """
    for row in board:
        if "🚢" in row:
            return False
    return True
