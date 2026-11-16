
import numpy as np
import time

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    Implements a Go policy combining local capture/defense logic with strategic heuristic expansion.
    """
    start_time = time.time()
    
    # --- Configuration ---
    BOARD_SIZE = 19
    SEARCH_RADIUS = 3  # Search radius for heuristic moves
    CENTER = (10, 10)  # 1-indexed center
    
    # --- Helper Class for Board Logic ---
    class BoardState:
        def __init__(self, size, me_stones, opp_stones):
            self.size = size
            self.board = np.zeros((size + 1, size + 1), dtype=int) # 1-indexed
            # 0: Empty, 1: Me, 2: Opponent
            for r, c in me_stones:
                self.board[r][c] = 1
            for r, c in opp_stones:
                self.board[r][c] = 2
                
        def is_on_board(self, r, c):
            return 1 <= r <= self.size and 1 <= c <= self.size

        def get_empty_neighbors(self, r, c):
            neighbors = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if self.is_on_board(nr, nc) and self.board[nr][nc] == 0:
                    neighbors.append((nr, nc))
            return neighbors

        def get_group_and_liberties(self, r, c):
            """Returns (group_set, liberties_count) for the stone at (r, c)."""
            color = self.board[r][c]
            if color == 0:
                return set(), 0
            
            group = set()
            liberties = set()
            stack = [(r, c)]
            visited = set()
            
            while stack:
                curr_r, curr_c = stack.pop()
                if (curr_r, curr_c) in visited:
                    continue
                visited.add((curr_r, curr_c))
                
                # Check if this point is part of the group
                if self.board[curr_r][curr_c] == color:
                    group.add((curr_r, curr_c))
                    # Check neighbors
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if self.is_on_board(nr, nc):
                            if self.board[nr][nc] == 0:
                                liberties.add((nr, nc))
                            elif self.board[nr][nc] == color:
                                stack.append((nr, nc))
            
            return group, len(liberties), liberties

        def get_legal_moves(self, player_color):
            """Returns list of legal moves. Player color 1 for Me, 2 for Opponent."""
            legal_moves = []
            for r in range(1, self.size + 1):
                for c in range(1, self.size + 1):
                    if self.board[r][c] != 0:
                        continue
                    
                    # Rule 1: Must have liberties after placement (or capture)
                    # Simulate placement
                    self.board[r][c] = player_color
                    
                    # Check own liberties
                    _, libs, _ = self.get_group_and_liberties(r, c)
                    
                    # Rule 2: Suicide rule (simple version)
                    # If libs == 0, check if we captured anything
                    if libs == 0:
                        captured = False
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = r + dr, c + dc
                            if self.is_on_board(nr, nc) and self.board[nr][nc] == (3 - player_color):
                                _, opp_libs, _ = self.get_group_and_liberties(nr, nc)
                                if opp_libs == 0:
                                    captured = True
                                    break
                        if not captured:
                            self.board[r][c] = 0 # Revert
                            continue
                    
                    # Rule 3: Ko rule (simple check: does this move undo the previous state?)
                    # Since we don't store full history in this simple function, we skip complex Ko detection 
                    # for the sake of performance, relying on basic liberties. 
                    # A full Ko check would require passing the previous board state.
                    
                    self.board[r][c] = 0 # Revert
                    legal_moves.append((r, c))
            return legal_moves

    # --- Initialization & Memory ---
    if 'turn' not in memory:
        memory['turn'] = 0
    memory['turn'] += 1
    
    # Convert lists to sets for faster lookup if needed
    me_set = set(me)
    opp_set = set(opponent)
    
    # Initialize Board State
    board = BoardState(BOARD_SIZE, me, opponent)
    
    # --- Phase 1: Critical Moves (Capture/Defense) ---
    
    # 1. Identify Opponent groups with 1 liberty (Atari)
    # 2. Identify My groups with 1 liberty (Atari)
    
    my_atari_groups = [] # list of (group, liberties_set)
    opp_atari_groups = [] # list of (group, liberties_set)
    
    visited_me = set()
    for r, c in me:
        if (r, c) not in visited_me:
            group, libs, lib_set = board.get_group_and_liberties(r, c)
            visited_me.update(group)
            if libs == 1:
                my_atari_groups.append((group, lib_set))
                
    visited_opp = set()
    for r, c in opponent:
        if (r, c) not in visited_opp:
            group, libs, lib_set = board.get_group_and_liberties(r, c)
            visited_opp.update(group)
            if libs == 1:
                opp_atari_groups.append((group, lib_set))
                
    # 1. Capture Moves (High Priority)
    # If opponent has a group with 1 liberty, play there.
    # Filter valid moves only.
    capture_moves = []
    for group, liberties in opp_atari_groups:
        for lib in liberties:
            # Validate move (basic check, assuming legal if empty)
            if board.board[lib[0]][lib[1]] == 0:
                # Check suicide rule for this specific capture
                # (Technically, capturing removes opponent stones, adding liberties)
                capture_moves.append(lib)
    
    if capture_moves:
        # Prioritize captures that save my own stones or maximize territory
        # Simple: Pick the first valid capture
        return capture_moves[0], memory

    # 2. Defense Moves (Critical)
    # If I have a group with 1 liberty, I MUST play there or lose the group.
    defense_moves = []
    for group, liberties in my_atari_groups:
        for lib in liberties:
            if board.board[lib[0]][lib[1]] == 0:
                # Check suicide
                # Simulating is safer but expensive. 
                # A simple check: if we play here, do we gain liberties?
                # Usually filling the last liberty of your own group is safe unless surrounded.
                defense_moves.append(lib)
    
    if defense_moves:
        return defense_moves[0], memory

    # --- Phase 2: Heuristic Expansion ---
    
    # Generate candidate moves
    # Candidates are empty spots near my stones or near opponent stones
    candidates = set()
    
    # Add moves near my stones
    for r, c in me:
        for dr in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
            for dc in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
                nr, nc = r + dr, c + dc
                if board.is_on_board(nr, nc) and board.board[nr][nc] == 0:
                    candidates.add((nr, nc))
                    
    # Add moves near opponent stones
    for r, c in opponent:
        for dr in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
            for dc in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
                nr, nc = r + dr, c + dc
                if board.is_on_board(nr, nc) and board.board[nr][nc] == 0:
                    candidates.add((nr, nc))
                    
    # If board is empty (first move), play center
    if not me and not opponent:
        return CENTER, memory
        
    # If candidates is empty (unlikely on 19x19 unless full), fallback to random empty or pass
    if not candidates:
        # Scan for any empty spot
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if board.board[r][c] == 0:
                    return (r, c), memory
        return (0, 0), memory # Pass

    # Evaluate candidates
    best_score = -float('inf')
    best_move = None
    
    for move in candidates:
        r, c = move
        
        # Safety Check: Self-Atari
        # If playing here reduces my liberties to 1 without capturing, it's bad.
        board.board[r][c] = 1 # Temporarily place
        _, libs, _ = board.get_group_and_liberties(r, c)
        
        # Check if we captured anything (liberties would increase implicitly in group calc, 
        # but let's be precise: if a neighbor opponent group has 0 liberties now, we captured)
        captured = False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if board.is_on_board(nr, nc) and board.board[nr][nc] == 2:
                _, opp_libs, _ = board.get_group_and_liberties(nr, nc)
                if opp_libs == 0:
                    captured = True
                    break
        
        board.board[r][c] = 0 # Revert
        
        if libs == 1 and not captured:
            continue # Bad move (self-atari)
            
        # Score Calculation
        score = 0
        
        # 1. Proximity to Me (Positive)
        # Prefer moves close to existing stones
        min_dist_me = min([abs(r - mr) + abs(c - mc) for mr, mc in me]) if me else 20
        score += (20 - min_dist_me) * 2 
        
        # 2. Proximity to Opponent (Aggressive/Defensive)
        # Prefer moves near opponent stones (hane, approach)
        min_dist_opp = min([abs(r - orow) + abs(c - ocol) for orow, ocol in opponent]) if opponent else 20
        score += (20 - min_dist_opp) * 1
        
        # 3. Center Bias (Territorial)
        # Prefer center over edges/corners in early/mid game
        dist_center = abs(r - 10) + abs(c - 10)
        score -= dist_center * 0.5
        
        # 4. Extension (Space)
        # Check empty neighbors (liberties of the potential group)
        empty_neighbors = len(board.get_empty_neighbors(r, c))
        score += empty_neighbors * 1.5
        
        # Update best
        if score > best_score:
            best_score = score
            best_move = move

    if best_move:
        return best_move, memory
    
    # Fallback
    return (0, 0), memory
