import random
from typing import List, Optional, Tuple

from app.game_logic import BOARD_SIZE

Coordinate = Tuple[int, int]


class BotAI:
    """
    Класс AI бота для Морского боя с тремя уровнями сложности: easy, medium, hard.
    В режиме hard бот использует комбинированную стратегию:
    - случайные выстрелы,
    - шахматная схема,
    - "знание" о координатах кораблей (читерство).
    Также реализована логика добивания корабля с корректным определением линии.
    """

    # Вероятности для hard режима
    CHEAT_PROBABILITY = 0.1  # 10% вероятность читерства
    CHECKER_PROBABILITY = 0.5  # 50% вероятность шахматной схемы
    RANDOM_PROBABILITY = 0.4  # 40% вероятность случайного выбора

    def __init__(self, difficulty: str, enemy_board: Optional[List[List[str]]] = None):
        self.difficulty = difficulty  # easy | medium | hard
        self.tried: set[Coordinate] = set()
        self.targets: list[Coordinate] = []  # клетки для добивания
        self.first_hit: Optional[Coordinate] = None
        self.last_hit: Optional[Coordinate] = None
        self.ship_positions: set[Coordinate] = set()  # для hard уровня - "знание" о кораблях
        self.hit_sequence: list[Coordinate] = []  # последовательность попаданий для определения направления
        self.ship_direction: Optional[str] = None  # 'horizontal' или 'vertical' для hard режима

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
        self.ship_direction = None

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

        # 1. ПРИОРИТЕТ: Если есть цели для добивания — бьем туда
        if self.targets:
            return self.targets.pop(0)

        # 2. Для hard режима - выбор стратегии по независимым вероятностям
        if self.difficulty == "hard":
            return self._choose_hard_strategy()

        # 3. medium — шахматные клетки
        if self.difficulty == "medium":
            coord = self._random_checker_untried()
            if coord is not None:
                return coord

        # 4. fallback — случайно
        return self._random_untried()

    def process_result(self, coord: Coordinate, hit: Optional[bool], ship_destroyed: bool) -> None:
        """
        Обрабатывает результат выстрела:
        - Добавляет клетку в tried
        - Если попадание — обновляет hit_sequence и генерирует новые цели
        - Если корабль уничтожен — сбрасывает охоту
        """
        was_targeting_shot = coord in self.targets
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

            # Удаляем попавшую цель из списка, если она там была
            if was_targeting_shot and coord in self.targets:
                self.targets.remove(coord)

            if ship_destroyed:
                # корабль добит — очистим состояние охоты
                self.reset_ship_hunt()
            else:
                if len(self.hit_sequence) == 1:
                    # Первое попадание - добавляем все 4 соседние клетки
                    for nx, ny in self._neighbors(x, y):
                        if (nx, ny) not in self.tried and (nx, ny) not in self.targets:
                            self.targets.append((nx, ny))
                else:
                    # Второе и последующие попадания - обновляем цели вдоль линии
                    self._update_targets_by_direction()
        else:
            # Промах
            if was_targeting_shot and coord in self.targets:
                self.targets.remove(coord)
            if self.hit_sequence:
                self._update_targets_after_miss(coord)

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

    def _choose_hard_strategy(self) -> Coordinate:
        """Выбирает стратегию для hard режима на основе независимых вероятностей"""
        possible_coords: List[Coordinate] = []

        # Читерство
        if random.random() < self.CHEAT_PROBABILITY:
            cheat_coord = self._get_known_ship_position()
            if cheat_coord is not None:
                possible_coords.append(cheat_coord)

        # Шахматная схема
        if random.random() < self.CHECKER_PROBABILITY:
            checker_coord = self._random_checker_untried()
            if checker_coord is not None:
                possible_coords.append(checker_coord)

        # Рандом
        if random.random() < self.RANDOM_PROBABILITY:
            random_coord = self._random_untried()
            possible_coords.append(random_coord)

        if possible_coords:
            return random.choice(possible_coords)

        # Fallback
        return self._random_untried()

    def _update_targets_by_direction(self) -> None:
        """Обновляет цели для добивания на основе направления корабля"""
        if len(self.hit_sequence) < 2:
            return

        # Определяем направление по первым двум попаданиям
        first = self.hit_sequence[0]
        second = self.hit_sequence[1]

        dx = second[0] - first[0]
        dy = second[1] - first[1]

        # Нормализуем
        dx = 0 if dx == 0 else dx // abs(dx)
        dy = 0 if dy == 0 else dy // abs(dy)

        self.ship_direction = 'horizontal' if dx != 0 else 'vertical'

        self.targets.clear()

        if self.ship_direction == 'horizontal':
            y_coord = first[1]
            min_x = min(c[0] for c in self.hit_sequence)
            max_x = max(c[0] for c in self.hit_sequence)

            # Проверяем левую сторону
            for x in range(min_x - 1, -1, -1):
                coord = (x, y_coord)
                if coord not in self.tried:
                    self.targets.append(coord)
                else:
                    break

            # Проверяем правую сторону
            for x in range(max_x + 1, BOARD_SIZE):
                coord = (x, y_coord)
                if coord not in self.tried:
                    self.targets.append(coord)
                else:
                    break
        else:
            x_coord = first[0]
            min_y = min(c[1] for c in self.hit_sequence)
            max_y = max(c[1] for c in self.hit_sequence)

            # Проверяем верх
            for y in range(min_y - 1, -1, -1):
                coord = (x_coord, y)
                if coord not in self.tried:
                    self.targets.append(coord)
                else:
                    break

            # Проверяем низ
            for y in range(max_y + 1, BOARD_SIZE):
                coord = (x_coord, y)
                if coord not in self.tried:
                    self.targets.append(coord)
                else:
                    break

    def _update_targets_after_miss(self, missed_coord: Coordinate) -> None:
        """
        Обновляет цели после промаха на одном конце линии:
        - Если промахнулись на краю линии, бот переключается на противоположную сторону.
        - Если промах где-то в середине — бот не меняет стратегию полностью.
        """
        if not self.hit_sequence or not self.ship_direction:
            return

        self.targets.clear()

        if self.ship_direction == 'horizontal':
            y_coord = self.hit_sequence[0][1]
            min_x = min(c[0] for c in self.hit_sequence)
            max_x = max(c[0] for c in self.hit_sequence)

            # Промах слева → идем вправо
            if missed_coord[0] <= min_x:
                for x in range(max_x + 1, BOARD_SIZE):
                    coord = (x, y_coord)
                    if coord not in self.tried:
                        self.targets.append(coord)
                        break
            # Промах справа → идем влево
            elif missed_coord[0] >= max_x:
                for x in range(min_x - 1, -1, -1):
                    coord = (x, y_coord)
                    if coord not in self.tried:
                        self.targets.append(coord)
                        break

        else:  # vertical
            x_coord = self.hit_sequence[0][0]
            min_y = min(c[1] for c in self.hit_sequence)
            max_y = max(c[1] for c in self.hit_sequence)

            # Промах сверху → идем вниз
            if missed_coord[1] <= min_y:
                for y in range(max_y + 1, BOARD_SIZE):
                    coord = (x_coord, y)
                    if coord not in self.tried:
                        self.targets.append(coord)
                        break
            # Промах снизу → идем вверх
            elif missed_coord[1] >= max_y:
                for y in range(min_y - 1, -1, -1):
                    coord = (x_coord, y)
                    if coord not in self.tried:
                        self.targets.append(coord)
                        break
