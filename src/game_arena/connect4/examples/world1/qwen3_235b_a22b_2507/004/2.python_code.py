
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    grid = np.array(board, dtype=np.int8)
    player = 1  # We are always the current player (1)

    # Check if a column is valid (not full)
    def is_valid(col):
        return grid[0, col] == 0

    # Drop a disc in the specified column for the given player
    def drop_piece(board, col, piece):
        for r in range(5, -1, -1):
            if board[r, col] == 0:
                board[r, col] = piece
                return r
        return -1

    # Remove a disc (for undoing moves in search)
    def undo_move(board, col):
        for r in range(6):
            if board[r, col] != 0:
                board[r, col] = 0
                return

    # Check if a player has won
    def winning_move(board, piece):
        # Horizontal
        for r in range(6):
            for c in range(4):
                if all(board[r, c+i] == piece for i in range(4)):
                    return True
        # Vertical
        for r in range(3):
            for c in range(7):
                if all(board[r+i, c] == piece for i in range(4)):
                    return True
        # Diagonal (positive slope)
        for r in range(3):
            for c in range(4):
                if all(board[r+i, c+i] == piece for i in range(4)):
                    return True
        # Diagonal (negative slope)
        for r in range(3, 6):
            for c in range(4):
                if all(board[r-i, c+i] == piece for i in range(4)):
                    return True
        return False

    # Heuristic evaluation function
    def evaluate_window(window, player):
        opponent = -1
        score = 0
        player_count = np.count_nonzero(window == player)
        opponent_count = np.count_nonzero(window == opponent)
        empty_count = np.count_nonzero(window == 0)

        if player_count == 4:
            score += 1000
        elif player_count == 3 and empty_count == 1:
            score += 10
        elif player_count == 2 and empty_count == 2:
            score += 2

        if opponent_count == 3 and empty_count == 1:
            score -= 80
        elif opponent_count == 2 and empty_count == 2:
            score -= 15

        return score

    def score_position(board, player):
        score = 0
        center_array = board[:, 3]
        score += np.count_nonzero(center_array == player) * 3

        # Score horizontal
        for r in range(6):
            row = board[r, :]
            for c in range(4):
                window = row[c:c+4]
                score += evaluate_window(window, player)

        # Score vertical
        for c in range(7):
            col = board[:, c]
            for r in range(3):
                window = col[r:r+4]
                score += evaluate_window(window, player)

        # Score positive diagonal
        for r in range(3):
            for c in range(4):
                window = [board[r+i, c+i] for i in range(4)]
                score += evaluate_window(window, player)

        # Score negative diagonal
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i, c+i] for i in range(4)]
                score += evaluate_window(window, player)

        return score

    # Minimax with alpha-beta pruning
    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_cols = [c for c in range(7) if is_valid(c)]
        is_terminal = winning_move(board, 1) or winning_move(board, -1) or len(valid_cols) == 0

        if depth == 0 or is_terminal:
            if is_terminal:
                if winning_move(board, 1):
                    return (None, 1000000)
                elif winning_move(board, -1):
                    return (None, -1000000)
                else:
                    return (None, 0)
            else:
                return (None, score_position(board, 1))

        if maximizing_player:
            value = -np.inf
            column = valid_cols[0]
            for col in valid_cols:
                temp_board = board.copy()
                drop_piece(temp_board, col, 1)
                new_score = minimax(temp_board, depth-1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = np.inf
            column = valid_cols[0]
            for col in valid_cols:
                temp_board = board.copy()
                drop_piece(temp_board, col, -1)
                new_score = minimax(temp_board, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # Find the best move
    valid_columns = [c for c in range(7) if is_valid(c)]
    if len(valid_columns) == 1:
        return valid_columns[0]

    # Use minimax with depth 6
    best_col, _ = minimax(grid, depth=6, alpha=-np.inf, beta=np.inf, maximizing_player=True)
    return int(best_col)
