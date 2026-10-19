
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)

    # Check for immediate winning move
    winning_move = find_winning_move(board_np, 1)
    if winning_move is not None:
        return winning_move

    # Check for opponent's winning move and block
    opponent_winning_move = find_winning_move(board_np, -1)
    if opponent_winning_move is not None:
        return opponent_winning_move

    # Prefer center if empty
    if board_np[1, 1, 1] == 0:
        return (1, 1, 1)

    # Prefer corners over edges
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if board_np[corner] == 0:
            return corner

    # Use minimax with alpha-beta pruning for deeper analysis
    best_move = minimax(board_np, depth=5, alpha=-float('inf'), beta=float('inf'), maximizing_player=True)
    if best_move is not None:
        return best_move

    # Fallback: pick a random legal move
    legal_moves = np.argwhere(board_np == 0)
    if len(legal_moves) > 0:
        return tuple(legal_moves[np.random.randint(len(legal_moves))])

    # Should never reach here if the board is not full
    return (0, 0, 0)

def find_winning_move(board: np.ndarray, player: int) -> Tuple[int, int, int]:
    # Check all rows, columns, and diagonals in all 3 layers (x, y, z)
    directions = [
        # Rows in each layer (fixed x, y, or z)
        [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if i == x],
        [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if j == y],
        [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if k == z],
        # Diagonals in each layer (fixed x, y, or z)
        [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if i == j == k],
        [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if i == (2 - j) and j == k],
        [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if i == j and j == (2 - k)],
        [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if i == (2 - j) and j == (2 - k)],
        # 3D diagonals (space diagonals)
        [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if i == j == k],
        [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if i == (2 - j) and j == (2 - k) and k == (2 - i)],
    ]

    # Check all possible lines (rows, columns, diagonals in all 3D layers)
    for x in range(3):
        for y in range(3):
            for z in range(3):
                # Check rows in x-layer (fixed x)
                for j in range(3):
                    for k in range(3):
                        if board[x, j, k] == 0:
                            if all(board[x, j, m] == player for m in range(3) if m != k):
                                return (x, j, k)
                # Check columns in y-layer (fixed y)
                for i in range(3):
                    for k in range(3):
                        if board[i, y, k] == 0:
                            if all(board[m, y, k] == player for m in range(3) if m != i):
                                return (i, y, k)
                # Check columns in z-layer (fixed z)
                for i in range(3):
                    for j in range(3):
                        if board[i, j, z] == 0:
                            if all(board[i, m, z] == player for m in range(3) if m != j):
                                return (i, j, z)
                # Check diagonals in x-layer (fixed x)
                if board[x, 0, 0] == board[x, 1, 1] == board[x, 2, 2] == player:
                    for k in range(3):
                        if board[x, k, k] == 0:
                            return (x, k, k)
                if board[x, 0, 2] == board[x, 1, 1] == board[x, 2, 0] == player:
                    for k in range(3):
                        if board[x, k, 2 - k] == 0:
                            return (x, k, 2 - k)
                # Check diagonals in y-layer (fixed y)
                if board[0, y, 0] == board[1, y, 1] == board[2, y, 2] == player:
                    for i in range(3):
                        if board[i, y, i] == 0:
                            return (i, y, i)
                if board[0, y, 2] == board[1, y, 1] == board[2, y, 0] == player:
                    for i in range(3):
                        if board[i, y, 2 - i] == 0:
                            return (i, y, 2 - i)
                # Check diagonals in z-layer (fixed z)
                if board[0, 0, z] == board[1, 1, z] == board[2, 2, z] == player:
                    for i in range(3):
                        if board[i, i, z] == 0:
                            return (i, i, z)
                if board[0, 2, z] == board[1, 1, z] == board[2, 0, z] == player:
                    for i in range(3):
                        if board[i, 2 - i, z] == 0:
                            return (i, 2 - i, z)
                # Check 3D space diagonals
                if board[0, 0, 0] == board[1, 1, 1] == board[2, 2, 2] == player:
                    for i in range(3):
                        if board[i, i, i] == 0:
                            return (i, i, i)
                if board[0, 0, 2] == board[1, 1, 1] == board[2, 2, 0] == player:
                    for i in range(3):
                        if board[i, i, 2 - i] == 0:
                            return (i, i, 2 - i)
                if board[0, 2, 0] == board[1, 1, 1] == board[2, 0, 2] == player:
                    for i in range(3):
                        if board[i, 2 - i, i] == 0:
                            return (i, 2 - i, i)
                if board[0, 2, 2] == board[1, 1, 1] == board[2, 0, 0] == player:
                    for i in range(3):
                        if board[i, 2 - i, 2 - i] == 0:
                            return (i, 2 - i, 2 - i)
    return None

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> Tuple[int, int, int]:
    if depth == 0 or is_terminal(board):
        return evaluate(board, maximizing_player)

    if maximizing_player:
        best_score = -float('inf')
        best_move = None
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i, j, k] == 0:
                        board[i, j, k] = 1
                        score = minimax(board, depth - 1, alpha, beta, False)[0]
                        board[i, j, k] = 0
                        if score > best_score:
                            best_score = score
                            best_move = (i, j, k)
                        alpha = max(alpha, best_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
        return (best_score, best_move)
    else:
        best_score = float('inf')
        best_move = None
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i, j, k] == 0:
                        board[i, j, k] = -1
                        score = minimax(board, depth - 1, alpha, beta, True)[0]
                        board[i, j, k] = 0
                        if score < best_score:
                            best_score = score
                            best_move = (i, j, k)
                        beta = min(beta, best_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
        return (best_score, best_move)

def evaluate(board: np.ndarray, maximizing_player: bool) -> float:
    player = 1 if maximizing_player else -1
    opponent = -1 if maximizing_player else 1

    # Check for win/loss
    if is_terminal(board):
        if check_win(board, player):
            return 1000 if maximizing_player else -1000
        elif check_win(board, opponent):
            return -1000 if maximizing_player else 1000
        else:
            return 0

    # Evaluate based on potential winning lines
    score = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == player:
                    score += 1
                elif board[i, j, k] == opponent:
                    score -= 1

    # Center control
    if board[1, 1, 1] == player:
        score += 5
    elif board[1, 1, 1] == opponent:
        score -= 5

    # Corner control
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if board[corner] == player:
            score += 3
        elif board[corner] == opponent:
            score -= 3

    return score

def is_terminal(board: np.ndarray) -> bool:
    return check_win(board, 1) or check_win(board, -1) or np.all(board != 0)

def check_win(board: np.ndarray, player: int) -> bool:
    # Check rows in each layer (fixed x, y, or z)
    for i in range(3):
        for j in range(3):
            if all(board[i, j, k] == player for k in range(3)):
                return True
        for k in range(3):
            if all(board[i, j, k] == player for j in range(3)):
                return True
    for j in range(3):
        for k in range(3):
            if all(board[i, j, k] == player for i in range(3)):
                return True

    # Check diagonals in each layer (fixed x, y, or z)
    for i in range(3):
        if board[i, 0, 0] == board[i, 1, 1] == board[i, 2, 2] == player:
            return True
        if board[i, 0, 2] == board[i, 1, 1] == board[i, 2, 0] == player:
            return True
    for j in range(3):
        if board[0, j, 0] == board[1, j, 1] == board[2, j, 2] == player:
            return True
        if board[0, j, 2] == board[1, j, 1] == board[2, j, 0] == player:
            return True
    for k in range(3):
        if board[0, 0, k] == board[1, 1, k] == board[2, 2, k] == player:
            return True
        if board[0, 2, k] == board[1, 1, k] == board[2, 0, k] == player:
            return True

    # Check 3D space diagonals
    if board[0, 0, 0] == board[1, 1, 1] == board[2, 2, 2] == player:
        return True
    if board[0, 0, 2] == board[1, 1, 1] == board[2, 2, 0] == player:
        return True
    if board[0, 2, 0] == board[1, 1, 1] == board[2, 0, 2] == player:
        return True
    if board[0, 2, 2] == board[1, 1, 1] == board[2, 0, 0] == player:
        return True

    return False
