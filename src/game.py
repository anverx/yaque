import random
import hashlib
import base64
from datetime import date
from typing import List, Tuple, Optional, Dict

class Game:

    def __init__(self, size: int, max_solutions: int = 1, max_attempts: int = 50000, seed: Optional[int] = None):
        self.size = size
        self.max_solutions = max_solutions

        # Set up seed for reproducibility
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        self.seed = seed
        random.seed(seed)

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


# ============================================================================
# Game encoding/decoding for compact sharing
# ============================================================================

def _bits_needed(n: int) -> int:
    """Number of bits needed to represent values 0 to n-1."""
    if n <= 1:
        return 1
    return (n - 1).bit_length()


def _pack_bits(values: List[int], bits_per_value: int) -> bytes:
    """Pack a list of values into bytes, each value using bits_per_value bits."""
    result = []
    current_byte = 0
    bits_in_current = 0

    for value in values:
        remaining_bits = bits_per_value
        while remaining_bits > 0:
            space_in_byte = 8 - bits_in_current
            bits_to_add = min(remaining_bits, space_in_byte)

            # Extract the top bits_to_add bits from the remaining value
            shift = remaining_bits - bits_to_add
            bits = (value >> shift) & ((1 << bits_to_add) - 1)

            # Add to current byte
            current_byte = (current_byte << bits_to_add) | bits
            bits_in_current += bits_to_add
            remaining_bits -= bits_to_add

            if bits_in_current == 8:
                result.append(current_byte)
                current_byte = 0
                bits_in_current = 0

    # Pad final byte if needed
    if bits_in_current > 0:
        current_byte <<= (8 - bits_in_current)
        result.append(current_byte)

    return bytes(result)


def _unpack_bits(data: bytes, num_values: int, bits_per_value: int) -> List[int]:
    """Unpack values from bytes."""
    values = []
    bit_index = 0

    for _ in range(num_values):
        value = 0
        for _ in range(bits_per_value):
            byte_index = bit_index // 8
            bit_in_byte = 7 - (bit_index % 8)
            if byte_index < len(data):
                bit = (data[byte_index] >> bit_in_byte) & 1
                value = (value << 1) | bit
            bit_index += 1
        values.append(value)

    return values


def encode_game(kingdoms: List[List[int]], queens: List[Tuple[int, int]]) -> bytes:
    """
    Encode a game (kingdoms + queens) to bytes.

    Format:
    - 1 byte: board size (N)
    - ceil(N * bits_per_queen / 8) bytes: queen columns (one per row)
    - ceil(N * (N-1) / 8) bytes: horizontal internal borders
    - ceil((N-1) * N / 8) bytes: vertical internal borders

    Total for 8x8: 1 + 3 + 7 + 7 = 18 bytes
    """
    n = len(kingdoms)
    bits_per_queen = _bits_needed(n)

    # Extract queen columns (queens sorted by row)
    queen_cols = [col for row, col in sorted(queens)]

    # Extract horizontal internal borders (between row and row+1)
    h_borders = []
    for row in range(n - 1):
        for col in range(n):
            has_border = 1 if kingdoms[row][col] != kingdoms[row + 1][col] else 0
            h_borders.append(has_border)

    # Extract vertical internal borders (between col and col+1)
    v_borders = []
    for row in range(n):
        for col in range(n - 1):
            has_border = 1 if kingdoms[row][col] != kingdoms[row][col + 1] else 0
            v_borders.append(has_border)

    # Pack everything
    result = bytes([n])
    result += _pack_bits(queen_cols, bits_per_queen)
    result += _pack_bits(h_borders, 1)
    result += _pack_bits(v_borders, 1)

    return result


def decode_game(data: bytes) -> Tuple[List[List[int]], List[Tuple[int, int]]]:
    """
    Decode bytes to (kingdoms, queens).

    Reconstructs kingdoms by flood-filling from queen positions using border data.
    """
    n = data[0]
    bits_per_queen = _bits_needed(n)

    # Calculate byte boundaries
    queen_bits = n * bits_per_queen
    queen_bytes = (queen_bits + 7) // 8
    h_border_count = (n - 1) * n
    h_border_bytes = (h_border_count + 7) // 8
    v_border_count = n * (n - 1)

    # Unpack queen columns
    queen_data = data[1:1 + queen_bytes]
    queen_cols = _unpack_bits(queen_data, n, bits_per_queen)
    queens = [(row, col) for row, col in enumerate(queen_cols)]

    # Unpack horizontal borders
    h_start = 1 + queen_bytes
    h_data = data[h_start:h_start + h_border_bytes]
    h_borders = _unpack_bits(h_data, h_border_count, 1)

    # Unpack vertical borders
    v_start = h_start + h_border_bytes
    v_data = data[v_start:]
    v_borders = _unpack_bits(v_data, v_border_count, 1)

    # Build border lookup tables
    # h_border[row][col] = True if border between (row,col) and (row+1,col)
    h_border = [[False] * n for _ in range(n - 1)]
    idx = 0
    for row in range(n - 1):
        for col in range(n):
            h_border[row][col] = h_borders[idx] == 1
            idx += 1

    # v_border[row][col] = True if border between (row,col) and (row,col+1)
    v_border = [[False] * (n - 1) for _ in range(n)]
    idx = 0
    for row in range(n):
        for col in range(n - 1):
            v_border[row][col] = v_borders[idx] == 1
            idx += 1

    # Flood fill from each queen to determine kingdoms
    kingdoms = [[-1] * n for _ in range(n)]

    for k, (qr, qc) in enumerate(queens):
        stack = [(qr, qc)]
        while stack:
            r, c = stack.pop()
            if kingdoms[r][c] != -1:
                continue
            kingdoms[r][c] = k

            # Up: no horizontal border above means connected
            if r > 0 and not h_border[r - 1][c] and kingdoms[r - 1][c] == -1:
                stack.append((r - 1, c))
            # Down: no horizontal border below means connected
            if r < n - 1 and not h_border[r][c] and kingdoms[r + 1][c] == -1:
                stack.append((r + 1, c))
            # Left: no vertical border to the left means connected
            if c > 0 and not v_border[r][c - 1] and kingdoms[r][c - 1] == -1:
                stack.append((r, c - 1))
            # Right: no vertical border to the right means connected
            if c < n - 1 and not v_border[r][c] and kingdoms[r][c + 1] == -1:
                stack.append((r, c + 1))

    return kingdoms, queens


def encode_game_b64(kingdoms: List[List[int]], queens: List[Tuple[int, int]]) -> str:
    """Encode a game to a URL-safe base64 string for sharing."""
    data = encode_game(kingdoms, queens)
    # Use URL-safe base64 and strip padding for shorter strings
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def decode_game_b64(code: str) -> Tuple[List[List[int]], List[Tuple[int, int]]]:
    """Decode a base64 string to (kingdoms, queens)."""
    # Add back padding if needed
    padding = 4 - (len(code) % 4)
    if padding != 4:
        code += '=' * padding
    data = base64.urlsafe_b64decode(code)
    return decode_game(data)


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

