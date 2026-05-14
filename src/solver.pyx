# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""Cython-compiled queens solver and kingdom builder.

Speeds up the backtracking solver and kingdom-growth algorithm by
~10-50x over pure Python. Random selection still happens via the
Python `random` module to preserve seed reproducibility (daily
puzzles depend on this).
"""

import random as _random

from libc.stdlib cimport malloc, free
from libc.string cimport memset


cdef inline bint _is_valid(int* placed_rows, int* placed_cols, int n_placed,
                           int row, int col) noexcept nogil:
    """Return 1 if (row, col) doesn't conflict with any placed queen."""
    cdef int i, pr, pc, dr, dc
    for i in range(n_placed):
        pr = placed_rows[i]
        pc = placed_cols[i]
        if pr == row or pc == col:
            return 0
        dr = pr - row
        if dr < 0:
            dr = -dr
        dc = pc - col
        if dc < 0:
            dc = -dc
        if dr <= 1 and dc <= 1:
            return 0
    return 1


cdef bint _backtrack(
    int kingdom_idx,
    int num_kingdoms,
    int* kingdom_offsets,
    int* kingdom_cell_rows,
    int* kingdom_cell_cols,
    int* placed_rows,
    int* placed_cols,
    list solutions,
    int max_count,
) noexcept:
    """Returns True if we should stop (max_count reached)."""
    cdef int start, end, i, row, col

    if len(solutions) >= max_count:
        return True

    if kingdom_idx == num_kingdoms:
        solutions.append([
            (placed_rows[k], placed_cols[k]) for k in range(num_kingdoms)
        ])
        return len(solutions) >= max_count

    start = kingdom_offsets[kingdom_idx]
    end = kingdom_offsets[kingdom_idx + 1]
    for i in range(start, end):
        row = kingdom_cell_rows[i]
        col = kingdom_cell_cols[i]
        if _is_valid(placed_rows, placed_cols, kingdom_idx, row, col):
            placed_rows[kingdom_idx] = row
            placed_cols[kingdom_idx] = col
            if _backtrack(
                kingdom_idx + 1, num_kingdoms,
                kingdom_offsets, kingdom_cell_rows, kingdom_cell_cols,
                placed_rows, placed_cols,
                solutions, max_count,
            ):
                return True
    return False


cdef bint _backtrack_count(
    int kingdom_idx,
    int num_kingdoms,
    int* kingdom_offsets,
    int* kingdom_cell_rows,
    int* kingdom_cell_cols,
    int* placed_rows,
    int* placed_cols,
    int* count,
    int max_count,
) noexcept nogil:
    """Counting variant; returns True when max_count is hit."""
    cdef int start, end, i, row, col

    if count[0] >= max_count:
        return True

    if kingdom_idx == num_kingdoms:
        count[0] += 1
        return count[0] >= max_count

    start = kingdom_offsets[kingdom_idx]
    end = kingdom_offsets[kingdom_idx + 1]
    for i in range(start, end):
        row = kingdom_cell_rows[i]
        col = kingdom_cell_cols[i]
        if _is_valid(placed_rows, placed_cols, kingdom_idx, row, col):
            placed_rows[kingdom_idx] = row
            placed_cols[kingdom_idx] = col
            if _backtrack_count(
                kingdom_idx + 1, num_kingdoms,
                kingdom_offsets, kingdom_cell_rows, kingdom_cell_cols,
                placed_rows, placed_cols,
                count, max_count,
            ):
                return True
    return False


cdef bint _backtrack_difficulty(
    int kingdom_idx,
    int num_kingdoms,
    int* kingdom_offsets,
    int* kingdom_cell_rows,
    int* kingdom_cell_cols,
    int* placed_rows,
    int* placed_cols,
    long* backtrack_count,
) noexcept nogil:
    """Counts backtracks until first solution; returns True when found."""
    cdef int start, end, i, row, col

    if kingdom_idx == num_kingdoms:
        return True

    start = kingdom_offsets[kingdom_idx]
    end = kingdom_offsets[kingdom_idx + 1]
    for i in range(start, end):
        row = kingdom_cell_rows[i]
        col = kingdom_cell_cols[i]
        if _is_valid(placed_rows, placed_cols, kingdom_idx, row, col):
            placed_rows[kingdom_idx] = row
            placed_cols[kingdom_idx] = col
            if _backtrack_difficulty(
                kingdom_idx + 1, num_kingdoms,
                kingdom_offsets, kingdom_cell_rows, kingdom_cell_cols,
                placed_rows, placed_cols,
                backtrack_count,
            ):
                return True
            backtrack_count[0] += 1
    return False


