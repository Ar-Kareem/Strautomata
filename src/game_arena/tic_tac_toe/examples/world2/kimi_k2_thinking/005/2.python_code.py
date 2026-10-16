
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determines the best move for a 4x4 Tic Tac Toe game.
    Returns a tuple (row, col) representing the move.
    """
    # Convert board to numpy array for efficient operations
    board_np = np.array(board, dtype=int)
    
    # Get legal moves ordered by strategic importance
    legal_moves = _get_ordered_moves(board_np)
    
    # Fallback: return first empty cell (should never trigger in valid games)
    if not legal_moves:
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    return (i, j)
    
    # 1. Check for immediate winning move
    for move in legal_moves:
        if _is_winning_move(board_np, move, player=1):
            return move
    
    # 2. Check for immediate blocking move (opponent could win)
    for move in legal_moves:
        if _is_winning_move(board_np, move, player=-1):
            return move
    
    # 3. Use minimax search to find the best strategic move
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        i, j = move
        board_np[i, j] = 1  # Make move
        score = _minimax(board_np, depth=4, alpha=float('-inf'), 
                        beta=float('inf'), maximizing=False)
        board_np[i, j] = 0  # Undo move
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def _get_ordered_moves(board_np: np.ndarray) -> List[Tuple[int, int]]:
    """Returns legal moves ordered by strategic priority: center, corners, then edges."""
    center = [(1, 1), (1, 2), (2, 1), (2, 2)]
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    edges = [(i, j) for i in range(4) for j in range(4) 
             if (i, j) not in center + corners]
    
    all_moves = center + corners + edges
    legal_moves = [move for move in all_moves if board_np[move] == 0]
    return legal_moves

def _is_winning_move(board_np: np.ndarray, move: Tuple[int, int], player: int) -> bool:
    """Check if placing a piece at move would win the game."""
    i, j = move
    original = board_np[i, j]
    board_np[i, j] = player
    won = _check_win(board_np, player)
    board_np[i, j] = original
    return won

def _check_win(board_np: np.ndarray, player: int) -> bool:
    """Check if the given player has won."""
    # Check rows
    if np.any(np.all(board_np == player, axis=1)):
        return True
    
    # Check columns
    if np.any(np.all(board_np == player, axis=0)):
        return True
    
    # Check main diagonal
    if np.all(np.diag(board_np) == player):
        return True
    
    # Check anti-diagonal
    if np.all(np.diag(np.fliplr(board_np)) == player):
        return True
    
    return False

def _evaluate(board_np: np.ndarray) -> float:
    """Heuristic evaluation of board state from player 1's perspective."""
    # Terminal states
    if _check_win(board_np, 1):
        return float('inf')
    if _check_win(board_np, -1):
        return float('-inf')
    
    # Draw
    if np.all(board_np != 0):
        return 0
    
    score = 0.0
    lines = _get_all_lines(board_np)
    
    for line in lines:
        count_1 = np.count_nonzero(line == 1)
        count_minus1 = np.count_nonzero(line == -1)
        
        # Only score lines that aren't blocked by both players
        if count_1 > 0 and count_minus1 == 0:
            score += 10  ** count_1
        elif count_minus1 > 0 and count_1 == 0:
            score -= 10 ** count_minus1
    
    return score

def _get_all_lines(board_np: np.ndarray) -> List[np.ndarray]:
    """Get all potential winning lines (rows, columns, diagonals)."""
    lines = []
    
    # Rows
    for i in range(4):
        lines.append(board_np[i, :])
    
    # Columns
    for j in range(4):
        lines.append(board_np[:, j])
    
    # Diagonals
    lines.append(np.diag(board_np))
    lines.append(np.diag(np.fliplr(board_np)))
    
    return lines

def _minimax(board_np: np.ndarray, depth: int, alpha: float, 
            beta: float, maximizing: bool) -> float:
    """Minimax search with alpha-beta pruning."""
    # Check terminal states
    if _check_win(board_np, 1):
        return float('inf')
    if _check_win(board_np, -1):
        return float(' -inf')
    
    # Check draw
    if np.all(board_np != 0):
        return 0
    
    if depth == 0:
        return _evaluate(board_np)
    
    legal_moves = _get_ordered_moves(board_np)
    
    if maximizing:
        max_eval = float('-inf')
        for move in legal_moves:
            i, j = move
            board_np[i, j] = 1
            eval = _minimax(board_np, depth - 1, alpha, beta, False)
            board_np[i, j] = 0
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            i, j = move
            board_np[i, j] = -1
            eval = _minimax(board_np, depth - 1, alpha, beta, True)
            board_np[i, j] = 0
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval
