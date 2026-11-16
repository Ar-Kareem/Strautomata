
import time
import numpy as np
from collections import deque

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

def get_queen_moves(board, r, c):
    """Yield all legal queen destinations from (r, c) on board."""
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            yield nr, nc
            nr += dr
            nc += dc

def count_queen_moves(board, r, c):
    """Count legal queen destinations from (r, c) on board."""
    cnt = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            cnt += 1
            nr += dr
            nc += dc
    return cnt

def generate_legal_moves(board, player):
    """Generate all legal moves for `player` formatted as (from, to, arrow)."""
    amazons = [tuple(p) for p in np.argwhere(board == player)]
    moves = []
    
    for fr, fc in amazons:
        board[fr, fc] = 0
        for tr, tc in get_queen_moves(board, fr, fc):
            board[tr, tc] = player
            for ar, ac in get_queen_moves(board, tr, tc):
                moves.append(((fr, fc), (tr, tc), (ar, ac)))
            board[tr, tc] = 0
        board[fr, fc] = player
        
    return moves

def evaluate_board(board):
    """
    Evaluate the board state from the perspective of player 1.
    Uses king-distance territory evaluation combined with queen mobility.
    """
    my_amazons = [tuple(p) for p in np.argwhere(board == 1)]
    opp_amazons = [tuple(p) for p in np.argwhere(board == 2)]
    
    # Check for terminal positions
    my_mob = sum(count_queen_moves(board, r, c) for r, c in my_amazons)
    opp_mob = sum(count_queen_moves(board, r, c) for r, c in opp_amazons)
    
    if my_mob == 0:
        return -10000.0
    if opp_mob == 0:
        return 10000.0
        
    # Multi-source BFS for territory distance (king moves through empty cells)
    INF = 999
    dist1 = np.full((6, 6), INF, dtype=int)
    dist2 = np.full((6, 6), INF, dtype=int)
    
    # BFS for Player 1
    q1 = deque()
    for r, c in my_amazons:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0 and dist1[nr, nc] == INF:
                dist1[nr, nc] = 1
                q1.append((nr, nc))
    while q1:
        r, c = q1.popleft()
        d = dist1[r, c]
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0 and dist1[nr, nc] == INF:
                dist1[nr, nc] = d + 1
                q1.append((nr, nc))

    # BFS for Player 2
    q2 = deque()
    for r, c in opp_amazons:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0 and dist2[nr, nc] == INF:
                dist2[nr, nc] = 1
                q2.append((nr, nc))
    while q2:
        r, c = q2.popleft()
        d = dist2[r, c]
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0 and dist2[nr, nc] == INF:
                dist2[nr, nc] = d + 1
                q2.append((nr, nc))

    territory_score = 0.0
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:
                d1 = dist1[r, c]
                d2 = dist2[r, c]
                if d1 < d2:
                    territory_score += 1.0 + 0.1 * (d2 - d1)
                elif d2 < d1:
                    territory_score -= (1.0 + 0.1 * (d1 - d2))

    mobility_score = my_mob - 1.2 * opp_mob
    return territory_score * 2.0 + mobility_score

def policy(board) -> str:
    """
    Main policy function for 6x6 Amazons.
    Returns: "from_r,from_c:to_r,to_c:arrow_r,arrow_col"
    """
    start_time = time.time()
    time_limit = 0.85  # safety margin under 1.0s
    
    board = np.array(board, dtype=int)
    all_moves = generate_legal_moves(board, player=1)
    
    if not all_moves:
        return "0,0:0,0:0,0"
    
    if len(all_moves) == 1:
        (fr, fc), (tr, tc), (ar, ac) = all_moves[0]
        return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

    # Pre-score moves at Depth 1
    opp_amazons = [tuple(p) for p in np.argwhere(board == 2)]
    scored_moves = []
    
    for move in all_moves:
        (fr, fc), (tr, tc), (ar, ac) = move
        
        # Apply move
        board[fr, fc] = 0
        board[tr, tc] = 1
        board[ar, ac] = -1
        
        # Fast heuristic eval
        val = evaluate_board(board)
        
        # Bonus for arrows restricting opponent amazons
        for opr, opc in opp_amazons:
            dist = max(abs(ar - opr), abs(ac - opc))
            if dist == 1:
                val += 1.5
            elif dist == 2:
                val += 0.5
                
        scored_moves.append((val, move))
        
        # Undo move
        board[ar, ac] = 0
        board[tr, tc] = 0
        board[fr, fc] = 1
        
        if time.time() - start_time > 0.4:
            break

    # Sort descending
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    best_move = scored_moves[0][1]
    best_val = scored_moves[0][0]

    # Search top candidate moves with 1-ply opponent response (minimax depth 2)
    candidates = [m for _, m in scored_moves[:18]]
    
    alpha = -float('inf')
    beta = float('inf')
    
    for move in candidates:
        if time.time() - start_time > time_limit:
            break
            
        (fr, fc), (tr, tc), (ar, ac) = move
        board[fr, fc] = 0
        board[tr, tc] = 1
        board[ar, ac] = -1
        
        opp_moves = generate_legal_moves(board, player=2)
        if not opp_moves:
            # Opponent has no moves, immediate win
            min_opp_val = 10000.0
        else:
            min_opp_val = float('inf')
            # Sample best opponent counter-moves
            for opp_move in opp_moves[:20]:
                (ofr, ofc), (otr, otc), (oar, oac) = opp_move
                board[ofr, ofc] = 0
                board[otr, otc] = 2
                board[oar, oac] = -1
                
                score = evaluate_board(board)
                
                board[oar, oac] = 0
                board[otr, otc] = 0
                board[ofr, ofc] = 2
                
                if score < min_opp_val:
                    min_opp_val = score
                if min_opp_val <= alpha:
                    break

        board[ar, ac] = 0
        board[tr, tc] = 0
        board[fr, fc] = 1

        if min_opp_val > best_val:
            best_val = min_opp_val
            best_move = move
        alpha = max(alpha, best_val)

    (fr, fc), (tr, tc), (ar, ac) = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
