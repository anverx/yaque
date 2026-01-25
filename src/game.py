from typing import List, Tuple

class Game:

    def __init__(self, size: int):

        queens:List[Tuple[int, int]] = self.place_queens(size)
        kingdoms: List[List[int]] = self.create_kingdoms(queens)
        # game:List[List[int]] = []

    def place_queens(self, no)->List[Tuple[int, int]]:
        pass

    def create_kingdoms(self, queens:List[Tuple[int, int]] )->List[List[int]]:
        pass