cdef _alloc_and_pack(
    list kingdoms,
    int** kingdom_offsets,
    int** kingdom_cell_rows,
    int** kingdom_cell_cols,
    int** placed_rows,
    int** placed_cols,
):
    """Allocate the C arrays and fill them from a Python kingdoms list."""
    cdef int size = len(kingdoms)
    cdef int num_kingdoms = size
    cdef int total_cells = size * size

    cdef list grouped_rows = [[] for _ in range(num_kingdoms)]
    cdef list grouped_cols = [[] for _ in range(num_kingdoms)]
    cdef int r, c, k, j, offset = 0
    for r in range(size):
        for c in range(size):
            k = kingdoms[r][c]
            grouped_rows[k].append(r)
            grouped_cols[k].append(c)

    kingdom_offsets[0] = <int*>malloc((num_kingdoms + 1) * sizeof(int))
    kingdom_cell_rows[0] = <int*>malloc(total_cells * sizeof(int))
    kingdom_cell_cols[0] = <int*>malloc(total_cells * sizeof(int))
    placed_rows[0] = <int*>malloc(num_kingdoms * sizeof(int))
    placed_cols[0] = <int*>malloc(num_kingdoms * sizeof(int))

    if not (kingdom_offsets[0] and kingdom_cell_rows[0] and kingdom_cell_cols[0]
            and placed_rows[0] and placed_cols[0]):
        raise MemoryError()

    for k in range(num_kingdoms):
        kingdom_offsets[0][k] = offset
        for j in range(len(grouped_rows[k])):
            kingdom_cell_rows[0][offset] = grouped_rows[k][j]
            kingdom_cell_cols[0][offset] = grouped_cols[k][j]
            offset += 1
    kingdom_offsets[0][num_kingdoms] = offset


cdef inline void _free_all(
    int* kingdom_offsets,
    int* kingdom_cell_rows,
    int* kingdom_cell_cols,
    int* placed_rows,
    int* placed_cols,
) noexcept:
    if kingdom_offsets: free(kingdom_offsets)
    if kingdom_cell_rows: free(kingdom_cell_rows)
    if kingdom_cell_cols: free(kingdom_cell_cols)
    if placed_rows: free(placed_rows)
    if placed_cols: free(placed_cols)


def find_all_solutions(list kingdoms, int max_count=100):
    """Find solutions to the queens puzzle.

    Returns a list of solutions; each solution is a list of (row, col)
    tuples, one per kingdom.
    """
    cdef int num_kingdoms = len(kingdoms)
    cdef int* kingdom_offsets = NULL
    cdef int* kingdom_cell_rows = NULL
    cdef int* kingdom_cell_cols = NULL
    cdef int* placed_rows = NULL
    cdef int* placed_cols = NULL

    _alloc_and_pack(
        kingdoms,
        &kingdom_offsets, &kingdom_cell_rows, &kingdom_cell_cols,
        &placed_rows, &placed_cols,
    )

    try:
        solutions = []
        _backtrack(
            0, num_kingdoms,
            kingdom_offsets, kingdom_cell_rows, kingdom_cell_cols,
            placed_rows, placed_cols,
            solutions, max_count,
        )
        return solutions
    finally:
        _free_all(kingdom_offsets, kingdom_cell_rows, kingdom_cell_cols,
                  placed_rows, placed_cols)


