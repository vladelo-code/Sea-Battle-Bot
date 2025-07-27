import random

# Задаем размер игрового поля
BOARD_SIZE = 10


# Функция генерации чистого поля
def create_empty_board():
    return [["⬜" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


# Функция вывода поля
def print_board(board, hide_ships=False):
    letters = "ABCDEFGHIJ"
    header = "  1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟"
    rows = []

    for i, row in enumerate(board):
        line = []
        for cell in row:
            if hide_ships and cell == "🚢":
                line.append("⬜")
            elif cell == "🚢":
                line.append("🚢")
            elif cell == "❌":
                line.append("❌")
            elif cell == "💥":
                line.append("💥")
            else:
                line.append("⬜")
        rows.append(f"{letters[i]} " + " ".join(line))

    # Оборачиваем в моноширный текст, чтобы всё было ровно
    return "<code>\n" + header + "\n" + "\n".join(rows) + "\n</code>"


# Функция размещения кораблей на поле
def place_ship(board, x, y, size, orientation):
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


# Функция генерации кораблей на поле
def place_all_ships(board):
    ship_sizes = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
    for size in ship_sizes:
        placed = False
        while not placed:
            x = random.randint(0, BOARD_SIZE - 1)
            y = random.randint(0, BOARD_SIZE - 1)
            orientation = random.choice(["horizontal", "vertical"])
            placed = place_ship(board, x, y, size, orientation)


# Функция для проверки на отсутствие кораблей в соседних клетках (включая диагонали)
def is_valid_position(board, x, y):
    directions = [(-1, -1), (-1, 0), (-1, 1),  # Верхняя строка
                  (0, -1), (0, 1),  # Левая и правая ячейки
                  (1, -1), (1, 0), (1, 1)]  # Нижняя строка
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
            if board[nx][ny] == "🚢":
                return False
    return True


# Функция для закрашивания соседних клеток вокруг уничтоженного корабля
def mark_surrounding(board, x, y):
    directions = [(-1, -1), (-1, 0), (-1, 1),  # Верхняя строка
                  (0, -1), (0, 1),  # Левая и правая ячейки
                  (1, -1), (1, 0), (1, 1)]  # Нижняя строка
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[nx][ny] == "⬜":
            board[nx][ny] = "❌"


# Функция проверки уничтожен ли корабль, и собирает его координаты
def is_ship_destroyed(board, x, y, visited=None):
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


# Функция для обработки уничтожения корабля
def handle_ship_destruction(board, x, y):
    destroyed, ship_cells = is_ship_destroyed(board, x, y)
    if destroyed:
        for sx, sy in ship_cells:
            mark_surrounding(board, sx, sy)


# Функция для обработки хода (выстрела)
def process_shot(board, x, y):
    if board[x][y] == "🚢":
        board[x][y] = "💥"
        handle_ship_destruction(board, x, y)  # Проверка и закрашивание
        return True
    elif board[x][y] == "⬜":
        board[x][y] = "❌"
        return False
    return None


# Функция проверки на победу
def check_victory(board):
    for row in board:
        if "🚢" in row:
            return False
    return True
