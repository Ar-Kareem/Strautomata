
import random
import numpy as np

def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    # Convert legal_moves to (row, col) pairs for easier handling
    legal_positions = [(i // 3, i % 3) for i in legal_moves]

    # Avoid cells where board[row][col] == 1 (already confirmed as ours)
    legal_positions = [(r, c) for r, c in legal_positions if board[r][c] != 1]

    if not legal_positions:
        # Fallback: return any legal move (shouldn't happen per problem constraints)
        return (legal_moves[0] // 3, legal_moves[0] % 3)

    # Evaluate all legal moves using minimax with alpha-beta pruning
    best_score = -float('inf')
    best_move = None

    for move in legal_positions:
        r, c = move
        # Simulate placing a mark (1) at (r, c)
        board[r][c] = 1
        score = minimax(board, False, -float('inf'), float('inf'))
        board[r][c] = 0  # Undo the move

        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def minimax(board: list[list[int]], is_maximizing: bool, alpha: float, beta: float) -> int:
    # Check if the game is over (win/loss/draw)
    if check_winner(board, 1):
        return 10 - len([cell for row in board for cell in row if cell == 0])  # Prefer faster wins
    elif check_winner(board, -1):  # Opponent wins (phantom assumption)
        return -10 + len([cell for row in board for cell in row if cell == 0])  # Prefer slower losses
    elif len([cell for row in board for cell in row if cell == 0]) == 0:
        return 0  # Draw

    if is_maximizing:
        best_score = -float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:  # Only consider empty cells (phantom assumption)
                    board[r][c] = 1
                    score = minimax(board, False, alpha, beta)
                    board[r][c] = 0
                    best_score = max(score, best_score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
        return best_score
    else:
        best_score = float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:  # Opponent's turn (phantom assumption)
                    board[r][c] = -1
                    score = minimax(board, True, alpha, beta)
                    board[r][c] = 0
                    best_score = min(score, best_score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
        return best_score

def check_winner(board: list[list[int]], player: int) -> bool:
    # Check rows, columns, and diagonals for a winner
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):  # Row
            return True
        if all(board[j][i] == player for j in range(3)):  # Column
            return True
    if all(board[i][i] == player for i in range(3)):  # Diagonal
        return True
    if all(board[i][2 - i] == player for i in range(3)):  # Anti-diagonal
        return True
    return False
