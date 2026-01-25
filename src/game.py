import random
from typing import List, Tuple

class Game:

    def __init__(self, size: int, max_solutions: int = 1, max_attempts: int = 50000):
        self.size = size
        self.max_solutions = max_solutions
        # Generate puzzles until we find one with acceptable number of solutions
        for attempt in range(max_attempts):
            self.queens: List[Tuple[int, int]] = self.place_queens(size)
            self.kingdoms: List[List[int]] = self.create_kingdoms(self.queens)
            solutions = self.count_solutions(max_count=max_solutions + 1)
            if 1 <= solutions <= max_solutions:
                self.num_solutions = solutions
                self.attempts = attempt + 1
                break
        else:
            raise ValueError(f"Could not generate puzzle with <={max_solutions} solutions after {max_attempts} attempts")

    def place_queens(self, no) -> List[Tuple[int, int]]:
        def is_valid(queens, row, col):
            for r, c in queens:
                if c == col:
                    return False
                if abs(r - row) <= 1 and abs(c - col) <= 1:
                    return False
            return True

        def backtrack(row, queens):
            if row == no:
                return queens[:]
            cols = list(range(no))
            random.shuffle(cols)
            for col in cols:
                if is_valid(queens, row, col):
                    queens.append((row, col))
                    result = backtrack(row + 1, queens)
                    if result is not None:
                        return result
                    queens.pop()
            return None

        result = backtrack(0, [])
        if result is None:
            raise ValueError(f"Cannot place {no} queens on {no}x{no} board")
        return result

    def print_queens(self):
        queen_set = set(self.queens)
        for row in range(self.size):
            line = ""
            for col in range(self.size):
                if (row, col) in queen_set:
                    line += "Q "
                else:
                    line += ". "
            print(line)

    def print_kingdoms(self):
        queen_set = set(self.queens)
        for row in range(self.size):
            line = ""
            for col in range(self.size):
                k = self.kingdoms[row][col]
                if (row, col) in queen_set:
                    line += f"Q "
                else:
                    line += f"{k} "
            print(line)

    def create_kingdoms(self, queens: List[Tuple[int, int]]) -> List[List[int]]:
        no = self.size
        kingdoms = [[-1] * no for _ in range(no)]
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        def get_free_neighbors(r, c):
            neighbors = []
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < no and 0 <= nc < no and kingdoms[nr][nc] == -1:
                    neighbors.append((nr, nc))
            return neighbors

        # Initialize: each queen starts a kingdom
        frontier = []
        for k, (r, c) in enumerate(queens):
            kingdoms[r][c] = k
            frontier.append([(r, c)])

        total = no * no
        filled = len(queens)

        # First ensure each kingdom has at least 2 cells (no single-cell kingdoms)
        for k, (r, c) in enumerate(queens):
            neighbors = get_free_neighbors(r, c)
            if neighbors:
                nr, nc = random.choice(neighbors)
                kingdoms[nr][nc] = k
                frontier[k].append((nr, nc))
                filled += 1

        # Grow kingdoms randomly until board is full
        while filled < total:
            active = [k for k in range(len(queens)) if frontier[k]]
            if not active:
                break

            k = random.choice(active)
            cell_idx = random.randrange(len(frontier[k]))
            r, c = frontier[k][cell_idx]

            neighbors = get_free_neighbors(r, c)

            if neighbors:
                nr, nc = random.choice(neighbors)
                kingdoms[nr][nc] = k
                frontier[k].append((nr, nc))
                filled += 1
            else:
                frontier[k].pop(cell_idx)

        return kingdoms

    def count_solutions(self, max_count: int = 2) -> int:
        """Count solutions for the puzzle, stopping early if we exceed max_count."""
        no = self.size
        num_kingdoms = no

        # Build list of cells for each kingdom
        kingdom_cells: List[List[Tuple[int, int]]] = [[] for _ in range(num_kingdoms)]
        for row in range(no):
            for col in range(no):
                k = self.kingdoms[row][col]
                kingdom_cells[k].append((row, col))

        def is_valid_placement(placed: List[Tuple[int, int]], row: int, col: int) -> bool:
            for r, c in placed:
                # Same row or column
                if r == row or c == col:
                    return False
                # Adjacent (including diagonal)
                if abs(r - row) <= 1 and abs(c - col) <= 1:
                    return False
            return True

        solutions_found = [0]  # Use list to allow modification in nested function

        def backtrack(kingdom_idx: int, placed: List[Tuple[int, int]]):
            if solutions_found[0] >= max_count:
                return

            if kingdom_idx == num_kingdoms:
                solutions_found[0] += 1
                return

            for row, col in kingdom_cells[kingdom_idx]:
                if is_valid_placement(placed, row, col):
                    placed.append((row, col))
                    backtrack(kingdom_idx + 1, placed)
                    placed.pop()
                    if solutions_found[0] >= max_count:
                        return

        backtrack(0, [])
        return solutions_found[0]


def main():
    game = Game(7)
    game.print_kingdoms()
    print(f"\nSolutions: {game.count_solutions(max_count=10)}")


if __name__ == "__main__":
    main()

