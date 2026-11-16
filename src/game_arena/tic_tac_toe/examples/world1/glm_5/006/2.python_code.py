
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Calculates the optimal move for a 3x3 Tic Tac Toe game using Minimax.
    Player is 1, Opponent is -1, Empty is 0.
    """
    
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
        return 0

    def is_full(b):
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return False
        return True

    def minimax(b, depth, is_maximizing):
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth
        if winner == -1:
            return depth - 10
        if is_full(b):
            return 0

        if is_maximizing:
            best_val = -math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = 1
                        value = minimax(b, depth + 1, False)
                        b[r][c] = 0
                        best_val = max(best_val, value)
            return best_val
        else:
            best_val = math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = -1
                        value = minimax(b, depth + 1, True)
                        b[r][c] = 0
                        best_val = min(best_val, value)
            return best_val

    # Optimization: If the board is empty, take the center immediately.
    # This saves computation time on the first move.
    empty_count = sum(row.count(0) for row in board)
    if empty_count == 9:
        return (1, 1)

    best_move = (-1, -1)
    best_value = -math.inf

    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                # Make the move
                board[r][c] = 1
                move_value = minimax(board, 0, False)
                # Undo the move
                board[r][c] = 0

                if move_value > best_value:
                    best_value = move_value
                    best_move = (r, c)

    return best_move
