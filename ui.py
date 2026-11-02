import pygame
import threading
import time

from algo import (
    ROWS,
    COLS,
    EMPTY,
    RED,
    YELLOW,
    create_board,
    get_next_open_row,
    is_valid_location,
    drop_piece,
    check_winner,
    winning_cells,
    is_draw,
    find_best_move,
)


# ============================================================
# CONFIGURATION
# ============================================================

WIDTH = 1200
HEIGHT = 800
FPS = 60

BG = (9, 10, 15)
GRID = (21, 22, 30)

PANEL = (22, 23, 32)
PANEL_HOVER = (32, 33, 44)
BORDER = (49, 51, 66)

WHITE = (246, 247, 252)
MUTED = (143, 146, 164)

RED_COLOR = (255, 55, 79)
YELLOW_COLOR = (255, 204, 43)

BOARD_COLOR = (27, 30, 49)
BOARD_BORDER = (52, 55, 78)
HOLE_COLOR = (9, 10, 16)

BLUE = (111, 124, 255)

ANIMATION_TIME = 0.24
AI_DEPTH = 4


# ============================================================
# BUTTON
# ============================================================

class Button:

    def __init__(
        self,
        rect,
        text,
        callback,
        accent=None,
        font_size=16,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.accent = accent
        self.font_size = font_size
        self.hovered = False

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, app):
        surface = app.screen

        background = (
            PANEL_HOVER if self.hovered else PANEL
        )

        border_color = (
            self.accent if self.accent else BORDER
        )

        pygame.draw.rect(
            surface,
            background,
            self.rect,
            border_radius=13,
        )

        pygame.draw.rect(
            surface,
            border_color,
            self.rect,
            2 if self.hovered else 1,
            border_radius=13,
        )

        text_color = (
            WHITE if self.hovered else (222, 224, 234)
        )

        # IMPORTANT: use app.font(), not self.font()
        app.draw_text(
            self.text,
            app.font(self.font_size, bold=True),
            text_color,
            self.rect.centerx,
            self.rect.centery,
        )


# ============================================================
# APPLICATION
# ============================================================

