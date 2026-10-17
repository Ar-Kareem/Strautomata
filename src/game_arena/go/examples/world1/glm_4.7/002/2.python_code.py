
import numpy as np
import random

# Global variable to track board state for Ko detection
PREV_BOARD_BYTES = None

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    global PREV_BOARD_BYTES
    
    # 1. Board Representation
    # Convert 1-based input lists to 0-based 19x19 numpy array
    # 0: Empty, 1: Me, 2: Opponent
    board = np.zeros((19, 19), dtype=int)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = 2
        
    # Cache coordinates for faster access
    my_coords = [(r-1, c-1) for r, c in me]
    opp_coords = [(r-1, c-1) for r, c in opponent]
    
    NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # 2. Opening Book
    if len(me) == 0:
        return (4, 4) # Standard Hoshi
    
    # 3. Helper Functions
    def get_group_liberties(r, c, board_state):
        """Finds the group and its liberties for a given stone using flood fill."""
        color = board_state[r, c]
        if color == 0: return set(), set()
        
        stack = [(r, c)]
        group = set()
        liberties = set()
        group.add((r, c))
        
        while stack:
            curr_r, curr_c = stack.pop()
            for dr, dc in NEIGHBORS:
                nr, nc = curr_r + dr, curr_c + dc
                if 0 <= nr < 19 and 0 <= nc < 19:
                    if board_state[nr, nc] == 0:
                        liberties.add((nr, nc))
                    elif board_state[nr, nc] == color and (nr, nc) not in group:
                        group.add((nr, nc))
                        stack.append((nr, nc))
        return group, liberties

    def is_move_legal(r, c, color, board_state, check_ko=True):
        """Checks if move is legal (not occupied, not suicide, not ko)."""
        if board_state[r, c] != 0: return False
        
        # Create a copy to simulate
        sim_board = board_state.copy()
        sim_board[r, c] = color
        opp_color = 3 - color
        
        # Check for captures (opponents with 0 liberties)
        captured = False
        for dr, dc in NEIGHBORS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and sim_board[nr, nc] == opp_color:
                # Check liberties of this opponent group
                _, opp_libs = get_group_liberties(nr, nc, sim_board)
                if len(opp_libs) == 0:
                    captured = True
                    # Remove the captured stones to finalize state for suicide/Ko check
                    captured_group, _ = get_group_liberties(nr, nc, sim_board)
                    for cr, cc in captured_group:
                        sim_board[cr, cc] = 0

        # Check for suicide (self has 0 liberties and no capture)
        if not captured:
            _, my_libs = get_group_liberties(r, c, sim_board)
            if len(my_libs) == 0:
                return False

        # Check Ko
        if check_ko and PREV_BOARD_BYTES is not None:
            if sim_board.tobytes() == PREV_BOARD_BYTES:
                return False
                
        return True

    # 4. Tactical Scan (Atari Detection)
    candidates = {} # (r, c) -> score
    
    # Check Opponent groups (Attack)
    checked = set()
    for r, c in opp_coords:
        if (r, c) in checked: continue
        group, liberties = get_group_liberties(r, c, board)
        for s in group: checked.add(s)
        
        if len(liberties) == 1:
            lib = list(liberties)[0]
            candidates[lib] = candidates.get(lib, 0) + 100 # Priority: Capture
            
    # Check Self groups (Defense)
    checked = set()
    for r, c in my_coords:
        if (r, c) in checked: continue
        group, liberties = get_group_liberties(r, c, board)
        for s in group: checked.add(s)
        
        if len(liberties) == 1:
            lib = list(liberties)[0]
            # Only save if the move doesn't immediately throw the stone away (basic heuristic)
            # We rely on the legality check to filter out pure suicide, 
            # but sometimes filling a liberty to connect is good.
            candidates[lib] = candidates.get(lib, 0) + 80 # Priority: Save

    # Process candidates
    if candidates:
        # Sort by score descending
        sorted_candidates = sorted(candidates.items(), key=lambda item: item[1], reverse=True)
        for (r, c), score in sorted_candidates:
            if is_move_legal(r, c, 1, board):
                # Update Ko state
                # We must simulate again to get the final board state for global update
                # (Optimized: we do this once for the winner)
                sim_board = board.copy()
                sim_board[r, c] = 1
                # Handle captures in simulation for history
                for dr, dc in NEIGHBORS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and sim_board[nr, nc] == 2:
                         _, opp_libs = get_group_liberties(nr, nc, sim_board)
                         if len(opp_libs) == 0:
                            g, _ = get_group_liberties(nr, nc, sim_board)
                            for gr, gc in g: sim_board[gr, gc] = 0
                PREV_BOARD_BYTES = sim_board.tobytes()
                
                return (r+1, c+1)

    # 5. Positional Evaluation (Fallback)
    # Generate candidate moves: points near existing stones
    valid_moves = set()
    
    # Sparse opening heuristic
    if len(me) + len(opponent) < 10:
        # Star points and 3-4 points (0-indexed: 2,3 is 3-4 point)
        star_points = [(3,3), (3,15), (15,3), (15,15), (2,3), (2,15), (15,2), (15,15), (3,2), (3,16)]
        random.shuffle(star_points)
        for sr, sc in star_points:
             if board[sr, sc] == 0 and is_move_legal(sr, sc, 1, board):
                 # Update Ko
                 sim_board = board.copy()
                 sim_board[sr, sc] = 1
                 PREV_BOARD_BYTES = sim_board.tobytes()
                 return (sr+1, sc+1)

    # General Case: Scan around stones
    all_coords = my_coords + opp_coords
    for r, c in all_coords:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    valid_moves.add((nr, nc))
                    
    if not valid_moves:
        # If board is full or no moves near stones, scan all
        for r in range(19):
            for c in range(19):
                if board[r, c] == 0: valid_moves.add((r, c))

    best_score = -9999
    best_move = None
    
    for r, c in valid_moves:
        if not is_move_legal(r, c, 1, board): continue
        
        score = 0
        
        # Proximity
        d_my = min([abs(r - mr) + abs(c - mc) for mr, mc in my_coords]) if my_coords else 999
        d_opp = min([abs(r - or_) + abs(c - oc) for or_, oc in opp_coords]) if opp_coords else 999
        
        if d_my == 1: score += 10
        elif d_my == 2: score += 5
        
        if d_opp == 1: score += 8
        elif d_opp == 2: score += 4
        
        # Shape (Lines)
        line = min(r, 18-r, c, 18-c)
        if line == 0: score -= 50
        elif line == 1: score -= 10
        elif line == 2 or line == 3: score += 5
        
        # Center bias
        dist_center = abs(r - 9) + abs(c - 9)
        score -= dist_center * 0.1
        
        # Randomness
        score += random.random() * 2
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    if best_move:
        # Update Ko state
        sim_board = board.copy()
        sim_board[best_move[0], best_move[1]] = 1
        # Handle captures
        for dr, dc in NEIGHBORS:
            nr, nc = best_move[0] + dr, best_move[1] + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and sim_board[nr, nc] == 2:
                 _, opp_libs = get_group_liberties(nr, nc, sim_board)
                 if len(opp_libs) == 0:
                    g, _ = get_group_liberties(nr, nc, sim_board)
                    for gr, gc in g: sim_board[gr, gc] = 0
        PREV_BOARD_BYTES = sim_board.tobytes()
        
        return (best_move[0] + 1, best_move[1] + 1)
    
    return (0, 0) # Pass
