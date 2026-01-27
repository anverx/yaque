import copy
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Line, Color, Ellipse
from kivy.clock import Clock
from typing import List, Tuple, Callable, Optional, Set

# Cell mark states
MARK_EMPTY = 0
MARK_CIRCLE = 1
MARK_QUEEN = 2

# Kingdom colors (RGB, 0-1 range)
KINGDOM_COLORS = [
    (0.9, 0.6, 0.6),   # 0: light red
    (0.6, 0.9, 0.6),   # 1: light green
    (0.6, 0.6, 0.9),   # 2: light blue
    (0.9, 0.9, 0.6),   # 3: light yellow
    (0.9, 0.6, 0.9),   # 4: light magenta
    (0.6, 0.9, 0.9),   # 5: light cyan
    (0.9, 0.8, 0.6),   # 6: light orange
    (0.8, 0.6, 0.9),   # 7: light purple
    (0.6, 0.8, 0.7),   # 8: light teal
    (0.85, 0.7, 0.7),  # 9: dusty rose
]


class BoardWidget(Widget):
    def __init__(self, kingdoms: List[List[int]], queens: List[Tuple[int, int]],
                 on_cell_click: Optional[Callable[[int, int], None]] = None,
                 on_solved: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(**kwargs)
        self.kingdoms = kingdoms
        self.queens = queens
        self.queen_set = set(queens)
        self.size_cells = len(kingdoms)
        self.on_cell_click = on_cell_click
        self.on_solved = on_solved
        self.solved = False
        # Track cell marks: 0=empty, 1=circle, 2=queen
        self.cell_marks = [[MARK_EMPTY] * self.size_cells for _ in range(self.size_cells)]
        self.show_solution = False
        # History for undo/redo
        self.history = []
        self.history_index = -1
        # Conflict tracking
        self.conflict_cells: Set[Tuple[int, int]] = set()
        self._validation_event = None
        self.hidden = True  # Start hidden until play is pressed
        self.bind(pos=self._trigger_redraw, size=self._trigger_redraw)

    def _trigger_redraw(self, *args):
        self.draw_board()

    def draw_board(self):
        self.canvas.clear()
        n = self.size_cells
        cell_w = self.width / n
        cell_h = self.height / n

        with self.canvas:
            if self.hidden:
                # Draw gray empty board when hidden
                Color(0.85, 0.85, 0.85, 1)
                Rectangle(pos=(self.x, self.y), size=(self.width, self.height))

                # Draw thin cell borders only
                Color(0.7, 0.7, 0.7, 1)
                for i in range(n + 1):
                    x = self.x + i * cell_w
                    Line(points=[x, self.y, x, self.y + self.height], width=1)
                    y = self.y + i * cell_h
                    Line(points=[self.x, y, self.x + self.width, y], width=1)

                # Draw outer border
                Color(0.5, 0.5, 0.5, 1)
                Line(points=[self.x, self.y, self.x + self.width, self.y], width=2)
                Line(points=[self.x, self.y + self.height, self.x + self.width, self.y + self.height], width=2)
                Line(points=[self.x, self.y, self.x, self.y + self.height], width=2)
                Line(points=[self.x + self.width, self.y, self.x + self.width, self.y + self.height], width=2)
                return

            # Draw kingdom colored cells
            for row in range(n):
                for col in range(n):
                    k = self.kingdoms[row][col]
                    color = KINGDOM_COLORS[k % len(KINGDOM_COLORS)]
                    Color(*color, 1)
                    # Kivy y=0 is bottom, so flip row
                    x = self.x + col * cell_w
                    y = self.y + (n - 1 - row) * cell_h
                    Rectangle(pos=(x, y), size=(cell_w, cell_h))

            # Draw thin cell borders
            Color(0.5, 0.5, 0.5, 1)
            for i in range(n + 1):
                # Vertical lines
                x = self.x + i * cell_w
                Line(points=[x, self.y, x, self.y + self.height], width=1)
                # Horizontal lines
                y = self.y + i * cell_h
                Line(points=[self.x, y, self.x + self.width, y], width=1)

            # Draw thick kingdom borders
            Color(0, 0, 0, 1)
            for row in range(n):
                for col in range(n):
                    k = self.kingdoms[row][col]
                    x = self.x + col * cell_w
                    y = self.y + (n - 1 - row) * cell_h

                    # Check right neighbor
                    if col < n - 1 and self.kingdoms[row][col + 1] != k:
                        Line(points=[x + cell_w, y, x + cell_w, y + cell_h], width=3)

                    # Check bottom neighbor (row + 1 in grid = y - cell_h in screen)
                    if row < n - 1 and self.kingdoms[row + 1][col] != k:
                        Line(points=[x, y, x + cell_w, y], width=3)

            # Draw outer border
            Line(points=[self.x, self.y, self.x + self.width, self.y], width=3)
            Line(points=[self.x, self.y + self.height, self.x + self.width, self.y + self.height], width=3)
            Line(points=[self.x, self.y, self.x, self.y + self.height], width=3)
            Line(points=[self.x + self.width, self.y, self.x + self.width, self.y + self.height], width=3)

            # Draw cell marks
            Color(0, 0, 0, 1)
            for row in range(n):
                for col in range(n):
                    mark = self.cell_marks[row][col]
                    if mark == MARK_EMPTY:
                        continue
                    x = self.x + col * cell_w
                    y = self.y + (n - 1 - row) * cell_h
                    if mark == MARK_CIRCLE:
                        # Small gray circle outline in center
                        Color(0.4, 0.4, 0.4, 1)
                        circ_size = min(cell_w, cell_h) * 0.15
                        circ_x = x + (cell_w - circ_size) / 2
                        circ_y = y + (cell_h - circ_size) / 2
                        Line(ellipse=(circ_x, circ_y, circ_size, circ_size), width=1.5)
                        Color(0, 0, 0, 1)
                    elif mark == MARK_QUEEN:
                        # Draw queen as circle with X (red if in conflict)
                        is_conflict = (row, col) in self.conflict_cells
                        if is_conflict:
                            Color(0.9, 0.2, 0.2, 1)  # Red for conflict
                        margin = min(cell_w, cell_h) * 0.15
                        size = min(cell_w, cell_h) - 2 * margin
                        cx = x + cell_w / 2
                        cy = y + cell_h / 2
                        Ellipse(pos=(cx - size/2, cy - size/2), size=(size, size))
                        # Draw X inside
                        Color(1, 1, 1, 1)
                        inner = size * 0.25
                        Line(points=[cx - inner, cy - inner, cx + inner, cy + inner], width=2)
                        Line(points=[cx - inner, cy + inner, cx + inner, cy - inner], width=2)
                        Color(0, 0, 0, 1)

            # Draw solution queens if enabled
            if self.show_solution:
                Color(0.2, 0.2, 0.8, 0.7)  # Semi-transparent blue
                for row, col in self.queens:
                    x = self.x + col * cell_w
                    y = self.y + (n - 1 - row) * cell_h
                    margin = min(cell_w, cell_h) * 0.15
                    size = min(cell_w, cell_h) - 2 * margin
                    cx = x + cell_w / 2
                    cy = y + cell_h / 2
                    Ellipse(pos=(cx - size/2, cy - size/2), size=(size, size))
                    Color(1, 1, 1, 1)
                    inner = size * 0.25
                    Line(points=[cx - inner, cy - inner, cx + inner, cy + inner], width=2)
                    Line(points=[cx - inner, cy + inner, cx + inner, cy - inner], width=2)
                    Color(0.2, 0.2, 0.8, 0.7)

    def _get_marked_queens(self) -> List[Tuple[int, int]]:
        """Get all cells marked as queens."""
        marked = []
        for row in range(self.size_cells):
            for col in range(self.size_cells):
                if self.cell_marks[row][col] == MARK_QUEEN:
                    marked.append((row, col))
        return marked

    def _find_conflicts(self) -> Set[Tuple[int, int]]:
        """Find all queens that conflict with each other."""
        conflicts = set()
        marked_queens = self._get_marked_queens()

        # Check each pair of queens for conflicts
        for i, (r1, c1) in enumerate(marked_queens):
            for r2, c2 in marked_queens[i + 1:]:
                # Same row or column
                if r1 == r2 or c1 == c2:
                    conflicts.add((r1, c1))
                    conflicts.add((r2, c2))
                # Adjacent (including diagonal)
                elif abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1:
                    conflicts.add((r1, c1))
                    conflicts.add((r2, c2))

        return conflicts

    def is_solved(self) -> bool:
        """Check if the puzzle is solved correctly."""
        marked_queens = self._get_marked_queens()

        # Must have exactly one queen per kingdom
        if len(marked_queens) != self.size_cells:
            return False

        # Check each kingdom has exactly one queen
        kingdom_queens = {}
        for row, col in marked_queens:
            k = self.kingdoms[row][col]
            if k in kingdom_queens:
                return False  # More than one queen in kingdom
            kingdom_queens[k] = (row, col)

        # Check all kingdoms have a queen
        if len(kingdom_queens) != self.size_cells:
            return False

        # Check no conflicts
        return len(self._find_conflicts()) == 0

    def _validate_after_delay(self, dt):
        """Called after delay to validate queen placements."""
        self.conflict_cells = self._find_conflicts()
        self.draw_board()

        # Check if solved
        if not self.solved and self.is_solved():
            self.solved = True
            if self.on_solved:
                self.on_solved()

    def _schedule_validation(self):
        """Schedule validation with delay."""
        # Cancel any pending validation
        if self._validation_event:
            self._validation_event.cancel()
        # Clear conflicts immediately
        self.conflict_cells = set()
        # Schedule new validation after delay
        self._validation_event = Clock.schedule_once(self._validate_after_delay, 0.5)

    def _save_state(self):
        # Remove any redo states
        self.history = self.history[:self.history_index + 1]
        # Save current state
        self.history.append(copy.deepcopy(self.cell_marks))
        self.history_index = len(self.history) - 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.cell_marks = copy.deepcopy(self.history[self.history_index])
            self._schedule_validation()
            self.draw_board()

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.cell_marks = copy.deepcopy(self.history[self.history_index])
            self._schedule_validation()
            self.draw_board()

    def reset(self):
        self._save_state()
        self.cell_marks = [[MARK_EMPTY] * self.size_cells for _ in range(self.size_cells)]
        self.conflict_cells = set()
        if self._validation_event:
            self._validation_event.cancel()
        self.draw_board()

    def on_touch_down(self, touch):
        if self.hidden:
            return super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            cell_w = self.width / self.size_cells
            cell_h = self.height / self.size_cells
            col = int((touch.x - self.x) / cell_w)
            row = self.size_cells - 1 - int((touch.y - self.y) / cell_h)
            # Clamp to valid range
            col = max(0, min(col, self.size_cells - 1))
            row = max(0, min(row, self.size_cells - 1))
            # Save state before change
            self._save_state()
            # Cycle mark state: empty -> circle -> queen -> empty
            self.cell_marks[row][col] = (self.cell_marks[row][col] + 1) % 3
            self.draw_board()
            # Schedule delayed validation
            self._schedule_validation()
            if self.on_cell_click:
                self.on_cell_click(row, col)
            return True
        return super().on_touch_down(touch)