class Puissance4App:

    def __init__(self):
        pygame.init()

        pygame.display.set_caption(
            "CONNECT FOUR | Desktop Game"
        )

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT),
            pygame.RESIZABLE,
        )

        self.clock = pygame.time.Clock()

        self.running = True
        self.scene = "home"
        self.mode = "ai"

        self.board = create_board()
        self.current_player = RED

        # None = playing
        # RED / YELLOW = winner
        # -1 = draw
        self.winner = None

        self.last_move = None
        self.winning_positions = []

        self.move_history = []
        self.animations = []

        self.hover_col = None
        self.buttons = []

        self.ai_thinking = False
        self.ai_result = None
        self.ai_lock = threading.Lock()
        self.game_id = 0

        self.result_button_rect = None

        self.message = ""
        self.message_until = 0

        self.rebuild_buttons()

    # ========================================================
    # FONTS AND DRAWING HELPERS
    # ========================================================

    @property
    def width(self):
        return self.screen.get_width()

    @property
    def height(self):
        return self.screen.get_height()

    def font(self, size, bold=False):
        return pygame.font.SysFont(
            "montserrat",
            max(12, int(size)),
            bold=bold,
        )

    def draw_text(
        self,
        text,
        font,
        color,
        x,
        y,
        center=True,
    ):
        rendered = font.render(str(text), True, color)
        rect = rendered.get_rect()

        if center:
            rect.center = (int(x), int(y))
        else:
            rect.topleft = (int(x), int(y))

        self.screen.blit(rendered, rect)
        return rect

    def draw_background(self):
        self.screen.fill(BG)

        spacing = 70

        for x in range(0, self.width, spacing):
            pygame.draw.line(
                self.screen,
                GRID,
                (x, 0),
                (x, self.height),
                1,
            )

        for y in range(25, self.height, spacing):
            pygame.draw.line(
                self.screen,
                GRID,
                (0, y),
                (self.width, y),
                1,
            )

        pygame.draw.circle(
            self.screen,
            (20, 16, 26),
            (self.width - 20, 30),
            145,
        )

    def draw_pill(self, text, x, y, color):
        font = self.font(12, bold=True)
        rendered = font.render(text, True, color)

        rect = rendered.get_rect()
        rect.center = (x, y)
        rect.inflate_ip(24, 13)

        pygame.draw.rect(
            self.screen,
            PANEL,
            rect,
            border_radius=20,
        )

        pygame.draw.rect(
            self.screen,
            BORDER,
            rect,
            1,
            border_radius=20,
        )

        self.screen.blit(
            rendered,
            rendered.get_rect(center=rect.center),
        )

    # ========================================================
    # BUTTON MANAGEMENT
    # ========================================================

    def add_button(
        self,
        rect,
        text,
        callback,
        accent=None,
        font_size=16,
    ):
        self.buttons.append(
            Button(
                rect,
                text,
                callback,
                accent,
                font_size,
            )
        )

    def rebuild_buttons(self):
        self.buttons = []

        w = self.width
        h = self.height

        if self.scene == "home":
            button_w = min(340, int(w * 0.45))
            button_h = 58

            x = (w - button_w) // 2
            y = int(h * 0.60)

            self.add_button(
                (x, y, button_w, button_h),
                "PLAY GAME",
                self.open_modes,
                RED_COLOR,
                18,
            )

            self.add_button(
                (x, y + 76, button_w, button_h),
                "QUIT",
                self.quit,
                None,
                16,
            )

        elif self.scene == "modes":
            card_w = min(330, int(w * 0.39))
            card_h = 190
            gap = 30

            total_w = card_w * 2 + gap
            left = (w - total_w) // 2
            top = int(h * 0.43)

            self.add_button(
                (left, top, card_w, card_h),
                "HUMAN VS HUMAN",
                self.start_human_game,
                RED_COLOR,
                18,
            )

            self.add_button(
                (
                    left + card_w + gap,
                    top,
                    card_w,
                    card_h,
                ),
                "HUMAN VS AI",
                self.start_ai_game,
                YELLOW_COLOR,
                18,
            )

            back_w = 180
            back_h = 48

            self.add_button(
                (
                    (w - back_w) // 2,
                    top + card_h + 30,
                    back_w,
                    back_h,
                ),
                "BACK",
                self.go_home,
                None,
                15,
            )

        elif self.scene == "game":
            # Only HOME and RESTART: no navbar.
            button_w = 132
            button_h = 44
            gap = 12

            total_w = button_w * 2 + gap
            start_x = w - total_w - 28
            top = 25

            self.add_button(
                (
                    start_x,
                    top,
                    button_w,
                    button_h,
                ),
                "HOME",
                self.go_home,
                None,
                14,
            )

            self.add_button(
                (
                    start_x + button_w + gap,
                    top,
                    button_w,
                    button_h,
                ),
                "RESTART",
                self.restart_game,
                RED_COLOR,
                14,
            )

    def update_buttons(self):
        mouse_pos = pygame.mouse.get_pos()

        for button in self.buttons:
            button.update(mouse_pos)

    def draw_buttons(self, allowed=None):
        for button in self.buttons:
            if allowed is not None and button.text not in allowed:
                continue

            button.draw(self)

    def handle_button_click(self, pos):
        for button in self.buttons:
            if button.rect.collidepoint(pos):
                button.callback()
                return True

        return False

    # ========================================================
    # NAVIGATION
    # ========================================================

    def open_modes(self):
        self.scene = "modes"
        self.rebuild_buttons()

    def go_home(self):
        self.game_id += 1
        self.ai_thinking = False

        with self.ai_lock:
            self.ai_result = None

        self.scene = "home"
        self.rebuild_buttons()

    def quit(self):
        self.running = False

    def start_human_game(self):
        self.mode = "human"
        self.reset_board()

        self.scene = "game"
        self.rebuild_buttons()

    def start_ai_game(self):
        self.mode = "ai"
        self.reset_board()

        self.scene = "game"
        self.rebuild_buttons()

    # ========================================================
    # GAME STATE
    # ========================================================

    def reset_board(self):
        self.game_id += 1

        self.board = create_board()
        self.current_player = RED
        self.winner = None

        self.last_move = None
        self.winning_positions = []

        self.move_history = []
        self.animations = []

        self.hover_col = None
        self.ai_thinking = False

        with self.ai_lock:
            self.ai_result = None

        self.result_button_rect = None

        self.message = ""
        self.message_until = 0

    def restart_game(self):
        self.reset_board()

    def can_play(self):
        if self.scene != "game":
            return False

        if self.winner is not None:
            return False

        if self.ai_thinking:
            return False

        if self.mode == "ai" and self.current_player == YELLOW:
            return False

        return True

    # ========================================================
    # MAKE A MOVE
    # ========================================================

    def make_move(self, col, piece):
        if self.winner is not None:
            return False

        if not is_valid_location(self.board, col):
            return False

        row = get_next_open_row(self.board, col)

        if row is None:
            return False

        self.move_history.append(
            {
                "board": [r[:] for r in self.board],
                "player": self.current_player,
                "last_move": self.last_move,
                "winner": self.winner,
                "winning_positions": self.winning_positions[:],
            }
        )

        drop_piece(
            self.board,
            row,
            col,
            piece,
        )

        self.last_move = (row, col)

        self.animations.append(
            {
                "row": row,
                "col": col,
                "piece": piece,
                "start": time.monotonic(),
            }
        )

        if check_winner(self.board, piece):
            self.winner = piece

            self.winning_positions = winning_cells(
                self.board,
                piece,
            )

        elif is_draw(self.board):
            self.winner = -1

        else:
            self.current_player = (
                YELLOW if piece == RED else RED
            )

        return True

    # ========================================================
    # UNDO
    # ========================================================

    def undo_move(self):
        if self.ai_thinking or not self.move_history:
            return

        if self.mode == "ai":
            steps = min(2, len(self.move_history))
        else:
            steps = 1

        for _ in range(steps):
            if not self.move_history:
                break

            state = self.move_history.pop()

            self.board = [r[:] for r in state["board"]]
            self.current_player = state["player"]
            self.last_move = state["last_move"]
            self.winner = state["winner"]

            self.winning_positions = (
                state["winning_positions"][:]
            )

        self.animations = []

    # ========================================================
    # AI
    # ========================================================

    def start_ai_turn(self):
        if self.mode != "ai":
            return

        if self.current_player != YELLOW:
            return

        if self.winner is not None or self.ai_thinking:
            return

        snapshot = [r[:] for r in self.board]
        current_id = self.game_id

        self.ai_thinking = True

        def worker():
            try:
                col = find_best_move(
                    snapshot,
                    ai_piece=YELLOW,
                    depth=AI_DEPTH,
                )
            except Exception:
                col = None

            with self.ai_lock:
                self.ai_result = (current_id, col)

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    def process_ai_result(self):
        result = None

        with self.ai_lock:
            if self.ai_result is not None:
                result = self.ai_result
                self.ai_result = None

        if result is None:
            return

        result_id, col = result

        if result_id != self.game_id:
            return

        self.ai_thinking = False

        if self.scene != "game":
            return

        if self.mode != "ai":
            return

        if self.winner is not None:
            return

        if self.current_player != YELLOW:
            return

        if col is not None and is_valid_location(self.board, col):
            self.make_move(col, YELLOW)

    # ========================================================
    # HOME SCREEN
    # ========================================================

    def draw_home(self):
        w = self.width
        h = self.height

        self.draw_pill(
            "STRATEGY  /  CLASSIC GAME",
            w // 2,
            int(h * 0.18),
            BLUE,
        )

        self.draw_text(
            "CONNECT",
            self.font(
                min(78, int(w * 0.075)),
                bold=True,
            ),
            WHITE,
            w // 2,
            int(h * 0.34),
        )

        self.draw_text(
            "4",
            self.font(
                min(108, int(w * 0.11)),
                bold=True,
            ),
            RED_COLOR,
            w // 2,
            int(h * 0.455),
        )

        self.draw_text(
            "CONNECT FOUR. THINK AHEAD.",
            self.font(15, bold=True),
            MUTED,
            w // 2,
            int(h * 0.535),
        )

        self.draw_buttons()

        self.draw_text(
            "RED  VS  YELLOW",
            self.font(11),
            MUTED,
            w // 2,
            h - 28,
        )

    # ========================================================
    # MODE SCREEN
    # ========================================================

    def draw_mode_card(
        self,
        rect,
        title,
        subtitle,
        accent,
        icon_type,
    ):
        hovered = rect.collidepoint(pygame.mouse.get_pos())

        background = PANEL_HOVER if hovered else PANEL
        border = accent if hovered else BORDER

        pygame.draw.rect(
            self.screen,
            background,
            rect,
            border_radius=20,
        )

        pygame.draw.rect(
            self.screen,
            border,
            rect,
            2 if hovered else 1,
            border_radius=20,
        )

        pygame.draw.rect(
            self.screen,
            accent,
            (rect.x + 24, rect.y + 22, 42, 4),
            border_radius=2,
        )

        cx = rect.centerx
        cy = rect.y + 66

        if icon_type == "players":
            pygame.draw.circle(
                self.screen,
                RED_COLOR,
                (cx - 18, cy),
                14,
            )

            pygame.draw.circle(
                self.screen,
                YELLOW_COLOR,
                (cx + 18, cy),
                14,
            )

        else:
            pygame.draw.circle(
                self.screen,
                YELLOW_COLOR,
                (cx, cy),
                20,
            )

            pygame.draw.circle(
                self.screen,
                PANEL,
                (cx, cy),
                9,
            )

        self.draw_text(
            title,
            self.font(18, bold=True),
            WHITE,
            cx,
            rect.y + 117,
        )

        self.draw_text(
            subtitle,
            self.font(12),
            MUTED,
            cx,
            rect.y + 145,
        )

        self.draw_text(
            "CLICK TO SELECT",
            self.font(10, bold=True),
            accent if hovered else MUTED,
            cx,
            rect.bottom - 19,
        )

    def draw_modes(self):
        w = self.width
        h = self.height

        self.draw_text(
            "CHOOSE YOUR MODE",
            self.font(
                min(46, int(w * 0.05)),
                bold=True,
            ),
            WHITE,
            w // 2,
            int(h * 0.20),
        )

        self.draw_text(
            "Choose how you want to play",
            self.font(16),
            MUTED,
            w // 2,
            int(h * 0.275),
        )

        card_w = min(330, int(w * 0.39))
        card_h = 190
        gap = 30

        total_w = card_w * 2 + gap
        left = (w - total_w) // 2
        top = int(h * 0.43)

        left_card = pygame.Rect(
            left,
            top,
            card_w,
            card_h,
        )

        right_card = pygame.Rect(
            left + card_w + gap,
            top,
            card_w,
            card_h,
        )

        self.draw_mode_card(
            left_card,
            "HUMAN VS HUMAN",
            "Play with a friend",
            RED_COLOR,
            "players",
        )

        self.draw_mode_card(
            right_card,
            "HUMAN VS AI",
            "Challenge the computer",
            YELLOW_COLOR,
            "ai",
        )

        self.draw_buttons(allowed={"BACK"})

    # ========================================================
    # BOARD GEOMETRY
    # ========================================================

    def board_geometry(self):
        w = self.width
        h = self.height

        available_w = min(w - 80, 770)
        available_h = h - 210

        cell = int(
            min(
                available_w / COLS,
                available_h / ROWS,
                90,
            )
        )

        cell = max(40, cell)

        board_w = cell * COLS
        board_h = cell * ROWS

        x = (w - board_w) // 2
        y = max(150, (h - board_h) // 2 + 35)

        return x, y, cell, board_w, board_h

    def get_column_at_pos(self, pos):
        x, y, cell, board_w, board_h = self.board_geometry()
        mx, my = pos

        if mx < x or mx >= x + board_w:
            return None

        if my < y or my >= y + board_h:
            return None

        return (mx - x) // cell

    # ========================================================
    # PIECES
    # ========================================================

    def draw_piece(
        self,
        x,
        y,
        radius,
        piece,
        highlight=False,
    ):
        color = RED_COLOR if piece == RED else YELLOW_COLOR

        if highlight:
            glow = (
                (105, 24, 40)
                if piece == RED
                else (103, 82, 20)
            )

            pygame.draw.circle(
                self.screen,
                glow,
                (int(x), int(y)),
                radius + 8,
            )

        pygame.draw.circle(
            self.screen,
            color,
            (int(x), int(y)),
            radius,
        )

        pygame.draw.circle(
            self.screen,
            (255, 255, 255),
            (
                int(x - radius * 0.28),
                int(y - radius * 0.30),
            ),
            max(2, radius // 5),
        )

    # ========================================================
    # DRAW BOARD
    # ========================================================

    def draw_board(self):
        x, y, cell, board_w, board_h = self.board_geometry()

        board_rect = pygame.Rect(
            x - 7,
            y - 7,
            board_w + 14,
            board_h + 14,
        )

        pygame.draw.rect(
            self.screen,
            BOARD_BORDER,
            board_rect,
            border_radius=19,
        )

        pygame.draw.rect(
            self.screen,
            BOARD_COLOR,
            (x, y, board_w, board_h),
            border_radius=13,
        )

        radius = int(cell * 0.37)
        now = time.monotonic()

        for row in range(ROWS):
            for col in range(COLS):
                cx = x + col * cell + cell // 2
                cy = y + row * cell + cell // 2

                piece = self.board[row][col]

                pygame.draw.circle(
                    self.screen,
                    HOLE_COLOR,
                    (cx, cy),
                    radius,
                )

                if piece != EMPTY:
                    self.draw_piece(
                        cx,
                        cy,
                        radius - 1,
                        piece,
                        (row, col) in self.winning_positions,
                    )

        # Falling piece animation
        for animation in self.animations:
            progress = min(
                1.0,
                (now - animation["start"]) / ANIMATION_TIME,
            )

            if progress >= 1.0:
                continue

            row = animation["row"]
            col = animation["col"]
            piece = animation["piece"]

            cx = x + col * cell + cell // 2
            target_y = y + row * cell + cell // 2
            start_y = y - cell

            eased = 1 - (1 - progress) ** 3

            current_y = start_y + (target_y - start_y) * eased

            self.draw_piece(
                cx,
                current_y,
                radius - 1,
                piece,
            )

        # Hover preview
        if (
            self.hover_col is not None
            and self.can_play()
            and is_valid_location(self.board, self.hover_col)
        ):
            col = self.hover_col

            cx = x + col * cell + cell // 2
            preview_y = y - 24

            color = (
                RED_COLOR
                if self.current_player == RED
                else YELLOW_COLOR
            )

            pygame.draw.circle(
                self.screen,
                color,
                (cx, preview_y),
                max(5, radius - 4),
                2,
            )

    # ========================================================
    # STATUS
    # ========================================================

    def current_status(self):
        if self.winner == RED:
            return "RED WINS!", RED_COLOR

        if self.winner == YELLOW:
            if self.mode == "ai":
                return "AI WINS!", YELLOW_COLOR

            return "YELLOW WINS!", YELLOW_COLOR

        if self.winner == -1:
            return "IT'S A DRAW!", WHITE

        if self.ai_thinking:
            return "AI IS THINKING...", YELLOW_COLOR

        if self.mode == "ai" and self.current_player == YELLOW:
            return "AI'S TURN", YELLOW_COLOR

        if self.current_player == RED:
            return "RED'S TURN", RED_COLOR

        return "YELLOW'S TURN", YELLOW_COLOR

    # ========================================================
    # GAME SCREEN
    # ========================================================

    def draw_game(self):
        w = self.width
        h = self.height

        self.draw_text(
            "CONNECT FOUR",
            self.font(25, bold=True),
            WHITE,
            28,
            32,
            center=False,
        )

        self.draw_text(
            "HUMAN VS AI" if self.mode == "ai" else "TWO PLAYERS",
            self.font(11, bold=True),
            MUTED,
            30,
            65,
            center=False,
        )

        self.draw_buttons()

        status, color = self.current_status()

        self.draw_pill(
            status,
            w // 2,
            108,
            color,
        )

        self.draw_board()

        if self.winner is not None:
            self.draw_result_overlay()

        self.draw_text(
            "CLICK A COLUMN TO DROP YOUR PIECE",
            self.font(11, bold=True),
            MUTED,
            w // 2,
            h - 25,
        )

    # ========================================================
    # RESULT OVERLAY
    # ========================================================

    def draw_result_overlay(self):
        w = self.width
        h = self.height

        overlay = pygame.Surface(
            (w, h),
            pygame.SRCALPHA,
        )

        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        box_w = min(430, w - 40)
        box_h = 220

        rect = pygame.Rect(
            (w - box_w) // 2,
            (h - box_h) // 2,
            box_w,
            box_h,
        )

        pygame.draw.rect(
            self.screen,
            PANEL,
            rect,
            border_radius=22,
        )

        pygame.draw.rect(
            self.screen,
            BORDER,
            rect,
            1,
            border_radius=22,
        )

        if self.winner == RED:
            title = "RED WINS!"
            accent = RED_COLOR

        elif self.winner == YELLOW:
            title = "AI WINS!" if self.mode == "ai" else "YELLOW WINS!"
            accent = YELLOW_COLOR

        else:
            title = "IT'S A DRAW!"
            accent = WHITE

        self.draw_text(
            title,
            self.font(30, bold=True),
            accent,
            w // 2,
            rect.y + 55,
        )

        self.draw_text(
            "Well played!",
            self.font(14),
            MUTED,
            w // 2,
            rect.y + 100,
        )

        button_rect = pygame.Rect(
            rect.centerx - 95,
            rect.y + 135,
            190,
            48,
        )

        self.result_button_rect = button_rect

        hovered = button_rect.collidepoint(
            pygame.mouse.get_pos()
        )

        pygame.draw.rect(
            self.screen,
            PANEL_HOVER if hovered else BG,
            button_rect,
            border_radius=12,
        )

        pygame.draw.rect(
            self.screen,
            accent,
            button_rect,
            1,
            border_radius=12,
        )

        self.draw_text(
            "PLAY AGAIN",
            self.font(14, bold=True),
            WHITE,
            button_rect.centerx,
            button_rect.centery,
        )

    # ========================================================
    # BOARD INPUT
    # ========================================================

    def handle_board_click(self, pos):
        if not self.can_play():
            return

        col = self.get_column_at_pos(pos)

        if col is None:
            return

        if not is_valid_location(self.board, col):
            self.message = "COLUMN IS FULL"
            self.message_until = time.monotonic() + 1.2
            return

        moved = self.make_move(
            col,
            self.current_player,
        )

        if (
            moved
            and self.mode == "ai"
            and self.winner is None
            and self.current_player == YELLOW
        ):
            self.start_ai_turn()

    # ========================================================
    # EVENTS
    # ========================================================

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                new_w = max(800, event.w)
                new_h = max(600, event.h)

                self.screen = pygame.display.set_mode(
                    (new_w, new_h),
                    pygame.RESIZABLE,
                )

                self.rebuild_buttons()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.scene != "home":
                        self.go_home()
                    else:
                        self.quit()

                elif self.scene == "game":
                    if event.key == pygame.K_r:
                        self.restart_game()

                    elif event.key == pygame.K_u:
                        self.undo_move()

                    elif pygame.K_1 <= event.key <= pygame.K_7:
                        col = event.key - pygame.K_1

                        x, y, cell, _, _ = self.board_geometry()

                        self.handle_board_click(
                            (
                                x + col * cell + 1,
                                y + 1,
                            )
                        )

            elif event.type == pygame.MOUSEMOTION:
                if self.scene == "game":
                    self.hover_col = self.get_column_at_pos(event.pos)
                else:
                    self.hover_col = None

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1:
                    continue

                pos = event.pos

                if self.scene == "home":
                    self.handle_button_click(pos)

                elif self.scene == "modes":
                    # The mode cards are the clickable buttons.
                    self.handle_button_click(pos)

                elif self.scene == "game":
                    if (
                        self.winner is not None
                        and self.result_button_rect is not None
                        and self.result_button_rect.collidepoint(pos)
                    ):
                        self.restart_game()

                    elif self.handle_button_click(pos):
                        continue

                    else:
                        self.handle_board_click(pos)

        return self.running

    # ========================================================
    # MAIN LOOP
    # ========================================================

    def run(self):
        while self.running:
            self.handle_events()
            self.process_ai_result()

            now = time.monotonic()

            self.animations = [
                animation
                for animation in self.animations
                if now - animation["start"] < ANIMATION_TIME
            ]

            self.update_buttons()
            self.draw_background()

            if self.scene == "home":
                self.draw_home()

            elif self.scene == "modes":
                self.draw_modes()

            elif self.scene == "game":
                self.draw_game()

            if self.message and time.monotonic() < self.message_until:
                self.draw_pill(
                    self.message,
                    self.width // 2,
                    self.height - 55,
                    RED_COLOR,
                )

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()