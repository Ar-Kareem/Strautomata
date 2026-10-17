
import numpy as np
import time

def policy(board: list[list[int]]) -> int:
    """Connect 4 policy: immediate win/block, fork detection, and minimax."""
    start = time.time()
    b = np.array(board, dtype=np.int8)
    
    # Legal moves
    legal = [c for c in range(7) if b[0, c] == 0]
    if not legal:
        return 0
    
    # 1. Immediate win
    for col in legal:
        r = _row(b, col)
        if _wins(b, r, col, 1):
            return col
    
    # 2. Immediate block
    for col in legal:
        r = _row(b, col)
        if _wins(b, r, col, -1):
            return col
    
    # 3. Create fork
    for col in legal:
        if _is_fork(b, col, 1):
            return col
    
    # 4. Block fork
    for col in legal:
        if _is_fork(b, col, -1):
            return col
    
    # 5. Shallow minimax if time permits
    if time.time() - start < 0.5:
        move, _ = _minimax(b, 4, -np.inf, np.inf, True, start)
        if move != -1:
            return move
    
    # 6. Heuristic fallback
    best = legal[len(legal)//2]
    best_score = -np.inf
    for col in legal:
        score = _heuristic(b, col, 1)
        if score > best_score:
            best_score = score
            best = col
    
    return best

def _row(board, col):
    """Get next open row."""
    for r in range(5, -1, -1):
        if board[r, col] == 0:
            return r
    return -1

def _wins(board, row, col, player):
    """Check if move wins (fast)."""
    board[row, col] = player
    win = _check(board, player)
    board[row, col] = 0
    return win

def _check(board, player):
    """Check if player has won."""
    # Horizontal
    for r in range(6):
        for c in range(4):
            if np.all(board[r, c:c+4] == player):
                return True
    
    # Vertical
    for c in range(7):
        for r in range(3):
            if np.all(board[r:r+4, c] == player):
                return True
    
    # Diagonal \
    for r in range(3):
        for c in range(4):
            if np.all([board[r+i, c+i] == player for i in range(4)]):
                return True
    
    # Diagonal /
    for r in range(3):
        for c in range(4):
            if np.all([board[r+3-i, c+i] == player for i in range(4)]):
                return True
    
    return False

def _is_fork(board, col, player):
    """Check if move creates two threats."""
    r = _row(board, col)
    if r == -1:
        return False
    
    board[r, col] = player
    threats = sum(1 for c in range(7) if board[0, c] == 0 
                  and _wins(board, _row(board, c), c, player))
    board[r, col] = 0
    
    return threats >= 2

def _heuristic(board, col, player):
    """Quick heuristic: center + threat count."""
    r = _row(board, col)
    if r == -1:
        return -np.inf
    
    score = (3 - abs(col - 3)) * 100  # Center preference
    
    board[r, col] = player
    
    # Count our 3-in-a-row threats
    threats = sum(1 for c in range(7) if board[0, c] == 0 
                  and _is_threat(board, _row(board, c), c, player, 3))
    score += threats * 500
    
    # Penalize opponent threats
    opp_threats = sum(1 for c in range(7) if board[0, c] == 0 
                      and _is_threat(board, _row(board, c), c, -player, 3))
    score -= opp_threats * 1000
    
    board[r, col] = 0
    return score

def _is_threat(board, row, col, player, length):
    """Check if move creates a line of given length."""
    board[row, col] = player
    
    for dr, dc in [(0,1), (1,0), (1,1), (1,-1)]:
        count = 1
        
        # Forward direction
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r, c] == player:
            count += 1
            r += dr
            c += dc
        
        # Backward direction
        r, c = row - dr, col - dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r, c] == player:
            count += 1
            r -= dr
            c -= dc
        
        if count >= length:
            board[row, col] = 0
            return True
    
    board[row, col] = 0
    return False

def _minimax(board, depth, alpha, beta, maximizing, start):
    """Alpha-beta pruning with time limit."""
    legal = [c for c in range(7) if board[0, c] == 0]
    if not legal:
        return -1, 0
    
    if depth == 0 or time.time() - start > 0.95:
        return -1, _eval(board)
    
    if maximizing:
        max_eval = -np.inf
        best_move = legal[0]
        legal.sort(key=lambda c: abs(c-3))  # Center-first ordering
        
        for col in legal:
            r = _row(board, col)
            if r == -1:
                continue
            
            board[r, col] = 1
            if _wins(board, r, col, 1):
                board[r, col] = 0
                return col, np.inf
            
            _, eval_ = _minimax(board, depth-1, alpha, beta, False, start)
            board[r, col] = 0
            
            if eval_ > max_eval:
                max_eval, best_move = eval_, col
            
            alpha = max(alpha, eval_)
            if beta <= alpha:
                break
        
        return best_move, max_eval
    else:
        min_eval = np.inf
        best_move = legal[0]
        legal.sort(key=lambda c: abs(c-3))
        
        for col in legal:
            r = _row(board, col)
            if r == -1:
                continue
            
            board[r, col] = -1
            if _wins(board, r, col, -1):
                board[r, col] = 0
                return col, -np.inf
            
            _, eval_ = _minimax(board, depth-1, alpha, beta, True, start)
            board[r, col] = 0
            
            if eval_ < min_eval:
                min_eval, best_move = eval_, col
            
            beta = min(beta, eval_)
            if beta <= alpha:
                break
        
        return best_move, min_eval

def _eval(board):
    """Static board evaluation."""
    score = 0
    
    # Center column
    center = np.sum(board[:, 3] == 1) - np.sum(board[:, 3] == -1)
    score += center * 3
    
    # Evaluate all windows
    for r in range(6):
        for c in range(7):
            # Horizontal
            if c <= 3:
                score += _score(board[r, c:c+4])
            
            # Vertical
            if r <= 2:
                score += _score(board[r:r+4, c])
            
            # Diagonal \
            if r <= 2 and c <= 3:
                score += _score([board[r+i, c+i] for i in range(4)])
            
            # Diagonal /
            if r >= 3 and c <= 3:
                score += _score([board[r-i, c+i] for i in range(4)])
    
    return score

def _score(window):
    """Score a 4-cell window."""
    if hasattr(window, 'tolist'):
        window = window.tolist()
    
    p = window.count(1)
    o = window.count(-1)
    e = window.count(0)
    
    if p == 4:
        return 1000
    if p == 3 and e == 1:
        return 5
    if p == 2 and e == 2:
        return 2
    if o == 4:
        return -1000
    if o == 3 and e == 1:
        return -10
    
    return 0