def count_solutions(list kingdoms, int max_count=2):
    """Count solutions, stopping early at max_count."""
    cdef int num_kingdoms = len(kingdoms)
    cdef int count = 0
    cdef int* kingdom_offsets = NULL
    cdef int* kingdom_cell_rows = NULL
    cdef int* kingdom_cell_cols = NULL
    cdef int* placed_rows = NULL
    cdef int* placed_cols = NULL

    _alloc_and_pack(
        kingdoms,
        &kingdom_offsets, &kingdom_cell_rows, &kingdom_cell_cols,
        &placed_rows, &placed_cols,
    )

    try:
        with nogil:
            _backtrack_count(
                0, num_kingdoms,
                kingdom_offsets, kingdom_cell_rows, kingdom_cell_cols,
                placed_rows, placed_cols,
                &count, max_count,
            )
        return count
    finally:
        _free_all(kingdom_offsets, kingdom_cell_rows, kingdom_cell_cols,
                  placed_rows, placed_cols)


def calculate_difficulty(list kingdoms):
    """Return backtrack count until the first solution is found.

    Higher = harder puzzle. Returns 0 if there are no solutions.
    """
    cdef int num_kingdoms = len(kingdoms)
    cdef long backtrack_count = 0
    cdef int* kingdom_offsets = NULL
    cdef int* kingdom_cell_rows = NULL
    cdef int* kingdom_cell_cols = NULL
    cdef int* placed_rows = NULL
    cdef int* placed_cols = NULL

    _alloc_and_pack(
        kingdoms,
        &kingdom_offsets, &kingdom_cell_rows, &kingdom_cell_cols,
        &placed_rows, &placed_cols,
    )

    try:
        with nogil:
            _backtrack_difficulty(
                0, num_kingdoms,
                kingdom_offsets, kingdom_cell_rows, kingdom_cell_cols,
                placed_rows, placed_cols,
                &backtrack_count,
            )
        return backtrack_count
    finally:
        _free_all(kingdom_offsets, kingdom_cell_rows, kingdom_cell_cols,
                  placed_rows, placed_cols)


# Direction offsets for 4-neighbor traversal.
cdef int _DR[4]
cdef int _DC[4]
_DR[0] = -1; _DR[1] = 1; _DR[2] = 0; _DR[3] = 0
_DC[0] = 0;  _DC[1] = 0; _DC[2] = -1; _DC[3] = 1


cdef inline int _idx(int row, int col, int size) noexcept nogil:
    return row * size + col


cdef inline int _count_same_kingdom_neighbors(
    int* kingdoms_flat, int size, int row, int col, int k,
) noexcept nogil:
    cdef int d, n_row, n_col, count = 0
    for d in range(4):
        n_row = row + _DR[d]
        n_col = col + _DC[d]
        if 0 <= n_row < size and 0 <= n_col < size:
            if kingdoms_flat[_idx(n_row, n_col, size)] == k:
                count += 1
    return count


cdef inline int _perimeter_change(
    int* kingdoms_flat, int size, int row, int col, int k,
) noexcept nogil:
    return 4 - 2 * _count_same_kingdom_neighbors(kingdoms_flat, size, row, col, k)


cdef int _gather_free_neighbors(
    int* kingdoms_flat, int size, int row, int col,
    int* out_rows, int* out_cols,
) noexcept nogil:
    """Return number of free 4-neighbors; fill out_rows/out_cols."""
    cdef int d, n_row, n_col, n = 0
    for d in range(4):
        n_row = row + _DR[d]
        n_col = col + _DC[d]
        if 0 <= n_row < size and 0 <= n_col < size:
            if kingdoms_flat[_idx(n_row, n_col, size)] == -1:
                out_rows[n] = n_row
                out_cols[n] = n_col
                n += 1
    return n


