from __future__ import annotations

import hashlib
import random
from datetime import date

from game_encoding import decode_game_b64, encode_game_b64

# Player mark states
MARK_EMPTY = 0
MARK_CIRCLE = 1
MARK_QUEEN = 2


class GenerationCancelled(Exception):
    """Raised when puzzle generation is cancelled."""
    pass


class Game:

    def __init__(self, size: int, max_solutions: int = 1, max_attempts: int = 50000,
                 seed: int | None = None, kingdom_strategy: str = 'mixed',
                 cancel_check: callable | None = None,
                 queen_placement: str = 'backtrack') -> None:
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
            cancel_check: Optional callable that returns True if generation should stop
            queen_placement: Queen placement algorithm:
                - 'backtrack': Fast backtracking (default, slight diagonal bias)
                - 'uniform': Rejection sampling (uniform distribution, no diagonal bias)
        """
        self.size = size
        self.max_solutions = max_solutions
        self.kingdom_strategy = kingdom_strategy
        self.queen_placement = queen_placement
        self._cancel_check = cancel_check

        # Set up seed for reproducibility
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        self.seed = seed
        random.seed(seed)

        # For larger boards, use best-of-N strategy instead of rejection sampling
        if size >= 8:
            self._generate_with_restarts(size, kingdom_strategy, max_solutions, max_attempts)
        else:
            self._generate_rejection_sampling(size, kingdom_strategy, max_solutions, max_attempts)

    def _is_cancelled(self) -> bool:
        """Check if generation has been cancelled."""
        return self._cancel_check is not None and self._cancel_check()

    def _place_queens(self, no: int) -> list[tuple[int, int]]:
        """Dispatch to the selected queen placement algorithm."""
        if self.queen_placement == 'uniform':
            return self.place_queens_uniform(no)
        return self.place_queens(no)

    def _generate_rejection_sampling(self, size: int, kingdom_strategy: str,
                                      max_solutions: int, max_attempts: int) -> None:
        """Traditional approach: generate until we find one with few solutions."""
        for attempt in range(max_attempts):
            # Check for cancellation every 100 attempts
            if attempt % 100 == 0 and self._is_cancelled():
                raise GenerationCancelled()

            self.queens = self._place_queens(size)
            self.kingdoms = self.create_kingdoms(self.queens, kingdom_strategy)
            solutions = self.count_solutions(max_count=max_solutions + 1)
            if 1 <= solutions <= max_solutions:
                self.num_solutions = solutions
                self.attempts = attempt + 1
                return
        raise ValueError(f"Could not generate puzzle with <={max_solutions} solutions after {max_attempts} attempts")

    def _generate_with_restarts(self, size: int, kingdom_strategy: str,
                                max_solutions: int, max_attempts: int) -> None:
        """Try best-of-N with restarts on fresh seeds when refinement stalls."""
        max_rounds = 5
        total_attempts = 0
        for round_num in range(max_rounds):
            if round_num > 0:
                # Fresh seed for each restart
                self.seed = random.randint(0, 2**31 - 1)
                random.seed(self.seed)
            if self._is_cancelled():
                raise GenerationCancelled()
            success = self._generate_best_of_n(
                size, kingdom_strategy, max_solutions, max_attempts
            )
            total_attempts += self.attempts
            if success:
                self.attempts = total_attempts
                return
        self.attempts = total_attempts
        raise ValueError(
            f"Could not generate puzzle with <={max_solutions} solutions "
            f"after {max_rounds} rounds ({total_attempts} attempts)"
        )

    def _generate_best_of_n(self, size: int, kingdom_strategy: str,
                            max_solutions: int, max_attempts: int) -> bool:
        """Generate N candidates, pick the best, then refine with local search."""
        # Phase 1: Best-of-N sampling - more samples for larger boards
        batch_size = min(5000 if size <= 8 else 8000, max_attempts)

        best_queens: list[tuple[int, int]] | None = None
        best_kingdoms: list[list[int]] | None = None
        best_solutions = 999999

        # Higher comparison limit to properly rank candidates
        comparison_limit = 200

        for attempt in range(batch_size):
            # Check for cancellation every 100 attempts
            if attempt % 100 == 0 and self._is_cancelled():
                raise GenerationCancelled()

            self.queens = self._place_queens(size)
            self.kingdoms = self.create_kingdoms(self.queens, kingdom_strategy)

            solutions = self.count_solutions(max_count=min(best_solutions, comparison_limit))

            if solutions <= max_solutions:
                self.num_solutions = solutions
                self.attempts = attempt + 1
                return True

            if solutions < best_solutions:
                best_solutions = solutions
                best_queens = self.queens
                best_kingdoms = [row[:] for row in self.kingdoms]

        if best_queens is None or best_kingdoms is None:
            self.attempts = batch_size
            return False

        # Phase 2: Local search refinement
        self.queens = best_queens
        self.kingdoms = [row[:] for row in best_kingdoms]
        current_solutions = best_solutions

        # Simple hill-climbing with more iterations for larger boards
        max_refinement = 2000 if size <= 8 else 5000
        no_improve_limit = 500 if size <= 8 else 1000
        no_improve = 0

        for refinement_step in range(max_refinement):
            # Check for cancellation every 100 steps
            if refinement_step % 100 == 0 and self._is_cancelled():
                raise GenerationCancelled()

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

        self.attempts = batch_size
        if current_solutions > max_solutions:
            return False

        self.num_solutions = current_solutions
        return True

    def _try_boundary_swap(self, current_solutions: int) -> int | None:
        """Try swapping a boundary cell between kingdoms. Returns new solution count if improved."""
        no = self.size
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Find all boundary cells (cells adjacent to a different kingdom)
        boundary_cells: list[tuple[int, int, int, int]] = []  # (row, col, from_kingdom, to_kingdom)

        for row in range(no):
            for col in range(no):
                # Skip queen cells - they must stay in their kingdom
                if (row, col) in set(self.queens):
                    continue

                current_k = self.kingdoms[row][col]

                for d_row, d_col in directions:
                    n_row, n_col = row + d_row, col + d_col
                    if 0 <= n_row < no and 0 <= n_col < no:
                        neighbor_k = self.kingdoms[n_row][n_col]
                        if neighbor_k != current_k:
                            # This cell can potentially move to neighbor's kingdom
                            boundary_cells.append((row, col, current_k, neighbor_k))
                            break

        if not boundary_cells:
            return None

        # Pick a random boundary cell and try the swap
        row, col, from_k, to_k = random.choice(boundary_cells)

        # Check if moving this cell would disconnect the from_kingdom
        # (Simple check: the from_kingdom must still be connected after removal)
        if not self._would_stay_connected(row, col, from_k):
            return None

        # Make the swap
        self.kingdoms[row][col] = to_k

        # Count solutions
        new_solutions = self.count_solutions(max_count=current_solutions)

        if new_solutions < current_solutions:
            # Keep the swap
            return new_solutions
        else:
            # Revert the swap
            self.kingdoms[row][col] = from_k
            return None

    def _would_stay_connected(self, remove_row: int, remove_col: int, kingdom: int) -> bool:
        """Check if kingdom would stay connected after removing cell (remove_row, remove_col)."""
        no = self.size
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # Find all cells in this kingdom except the one being removed
        kingdom_cells = []
        for row in range(no):
            for col in range(no):
                if self.kingdoms[row][col] == kingdom and (row, col) != (remove_row, remove_col):
                    kingdom_cells.append((row, col))

        if len(kingdom_cells) <= 1:
            return True  # Single cell or empty is trivially connected

        # BFS to check connectivity
        start = kingdom_cells[0]
        visited = {start}
        queue = [start]

        while queue:
            row, col = queue.pop(0)
            for d_row, d_col in directions:
                n_row, n_col = row + d_row, col + d_col
                if (n_row, n_col) in kingdom_cells and (n_row, n_col) not in visited:
                    visited.add((n_row, n_col))
                    queue.append((n_row, n_col))

        return len(visited) == len(kingdom_cells)

    def place_queens(self, no: int) -> list[tuple[int, int]]:
        """Place queens using backtracking with random row/column order."""
        def is_valid(placed: dict[int, int], row: int, col: int) -> bool:
            for placed_row, placed_col in placed.items():
                if placed_col == col:
                    return False
                if abs(placed_row - row) <= 1 and abs(placed_col - col) <= 1:
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

        rows = list(range(no))
        random.shuffle(rows)

        result = backtrack(0, rows, {})
        if result is None:
            raise ValueError(f"Cannot place {no} queens on {no}x{no} board")
        return [(row, result[row]) for row in range(no)]

    def place_queens_uniform(self, no: int) -> list[tuple[int, int]]:
        """Place queens using rejection sampling for uniform distribution.

        Shuffles a random permutation and checks the adjacency constraint.
        Rejects overly diagonal layouts (|row-col correlation| > 0.5).
        """
        mean = (no - 1) / 2.0
        var = sum((r - mean) ** 2 for r in range(no)) / no
        max_corr = 0.5

        for _ in range(10000):
            cols = list(range(no))
            random.shuffle(cols)
            if not all(abs(cols[i] - cols[i + 1]) >= 2 for i in range(no - 1)):
                continue
            cov = sum((r - mean) * (cols[r] - mean) for r in range(no)) / no
            if var > 0 and abs(cov / var) > max_corr:
                continue
            return [(row, cols[row]) for row in range(no)]
        raise ValueError(f"Cannot place {no} queens on {no}x{no} board")

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
                    line += "Q "
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
        attacked_by: dict[tuple[int, int], set[int]] = {
            (row, col): set() for row in range(no) for col in range(no)
        }

        for k, (queen_row, queen_col) in enumerate(queens):
            # Same row
            for col in range(no):
                if col != queen_col:
                    attacked_by[(queen_row, col)].add(k)
            # Same column
            for row in range(no):
                if row != queen_row:
                    attacked_by[(row, queen_col)].add(k)
            # Adjacent cells
            for d_row in [-1, 0, 1]:
                for d_col in [-1, 0, 1]:
                    if d_row == 0 and d_col == 0:
                        continue
                    n_row, n_col = queen_row + d_row, queen_col + d_col
                    if 0 <= n_row < no and 0 <= n_col < no:
                        attacked_by[(n_row, n_col)].add(k)

        # Cells attacked by OTHER queens (not this kingdom's queen) are safe to add
        def is_attacked_by_others(row: int, col: int, k: int) -> bool:
            """Check if cell is attacked by any queen other than kingdom k's queen."""
            attackers = attacked_by[(row, col)]
            return bool(attackers - {k})

        # Assign growth strategy
        if kingdom_strategy == 'classic':
            strategies = [0] * no
        elif kingdom_strategy == 'jagged':
            strategies = [1] * no
        else:
            strategies = [random.choice([-1, 0, 1]) for _ in range(no)]

        def get_free_neighbors(row: int, col: int) -> list[tuple[int, int]]:
            neighbors: list[tuple[int, int]] = []
            for d_row, d_col in directions:
                n_row, n_col = row + d_row, col + d_col
                if 0 <= n_row < no and 0 <= n_col < no and kingdoms[n_row][n_col] == -1:
                    neighbors.append((n_row, n_col))
            return neighbors

        def count_same_kingdom_neighbors(row: int, col: int, k: int) -> int:
            count = 0
            for d_row, d_col in directions:
                n_row, n_col = row + d_row, col + d_col
                if 0 <= n_row < no and 0 <= n_col < no and kingdoms[n_row][n_col] == k:
                    count += 1
            return count

        def perimeter_change(row: int, col: int, k: int) -> int:
            adjacent = count_same_kingdom_neighbors(row, col, k)
            return 4 - 2 * adjacent

        def pick_neighbor(neighbors: list[tuple[int, int]], k: int) -> tuple[int, int]:
            """Pick a neighbor, ALWAYS preferring cells attacked by other queens."""
            # Cells attacked by other queens cannot be valid queen positions for this kingdom
            safe_neighbors = [(row, col) for row, col in neighbors if is_attacked_by_others(row, col, k)]

            # ALWAYS prefer safe cells to minimize solutions (100%)
            if safe_neighbors:
                neighbors = safe_neighbors

            strategy = strategies[k]
            if strategy == 0 or len(neighbors) == 1:
                return random.choice(neighbors)

            candidates = [(n_row, n_col, perimeter_change(n_row, n_col, k)) for n_row, n_col in neighbors]

            if strategy == 1:
                target = max(change for _, _, change in candidates)
            else:
                target = min(change for _, _, change in candidates)

            best = [(n_row, n_col) for n_row, n_col, change in candidates if change == target]
            return random.choice(best)

        # Initialize: each queen starts a kingdom
        frontier = []
        for k, (row, col) in enumerate(queens):
            kingdoms[row][col] = k
            frontier.append([(row, col)])

        total = no * no
        filled = len(queens)

        # First ensure each kingdom has at least 2 cells
        for k, (row, col) in enumerate(queens):
            neighbors = get_free_neighbors(row, col)
            if neighbors:
                safe = [(n_row, n_col) for n_row, n_col in neighbors if is_attacked_by_others(n_row, n_col, k)]
                choice_from = safe if safe else neighbors
                n_row, n_col = random.choice(choice_from)
                kingdoms[n_row][n_col] = k
                frontier[k].append((n_row, n_col))
                filled += 1

        # Grow kingdoms until board is full
        while filled < total:
            active = [k for k in range(len(queens)) if frontier[k]]
            if not active:
                break

            k = random.choice(active)
            cell_idx = random.randrange(len(frontier[k]))
            row, col = frontier[k][cell_idx]

            neighbors = get_free_neighbors(row, col)

            if neighbors:
                n_row, n_col = pick_neighbor(neighbors, k)
                kingdoms[n_row][n_col] = k
                frontier[k].append((n_row, n_col))
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
            for placed_row, placed_col in placed:
                # Same row or column
                if placed_row == row or placed_col == col:
                    return False
                # Adjacent (including diagonal)
                if abs(placed_row - row) <= 1 and abs(placed_col - col) <= 1:
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
            for placed_row, placed_col in placed:
                if placed_row == row or placed_col == col:
                    return False
                if abs(placed_row - row) <= 1 and abs(placed_col - col) <= 1:
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

    def calculate_difficulty(self) -> int:
        """Calculate difficulty score based on solver backtrack count.

        Higher score = more difficult puzzle.
        Returns the number of backtrack steps needed to find the first solution.
        """
        no = self.size
        num_kingdoms = no

        # Build list of cells for each kingdom
        kingdom_cells: list[list[tuple[int, int]]] = [[] for _ in range(num_kingdoms)]
        for row in range(no):
            for col in range(no):
                k = self.kingdoms[row][col]
                kingdom_cells[k].append((row, col))

        def is_valid_placement(placed: list[tuple[int, int]], row: int, col: int) -> bool:
            for placed_row, placed_col in placed:
                if placed_row == row or placed_col == col:
                    return False
                if abs(placed_row - row) <= 1 and abs(placed_col - col) <= 1:
                    return False
            return True

        backtrack_count = [0]
        found = [False]

        def backtrack(kingdom_idx: int, placed: list[tuple[int, int]]) -> None:
            if found[0]:
                return

            if kingdom_idx == num_kingdoms:
                found[0] = True
                return

            for row, col in kingdom_cells[kingdom_idx]:
                if is_valid_placement(placed, row, col):
                    placed.append((row, col))
                    backtrack(kingdom_idx + 1, placed)
                    placed.pop()
                    if found[0]:
                        return
                    backtrack_count[0] += 1

        backtrack(0, [])
        return backtrack_count[0]

    def encode(self) -> str:
        """Encode this game to a shareable base64 string."""
        return encode_game_b64(self.kingdoms, self.queens)

    @classmethod
    def from_code(cls, code: str) -> Game:
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


