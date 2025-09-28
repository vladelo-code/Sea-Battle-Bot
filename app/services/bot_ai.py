import random
from typing import List, Optional, Tuple

from app.game_logic import BOARD_SIZE

Coordinate = Tuple[int, int]


class BotAI:
    HARD_HIT_PROBABILITY = 0.7  # 70% вероятность использовать знание о кораблях в hard режиме

    def __init__(self, difficulty: str, enemy_board: Optional[List[List[str]]] = None):
        self.difficulty = difficulty  # easy | medium | hard
        self.tried: set[Coordinate] = set()
        self.targets: list[Coordinate] = []  # клетки для добивания
        self.first_hit: Optional[Coordinate] = None
        self.last_hit: Optional[Coordinate] = None
        self.ship_positions: set[Coordinate] = set()  # для hard уровня - "знание" о кораблях
        self.hit_sequence: list[Coordinate] = []  # последовательность попаданий для определения направления

        # Для medium/hard — предвычисляем клетки по «шахматной» схеме
        self.checker_cells: list[Coordinate] = [
            (x, y) for x in range(BOARD_SIZE) for y in range(BOARD_SIZE)
            if (x + y) % 2 == 0
        ]
        random.shuffle(self.checker_cells)

        # Для hard уровня - "знаем" позиции всех кораблей противника
        if difficulty == "hard" and enemy_board is not None:
            self._extract_ship_positions(enemy_board)

    def reset_ship_hunt(self) -> None:
        """Сбрасывает состояние охоты на корабль после его уничтожения"""
        self.targets.clear()
        self.first_hit = None
        self.last_hit = None
        self.hit_sequence.clear()

    def _neighbors(self, x: int, y: int) -> List[Coordinate]:
        """Возвращает соседние клетки (вверх, вниз, влево, вправо) для добивания"""
        res: List[Coordinate] = []
        if x > 0:
            res.append((x - 1, y))
        if x < BOARD_SIZE - 1:
            res.append((x + 1, y))
        if y > 0:
            res.append((x, y - 1))
        if y < BOARD_SIZE - 1:
            res.append((x, y + 1))
        return res

    def _random_untried(self) -> Coordinate:
        """Случайная клетка, по которой еще не стреляли"""
        candidates = [
            (x, y)
            for x in range(BOARD_SIZE)
            for y in range(BOARD_SIZE)
            if (x, y) not in self.tried
        ]
        return random.choice(candidates)

    def _random_checker_untried(self) -> Optional[Coordinate]:
        """Случайная клетка по шахматной схеме, по которой еще не стреляли"""
        for coord in list(self.checker_cells):
            if coord not in self.tried:
                return coord
        return None

    def choose_shot(self) -> Coordinate:
        """Выбирает следующую клетку для выстрела в зависимости от уровня сложности"""
        # Easy уровень - только случайные выстрелы, никакой стратегии
        if self.difficulty == "easy":
            return self._random_untried()

        # Если есть цели для добивания — бьем туда (для medium/hard)
        if self.targets:
            return self.targets.pop(0)

        # Hard — с вероятностью HARD_HIT_PROBABILITY "знаем" где корабль
        if self.difficulty == "hard" and random.random() < self.HARD_HIT_PROBABILITY:
            known_ship = self._get_known_ship_position()
            if known_ship is not None:
                return known_ship

        # medium/hard — шахматные клетки
        if self.difficulty in ["medium", "hard"]:
            coord = self._random_checker_untried()
            if coord is not None:
                return coord

        # fallback — случайно
        return self._random_untried()

    def process_result(self, coord: Coordinate, hit: Optional[bool], ship_destroyed: bool) -> None:
        """
        Обрабатывает результат выстрела:
        - Добавляет клетку в tried
        - Если попадание — обновляет hit_sequence и генерирует новые цели
        - Если корабль уничтожен — сбрасывает охоту
        """
        self.tried.add(coord)

        # Easy уровень - никакой стратегии добивания
        if self.difficulty == "easy":
            return

        if hit:
            x, y = coord
            if self.first_hit is None:
                self.first_hit = coord
            self.last_hit = coord
            self.hit_sequence.append(coord)

            if ship_destroyed:
                # корабль добит — очистим состояние охоты
                self.reset_ship_hunt()
            else:
                # Hard уровень - если 2+ попаданий подряд, добиваем вдоль линии
                if self.difficulty == "hard" and len(self.hit_sequence) >= 2:
                    self.targets = self._get_direction_targets()
                else:
                    # Medium/Hard уровни - добавляем соседние клетки для добивания
                    for nx, ny in self._neighbors(x, y):
                        if (nx, ny) not in self.tried and (nx, ny) not in self.targets:
                            self.targets.append((nx, ny))
        else:
            # мимо — ничего не делаем
            pass

    def _extract_ship_positions(self, enemy_board: List[List[str]]) -> None:
        """Для hard уровня - извлекаем реальные позиции всех кораблей противника"""
        self.ship_positions = set()
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                if enemy_board[x][y] == "🚢":
                    self.ship_positions.add((x, y))

    def _get_known_ship_position(self) -> Optional[Coordinate]:
        """Возвращает известную позицию корабля, если она еще не стреляна"""
        for coord in self.ship_positions:
            if coord not in self.tried:
                return coord
        return None

    def _get_direction_targets(self) -> List[Coordinate]:
        """
        Для hard уровня - возвращает клетки вдоль линии корабля для продолжения выстрелов.
        Логика исправлена: учитывает промахи с одной стороны и продолжает в противоположную сторону.
        """
        if len(self.hit_sequence) < 2:
            return []

        # Определяем направление по первым двум попаданиям
        first = self.hit_sequence[0]
        second = self.hit_sequence[1]

        dx = second[0] - first[0]
        dy = second[1] - first[1]

        if dx != 0:
            dx //= abs(dx)
        if dy != 0:
            dy //= abs(dy)

        direction_targets = []

        # Сортируем попадания по линии
        hits_sorted = sorted(self.hit_sequence, key=lambda c: (c[0], c[1]))

        # Проверяем оба конца линии и учитываем блокировки (промахи)
        for end in [hits_sorted[0], hits_sorted[-1]]:
            # Продолжаем в направлении линии
            nx, ny = end
            while True:
                nx += dx
                ny += dy
                if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE):
                    break
                if (nx, ny) in self.tried:
                    # если промахнута клетка — блокируем дальнейшее продолжение
                    break
                if (nx, ny) not in direction_targets:
                    direction_targets.append((nx, ny))

            # Противоположная сторона
            nx, ny = end
            while True:
                nx -= dx
                ny -= dy
                if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE):
                    break
                if (nx, ny) in self.tried:
                    break
                if (nx, ny) not in direction_targets:
                    direction_targets.append((nx, ny))

        return direction_targets