def create_kingdoms(list queens, int size, str kingdom_strategy='mixed'):
    """Build the kingdom grid by growing from each queen's cell.

    Args:
        queens: list of (row, col) tuples, one per kingdom.
        size: board size.
        kingdom_strategy: 'classic', 'jagged', or 'mixed'.

    Returns:
        A `size x size` list-of-lists with each cell's kingdom id.
    """
    cdef int no = size
    cdef int total = no * no
    cdef int num_kingdoms = len(queens)

    # Bit-packed attack map: attacked_by[cell] has bit k set if queen k attacks.
    # Supports up to 32 kingdoms which is well above our 9x9 max.
    cdef unsigned int* attacked_by = <unsigned int*>malloc(total * sizeof(unsigned int))
    cdef int* kingdoms_flat = <int*>malloc(total * sizeof(int))
    cdef int* queen_rows = <int*>malloc(num_kingdoms * sizeof(int))
    cdef int* queen_cols = <int*>malloc(num_kingdoms * sizeof(int))
    cdef int* strategies = <int*>malloc(num_kingdoms * sizeof(int))
    cdef int* free_rows = <int*>malloc(4 * sizeof(int))
    cdef int* free_cols = <int*>malloc(4 * sizeof(int))
    cdef int* safe_rows = <int*>malloc(4 * sizeof(int))
    cdef int* safe_cols = <int*>malloc(4 * sizeof(int))

    if not (attacked_by and kingdoms_flat and queen_rows and queen_cols
            and strategies and free_rows and free_cols and safe_rows and safe_cols):
        if attacked_by: free(attacked_by)
        if kingdoms_flat: free(kingdoms_flat)
        if queen_rows: free(queen_rows)
        if queen_cols: free(queen_cols)
        if strategies: free(strategies)
        if free_rows: free(free_rows)
        if free_cols: free(free_cols)
        if safe_rows: free(safe_rows)
        if safe_cols: free(safe_cols)
        raise MemoryError()

    # Frontier per kingdom: a Python list of (row, col) tuples each. We use
    # Python lists here so that random.choice/randrange work directly on them.
    cdef list frontier = [[] for _ in range(num_kingdoms)]

    cdef int k, row, col, queen_row, queen_col, d_row, d_col, n_row, n_col
    cdef int n_free, n_safe, i, filled, cell_idx, strategy
    cdef int active_count, best_count
    cdef int target_change, change
    cdef unsigned int mask, attackers, other_attackers
    cdef list active
    cdef list kingdom_frontier
    cdef list result
    cdef list row_list

    _random_choice = _random.choice
    _random_randrange = _random.randrange

    try:
        # Init kingdoms to -1.
        for i in range(total):
            kingdoms_flat[i] = -1
        memset(attacked_by, 0, total * sizeof(unsigned int))

        for k in range(num_kingdoms):
            qr_qc = queens[k]
            queen_row = qr_qc[0]
            queen_col = qr_qc[1]
            queen_rows[k] = queen_row
            queen_cols[k] = queen_col
            mask = 1u << <unsigned int>k

            # Same row (excluding queen's own column).
            for col in range(no):
                if col != queen_col:
                    attacked_by[_idx(queen_row, col, no)] |= mask
            # Same column.
            for row in range(no):
                if row != queen_row:
                    attacked_by[_idx(row, queen_col, no)] |= mask
            # Adjacent cells.
            for d_row in range(-1, 2):
                for d_col in range(-1, 2):
                    if d_row == 0 and d_col == 0:
                        continue
                    n_row = queen_row + d_row
                    n_col = queen_col + d_col
                    if 0 <= n_row < no and 0 <= n_col < no:
                        attacked_by[_idx(n_row, n_col, no)] |= mask

        # Strategies.
        if kingdom_strategy == 'classic':
            for k in range(num_kingdoms):
                strategies[k] = 0
        elif kingdom_strategy == 'jagged':
            for k in range(num_kingdoms):
                strategies[k] = 1
        else:  # 'mixed'
            for k in range(num_kingdoms):
                strategies[k] = _random_choice([-1, 0, 1])

        # Seed each kingdom with its queen.
        filled = num_kingdoms
        for k in range(num_kingdoms):
            queen_row = queen_rows[k]
            queen_col = queen_cols[k]
            kingdoms_flat[_idx(queen_row, queen_col, no)] = k
            (<list>frontier[k]).append((queen_row, queen_col))

        # Phase 1: ensure each kingdom has at least 2 cells.
        for k in range(num_kingdoms):
            queen_row = queen_rows[k]
            queen_col = queen_cols[k]
            mask = 1u << <unsigned int>k
            n_free = _gather_free_neighbors(
                kingdoms_flat, no, queen_row, queen_col, free_rows, free_cols,
            )
            if n_free == 0:
                continue
            n_safe = 0
            for i in range(n_free):
                attackers = attacked_by[_idx(free_rows[i], free_cols[i], no)]
                if (attackers & ~mask) != 0:
                    safe_rows[n_safe] = free_rows[i]
                    safe_cols[n_safe] = free_cols[i]
                    n_safe += 1
            if n_safe > 0:
                cell_idx = _random_randrange(n_safe)
                n_row = safe_rows[cell_idx]
                n_col = safe_cols[cell_idx]
            else:
                cell_idx = _random_randrange(n_free)
                n_row = free_rows[cell_idx]
                n_col = free_cols[cell_idx]
            kingdoms_flat[_idx(n_row, n_col, no)] = k
            (<list>frontier[k]).append((n_row, n_col))
            filled += 1

        # Phase 2: grow kingdoms until board is full.
        while filled < total:
            active = [k for k in range(num_kingdoms) if frontier[k]]
            if not active:
                break

            k = _random_choice(active)
            kingdom_frontier = <list>frontier[k]
            cell_idx = _random_randrange(len(kingdom_frontier))
            row, col = kingdom_frontier[cell_idx]

            n_free = _gather_free_neighbors(
                kingdoms_flat, no, row, col, free_rows, free_cols,
            )
            if n_free == 0:
                # No more growth from this frontier cell; drop it.
                kingdom_frontier.pop(cell_idx)
                continue

            # Filter to cells attacked by other queens.
            mask = 1u << <unsigned int>k
            n_safe = 0
            for i in range(n_free):
                attackers = attacked_by[_idx(free_rows[i], free_cols[i], no)]
                if (attackers & ~mask) != 0:
                    safe_rows[n_safe] = free_rows[i]
                    safe_cols[n_safe] = free_cols[i]
                    n_safe += 1
            if n_safe > 0:
                n_free = n_safe
                # Move safe into free arrays for unified handling.
                for i in range(n_safe):
                    free_rows[i] = safe_rows[i]
                    free_cols[i] = safe_cols[i]

            strategy = strategies[k]
            if strategy == 0 or n_free == 1:
                cell_idx = _random_randrange(n_free)
                n_row = free_rows[cell_idx]
                n_col = free_cols[cell_idx]
            else:
                # Pick by perimeter change.
                if strategy == 1:
                    target_change = -10000
                    for i in range(n_free):
                        change = _perimeter_change(
                            kingdoms_flat, no, free_rows[i], free_cols[i], k,
                        )
                        if change > target_change:
                            target_change = change
                else:
                    target_change = 10000
                    for i in range(n_free):
                        change = _perimeter_change(
                            kingdoms_flat, no, free_rows[i], free_cols[i], k,
                        )
                        if change < target_change:
                            target_change = change
                # Reservoir-style pick among ties.
                best_count = 0
                for i in range(n_free):
                    change = _perimeter_change(
                        kingdoms_flat, no, free_rows[i], free_cols[i], k,
                    )
                    if change == target_change:
                        safe_rows[best_count] = free_rows[i]
                        safe_cols[best_count] = free_cols[i]
                        best_count += 1
                cell_idx = _random_randrange(best_count)
                n_row = safe_rows[cell_idx]
                n_col = safe_cols[cell_idx]

            kingdoms_flat[_idx(n_row, n_col, no)] = k
            kingdom_frontier.append((n_row, n_col))
            filled += 1

        # Convert flat array back to list-of-lists.
        result = []
        for row in range(no):
            row_list = []
            for col in range(no):
                row_list.append(kingdoms_flat[_idx(row, col, no)])
            (<list>result).append(row_list)
        return result

    finally:
        free(attacked_by)
        free(kingdoms_flat)
        free(queen_rows)
        free(queen_cols)
        free(strategies)
        free(free_rows)
        free(free_cols)
        free(safe_rows)
        free(safe_cols)
