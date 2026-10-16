
import numpy as np

# Precompute all 5-in-a-row lines (32 total: 12 horizontal, 12 vertical, 4 \, 4 /)
_LINES = []
# Horizontal (6 rows × 2 segments)
for r in range(6):
    _LINES.append([(r, c) for c in range(5)])
    _LINES.append([(r, c) for c in range(1, 6)])
# Vertical (6 cols × 2 segments)
for c in range(6):
    _LINES.append([(r, c) for r in range(5)])
    _LINES.append([(r, c) for r in range(1, 6)])
# Diagonal \ (2×2 starting positions)
for r in range(2):
    for c in range(2):
        _LINES.append([(r + i, c + i) for i in range(5)])
# Diagonal / (2×2 starting positions)
for r in range(2):
    for c in range(4, 6):
        _LINES.append([(r + i, c - i) for i in range(5)])

_QUAD_OFFSET = [(0, 0), (0, 3), (3, 0), (3, 3)]

def _check_win(board: np.ndarray) -> bool:
    """Return True if board has any 5-in-a-row."""
    for line in _LINES:
        s = (board[line[0][0], line[0][1]] +
             board[line[1][0], line[1][1]] +
             board[line[2][0], line[2][1]] +
             board[line[3][0], line[3][1]] +
             board[line[4][0], line[4][1]])
        if s == 5:
            return True
    return False

def _evaluate(me: np.ndarray, opp: np.ndarray) -> int:
    """Heuristic score: sum of 10^k for lines with k stones."""
    score = 0
    for line in _LINES:
        me_sum = (me[line[0][0], line[0][1]] +
                  me[line[1][0], line[1][1]] +
                  me[line[2][0], line[2][1]] +
                  me[line[3][0], line[3][1]] +
                  me[line[4][0], line[4][1]])
        opp_sum = (opp[line[0][0], line[0][1]] +
                   opp[line[1][0], line[1][1]] +
                   opp[line[2][0], line[2][1]] +
                   opp[line[3][0], line[3][1]] +
                   opp[line[4][0], line[4][1]])
        if me_sum > 0 and opp_sum == 0:
            score += 10 ** me_sum
        elif opp_sum > 0 and me_sum == 0:
            score -= 10 ** opp_sum
    return score

def _apply_move(me: np.ndarray, opp: np.ndarray, r: int, c: int, quad: int, d: str):
    """Place stone for 'me' at (r,c), rotate quad, return new boards."""
    new_me = me.copy()
    new_opp = opp.copy()
    new_me[r, c] = 1
    
    br, bc = _QUAD_OFFSET[quad]
    sub_me = new_me[br:br+3, bc:bc+3]
    sub_opp = new_opp[br:br+3, bc:bc+3]
    
    if d == 'R':  # Clockwise
        new_me[br:br+3, bc:bc+3] = np.rot90(sub_me, -1)
        new_opp[br:br+3, bc:bc+3] = np.rot90(sub_opp, -1)
    else:  # 'L' Counter-clockwise
        new_me[br:br+3, bc:bc+3] = np.rot90(sub_me, 1)
        new_opp[br:br+3, bc:bc+3] = np.rot90(sub_opp, 1)
        
    return new_me, new_opp

def _minimax(me: np.ndarray, opp: np.ndarray, depth: int, is_maximizing: bool,
             alpha: float, beta: float) -> float:
    """Minimax with alpha-beta pruning to given depth."""
    if depth == 0:
        return _evaluate(me, opp)
    
    # Get empty cells
    empty = np.argwhere((me == 0) & (opp == 0))
    if len(empty) == 0:
        return 0  # Draw by full board
    
    if is_maximizing:
        max_eval = -float('inf')
        for r, c in empty:
            for quad in range(4):
                for d in ['L', 'R']:
                    new_me, new_opp = _apply_move(me, opp, r, c, quad, d)
                    
                    me_wins = _check_win(new_me)
                    opp_wins = _check_win(new_opp)
                    
                    if me_wins and not opp_wins:
                        return 10000
                    if opp_wins and not me_wins:
                        val = -10000
                    elif me_wins and opp_wins:
                        val = 0
                    else:
                        val = _minimax(new_me, new_opp, depth - 1, False, alpha, beta)
                    
                    max_eval = max(max_eval, val)
                    alpha = max(alpha, val)
                    if beta <= alpha:
                        return max_eval
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in empty:
            for quad in range(4):
                for d in ['L', 'R']:
                    # Opponent moves: swap roles for the recursive call perspective
                    new_opp, new_me = _apply_move(opp, me, r, c, quad, d)
                    
                    me_wins = _check_win(new_me)
                    opp_wins = _check_win(new_opp)
                    
                    if me_wins and not opp_wins:
                        return 10000
                    if opp_wins and not me_wins:
                        val = -10000
                    elif me_wins and opp_wins:
                        val = 0
                    else:
                        val = _minimax(new_me, new_opp, depth - 1, True, alpha, beta)
                    
                    min_eval = min(min_eval, val)
                    beta = min(beta, val)
                    if beta <= alpha:
                        return min_eval
        return min_eval

def policy(you, opponent) -> str:
    """
    Determine next move for Pentago.
    you/opponent: 6x6 arrays (0/1) indicating stone positions.
    Returns: "row,col,quad,dir" (1-indexed row/col, 0-3 quad, L/R).
    """
    me = np.array(you, dtype=np.int8)
    opp = np.array(opponent, dtype=np.int8)
    
    empty = np.argwhere((me == 0) & (opp == 0))
    best_move = None
    best_score = -float('inf')
    
    # 1. Check for immediate winning moves
    for r, c in empty:
        for quad in range(4):
            for d in ['L', 'R']:
                new_me, new_opp = _apply_move(me, opp, r, c, quad, d)
                if _check_win(new_me) and not _check_win(new_opp):
                    return f"{r+1},{c+1},{quad},{d}"
    
    # 2. Depth-2 minimax search
    for r, c in empty:
        for quad in range(4):
            for d in ['L', 'R']:
                new_me, new_opp = _apply_move(me, opp, r, c, quad, d)
                
                # Skip immediate loss moves (unless forced)
                if _check_win(new_opp) and not _check_win(new_me):
                    continue
                
                if _check_win(new_me) and _check_win(new_opp):
                    score = 0
                else:
                    # Opponent's turn, search depth 1 (total depth 2)
                    score = _minimax(new_me, new_opp, 1, False, -float('inf'), float('inf'))
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, d)
    
    # If all moves lose or draw, pick first legal
    if best_move is None:
        r, c = empty[0]
        best_move = (r, c, 0, 'L')
    
    r, c, quad, d = best_move
    return f"{r+1},{c+1},{quad},{d}"
