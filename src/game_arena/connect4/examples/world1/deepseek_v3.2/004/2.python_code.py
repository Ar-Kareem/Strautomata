
import copy
import math

def policy(board: list[list[int]]) -> int:
    # Constants
    ROWS = 6
    COLS = 7
    WIN_LENGTH = 4
    PLAYER = 1
    OPPONENT = -1

    # Helper functions
    def get_valid_moves(board):
        """Return list of column indices that are not full."""
        return [c for c in range(COLS) if board[0][c] == 0]

    def make_move(board, col, player):
        """Return a new board with player's disc dropped in column col."""
        new_board = copy.deepcopy(board)
        for row in range(ROWS - 1, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board

    def count_window(window, player):
        """Count how many discs of player are in the window."""
        return sum(1 for cell in window if cell == player)

    def is_win(board, player):
        """Check if player has won."""
        # Check horizontal
        for r in range(ROWS):
            for c in range(COLS - WIN_LENGTH + 1):
                window = [board[r][c + i] for i in range(WIN_LENGTH)]
                if all(cell == player for cell in window):
                    return True
        # Check vertical
        for r in range(ROWS - WIN_LENGTH + 1):
            for c in range(COLS):
                window = [board[r + i][c] for i in range(WIN_LENGTH)]
                if all(cell == player for cell in window):
                    return True
        # Check diagonal (positive slope)
        for r in range(ROWS - WIN_LENGTH + 1):
            for c in range(COLS - WIN_LENGTH + 1):
                window = [board[r + i][c + i] for i in range(WIN_LENGTH)]
                if all(cell == player for cell in window):
                    return True
        # Check diagonal (negative slope)
        for r in range(WIN_LENGTH - 1, ROWS):
            for c in range(COLS - WIN_LENGTH + 1):
                window = [board[r - i][c + i] for i in range(WIN_LENGTH)]
                if all(cell == player for cell in window):
                    return True
        return False

    def evaluate_window(window, player):
        """Score a single window of length 4 for the given player."""
        opponent = PLAYER if player == OPPONENT else OPPONENT
        if opponent in window and player in window:
            return 0  # blocked window, no threat
        count_player = window.count(player)
        count_empty = window.count(0)
        if count_player == 4:
            return 1000000  # should already be caught by is_win
        if count_player == 3 and count_empty == 1:
            return 100
        if count_player == 2 and count_empty == 2:
            return 10
        if count_player == 1 and count_empty == 3:
            return 1
        # opponent's windows (negative for our evaluation)
        if count_player == 0:
            count_opponent = window.count(opponent)
            if count_opponent == 3 and count_empty == 1:
                return -1000  # opponent threat (we'll block elsewhere)
            if count_opponent == 2 and count_empty == 2:
                return -50
            if count_opponent == 1 and count_empty == 3:
                return -1
        return 0

    def evaluate_board(board):
        """Heuristic evaluation of the board for PLAYER (us)."""
        score = 0
        # Prefer center column
        center_col = COLS // 2
        center_count = sum(board[r][center_col] == PLAYER for r in range(ROWS))
        score += center_count * 3

        # Evaluate all windows of length 4
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - WIN_LENGTH + 1):
                window = [board[r][c + i] for i in range(WIN_LENGTH)]
                score += evaluate_window(window, PLAYER)
        # Vertical
        for r in range(ROWS - WIN_LENGTH + 1):
            for c in range(COLS):
                window = [board[r + i][c] for i in range(WIN_LENGTH)]
                score += evaluate_window(window, PLAYER)
        # Diagonal (positive slope)
        for r in range(ROWS - WIN_LENGTH + 1):
            for c in range(COLS - WIN_LENGTH + 1):
                window = [board[r + i][c + i] for i in range(WIN_LENGTH)]
                score += evaluate_window(window, PLAYER)
        # Diagonal (negative slope)
        for r in range(WIN_LENGTH - 1, ROWS):
            for c in range(COLS - WIN_LENGTH + 1):
                window = [board[r - i][c + i] for i in range(WIN_LENGTH)]
                score += evaluate_window(window, PLAYER)
        return score

    def minimax(board, depth, alpha, beta, maximizing_player):
        """Minimax with alpha-beta pruning.
        Returns (score, move_column) for the current player at this node.
        """
        valid_moves = get_valid_moves(board)
        # Terminal conditions
        if is_win(board, PLAYER):
            return (1000000, None)
        if is_win(board, OPPONENT):
            return (-1000000, None)
        if depth == 0 or not valid_moves:
            return (evaluate_board(board), None)

        if maximizing_player:
            max_score = -math.inf
            best_move = valid_moves[0]
            for col in valid_moves:
                child = make_move(board, col, PLAYER)
                score, _ = minimax(child, depth - 1, alpha, beta, False)
                if score > max_score:
                    max_score = score
                    best_move = col
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return (max_score, best_move)
        else:
            min_score = math.inf
            best_move = valid_moves[0]
            for col in valid_moves:
                child = make_move(board, col, OPPONENT)
                score, _ = minimax(child, depth - 1, alpha, beta, True)
                if score < min_score:
                    min_score = score
                    best_move = col
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return (min_score, best_move)

    # First, check for immediate winning move
    valid_moves = get_valid_moves(board)
    for col in valid_moves:
        new_board = make_move(board, col, PLAYER)
        if is_win(new_board, PLAYER):
            return col

    # Then, check for opponent's immediate winning move and block it
    for col in valid_moves:
        new_board = make_move(board, col, OPPONENT)
        if is_win(new_board, OPPONENT):
            return col

    # Otherwise, run minimax with depth 5 (adjustable)
    depth = 5
    _, best_col = minimax(board, depth, -math.inf, math.inf, True)
    # If minimax returns None (shouldn't happen), pick first valid move
    if best_col is None:
        return valid_moves[0]
    return best_col
