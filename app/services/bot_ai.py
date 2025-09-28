from __future__ import annotations

import random
from typing import List, Optional, Tuple

from app.game_logic import BOARD_SIZE


Coordinate = Tuple[int, int]


class BotAI:
    def __init__(self, difficulty: str):
        self.difficulty = difficulty  # easy | medium | hard
        self.tried: set[Coordinate] = set()
        self.targets: list[Coordinate] = []  # клетки для добивания
        self.first_hit: Optional[Coordinate] = None
        self.last_hit: Optional[Coordinate] = None

        # Для hard — предвычисляем клетки по «шахматной» схеме
        self.checker_cells: list[Coordinate] = [
            (x, y) for x in range(BOARD_SIZE) for y in range(BOARD_SIZE)
            if (x + y) % 2 == 0
        ]
        random.shuffle(self.checker_cells)

    def reset_ship_hunt(self) -> None:
        self.targets.clear()
        self.first_hit = None
        self.last_hit = None

    def _neighbors(self, x: int, y: int) -> List[Coordinate]:
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
        candidates = [
            (x, y)
            for x in range(BOARD_SIZE)
            for y in range(BOARD_SIZE)
            if (x, y) not in self.tried
        ]
        return random.choice(candidates)

    def _random_checker_untried(self) -> Optional[Coordinate]:
        for coord in list(self.checker_cells):
            if coord not in self.tried:
                return coord
        return None

    def choose_shot(self) -> Coordinate:
        # easy — просто случайный ход по нестрелянным клеткам
        if self.difficulty == "easy":
            return self._random_untried()

        # medium/hard — если есть цели для добивания — бьем туда
        if self.targets:
            return self.targets.pop(0)

        # hard — сначала шахматные клетки
        if self.difficulty == "hard":
            coord = self._random_checker_untried()
            if coord is not None:
                return coord

        # medium/hard fallback — случайно
        return self._random_untried()

    def process_result(self, coord: Coordinate, hit: Optional[bool], ship_destroyed: bool) -> None:
        # hit: True — попадание, False — мимо, None — неверный ход (не должно происходить)
        self.tried.add(coord)

        if hit:
            x, y = coord
            if self.first_hit is None:
                self.first_hit = coord
            self.last_hit = coord

            if ship_destroyed:
                # корабль добит — очистим состояние охоты
                self.reset_ship_hunt()
            else:
                # добавим соседние клетки в очередь целей
                for nx, ny in self._neighbors(x, y):
                    if (nx, ny) not in self.tried and (nx, ny) not in self.targets:
                        self.targets.append((nx, ny))
        else:
            # мимо — ничего не делаем (на medium/hard вернемся к случайным/шахматным)
            pass


