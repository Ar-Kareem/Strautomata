
import numpy as np
from collections import deque

def policy(me, opponent, memory):
    """
    Go policy that prioritizes captures, saves, and strategic shape moves.
    """
    # Constants
    BOARD_SIZE = 19
    EMPTY = 0
    ME = 1
    OPP = 2
    WALL = 3
    
    # Initialize Board (with padding for simplified bounds checking)
    # 21x21 grid. Indices 1-19 are the board. 0 and 20 are walls.
    board = np.full((BOARD_SIZE + 2, BOARD_SIZE + 2), WALL, dtype=int)
    
    # Helper to place stones
    for r, c in me:
        board[r, c] = ME
    for r, c in opponent:
        board[r, c] = OPP

    # --- Helper Functions ---

    def get_group(board, r, c):
        """
        BFS to find a group of connected stones and its liberties.
        Returns: (set of stone coordinates, set of liberty coordinates)
        """
        player = board[r, c]
        if player == EMPTY or player == WALL:
            return set(), set()
            
        stones = set()
        liberties = set()
        queue = deque([(r, c)])
        visited = set([(r, c)])
        
        while queue:
            cr, cc = queue.popleft()
            stones.add((cr, cc))
            
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = cr + dr, cc + dc
                val = board[nr, nc]
                
                if val == EMPTY:
                    liberties.add((nr, nc))
                elif val == player and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
                    
        return stones, liberties

    def is_legal_move(board, r, c, player, ko_point):
        """
        Check if a move is legal.
        1. Spot must be empty.
        2. Not a Ko point.
        3. Not suicide (must capture or have liberties).
        """
        if board[r, c] != EMPTY:
            return False
        if ko_point and (r, c) == ko_point:
            return False
            
        # Simulate move
        test_board = board.copy()
        test_board[r, c] = player
        
        # Check for captures first
        opponent = OPP if player == ME else ME
        captured_stone = False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if test_board[nr, nc] == opponent:
                _, opp_libs = get_group(test_board, nr, nc)
                if not opp_libs:
                    captured_stone = True
                    # Remove captured stones for accurate suicide check
                    grp, _ = get_group(test_board, nr, nc)
                    for gr, gc in grp:
                        test_board[gr, gc] = EMPTY
        
        # Check for suicide
        my_group, my_libs = get_group(test_board, r, c)
        if not my_libs and not captured_stone:
            return False
            
        return True

    # --- Strategic Logic ---

    ko_point = memory.get('ko_point')
    
    # Candidate moves: We look at moves near existing stones to ensure locality
    candidates = set()
    
    # If board is empty, play star point
    if not me and not opponent:
        return (4, 4), {}

    # Generate candidates around all stones (Manhattan distance 2)
    for r, c in me + opponent:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19:
                    if board[nr, nc] == EMPTY:
                        candidates.add((nr, nc))
    
    # Add some random moves to the candidate list to ensure we have options
    # (In case the board is wide open but we have a few stones)
    if len(candidates) < 20:
        for _ in range(50):
            r, c = np.random.randint(1, 20), np.random.randint(1, 20)
            if board[r, c] == EMPTY:
                candidates.add((r, c))

    best_move = None
    best_score = -float('inf')
    
    # Score tracking
    # Priority: Capture > Save > Atari > Extension > Random
    
    for r, c in candidates:
        if not is_legal_move(board, r, c, ME, ko_point):
            continue
            
        score = 0
        
        # 1. Capture Logic (Highest Priority)
        # Check adjacent opponent groups
        captures_count = 0
        captures_groups = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if board[nr, nc] == OPP:
                stones, libs = get_group(board, nr, nc)
                if (r, c) in libs:
                    if len(libs) == 1: # Atari capture
                        captures_count += len(stones)
                        captures_groups.append(stones)
        
        if captures_count > 0:
            score += captures_count * 1000
            
        # 2. Save Logic (Save own groups in Atari)
        # If this move fills a liberty of a friendly group in Atari, it's saving it
        # (Unless it's a self-atari into death, which is_legal handles partially)
        is_saving = False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if board[nr, nc] == ME:
                stones, libs = get_group(board, nr, nc)
                if (r, c) in libs and len(libs) == 1:
                    # We are saving a group in atari
                    score += len(stones) * 800
                    is_saving = True

        # 3. Atari Logic (Put opponent in Atari)
        # If move reduces opponent to 1 liberty
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if board[nr, nc] == OPP:
                stones, libs = get_group(board, nr, nc)
                if (r, c) in libs and len(libs) == 2:
                    # This move puts them in atari
                    score += len(stones) * 20

        # 4. Eye/Shape Heuristics
        # Prefer moves that create liberties (empty neighbors)
        neighbors_empty = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if board[r+dr, c+dc] == EMPTY:
                neighbors_empty += 1
        score += neighbors_empty * 2
        
        # 5. Connectivity
        # Prefer moves adjacent to friendly stones
        neighbors_friendly = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if board[r+dr, c+dc] == ME:
                neighbors_friendly += 1
        score += neighbors_friendly * 5

        # Tie-breaker: Random small noise
        score += np.random.rand()
        
        if score > best_score:
            best_score = score
            best_move = (r, c)

    # Handle Ko for next memory state
    # If we made a capture of exactly 1 stone, we need to check if that creates a Ko
    next_ko_point = None
    if best_move:
        # Very simplified Ko check:
        # If we captured exactly one stone, that stone location is a potential Ko point for opponent
        # This is not perfectly accurate (needs to check if recapture recreates board state)
        # But sufficient for arena logic usually.
        
        # Re-evaluate the chosen move to see if it was a single capture
        r, c = best_move
        single_captured_pos = None
        captured_count = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if board[nr, nc] == OPP:
                stones, libs = get_group(board, nr, nc)
                if len(libs) == 1 and (r, c) in libs:
                    captured_count += len(stones)
                    if len(stones) == 1:
                        single_captured_pos = (nr, nc)
        
        # If we captured exactly 1 stone total, set Ko point
        if captured_count == 1:
            next_ko_point = single_captured_pos

    if best_move is None:
        # Pass
        return (0, 0), {}

    return best_move, {'ko_point': next_ko_point}

