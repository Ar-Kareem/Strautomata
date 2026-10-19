
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Calculates the optimal move for a 3x3 Tic Tac Toe game using Minimax with Alpha-Beta pruning.
    Player 1 (AI) maximizes, Player -1 (Opponent) minimizes.
    """

    def check_winner(b: list[list[int]]) -> int:
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

    def is_full(b: list[list[int]]) -> bool:
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    return False
        return True

    def minimax(b: list[list[int]], depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
        winner = check_winner(b)
        
        # Terminal states
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
                        value = minimax(b, depth + 1, False, alpha, beta)
                        b[r][c] = 0
                        best_val = max(best_val, value)
                        alpha = max(alpha, best_val)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return best_val
        else:
            best_val = math.inf
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = -1
                        value = minimax(b, depth + 1, True, alpha, beta)
                        b[r][c] = 0
                        best_val = min(best_val, value)
                        beta = min(beta, best_val)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return best_val

    best_score = -math.inf
    best_move = (-1, -1)
    
    # Iterate through all possible moves to find the best one
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1  # Make move
                score = minimax(board, 0, False, -math.inf, math.inf)
                board[r][c] = 0  # Undo move
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
                    
    return best_move
