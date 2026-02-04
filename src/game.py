import random
import hashlib
from datetime import date
from typing import List, Tuple, Optional, Dict

from game_encoding import encode_game, encode_game_b64, decode_game_b64

class Game:

    def __init__(self, size: int, max_solutions: int = 1, max_attempts: int = 50000,
                 seed: Optional[int] = None, kingdom_strategy: str = 'mixed'):
        """Create a new puzzle.

        Args:
            size: Board size (6, 7, 8, or 9)
            max_solutions: Maximum acceptable number of solutions
            max_attempts: Maximum generation attempts before giving up
            seed: Random seed for reproducibility
            kingdom_strategy: How to grow kingdoms:
                - 'classic': Original random growth
                - 'mixed': Each kingdom randomly picks jagged/compact/random
                - 'jagged': All kingdoms maximize perimeter (snaky shapes)
        """
        self.size = size
        self.max_solutions = max_solutions
        self.kingdom_strategy = kingdom_strategy

        # Set up seed for reproducibility
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        self.seed = seed
        random.seed(seed)

        # Generate puzzles until we find one with acceptable number of solutions
        for attempt in range(max_attempts):
            self.queens: List[Tuple[int, int]] = self.place_queens(size)
            self.kingdoms: List[List[int]] = self.create_kingdoms(self.queens, kingdom_strategy)
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

    def create_kingdoms(self, queens: List[Tuple[int, int]], kingdom_strategy: str = 'mixed') -> List[List[int]]:
        no = self.size
        kingdoms = [[-1] * no for _ in range(no)]
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Assign growth strategy to each kingdom based on overall strategy:
        # 1 = maximize perimeter (jagged), -1 = minimize (compact), 0 = random
        if kingdom_strategy == 'classic':
            strategies = [0] * no  # All random
        elif kingdom_strategy == 'jagged':
            strategies = [1] * no  # All maximize perimeter
        else:  # 'mixed'
            strategies = [random.choice([-1, 0, 1]) for _ in range(no)]

        def get_free_neighbors(r, c):
            neighbors = []
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < no and 0 <= nc < no and kingdoms[nr][nc] == -1:
                    neighbors.append((nr, nc))
            return neighbors

        def count_same_kingdom_neighbors(r, c, k):
            """Count how many neighbors of (r,c) belong to kingdom k."""
            count = 0
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < no and 0 <= nc < no and kingdoms[nr][nc] == k:
                    count += 1
            return count

        def perimeter_change(r, c, k):
            """Calculate perimeter change if cell (r,c) is added to kingdom k.
            +2 = extends outward (1 adjacent), 0 = neutral (2 adjacent), -2 = fills gap (3 adjacent)
            """
            adjacent = count_same_kingdom_neighbors(r, c, k)
            return 4 - 2 * adjacent

        def pick_neighbor(neighbors, k):
            """Pick a neighbor based on kingdom's growth strategy."""
            strategy = strategies[k]
            if strategy == 0 or len(neighbors) == 1:
                return random.choice(neighbors)

            # Calculate perimeter change for each candidate
            candidates = [(nr, nc, perimeter_change(nr, nc, k)) for nr, nc in neighbors]

            if strategy == 1:  # Maximize perimeter (jagged)
                target = max(change for _, _, change in candidates)
            else:  # strategy == -1, minimize perimeter (compact)
                target = min(change for _, _, change in candidates)

            best = [(nr, nc) for nr, nc, change in candidates if change == target]
            return random.choice(best)

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

        # Grow kingdoms until board is full
        while filled < total:
            active = [k for k in range(len(queens)) if frontier[k]]
            if not active:
                break

            k = random.choice(active)
            cell_idx = random.randrange(len(frontier[k]))
            r, c = frontier[k][cell_idx]

            neighbors = get_free_neighbors(r, c)

            if neighbors:
                nr, nc = pick_neighbor(neighbors, k)
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

    def encode(self) -> str:
        """Encode this game to a shareable base64 string."""
        return encode_game_b64(self.kingdoms, self.queens)

    @classmethod
    def from_code(cls, code: str) -> 'Game':
        """Create a Game from an encoded string."""
        kingdoms, queens = decode_game_b64(code)
        game = object.__new__(cls)
        game.size = len(kingdoms)
        game.kingdoms = kingdoms
        game.queens = queens
        game.max_solutions = None
        game.seed = None
        game.num_solutions = None
        game.attempts = None
        return game


SECRET = "yaque_daily_puzzle_2024"


def get_daily_seed(day: date, size: int, secret: str = SECRET, offset: int = 0) -> int:
    """Generate a reproducible seed for a given date and puzzle size."""
    data = f"{day.isoformat()}:{size}:{secret}:{offset}"
    hash_bytes = hashlib.sha256(data.encode()).digest()
    # Use first 4 bytes as seed (31 bits to stay positive)
    seed = int.from_bytes(hash_bytes[:4], 'big') & 0x7FFFFFFF
    return seed


def get_daily_game(day: date, size: int, secret: str = SECRET,
                   max_solutions: int = 1, max_seed_attempts: int = 100) -> Game:
    """Generate a daily puzzle for a given date and size, trying multiple seeds if needed."""
    for offset in range(max_seed_attempts):
        seed = get_daily_seed(day, size, secret, offset)
        try:
            game = Game(size, max_solutions=max_solutions, seed=seed)
            game.seed_offset = offset  # Store which offset worked
            return game
        except ValueError:
            continue
    raise ValueError(f"Could not generate puzzle for {day} size {size} after {max_seed_attempts} seed attempts")


def get_daily_games(day: date = None, secret: str = SECRET, max_solutions: int = 1) -> Dict[int, Game]:
    """Generate the 3 daily puzzles (sizes 6, 7, 8) for a given date."""
    if day is None:
        day = date.today()

    games = {}
    for size in [6, 7, 8]:
        games[size] = get_daily_game(day, size, secret, max_solutions=max_solutions)

    return games


def main():
    for size in [6, 7, 8]:
        print(f"\n{'='*40}")
        print(f"Testing {size}x{size} board:")
        print('='*40)

        game = Game(size, max_solutions=4)
        game.print_kingdoms()

        # Encode
        code = game.encode()
        raw_bytes = encode_game(game.kingdoms, game.queens)
        print(f"\nEncoded: {code}")
        print(f"Length: {len(code)} chars, {len(raw_bytes)} bytes")

        # Decode and verify
        decoded = Game.from_code(code)
        assert decoded.kingdoms == game.kingdoms, "Kingdoms mismatch!"
        assert decoded.queens == game.queens, "Queens mismatch!"
        print("Decode verified OK")


if __name__ == "__main__":
    main()

