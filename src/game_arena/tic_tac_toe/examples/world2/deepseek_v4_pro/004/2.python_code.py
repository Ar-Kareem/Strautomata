
import numpy as np
from typing import Tuple

def policy(board: list[list[int]]) -> Tuple[int, int]:
    """
    A minimax-based policy with alpha-beta pruning for 4x4 Tic Tac Toe.
    """
    # Convert board to numpy array for efficiency
    state = np.array(board, dtype=np.int8)

    # 1. Check if there is an immediate winning move
    for r in range(4):
        for c in range(4):
            if state[r, c] == 0:
                state[r, c] = 1
                if check_win(state, 1):
                    return (r, c)
                state[r, c] = 0

    # 2. Block opponent's immediate winning move
    for r in range(4):
        for c in range(4):
            if state[r, c] == 0:
                state[r, c] = -1
                if check_win(state, -1):
                    return (r, c)
                state[r, c] = 0

    # 3. Use minimax with alpha-beta to find best move
    best_move = minimax_decision(state)
    if best_move is None:
        # Fallback: pick first available move to guarantee legality
        for r in range(4):
            for c in range(4):
                if state[r, c] == 0:
                    return (r, c)
    return best_move


def check_win(board: np.ndarray, player: int) -> bool:
    """Check if player has won."""
    # Rows and columns
    for i in range(4):
        if np.all(board[i, :] == player) or np.all(board[:, i] == player):
            return True
    # Diagonals
    if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
        return True
    # 2x2 corners
    if (board[0, 0] == player and board[0, 3] == player and
        board[3, 0] == player and board[3, 3] == player):
        return True
    # 2x2 blocks
    for r in range(3):
        for c in range(3):
            if (board[r, c] == player and board[r, c+1] == player and
                board[r+1, c] == player and board[r+1, c+1] == player):
                return True
    return False


def is_terminal(board: np.ndarray) -> bool:
    """Check if game is over."""
    if check_win(board, 1) or check_win(board, -1):
        return True
    return not np.any(board == 0)


def evaluate(board: np.ndarray) -> int:
    """Heuristic evaluation from perspective of player 1."""
    if check_win(board, 1):
        return 10000
    if check_win(board, -1):
        return -10000
    if not np.any(board == 0):
        return 0

    score = 0
    # Center control heuristic
    center_positions = [(1,1), (1,2), (2,1), (2,2)]
    for r, c in center_positions:
        if board[r, c] == 1:
            score += 30
        elif board[r, c] == -1:
            score -= 30

    # Line potential heuristic
    lines = []
    # rows & cols
    for i in range(4):
        lines.append(board[i, :])
        lines.append(board[:, i])
    # diagonals
    lines.append(np.diag(board))
    lines.append(np.diag(np.fliplr(board)))
    # corners
    lines.append(np.array([board[0,0], board[0,3], board[3,0], board[3,3]]))
    # 2x2 blocks
    for r in range(3):
        for c in range(3):
            lines.append(np.array([board[r,c], board[r,c+1], board[r+1,c], board[r+1,c+1]]))

    for line in lines:
        if np.any(line == 1) and not np.any(line == -1):
            # count player 1 pieces
            count = np.sum(line == 1)
            if count == 3:
                score += 500
            elif count == 2:
                score += 50
            elif count == 1:
                score += 10
        elif np.any(line == -1) and not np.any(line == 1):
            count = np.sum(line == -1)
            if count == 3:
                score -= 500
            elif count == 2:
                score -= 50
            elif count == 1:
                score -= 10
    return score


def minimax_decision(board: np.ndarray, max_depth: int = 4) -> Tuple[int, int]:
    """Choose best move with minimax and alpha-beta."""
    best_score = -np.inf
    best_move = None
    alpha = -np.inf
    beta = np.inf

    moves = list(available_moves(board))
    # Order moves by center preference heuristic
    moves.sort(key=lambda m: center_heuristic(board, m), reverse=True)

    for r, c in moves:
        board[r, c] = 1
        score = minimax(board, max_depth-1, alpha, beta, False)
        board[r, c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best_move


def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """Minimax with alpha-beta pruning."""
    if is_terminal(board) or depth == 0:
        return evaluate(board)

    if maximizing:
        max_eval = -np.inf
        for r, c in available_moves(board):
            board[r, c] = 1
            eval_score = minimax(board, depth-1, alpha, beta, False)
            board[r, c] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = np.inf
        for r, c in available_moves(board):
            board[r, c] = -1
            eval_score = minimax(board, depth-1, alpha, beta, True)
            board[r, c] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def available_moves(board: np.ndarray):
    """Generator yielding empty cells."""
    for r in range(4):
        for c in range(4):
            if board[r, c] == 0:
                yield (r, c)


def center_heuristic(board: np.ndarray, move: Tuple[int, int]) -> int:
    """Give higher score to center moves."""
    r, c = move
    # Closer to center, the better
    dist = abs(r-1.5) + abs(c-1.5)
    return -dist
