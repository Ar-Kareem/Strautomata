
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for Player 1 (AI) using the Minimax algorithm.
    Returns a tuple (row, col) representing the best move.
    """
    
    # Check if the game has a winner
    def check_winner(b):
        # Check rows
        for r in range(3):
            if b[r][0] == b[r][1] == b[r][2] != 0:
                return b[r][0]
        # Check columns
        for c in range(3):
            if b[0][c] == b[1][c] == b[2][c] != 0:
                return b[0][c]
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return b[0][2]
        return None

    # Check if the board is full
    def is_full(b):
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return False
        return True

    # Minimax recursive algorithm
    def minimax(b, depth, is_maximizing):
        winner = check_winner(b)
        if winner == 1:   # AI wins
            return 10 - depth
        if winner == -1:  # Opponent wins
            return depth - 10
        if is_full(b):    # Draw
            return 0

        if is_maximizing:
            best_val = -math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = 1
                        val = minimax(b, depth + 1, False)
                        b[r][c] = 0
                        best_val = max(best_val, val)
            return best_val
        else:
            best_val = math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = -1
                        val = minimax(b, depth + 1, True)
                        b[r][c] = 0
                        best_val = min(best_val, val)
            return best_val

    best_score = -math.inf
    best_move = (-1, -1)

    # Iterate over all possible moves to find the optimal one
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1  # Make move
                move_score = minimax(board, 0, False)
                board[r][c] = 0  # Undo move
                
                if move_score > best_score:
                    best_score = move_score
                    best_move = (r, c)

    return best_move
