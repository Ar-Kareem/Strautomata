
import numpy as np

def evaluate(board):
    # Check all winning combinations, return scores
    winning_positions = [
        # Individual layers
        [(0, 0, 0), (0, 0, 1), (0, 0, 2)],
        [(0, 1, 0), (0, 1, 1), (0, 1, 2)],
        [(0, 2, 0), (0, 2, 1), (0, 2, 2)],
        [(1, 0, 0), (1, 0, 1), (1, 0, 2)],
        [(1, 1, 0), (1, 1, 1), (1, 1, 2)],
        [(1, 2, 0), (1, 2, 1), (1, 2, 2)],
        [(2, 0, 0), (2, 0, 1), (2, 0, 2)],
        [(2, 1, 0), (2, 1, 1), (2, 1, 2)],
        [(2, 2, 0), (2, 2, 1), (2, 2, 2)],
        
        # Vertical columns
        [(0, 0, 0), (1, 0, 0), (2, 0, 0)],
        [(0, 0, 1), (1, 0, 1), (2, 0, 1)],
        [(0, 0, 2), (1, 0, 2), (2, 0, 2)],
        [(0, 1, 0), (1, 1, 0), (2, 1, 0)],
        [(0, 1, 1), (1, 1, 1), (2, 1, 1)],
        [(0, 1, 2), (1, 1, 2), (2, 1, 2)],
        [(0, 2, 0), (1, 2, 0), (2, 2, 0)],
        [(0, 2, 1), (1, 2, 1), (2, 2, 1)],
        [(0, 2, 2), (1, 2, 2), (2, 2, 2)],
        
        # Diagonals
        [(0, 0, 0), (1, 1, 1), (2, 2, 2)],
        [(0, 0, 2), (1, 1, 1), (2, 2, 0)],
        [(0, 2, 0), (1, 1, 1), (2, 0, 2)],
        [(0, 2, 2), (1, 1, 1), (2, 0, 0)],
        
        # Layer-wise diagonals
        [(0, 0, 0), (1, 1, 1), (2, 0, 2)],
        [(0, 0, 2), (1, 1, 1), (2, 0, 0)],
        [(0, 2, 0), (1, 1, 1), (2, 2, 2)],
        [(0, 2, 2), (1, 1, 1), (2, 2, 0)],
    ]

    for positions in winning_positions:
        scores = [board[i][j][k] for i, j, k in positions]
        if scores == [1, 1, 1]:
            return 10  # Current player wins
        elif scores == [-1, -1, -1]:
            return -10  # Opponent wins

    return 0  # No winner yet

def minimax(board, depth, maximizing_player):
    score = evaluate(board)

    # If the game is over, return the score
    if score == 10 or score == -10:
        return score

    if all(board[i][j][k] != 0 for i in range(3) for j in range(3) for k in range(3)):
        return 0  # Draw

    if maximizing_player:
        best_value = -float('inf')
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:  # Check for empty cell
                        board[i][j][k] = 1  # Max player's turn
                        best_value = max(best_value, minimax(board, depth + 1, False))
                        board[i][j][k] = 0  # Undo move
        return best_value
    else:
        best_value = float('inf')
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:  # Check for empty cell
                        board[i][j][k] = -1  # Min player's turn
                        best_value = min(best_value, minimax(board, depth + 1, True))
                        board[i][j][k] = 0  # Undo move
        return best_value

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    best_move = None
    best_value = -float('inf')

    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:  # Check for empty cell
                    board[i][j][k] = 1  # Max player's turn
                    move_value = minimax(board, 0, False)
                    board[i][j][k] = 0  # Undo move

                    if move_value > best_value:
                        best_value = move_value
                        best_move = (i, j, k)

    return best_move
