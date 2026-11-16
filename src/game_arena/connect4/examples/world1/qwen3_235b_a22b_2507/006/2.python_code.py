
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    grid = np.array(board, dtype=np.int8)
    
    # Constants
    ROWS, COLS = 6, 7
    EMPTY = 0
    PLAYER = 1  # current player
    OPPONENT = -1

    def is_valid_col(col):
        return grid[0, col] == EMPTY

    def drop_piece(col, piece):
        for r in range(ROWS-1, -1, -1):
            if grid[r, col] == EMPTY:
                grid[r, col] = piece
                return r
        return -1

    def undo_move(row, col):
        grid[row, col] = EMPTY

    def get_valid_moves():
        return [c for c in range(COLS) if is_valid_col(c)]

    def check_winner(piece):
        # Check horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(grid[r, c+i] == piece for i in range(4)):
                    return True
        # Check vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(grid[r+i, c] == piece for i in range(4)):
                    return True
        # Check diagonal /
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if all(grid[r-i, c+i] == piece for i in range(4)):
                    return True
        # Check diagonal \
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(grid[r+i, c+i] == piece for i in range(4)):
                    return True
        return False

    def evaluate_window(window, player):
        score = 0
        opp = OPPONENT if player == PLAYER else PLAYER

        if np.sum(window == player) == 4:
            score += 1000
        elif np.sum(window == player) == 3 and np.sum(window == EMPTY) == 1:
            score += 10
        elif np.sum(window == player) == 2 and np.sum(window == EMPTY) == 2:
            score += 3

        if np.sum(window == opp) == 3 and np.sum(window == EMPTY) == 1:
            score -= 80

        return score

    def score_position():
        score = 0
        # Center column preference
        center_col = grid[:, COLS//2]
        center_count = np.sum(center_col == PLAYER)
        score += center_count * 6

        # Evaluate all possible windows of 4
        # Horizontal
        for r in range(ROWS):
            row_array = grid[r, :]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, PLAYER)

        # Vertical
        for c in range(COLS):
            col_array = grid[:, c]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, PLAYER)

        # Diagonals /
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [grid[r+i, c+3-i] for i in range(4)]
                score += evaluate_window(np.array(window), PLAYER)

        # Diagonals \
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [grid[r+i, c+i] for i in range(4)]
                score += evaluate_window(np.array(window), PLAYER)

        return score

    def minimax(depth, alpha, beta, maximizing_player):
        valid_moves = get_valid_moves()
        if not valid_moves or depth == 0:
            return None, score_position()

        if maximizing_player:
            value = -np.inf
            column = valid_moves[0]
            for col in valid_moves:
                row = drop_piece(col, PLAYER)
                _, new_score = minimax(depth - 1, alpha, beta, False)
                undo_move(row, col)
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = np.inf
            column = valid_moves[0]
            for col in valid_moves:
                row = drop_piece(col, OPPONENT)
                _, new_score = minimax(depth - 1, alpha, beta, True)
                undo_move(row, col)
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return column, value

    # First, check if we can win in one move
    for col in range(COLS):
        if not is_valid_col(col):
            continue
        row = drop_piece(col, PLAYER)
        if check_winner(PLAYER):
            undo_move(row, col)
            return col
        undo_move(row, col)

    # Check if opponent can win in one move, block it
    for col in range(COLS):
        if not is_valid_col(col):
            continue
        row = drop_piece(col, OPPONENT)
        if check_winner(OPPONENT):
            undo_move(row, col)
            return col
        undo_move(row, col)

    # Otherwise, use minimax with depth limit
    # Adjust depth based on remaining space for safety
    depth = 6
    best_col, _ = minimax(depth, -np.inf, np.inf, True)
    return best_col
