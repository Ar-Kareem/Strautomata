
import numpy as np
from collections import deque
from typing import List, Tuple, Dict, Set

# Board is 1-indexed: positions 1..19, with 0 and 20 as borders
BOARD_SIZE = 19
PADDING = 1
TOTAL_SIZE = BOARD_SIZE + 2 * PADDING
NEIGHBORS = [(1,0), (-1,0), (0,1), (0,-1)]
CORNERS = [(3,3), (3,17), (17,3), (17,17)]
CENTER = (10, 10)

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    """
    Capture-first Go policy with simple heuristics.
    Priorities: 1) Capture, 2) Defense, 3) Corners, 4) Edge extension, 5) Influence
    """
    # Initialize board (1-indexed with padding)
    board = np.zeros((TOTAL_SIZE, TOTAL_SIZE), dtype=np.int8)
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = -1
    
    # First move: center
    if len(me) == 0 and len(opponent) == 0:
        return CENTER, memory
    
    # Find legal moves in relevant region
    legal_moves = find_legal_moves(board)
    
    if not legal_moves:
        return (0, 0), memory
    
    # Select best move
    return select_best_move(board, legal_moves), memory

def find_legal_moves(board):
    """Find all legal moves, focusing on region near existing stones."""
    stone_positions = np.argwhere(board[1:-1, 1:-1] != 0)
    if len(stone_positions) > 0:
        rows = stone_positions[:, 0] + 1
        cols = stone_positions[:, 1] + 1
        min_r, max_r = max(1, rows.min() - 2), min(19, rows.max() + 2)
        min_c, max_c = max(1, cols.min() - 2), min(19, cols.max() + 2)
    else:
        min_r, max_r, min_c, max_c = 1, 19, 1, 19
    
    legal_moves = []
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if board[r, c] == 0 and is_legal(board, r, c):
                legal_moves.append((r, c))
    
    # Fallback to full board if no moves in region
    if not legal_moves:
        for r in range(1, 20):
            for c in range(1, 20):
                if board[r, c] == 0 and is_legal(board, r, c):
                    legal_moves.append((r, c))
    
    return legal_moves

def is_legal(board, r, c):
    """Check if placing stone at (r,c) is legal (no suicide)."""
    color = 1
    board[r, c] = color
    
    # Check if move captures opponent stones
    legal = False
    for dr, dc in NEIGHBORS:
        nr, nc = r + dr, c + dc
        if board[nr, nc] == -color and not has_liberty(board, nr, nc):
            legal = True
            break
    
    # If no capture, check self-liberty
    if not legal:
        legal = has_liberty(board, r, c)
    
    board[r, c] = 0
    return legal

def has_liberty(board, r, c):
    """Check if stone/group at (r,c) has at least one liberty."""
    color = board[r, c]
    seen = set()
    dq = deque([(r, c)])
    
    while dq:
        cr, cc = dq.popleft()
        if (cr, cc) in seen:
            continue
        seen.add((cr, cc))
        
        for dr, dc in NEIGHBORS:
            nr, nc = cr + dr, cc + dc
            if board[nr, nc] == 0:
                return True
            if board[nr, nc] == color and (nr, nc) not in seen:
                dq.append((nr, nc))
    
    return False

def select_best_move(board, legal_moves):
    """Select best move based on heuristics."""
    best_move = legal_moves[0]
    best_score = -10000
    
    for move in legal_moves:
        score = evaluate_move(board, move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def evaluate_move(board, move):
    """Score a move."""
    r, c = move
    score = 0
    
    # 1. Capture value (highest priority)
    cap_val = capture_value(board, move)
    if cap_val > 0:
        return 10000 + cap_val
    
    # 2. Defense
    if is_defense_move(board, move):
        return 5000
    
    # 3. Corner moves
    if move in CORNERS:
        return 1000
    
    # 4. Edge moves
    if r in (2, 3, 4, 17, 18) or c in (2, 3, 4, 17, 18):
        score += 100
    
    # 5. Center distance (prefer center)
    score -= (abs(r - 10) + abs(c - 10))
    
    # 6. Pressure on opponent (distance 2-3 is ideal)
    opp_stones = np.argwhere(board == -1)
    if len(opp_stones) > 0:
        min_dist = min([abs(r - os[0]) + abs(c - os[1]) for os in opp_stones])
        if 2 <= min_dist <= 3:
            score += 50 - min_dist * 10
    
    # 7. Avoid overconcentration
    my_stones = np.argwhere(board == 1)
    if len(my_stones) > 0:
        min_dist = min([abs(r - ms[0]) + abs(c - ms[1]) for ms in my_stones])
        score += min_dist
    
    return score

def capture_value(board, move):
    """Calculate number of stones captured by this move."""
    r, c = move
    board[r, c] = 1
    
    total = 0
    seen = set()
    for dr, dc in NEIGHBORS:
        nr, nc = r + dr, c + dc
        if board[nr, nc] == -1 and (nr, nc) not in seen:
            group = get_group(board, nr, nc)
            if not has_liberty(board, nr, nc):
                total += len(group)
                seen.update(group)
    
    board[r, c] = 0
    return total

def is_defense_move(board, move):
    """Check if move defends a group in atari."""
    r, c = move
    board[r, c] = 1
    
    defended = False
    for dr, dc in NEIGHBORS:
        nr, nc = r + dr, c + dc
        if board[nr, nc] == 1:
            group = get_group(board, nr, nc)
            new_libs = get_liberties(board, group)
            
            board[r, c] = 0
            orig_group = get_group(board, nr, nc)
            old_libs = get_liberties(board, orig_group)
            
            if len(old_libs) <= 1 and len(new_libs) > len(old_libs):
                defended = True
                break
            
            board[r, c] = 1
    
    board[r, c] = 0
    return defended

def get_group(board, r, c):
    """Get all stones in connected group."""
    color = board[r, c]
    group = {(r, c)}
    dq = deque([(r, c)])
    
    while dq:
        cr, cc = dq.popleft()
        for dr, dc in NEIGHBORS:
            nr, nc = cr + dr, cc + dc
            if board[nr, nc] == color and (nr, nc) not in group:
                group.add((nr, nc))
                dq.append((nr, nc))
    
    return group

def get_liberties(board, group):
    """Get all liberties of a group."""
    libs = set()
    for r, c in group:
        for dr, dc in NEIGHBORS:
            nr, nc = r + dr, c + dc
            if board[nr, nc] == 0:
                libs.add((nr, nc))
    return libs
