from __future__ import annotations

import copy
import os
from typing import Any, Callable

from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Line, Color, Ellipse, PushMatrix, PopMatrix, Rotate, Scale, Translate
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation

from ui_constants import (
    COLOR_BLACK, COLOR_WHITE,
    BOARD_HIDDEN_BG, BOARD_HIDDEN_GRID, BOARD_HIDDEN_BORDER,
    BOARD_CELL_BORDER, BOARD_KINGDOM_BORDER,
    BOARD_QUEEN_NORMAL, BOARD_QUEEN_GOLDEN, BOARD_QUEEN_CONFLICT, BOARD_QUEEN_SOLUTION,
    BOARD_CIRCLE_NORMAL, BOARD_CIRCLE_BLOCKED,
    KINGDOM_COLORS
)

# Load queen texture
ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icons')
QUEEN_TEXTURE = CoreImage(os.path.join(ICONS_DIR, 'queen.png')).texture
QUEEN_RED_TEXTURE = None  # Will be created on demand for conflicts

# Cell mark states
MARK_EMPTY = 0
MARK_CIRCLE = 1
MARK_QUEEN = 2


class BoardWidget(Widget):
    def __init__(
        self,
        kingdoms: list[list[int]],
        queens: list[tuple[int, int]],
        on_cell_click: Callable[[int, int], None] | None = None,
        on_solved: Callable[[], None] | None = None,
        on_hidden_click: Callable[[], None] | None = None,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.kingdoms = kingdoms
        self.queens = queens
        self.queen_set = set(queens)
        self.size_cells = len(kingdoms)
        self.on_cell_click = on_cell_click
        self.on_solved = on_solved
        self.on_hidden_click = on_hidden_click
        self.solved = False
        # Track cell marks: 0=empty, 1=circle, 2=queen
        self.cell_marks: list[list[int]] = [[MARK_EMPTY] * self.size_cells for _ in range(self.size_cells)]
        self.show_solution = False
        # All possible solutions (populated when solved)
        self.all_solutions: list[list[tuple[int, int]]] = []
        self.current_solution_index = 0
        # History for undo/redo
        self.history: list[list[list[int]]] = []
        self.history_index = -1
        # Conflict tracking
        self.conflict_cells: set[tuple[int, int]] = set()
        self.blocked_cells: set[tuple[int, int]] = set()  # Circles in fully-blocked kingdoms
        self._validation_event: Any = None
        self.hidden = True  # Start hidden until play is pressed
        # Victory celebration animation
        self.celebrating = False
        self.celebration_progress = 0.0
        self._celebration_event: Any = None
        self.bind(pos=self._trigger_redraw, size=self._trigger_redraw)

    def _trigger_redraw(self, *args: Any) -> None:
        self.draw_board()

    def draw_board(self) -> None:
        self.canvas.clear()
        n = self.size_cells
        cell_w = self.width / n
        cell_h = self.height / n

        with self.canvas:
            if self.hidden:
                # Draw gray empty board when hidden
                Color(*BOARD_HIDDEN_BG)
                Rectangle(pos=(self.x, self.y), size=(self.width, self.height))

                # Draw thin cell borders only
                Color(*BOARD_HIDDEN_GRID)
                for i in range(n + 1):
                    x = self.x + i * cell_w
                    Line(points=[x, self.y, x, self.y + self.height], width=1)
                    y = self.y + i * cell_h
                    Line(points=[self.x, y, self.x + self.width, y], width=1)

                # Draw outer border
                Color(*BOARD_HIDDEN_BORDER)
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
            Color(*BOARD_CELL_BORDER)
            for i in range(n + 1):
                # Vertical lines
                x = self.x + i * cell_w
                Line(points=[x, self.y, x, self.y + self.height], width=1)
                # Horizontal lines
                y = self.y + i * cell_h
                Line(points=[self.x, y, self.x + self.width, y], width=1)

            # Draw thick kingdom borders
            Color(*BOARD_KINGDOM_BORDER)
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

            # When solved and showing solutions, draw the current solution queens (blue, 30% bigger)
            if self.solved and not self.celebrating and self.show_solution and self.all_solutions:
                solution = self.all_solutions[self.current_solution_index]
                Color(*BOARD_QUEEN_SOLUTION)
                for row, col in solution:
                    x = self.x + col * cell_w
                    y = self.y + (n - 1 - row) * cell_h
                    # 30% bigger than normal queen size
                    margin = min(cell_w, cell_h) * 0.2
                    base_size = min(cell_w, cell_h) - 2 * margin
                    size = base_size * 1.3
                    qx = x + (cell_w - size) / 2
                    qy = y + (cell_h - size) / 2
                    Rectangle(pos=(qx, qy), size=(size, size), texture=QUEEN_TEXTURE)

            # Draw cell marks (user's placements)
            Color(*COLOR_BLACK)
            for row in range(n):
                for col in range(n):
                    mark = self.cell_marks[row][col]
                    if mark == MARK_EMPTY:
                        continue
                    x = self.x + col * cell_w
                    y = self.y + (n - 1 - row) * cell_h
                    if mark == MARK_CIRCLE:
                        # Small circle outline in center - red if blocked, gray otherwise
                        is_blocked = (row, col) in self.blocked_cells
                        if is_blocked:
                            Color(*BOARD_CIRCLE_BLOCKED)
                        else:
                            Color(*BOARD_CIRCLE_NORMAL)
                        circ_size = min(cell_w, cell_h) * 0.15
                        circ_x = x + (cell_w - circ_size) / 2
                        circ_y = y + (cell_h - circ_size) / 2
                        Line(ellipse=(circ_x, circ_y, circ_size, circ_size), width=1.5)
                        Color(*COLOR_BLACK)
                    elif mark == MARK_QUEEN:
                        # Draw queen icon
                        is_conflict = (row, col) in self.conflict_cells
                        margin = min(cell_w, cell_h) * 0.2
                        size = min(cell_w, cell_h) - 2 * margin
                        cx = x + cell_w / 2  # Center of cell
                        cy = y + cell_h / 2

                        if self.celebrating:
                            # Celebration animation - all queens together
                            progress = self.celebration_progress

                            # Eased progress for smooth animation
                            eased = 1 - (1 - progress) ** 2  # Ease out quad

                            # Rotation: 0 to 360 degrees
                            rotation = eased * 360

                            # Scale pulse: 1.0 -> 2.0 -> 1.0
                            if progress < 0.5:
                                scale = 1.0 + 1.0 * (progress * 2)
                            else:
                                scale = 2.0 - 1.0 * ((progress - 0.5) * 2)

                            # Golden color
                            Color(*BOARD_QUEEN_GOLDEN)

                            # Apply transforms
                            PushMatrix()
                            Translate(cx, cy, 0)
                            Rotate(angle=rotation, axis=(0, 0, 1))
                            Scale(scale, scale, 1)
                            Translate(-size/2, -size/2, 0)
                            Rectangle(pos=(0, 0), size=(size, size), texture=QUEEN_TEXTURE)
                            PopMatrix()
                        elif self.solved:
                            # Golden queens on top of blue solution queens
                            Color(*BOARD_QUEEN_GOLDEN)
                            qx = x + (cell_w - size) / 2
                            qy = y + (cell_h - size) / 2
                            Rectangle(pos=(qx, qy), size=(size, size), texture=QUEEN_TEXTURE)
                        else:
                            # Normal drawing
                            if is_conflict:
                                Color(*BOARD_QUEEN_CONFLICT)
                            else:
                                Color(*BOARD_QUEEN_NORMAL)
                            qx = x + (cell_w - size) / 2
                            qy = y + (cell_h - size) / 2
                            Rectangle(pos=(qx, qy), size=(size, size), texture=QUEEN_TEXTURE)
                        Color(*COLOR_BLACK)

    def _get_marked_queens(self) -> list[tuple[int, int]]:
        """Get all cells marked as queens."""
        marked = []
        for row in range(self.size_cells):
            for col in range(self.size_cells):
                if self.cell_marks[row][col] == MARK_QUEEN:
                    marked.append((row, col))
        return marked

    def _find_conflicts(self) -> set[tuple[int, int]]:
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
                # Same kingdom
                elif self.kingdoms[r1][c1] == self.kingdoms[r2][c2]:
                    conflicts.add((r1, c1))
                    conflicts.add((r2, c2))

        return conflicts

    def _find_blocked_kingdoms(self) -> set[tuple[int, int]]:
        """Find all cells in kingdoms that are entirely marked as 'no queen' (circles)."""
        blocked = set()

        # Group cells by kingdom
        kingdom_cells = {}
        for row in range(self.size_cells):
            for col in range(self.size_cells):
                k = self.kingdoms[row][col]
                if k not in kingdom_cells:
                    kingdom_cells[k] = []
                kingdom_cells[k].append((row, col))

        # Check each kingdom
        for k, cells in kingdom_cells.items():
            has_queen = False
            all_marked = True
            for row, col in cells:
                mark = self.cell_marks[row][col]
                if mark == MARK_QUEEN:
                    has_queen = True
                    break
                if mark == MARK_EMPTY:
                    all_marked = False

            # Kingdom is blocked if all cells are circles (no queen, no empty)
            if not has_queen and all_marked:
                for row, col in cells:
                    if self.cell_marks[row][col] == MARK_CIRCLE:
                        blocked.add((row, col))

        return blocked

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

    def _validate_after_delay(self, dt: float) -> None:
        """Called after delay to validate queen placements."""
        self.conflict_cells = self._find_conflicts()
        self.blocked_cells = self._find_blocked_kingdoms()
        self.draw_board()

        # Check if solved
        if not self.solved and self.is_solved():
            self.solved = True
            self.start_celebration()
            if self.on_solved:
                self.on_solved()

    def start_celebration(self) -> None:
        """Start the victory celebration animation."""
        self.celebrating = True
        self.celebration_progress = 0.0
        # Run animation for ~1.5 seconds at 60fps
        self._celebration_event = Clock.schedule_interval(self._update_celebration, 1/60)

    def _update_celebration(self, dt: float) -> None:
        """Update celebration animation frame."""
        self.celebration_progress += dt / 2.5  # 2.5 second animation
        if self.celebration_progress >= 1.0:
            self.celebration_progress = 1.0
            self.celebrating = False
            if self._celebration_event:
                self._celebration_event.cancel()
                self._celebration_event = None
        self.draw_board()

    def _schedule_validation(self) -> None:
        """Schedule validation with delay."""
        # Cancel any pending validation
        if self._validation_event:
            self._validation_event.cancel()
        # Clear conflicts and blocked cells immediately
        self.conflict_cells = set()
        self.blocked_cells = set()
        # Schedule new validation after delay
        self._validation_event = Clock.schedule_once(self._validate_after_delay, 0.5)

    def _save_state(self) -> None:
        # Remove any redo states
        self.history = self.history[:self.history_index + 1]
        # Save current state
        self.history.append(copy.deepcopy(self.cell_marks))
        self.history_index = len(self.history) - 1

    def undo(self) -> None:
        if self.history_index > 0:
            self.history_index -= 1
            self.cell_marks = copy.deepcopy(self.history[self.history_index])
            self._schedule_validation()
            self.draw_board()

    def redo(self) -> None:
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.cell_marks = copy.deepcopy(self.history[self.history_index])
            self._schedule_validation()
            self.draw_board()

    def reset(self) -> None:
        self._save_state()
        self.cell_marks = [[MARK_EMPTY] * self.size_cells for _ in range(self.size_cells)]
        self.conflict_cells = set()
        self.blocked_cells = set()
        if self._validation_event:
            self._validation_event.cancel()
        # Cancel any celebration
        if self._celebration_event:
            self._celebration_event.cancel()
            self._celebration_event = None
        self.celebrating = False
        self.celebration_progress = 0.0
        self.draw_board()

    def auto_solve(self) -> None:
        """Place the correct solution and play celebration."""
        # Clear board first
        self.cell_marks = [[MARK_EMPTY] * self.size_cells for _ in range(self.size_cells)]
        self.conflict_cells = set()
        self.blocked_cells = set()

        # Place queens at solution positions
        for row, col in self.queens:
            self.cell_marks[row][col] = MARK_QUEEN

        # Mark as solved and start celebration
        self.solved = True
        self.start_celebration()

    def cycle_solution(self) -> int:
        """Cycle to the next solution. Returns the new solution index (0-based)."""
        if not self.all_solutions:
            return 0
        self.current_solution_index = (self.current_solution_index + 1) % len(self.all_solutions)
        self.draw_board()
        return self.current_solution_index

    def _get_cell_at_pos(self, x: float, y: float) -> tuple[int, int]:
        """Convert screen coordinates to cell (row, col)."""
        cell_w = self.width / self.size_cells
        cell_h = self.height / self.size_cells
        col = int((x - self.x) / cell_w)
        row = self.size_cells - 1 - int((y - self.y) / cell_h)
        # Clamp to valid range
        col = max(0, min(col, self.size_cells - 1))
        row = max(0, min(row, self.size_cells - 1))
        return row, col

    def on_touch_down(self, touch: Any) -> bool:
        if self.hidden:
            if self.collide_point(*touch.pos) and self.on_hidden_click:
                self.on_hidden_click()
                return True
            return super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            # Grab the touch to track it for drag-to-mark
            touch.grab(self)
            row, col = self._get_cell_at_pos(touch.x, touch.y)
            # Save state before any changes (for undo)
            self._save_state()
            # Store drag tracking info
            touch.ud['start_cell'] = (row, col)
            touch.ud['last_cell'] = (row, col)
            touch.ud['is_drag'] = False
            touch.ud['marked_cells'] = set()
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: Any) -> bool:
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        if self.hidden:
            return True
        if not self.collide_point(*touch.pos):
            return True

        row, col = self._get_cell_at_pos(touch.x, touch.y)
        last_cell = touch.ud.get('last_cell')

        # If moved to a different cell, it's a drag
        if last_cell and (row, col) != last_cell:
            # First time detecting drag - also mark the starting cell
            if not touch.ud['is_drag']:
                touch.ud['is_drag'] = True
                start_row, start_col = touch.ud['start_cell']
                if self.cell_marks[start_row][start_col] == MARK_EMPTY:
                    self.cell_marks[start_row][start_col] = MARK_CIRCLE
                    touch.ud['marked_cells'].add((start_row, start_col))
            # Mark the new cell with circle as we drag
            if self.cell_marks[row][col] == MARK_EMPTY:
                self.cell_marks[row][col] = MARK_CIRCLE
                touch.ud['marked_cells'].add((row, col))
            self.draw_board()
            touch.ud['last_cell'] = (row, col)

        return True

    def on_touch_up(self, touch: Any) -> bool:
        if touch.grab_current is not self:
            return super().on_touch_up(touch)

        touch.ungrab(self)

        if self.hidden:
            return True

        start_cell = touch.ud.get('start_cell')
        is_drag = touch.ud.get('is_drag', False)
        marked_cells = touch.ud.get('marked_cells', set())

        if start_cell:
            row, col = start_cell
            if is_drag:
                # Drag completed - state was saved at touch_down
                if marked_cells:
                    self._schedule_validation()
            else:
                # Single tap - cycle mark state (state was saved at touch_down)
                self.cell_marks[row][col] = (self.cell_marks[row][col] + 1) % 3
                self.draw_board()
                self._schedule_validation()
                if self.on_cell_click:
                    self.on_cell_click(row, col)

        return True