# -----------------------------------------------------------------------------
# Player mark validation
# -----------------------------------------------------------------------------

def validate_player_marks(
    kingdoms: list[list[int]],
    cell_marks: list[list[int]]
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    """Validate player's marks and find problems.

    Args:
        kingdoms: The kingdom grid (from Game.kingdoms)
        cell_marks: Player's marks grid (MARK_EMPTY/MARK_CIRCLE/MARK_QUEEN)

    Returns:
        (conflicts, blocked) where:
        - conflicts: Queen positions that conflict (same row/col/kingdom or adjacent)
        - blocked: Circle positions in fully-blocked rows/columns/kingdoms
    """
    n = len(kingdoms)
    conflicts: set[tuple[int, int]] = set()
    blocked: set[tuple[int, int]] = set()

    # Collect marked queens and build kingdom map
    marked_queens: list[tuple[int, int]] = []
    kingdom_cells: dict[int, list[tuple[int, int]]] = {}
    for row in range(n):
        for col in range(n):
            if cell_marks[row][col] == MARK_QUEEN:
                marked_queens.append((row, col))
            k = kingdoms[row][col]
            if k not in kingdom_cells:
                kingdom_cells[k] = []
            kingdom_cells[k].append((row, col))

    # Check queen conflicts (same row, column, kingdom, or adjacent)
    for i, (row1, col1) in enumerate(marked_queens):
        for row2, col2 in marked_queens[i + 1:]:
            same_row = row1 == row2
            same_col = col1 == col2
            adjacent = abs(row1 - row2) <= 1 and abs(col1 - col2) <= 1
            same_kingdom = kingdoms[row1][col1] == kingdoms[row2][col2]
            if same_row or same_col or adjacent or same_kingdom:
                conflicts.add((row1, col1))
                conflicts.add((row2, col2))

    # Check blocked kingdoms (all cells are circles)
    for cells in kingdom_cells.values():
        has_queen = any(cell_marks[row][col] == MARK_QUEEN for row, col in cells)
        all_circles = all(cell_marks[row][col] == MARK_CIRCLE for row, col in cells)
        if not has_queen and all_circles:
            blocked.update(cells)

    # Check blocked rows
    for row in range(n):
        has_queen = any(cell_marks[row][col] == MARK_QUEEN for col in range(n))
        all_circles = all(cell_marks[row][col] == MARK_CIRCLE for col in range(n))
        if not has_queen and all_circles:
            blocked.update((row, col) for col in range(n))

    # Check blocked columns
    for col in range(n):
        has_queen = any(cell_marks[row][col] == MARK_QUEEN for row in range(n))
        all_circles = all(cell_marks[row][col] == MARK_CIRCLE for row in range(n))
        if not has_queen and all_circles:
            blocked.update((row, col) for row in range(n))

    return conflicts, blocked


def check_player_solution(
    kingdoms: list[list[int]],
    cell_marks: list[list[int]]
) -> bool:
    """Check if player's marks represent a valid solution.

    A valid solution has exactly one queen per kingdom with no conflicts.
    """
    n = len(kingdoms)

    # Count queens and check kingdom assignment
    kingdom_queens: dict[int, tuple[int, int]] = {}
    for row in range(n):
        for col in range(n):
            if cell_marks[row][col] == MARK_QUEEN:
                k = kingdoms[row][col]
                if k in kingdom_queens:
                    return False  # More than one queen in kingdom
                kingdom_queens[k] = (row, col)

    # Must have exactly one queen per kingdom
    if len(kingdom_queens) != n:
        return False

    # Check no conflicts
    conflicts, _ = validate_player_marks(kingdoms, cell_marks)
    return len(conflicts) == 0


SECRET = "yaque_daily_puzzle_2024"


def get_daily_seed(day: date, size: int, secret: str = SECRET, offset: int = 0) -> int:
    """Generate a reproducible seed for a given date and puzzle size."""
    data = f"{day.isoformat()}:{size}:{secret}:{offset}"
    hash_bytes = hashlib.sha256(data.encode()).digest()
    # Use first 4 bytes as seed (31 bits to stay positive)
    seed = int.from_bytes(hash_bytes[:4], 'big') & 0x7FFFFFFF
    return seed


def get_daily_game(day: date, size: int, secret: str = SECRET,
                   max_solutions: int = 1, max_seed_attempts: int = 100,
                   kingdom_strategy: str = 'jagged', cancel_check: callable | None = None) -> Game:
    """Generate a daily puzzle for a given date and size, trying multiple seeds if needed.

    First tries to find a puzzle with max_solutions, then falls back to higher limits.
    """
    # Try progressively relaxed solution limits
    solution_tiers = [max_solutions]
    if max_solutions < 4:
        solution_tiers.append(4)
    if max_solutions < 10:
        solution_tiers.append(10)

    for tier_max in solution_tiers:
        for offset in range(max_seed_attempts):
            seed = get_daily_seed(day, size, secret, offset)
            try:
                game = Game(size, max_solutions=tier_max, seed=seed,
                           kingdom_strategy=kingdom_strategy, cancel_check=cancel_check)
                game.seed_offset = offset  # Store which offset worked
                return game
            except (ValueError, GenerationCancelled):
                if cancel_check and cancel_check():
                    raise GenerationCancelled() from None
                continue

    raise ValueError(f"Could not generate puzzle for {day} size {size} after all attempts")


def get_daily_games(day: date | None = None, secret: str = SECRET, max_solutions: int = 1) -> dict[int, Game]:
    """Generate the 3 daily puzzles (sizes 6, 7, 8) for a given date."""
    if day is None:
        day = date.today()

    games = {}
    for size in [6, 7, 8]:
        games[size] = get_daily_game(day, size, secret, max_solutions=max_solutions)

    return games
