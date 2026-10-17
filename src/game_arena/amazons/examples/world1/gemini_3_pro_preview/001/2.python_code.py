
import numpy as np
import time
import random
from collections import deque

def policy(board: np.ndarray) -> str:
    """
    Amazons policy for a 6x6 board.
    Objective: Return a legal move string "r1,c1:r2,c2:r3,c3".
    Strategy: 1-ply Greedy search maximizing Territory (King distance) and Mobility.
    """
    start_time = time.time()
    TIME_SAFEGUARD = 0.90  # Seconds
    R, C = board.shape

    # Identify locations of amazons
    # my_amazons (1), opp_amazons (2)
    my_ids = list(zip(*np.where(board == 1)))
    opp_ids = list(zip(*np.where(board == 2)))

    # Standard Queen directions (orthogonal + diagonal)
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]

    # --- Helper Functions ---

    def get_slide_moves(r, c, current_board):
        """Yields all (r_to, c_to) reachable from (r, c) by sliding."""
        for dr, dc in directions:
            cr, cc = r, c
            while True:
                cr += dr
                cc += dc
                if 0 <= cr < R and 0 <= cc < C and current_board[cr, cc] == 0:
                    yield (cr, cc)
                else:
                    break

    def evaluate(my_pos, opp_pos, current_board):
        """
        Calculates a score based on Territory and Mobility.
        Uses BFS to compute minimum King Distance to all empty cells.
        """
        # Initialize distance maps with a "large" value (100 is > max path on 6x6)
        d_my = np.full((R, C), 100, dtype=np.int8)
        d_opp = np.full((R, C), 100, dtype=np.int8)

        # BFS for My Territory
        q = deque()
        for r, c in my_pos:
            d_my[r, c] = 0
            q.append((r, c))
        
        while q:
            r, c = q.popleft()
            d = d_my[r, c]
            # Expansion (King moves)
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < R and 0 <= nc < C:
                        # Can enter if empty and unvisited
                        if current_board[nr, nc] == 0 and d_my[nr, nc] == 100:
                            d_my[nr, nc] = d + 1
                            q.append((nr, nc))

        # BFS for Opponent Territory
        q = deque()
        for r, c in opp_pos:
            d_opp[r, c] = 0
            q.append((r, c))
            
        while q:
            r, c = q.popleft()
            d = d_opp[r, c]
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < R and 0 <= nc < C:
                        if current_board[nr, nc] == 0 and d_opp[nr, nc] == 100:
                            d_opp[nr, nc] = d + 1
                            q.append((nr, nc))

        # --- Scoring ---
        # 1. Territory: Count squares where distance(Me) < distance(Opp)
        # Note: Squares unreachable by both remain neutral (diff 0)
        # We only care about reachable squares (dist < 100)
        
        my_terr = np.sum((d_my < d_opp) & (d_my < 100))
        opp_terr = np.sum((d_opp < d_my) & (d_opp < 100))
        
        # 2. Mobility: Total reachable squares (area of influence)
        my_mob = np.sum(d_my < 100)
        opp_mob = np.sum(d_opp < 100)

        # Weight territory higher than raw mobility
        return (my_terr - opp_terr) * 10.0 + (my_mob - opp_mob) * 1.0

    # --- Main Search Logic ---

    best_move = None
    best_score = -float('inf')

    # Generate Amazon Moves (Phase 1)
    phase1_candidates = []
    for r1, c1 in my_ids:
        # Check all slides
        for r2, c2 in get_slide_moves(r1, c1, board):
            phase1_candidates.append((r1, c1, r2, c2))

    # Shuffle to ensure variety if we timeout
    random.shuffle(phase1_candidates)
    
    moves_evaluated = 0

    for r1, c1, r2, c2 in phase1_candidates:
        # Global timeout check
        if time.time() - start_time > TIME_SAFEGUARD:
            break

        # Apply Amazon Move
        board[r1, c1] = 0
        board[r2, c2] = 1

        # Generate Arrow Shots (Phase 2)
        shots = list(get_slide_moves(r2, c2, board))
        
        if not shots:
            # No legal shot means this Amazon move leads to a stuck state (illegal)
            board[r2, c2] = 0
            board[r1, c1] = 1
            continue

        for r3, c3 in shots:
            moves_evaluated += 1
            
            # Granular timeout check inside the dense loop
            if moves_evaluated % 50 == 0:
                if time.time() - start_time > TIME_SAFEGUARD:
                    board[r2, c2] = 0
                    board[r1, c1] = 1
                    if best_move: return best_move
                    return f"{r1},{c1}:{r2},{c2}:{r3},{c3}"

            # Apply Shot
            board[r3, c3] = -1

            # Evaluate Board State
            # Updates my_ids location for BFS
            current_my_ids = [p for p in my_ids if p != (r1, c1)]
            current_my_ids.append((r2, c2))
            
            score = evaluate(current_my_ids, opp_ids, board)

            if score > best_score:
                best_score = score
                best_move = f"{r1},{c1}:{r2},{c2}:{r3},{c3}"
            elif best_move is None:
                # Ensure we have at least one valid fallback
                best_score = score
                best_move = f"{r1},{c1}:{r2},{c2}:{r3},{c3}"

            # Revert Shot
            board[r3, c3] = 0

        # Revert Amazon Move
        board[r2, c2] = 0
        board[r1, c1] = 1

    # Safe Fallback: if loop finished with no moves (impossible in valid game) or instantaneous timeout
    if best_move is None and phase1_candidates:
        r1, c1, r2, c2 = phase1_candidates[0]
        # Simulate briefly to get one valid shot
        board[r1, c1] = 0; board[r2, c2] = 1
        s = list(get_slide_moves(r2, c2, board))
        board[r2, c2] = 0; board[r1, c1] = 1
        if s:
            return f"{r1},{c1}:{r2},{c2}:{s[0][0]},{s[0][1]}"

    return best_move if best_move else ""
