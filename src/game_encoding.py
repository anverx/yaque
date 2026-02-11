"""Game encoding/decoding for compact sharing."""

import base64


def _bits_needed(n: int) -> int:
    """Number of bits needed to represent values 0 to n-1."""
    if n <= 1:
        return 1
    return (n - 1).bit_length()


def _pack_bits(values: list[int], bits_per_value: int) -> bytes:
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


def _unpack_bits(data: bytes, num_values: int, bits_per_value: int) -> list[int]:
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


def encode_game(kingdoms: list[list[int]], queens: list[tuple[int, int]]) -> bytes:
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


def decode_game(data: bytes) -> tuple[list[list[int]], list[tuple[int, int]]]:
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


def encode_game_b64(kingdoms: list[list[int]], queens: list[tuple[int, int]]) -> str:
    """Encode a game to a URL-safe base64 string for sharing."""
    data = encode_game(kingdoms, queens)
    # Use URL-safe base64 and strip padding for shorter strings
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def decode_game_b64(code: str) -> tuple[list[list[int]], list[tuple[int, int]]]:
    """Decode a base64 string to (kingdoms, queens)."""
    # Add back padding if needed
    padding = 4 - (len(code) % 4)
    if padding != 4:
        code += '=' * padding
    data = base64.urlsafe_b64decode(code)
    return decode_game(data)


# -----------------------------------------------------------------------------
# Board state encoding (for saving/restoring play progress)
# -----------------------------------------------------------------------------

def encode_board_state(cell_marks: list[list[int]]) -> str:
    """
    Encode board state to a compact base64 string.

    Each cell can be: 0 (empty), 1 (queen), 2 (X/no-queen) = 2 bits per cell.
    Format: 1 byte size + packed 2-bit cell values.

    8x8: 1 + 16 = 17 bytes -> ~24 chars base64
    7x7: 1 + 13 = 14 bytes -> ~20 chars base64
    6x6: 1 + 9 = 10 bytes -> ~16 chars base64
    """
    n = len(cell_marks)
    # Flatten to 1D list
    values = [cell_marks[r][c] for r in range(n) for c in range(n)]

    # Pack: size byte + 2 bits per cell
    data = bytes([n]) + _pack_bits(values, 2)
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def decode_board_state(encoded: str) -> list[list[int]]:
    """
    Decode a base64 string back to 2D cell_marks array.

    Returns list of lists with cell values (0=empty, 1=queen, 2=X).
    """
    # Add back padding if needed
    padding = 4 - (len(encoded) % 4)
    if padding != 4:
        encoded += '=' * padding
    data = base64.urlsafe_b64decode(encoded)

    n = data[0]
    num_cells = n * n
    values = _unpack_bits(data[1:], num_cells, 2)

    # Reshape to 2D
    return [values[r * n:(r + 1) * n] for r in range(n)]
