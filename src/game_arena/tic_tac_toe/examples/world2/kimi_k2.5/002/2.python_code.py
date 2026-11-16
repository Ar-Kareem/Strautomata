
from typing import List, Tuple

# Precompute all winning lines (4-in-a-row) for 4x4 board
WIN_LINES = [
    # Rows
    [(0, 0), (0, 1), (0, 2), (0, 3)],
    [(1, 0), (1, 1), (1, 2), (1, 3)],
    [(2, 0), (2, 1), (2, 2), (2, 3)],
    [(3, 0), (3, 1), (3, 2), (3, 3)],
    # Columns
    [(0, 0), (1, 0), (2, 0), (3, 0)],
    [(0, 1), (1, 1), (2, 1), (3, 1)],
    [(0, 2), (1, 2), (2, 2), (3, 2)],
    [(0, 3), (1, 3), (2, 3), (3, 3)],
    # Diagonals
    [(0, 0), (1, 1), (2, 2), (3, 3)],
    [(0, 3), (1, 2), (2, 1), (3, 0)]
]

def get_empty_cells(board: List[List[int]]) -> List[Tuple[int, int]]:
    """Return list of empty cell coordinates."""
    return [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

def is_winner(board: List[List[int]], player: int) -> bool:
    """Check if player has won (4 in a row)."""
    for line in WIN_LINES:
        if all(board[r][c] == player for r, c in line):
            return True
    return False

def would_win(board: List[List[int]], move: Tuple[int, int], player: int) -> bool:
    """Check if placing player at move results in a win, without modifying board."""
    r, c = move
    # Check row r
    if all(board[r][i] == player for i in range(4) if i != c):
        return True
    # Check column c
    if all(board[i][c] == player for i in range(4) if i != r):
        return True
    # Check main diagonal (r == c)
    if r == c:
        if all(board[i][i] == player for i in range(4) if i != r):
            return True
    # Check anti-diagonal (r + c == 3)
    if r + c == 3:
        if all(board[i][3 - i] == player for i in range(4) if i != r):
            return True
    return False

def evaluate(board: List[List[int]]) -> int:
    """Heuristic evaluation of board state from perspective of player 1."""
    score = 0
    for line in WIN_LINES:
        vals = [board[r][c] for r, c in line]
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        
        if opp_count == 0:
            # Lines only we threaten
            if my_count == 4:
                score += 10000
            elif my_count == 3:
                score += 100
            elif my_count == 2:
                score += 10
            elif my_count == 1:
                score += 1
        elif my_count == 0:
            # Lines only opponent threatens
            if opp_count == 4:
                score -= 10000
            elif opp_count == 3:
                score -= 100
            elif opp_count == 2:
                score -= 10
            elif opp_count == 1:
                score -= 1
    return score

def minimax(board: List[List[int]], depth: int, is_maximizing: bool, 
            alpha: float, beta: float) -> int:
    """Alpha-beta minimax search."""
    if depth == 0:
        return evaluate(board)
    
    moves = get_empty_cells(board)
    if not moves:
        return 0  # Draw
    
    if is_maximizing:
        max_eval = -float('inf')
        for r, c in moves:
            board[r][c] = 1
            if is_winner(board, 1):
                board[r][c] = 0
                return 10000
            eval_score = minimax(board, depth - 1, False, alpha, beta)
            board[r][c] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in moves:
            board[r][c] = -1
            if is_winner(board, -1):
                board[r][c] = 0
                return -10000
            eval_score = minimax(board, depth - 1, True, alpha, beta)
            board[r][c] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """Determine next move for player 1."""
    moves = get_empty_cells(board)
    if not moves:
        return (0, 0)  # Should not happen in valid game
    
    # 1. Immediate win
    for move in moves:
        if would_win(board, move, 1):
            return move
    
    # 2. Block opponent immediate win
    for move in moves:
        if would_win(board, move, -1):
            return move
    
    # 3. Determine search depth based on game progression
    n_empty = len(moves)
    if n_empty >= 12:
        depth = 2
    elif n_empty >= 8:
        depth = 3
    elif n_empty >= 4:
        depth = 4
    else:
        depth = n_empty  # Exhaustive search for endgame
    
    # Sort moves by centrality to improve alpha-beta pruning
    # (Center moves are usually better)
    def centrality(move):
        r, c = move
        return abs(r - 1.5) + abs(c - 1.5)
    
    moves.sort(key=centrality)
    
    best_move = moves[0]
    best_score = -float('inf')
    
    for move in moves:
        r, c = move
        board[r][c] = 1
        score = minimax(board, depth - 1, False, -float('inf'), float('inf'))
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
