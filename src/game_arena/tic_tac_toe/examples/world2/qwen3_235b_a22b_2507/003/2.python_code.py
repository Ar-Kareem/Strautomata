
import numpy as np

def _is_win(board: np.ndarray, player: int) -> bool:
    # Check rows, cols, diags for 4 in a row
    for i in range(4):
        if np.all(board[i, :] == player):
            return True
        if np.all(board[:, i] == player):
            return True
    if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
        return True
    return False

def _get_legal_moves(board: np.ndarray):
    return [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]

def _evaluate(board: np.ndarray) -> float:
    score = 0
    lines = []
    # Add rows
    for i in range(4):
        lines.append(board[i, :])
    # Add cols
    for j in range(4):
        lines.append(board[:, j])
    # Diagonals
    lines.append(np.diag(board))
    lines.append(np.diag(np.fliplr(board)))
    
    for line in lines:
        mine = np.sum(line == 1)
        opp = np.sum(line == -1)
        if opp == 0:
            if mine == 3:
                score += 1000
            elif mine == 2:
                score += 100
            elif mine == 1:
                score += 10
        elif mine == 0:
            if opp == 3:
                score -= 1000
            elif opp == 2:
                score -= 100
            elif opp == 1:
                score -= 10
    return score

def _minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool):
    if _is_win(board, 1):
        return float('inf')
    if _is_win(board, -1):
        return float('-inf')
    if depth == 0 or len(_get_legal_moves(board)) == 0:
        return _evaluate(board)

    moves = _get_legal_moves(board)
    # Move ordering: center first for speed
    moves.sort(key=lambda x: abs(x[0]-1.5) + abs(x[1]-1.5))  # Prefer center

    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            board[move] = 1
            eval_score = _minimax(board, depth - 1, alpha, beta, False)
            board[move] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            board[move] = -1
            eval_score = _minimax(board, depth - 1, alpha, beta, True)
            board[move] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    np_board = np.array(board, dtype=int)
    
    # Check if I can win in one move
    for i in range(4):
        for j in range(4):
            if np_board[i, j] == 0:
                np_board[i, j] = 1
                if _is_win(np_board, 1):
                    return (i, j)
                np_board[i, j] = 0

    # Check if opponent can win in one move — block
    for i in range(4):
        for j in range(4):
            if np_board[i, j] == 0:
                np_board[i, j] = -1
                if _is_win(np_board, -1):
                    np_board[i, j] = 0
                    return (i, j)
                np_board[i, j] = 0

    # If no immediate threat, use minimax
    legal_moves = _get_legal_moves(np_board)
    if not legal_moves:
        return (0, 0)  # should not happen, but fallback

    # Prefer center moves
    legal_moves.sort(key=lambda x: abs(x[0]-1.5) + abs(x[1]-1.5))

    best_move = legal_moves[0]
    best_value = float('-inf')
    
    depth = 6  # Adjust depth based on game state
    for move in legal_moves:
        np_board[move] = 1
        value = _minimax(np_board, depth - 1, float('-inf'), float('inf'), False)
        np_board[move] = 0
        if value > best_value:
            best_value = value
            best_move = move

    return best_move
