from __future__ import annotations

import random
import hashlib
from datetime import date

from game_encoding import encode_game, encode_game_b64, decode_game_b64

class Game:

    def __init__(self, size: int, max_solutions: int = 1, max_attempts: int = 50000,
                 seed: int | None = None, kingdom_strategy: str = 'mixed') -> None:
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

        # For larger boards, use best-of-N strategy instead of rejection sampling
        if size >= 8:
            self._generate_best_of_n(size, kingdom_strategy, max_solutions, max_attempts)
        else:
            self._generate_rejection_sampling(size, kingdom_strategy, max_solutions, max_attempts)

    def _generate_rejection_sampling(self, size: int, kingdom_strategy: str,
                                      max_solutions: int, max_attempts: int) -> None:
        """Traditional approach: generate until we find one with few solutions."""
        for attempt in range(max_attempts):
            self.queens = self.place_queens(size)
            self.kingdoms = self.create_kingdoms(self.queens, kingdom_strategy)
            solutions = self.count_solutions(max_count=max_solutions + 1)
            if 1 <= solutions <= max_solutions:
                self.num_solutions = solutions
                self.attempts = attempt + 1
                return
        raise ValueError(f"Could not generate puzzle with <={max_solutions} solutions after {max_attempts} attempts")

    def _generate_best_of_n(self, size: int, kingdom_strategy: str,
                            max_solutions: int, max_attempts: int) -> None:
        """Generate N candidates, pick the best, then refine with local search."""
        # Phase 1: Best-of-N sampling - more samples for larger boards
        batch_size = min(5000 if size <= 8 else 8000, max_attempts)

        best_queens: list[tuple[int, int]] | None = None
        best_kingdoms: list[list[int]] | None = None
        best_solutions = 999999

        # Higher comparison limit to properly rank candidates
        comparison_limit = 200

        for attempt in range(batch_size):
            self.queens = self.place_queens(size)
            self.kingdoms = self.create_kingdoms(self.queens, kingdom_strategy)

            solutions = self.count_solutions(max_count=min(best_solutions, comparison_limit))

            if solutions <= max_solutions:
                self.num_solutions = solutions
                self.attempts = attempt + 1
                return

            if solutions < best_solutions:
                best_solutions = solutions
                best_queens = self.queens
                best_kingdoms = [row[:] for row in self.kingdoms]

        if best_queens is None or best_kingdoms is None:
            raise ValueError(f"Could not generate any puzzle after {batch_size} attempts")

        # Phase 2: Local search refinement
        self.queens = best_queens
        self.kingdoms = [row[:] for row in best_kingdoms]
        current_solutions = best_solutions

        # Simple hill-climbing with more iterations for larger boards
        max_refinement = 2000 if size <= 8 else 5000
        no_improve_limit = 500 if size <= 8 else 1000
        no_improve = 0

        for _ in range(max_refinement):
            if current_solutions <= max_solutions:
                break
            if no_improve >= no_improve_limit:
                break

            improved = self._try_boundary_swap(current_solutions)
            if improved is not None and improved < current_solutions:
                current_solutions = improved
                no_improve = 0
            else:
                no_improve += 1

        self.num_solutions = current_solutions
        self.attempts = batch_size

    def _try_boundary_swap(self, current_solutions: int) -> int | None:
        """Try swapping a boundary cell between kingdoms. Returns new solution count if improved."""
        no = self.size
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Find all boundary cells (cells adjacent to a different kingdom)
        boundary_cells: list[tuple[int, int, int, int]] = []  # (row, col, from_kingdom, to_kingdom)

        for r in range(no):
            for c in range(no):
                # Skip queen cells - they must stay in their kingdom
                if (r, c) in set(self.queens):
                    continue

                current_k = self.kingdoms[r][c]

                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < no and 0 <= nc < no:
                        neighbor_k = self.kingdoms[nr][nc]
                        if neighbor_k != current_k:
                            # This cell can potentially move to neighbor's kingdom
                            boundary_cells.append((r, c, current_k, neighbor_k))
                            break

        if not boundary_cells:
            return None

        # Pick a random boundary cell and try the swap
        r, c, from_k, to_k = random.choice(boundary_cells)

        # Check if moving this cell would disconnect the from_kingdom
        # (Simple check: the from_kingdom must still be connected after removal)
        if not self._would_stay_connected(r, c, from_k):
            return None

        # Make the swap
        self.kingdoms[r][c] = to_k

        # Count solutions
        new_solutions = self.count_solutions(max_count=current_solutions)

        if new_solutions < current_solutions:
            # Keep the swap
            return new_solutions
        else:
            # Revert the swap
            self.kingdoms[r][c] = from_k
            return None

    def _would_stay_connected(self, remove_r: int, remove_c: int, kingdom: int) -> bool:
        """Check if kingdom would stay connected after removing cell (remove_r, remove_c)."""
        no = self.size
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Find all cells in this kingdom except the one being removed
        kingdom_cells = []
        for r in range(no):
            for c in range(no):
                if self.kingdoms[r][c] == kingdom and (r, c) != (remove_r, remove_c):
                    kingdom_cells.append((r, c))

        if len(kingdom_cells) <= 1:
            return True  # Single cell or empty is trivially connected

        # BFS to check connectivity
        start = kingdom_cells[0]
        visited = {start}
        queue = [start]

        while queue:
            r, c = queue.pop(0)
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if (nr, nc) in kingdom_cells and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))

        return len(visited) == len(kingdom_cells)

    def place_queens(self, no: int) -> list[tuple[int, int]]:
        def is_valid(placed: dict[int, int], row: int, col: int) -> bool:
            for r, c in placed.items():
                if c == col:
                    return False
                if abs(r - row) <= 1 and abs(c - col) <= 1:
                    return False
            return True

        def backtrack(row_idx: int, rows: list[int], placed: dict[int, int]) -> dict[int, int] | None:
            if row_idx == no:
                return placed.copy()
            row = rows[row_idx]
            cols = list(range(no))
            random.shuffle(cols)
            for col in cols:
                if is_valid(placed, row, col):
                    placed[row] = col
                    result = backtrack(row_idx + 1, rows, placed)
                    if result is not None:
                        return result
                    del placed[row]
            return None

        # Process rows in random order to distribute "freedom" evenly
        rows = list(range(no))
        random.shuffle(rows)

        result = backtrack(0, rows, {})
        if result is None:
            raise ValueError(f"Cannot place {no} queens on {no}x{no} board")
        return [(r, result[r]) for r in range(no)]

    def print_queens(self) -> None:
        queen_set = set(self.queens)
        for row in range(self.size):
            line = ""
            for col in range(self.size):
                if (row, col) in queen_set:
                    line += "Q "
                else:
                    line += ". "
            print(line)

    def print_kingdoms(self) -> None:
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

    def create_kingdoms(self, queens: list[tuple[int, int]], kingdom_strategy: str = 'mixed') -> list[list[int]]:
        """Create kingdoms using constrained growth to minimize solutions.

        Key insight: For a puzzle to have few solutions, each kingdom should have
        few valid queen positions. A cell is "attacked" if it shares a row/column
        with another queen or is adjacent to one. By preferring attacked cells,
        we ensure each kingdom's queen position is one of very few valid spots.
        """
        no = self.size
        kingdoms = [[-1] * no for _ in range(no)]
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Build attack map: for each cell, which queens attack it
        queen_set = set(queens)
        attacked_by: dict[tuple[int, int], set[int]] = {(r, c): set() for r in range(no) for c in range(no)}

        for k, (qr, qc) in enumerate(queens):
            # Same row
            for c in range(no):
                if c != qc:
                    attacked_by[(qr, c)].add(k)
            # Same column
            for r in range(no):
                if r != qr:
                    attacked_by[(r, qc)].add(k)
            # Adjacent cells
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = qr + dr, qc + dc
                    if 0 <= nr < no and 0 <= nc < no:
                        attacked_by[(nr, nc)].add(k)

        # Cells attacked by OTHER queens (not this kingdom's queen) are safe to add
        def is_attacked_by_others(r: int, c: int, k: int) -> bool:
            """Check if cell is attacked by any queen other than kingdom k's queen."""
            attackers = attacked_by[(r, c)]
            return bool(attackers - {k})

        # Assign growth strategy
        if kingdom_strategy == 'classic':
            strategies = [0] * no
        elif kingdom_strategy == 'jagged':
            strategies = [1] * no
        else:
            strategies = [random.choice([-1, 0, 1]) for _ in range(no)]

        def get_free_neighbors(r: int, c: int) -> list[tuple[int, int]]:
            neighbors: list[tuple[int, int]] = []
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < no and 0 <= nc < no and kingdoms[nr][nc] == -1:
                    neighbors.append((nr, nc))
            return neighbors

        def count_same_kingdom_neighbors(r: int, c: int, k: int) -> int:
            count = 0
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < no and 0 <= nc < no and kingdoms[nr][nc] == k:
                    count += 1
            return count

        def perimeter_change(r: int, c: int, k: int) -> int:
            adjacent = count_same_kingdom_neighbors(r, c, k)
            return 4 - 2 * adjacent

        def pick_neighbor(neighbors: list[tuple[int, int]], k: int) -> tuple[int, int]:
            """Pick a neighbor, ALWAYS preferring cells attacked by other queens."""
            # Cells attacked by other queens cannot be valid queen positions for this kingdom
            safe_neighbors = [(r, c) for r, c in neighbors if is_attacked_by_others(r, c, k)]

            # ALWAYS prefer safe cells to minimize solutions (100%)
            if safe_neighbors:
                neighbors = safe_neighbors

            strategy = strategies[k]
            if strategy == 0 or len(neighbors) == 1:
                return random.choice(neighbors)

            candidates = [(nr, nc, perimeter_change(nr, nc, k)) for nr, nc in neighbors]

            if strategy == 1:
                target = max(change for _, _, change in candidates)
            else:
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

        # First ensure each kingdom has at least 2 cells
        for k, (r, c) in enumerate(queens):
            neighbors = get_free_neighbors(r, c)
            if neighbors:
                safe = [(nr, nc) for nr, nc in neighbors if is_attacked_by_others(nr, nc, k)]
                choice_from = safe if safe else neighbors
                nr, nc = random.choice(choice_from)
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
        kingdom_cells: list[list[tuple[int, int]]] = [[] for _ in range(num_kingdoms)]
        for row in range(no):
            for col in range(no):
                k = self.kingdoms[row][col]
                kingdom_cells[k].append((row, col))

        def is_valid_placement(placed: list[tuple[int, int]], row: int, col: int) -> bool:
            for r, c in placed:
                # Same row or column
                if r == row or c == col:
                    return False
                # Adjacent (including diagonal)
                if abs(r - row) <= 1 and abs(c - col) <= 1:
                    return False
            return True

        solutions_found = [0]  # Use list to allow modification in nested function

        def backtrack(kingdom_idx: int, placed: list[tuple[int, int]]) -> None:
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

    def find_all_solutions(self, max_count: int = 100) -> list[list[tuple[int, int]]]:
        """Find all solutions for the puzzle, up to max_count."""
        no = self.size
        num_kingdoms = no

        # Build list of cells for each kingdom
        kingdom_cells: list[list[tuple[int, int]]] = [[] for _ in range(num_kingdoms)]
        for row in range(no):
            for col in range(no):
                k = self.kingdoms[row][col]
                kingdom_cells[k].append((row, col))

        def is_valid_placement(placed: list[tuple[int, int]], row: int, col: int) -> bool:
            for r, c in placed:
                if r == row or c == col:
                    return False
                if abs(r - row) <= 1 and abs(c - col) <= 1:
                    return False
            return True

        solutions: list[list[tuple[int, int]]] = []

        def backtrack(kingdom_idx: int, placed: list[tuple[int, int]]) -> None:
            if len(solutions) >= max_count:
                return

            if kingdom_idx == num_kingdoms:
                solutions.append(list(placed))
                return

            for row, col in kingdom_cells[kingdom_idx]:
                if is_valid_placement(placed, row, col):
                    placed.append((row, col))
                    backtrack(kingdom_idx + 1, placed)
                    placed.pop()
                    if len(solutions) >= max_count:
                        return

        backtrack(0, [])
        return solutions

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


def get_daily_games(day: date | None = None, secret: str = SECRET, max_solutions: int = 1) -> dict[int, Game]:
    """Generate the 3 daily puzzles (sizes 6, 7, 8) for a given date."""
    if day is None:
        day = date.today()

    games = {}
    for size in [6, 7, 8]:
        games[size] = get_daily_game(day, size, secret, max_solutions=max_solutions)

    return games


def main() -> None:
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

