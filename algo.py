ROWS = 6
COLS = 7

EMPTY = 0
RED = 1
YELLOW = 2

WINDOW_LENGTH = 4


def create_board():
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]


def is_valid_location(board, col):
    return 0 <= col < COLS and board[0][col] == EMPTY


def get_valid_moves(board):
    return [col for col in range(COLS) if is_valid_location(board, col)]


def get_next_open_row(board, col):
    for row in range(ROWS - 1, -1, -1):
        if board[row][col] == EMPTY:
            return row
    return None


def drop_piece(board, row, col, piece):
    if row is not None and 0 <= row < ROWS and 0 <= col < COLS:
        board[row][col] = piece


def winning_cells(board, piece):
    # Horizontal
    for row in range(ROWS):
        for col in range(COLS - 3):
            cells = [(row, col + i) for i in range(4)]
            if all(board[r][c] == piece for r, c in cells):
                return cells

    # Vertical
    for row in range(ROWS - 3):
        for col in range(COLS):
            cells = [(row + i, col) for i in range(4)]
            if all(board[r][c] == piece for r, c in cells):
                return cells

    # Diagonal: bottom-left to top-right
    for row in range(3, ROWS):
        for col in range(COLS - 3):
            cells = [(row - i, col + i) for i in range(4)]
            if all(board[r][c] == piece for r, c in cells):
                return cells

    # Diagonal: top-left to bottom-right
    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            cells = [(row + i, col + i) for i in range(4)]
            if all(board[r][c] == piece for r, c in cells):
                return cells

    return []


def check_winner(board, piece):
    return bool(winning_cells(board, piece))


def is_draw(board):
    return all(board[0][col] != EMPTY for col in range(COLS))


def copy_board(board):
    return [row[:] for row in board]


def evaluate_window(window, piece):
    opponent = RED if piece == YELLOW else YELLOW
    score = 0

    own_count = window.count(piece)
    opponent_count = window.count(opponent)
    empty_count = window.count(EMPTY)

    if own_count == 4:
        score += 100000
    elif own_count == 3 and empty_count == 1:
        score += 100
    elif own_count == 2 and empty_count == 2:
        score += 10

    if opponent_count == 3 and empty_count == 1:
        score -= 120

    return score


def score_position(board, piece):
    score = 0

    # Prefer the centre column
    center_col = COLS // 2
    center_count = sum(
        1 for row in range(ROWS) if board[row][center_col] == piece
    )
    score += center_count * 6

    # Horizontal windows
    for row in range(ROWS):
        for col in range(COLS - 3):
            window = board[row][col:col + 4]
            score += evaluate_window(window, piece)

    # Vertical windows
    for col in range(COLS):
        for row in range(ROWS - 3):
            window = [board[row + i][col] for i in range(4)]
            score += evaluate_window(window, piece)

    # Diagonal: bottom-left to top-right
    for row in range(3, ROWS):
        for col in range(COLS - 3):
            window = [board[row - i][col + i] for i in range(4)]
            score += evaluate_window(window, piece)

    # Diagonal: top-left to bottom-right
    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            window = [board[row + i][col + i] for i in range(4)]
            score += evaluate_window(window, piece)

    return score


def is_terminal_node(board):
    return (
        check_winner(board, RED)
        or check_winner(board, YELLOW)
        or is_draw(board)
    )


def minimax(board, depth, alpha, beta, maximizing_player, ai_piece):
    opponent = RED if ai_piece == YELLOW else YELLOW
    valid_moves = get_valid_moves(board)

    if check_winner(board, ai_piece):
        return None, 1_000_000 + depth

    if check_winner(board, opponent):
        return None, -1_000_000 - depth

    if depth == 0 or is_draw(board):
        return None, score_position(board, ai_piece)

    # Prefer centre columns for stronger pruning
    valid_moves.sort(key=lambda col: abs(COLS // 2 - col))

    if maximizing_player:
        best_score = float("-inf")
        best_col = valid_moves[0] if valid_moves else None

        for col in valid_moves:
            row = get_next_open_row(board, col)
            child = copy_board(board)
            drop_piece(child, row, col, ai_piece)

            _, score = minimax(
                child, depth - 1, alpha, beta, False, ai_piece
            )

            if score > best_score:
                best_score = score
                best_col = col

            alpha = max(alpha, best_score)

            if alpha >= beta:
                break

        return best_col, best_score

    best_score = float("inf")
    best_col = valid_moves[0] if valid_moves else None

    for col in valid_moves:
        row = get_next_open_row(board, col)
        child = copy_board(board)
        drop_piece(child, row, col, opponent)

        _, score = minimax(
            child, depth - 1, alpha, beta, True, ai_piece
        )

        if score < best_score:
            best_score = score
            best_col = col

        beta = min(beta, best_score)

        if alpha >= beta:
            break

    return best_col, best_score


def find_best_move(board, ai_piece=YELLOW, depth=4):
    valid_moves = get_valid_moves(board)

    if not valid_moves:
        return None

    # First, take a winning move if one exists.
    for col in valid_moves:
        row = get_next_open_row(board, col)
        child = copy_board(board)
        drop_piece(child, row, col, ai_piece)

        if check_winner(child, ai_piece):
            return col

    # Otherwise, block an immediate opponent win.
    opponent = RED if ai_piece == YELLOW else YELLOW

    for col in valid_moves:
        row = get_next_open_row(board, col)
        child = copy_board(board)
        drop_piece(child, row, col, opponent)

        if check_winner(child, opponent):
            return col

    col, _ = minimax(
        copy_board(board),
        depth,
        float("-inf"),
        float("inf"),
        True,
        ai_piece,
    )

    return col if col is not None else valid_moves[0]