
import numpy as np

def policy(me, opponent):
    board_size = 19
    board = np.zeros((board_size, board_size), dtype=int)
    
    # Populate board: 1 = Me, 2 = Opponent
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = 2
        
    # --- 1. Group Analysis ---
    # Identify connected components and their liberties
    visited = np.zeros((board_size, board_size), dtype=bool)
    groups = [] # List of dicts: {'color': int, 'stones': set, 'liberties': set}
    stone_to_group = {} # Map (r, c) -> index in groups
    
    for r in range(board_size):
        for c in range(board_size):
            if board[r, c] != 0 and not visited[r, c]:
                color = board[r, c]
                stones = set()
                liberties = set()
                queue = [(r, c)]
                visited[r, c] = True
                
                # BFS to find group
                while queue:
                    cr, cc = queue.pop(0)
                    stones.add((cr, cc))
                    
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < board_size and 0 <= nc < board_size:
                            if board[nr, nc] == 0:
                                liberties.add((nr, nc))
                            elif board[nr, nc] == color and not visited[nr, nc]:
                                visited[nr, nc] = True
                                queue.append((nr, nc))
                
                idx = len(groups)
                groups.append({'color': color, 'stones': stones, 'liberties': liberties})
                for s in stones:
                    stone_to_group[s] = idx

    # --- 2. Tactical Move Generation ---
    candidates = [] # List of (score, move_tuple)
    
    # Find groups in Atari
    my_atari = [i for i, g in enumerate(groups) if g['color'] == 1 and len(g['liberties']) == 1]
    opp_atari = [i for i, g in enumerate(groups) if g['color'] == 2 and len(g['liberties']) == 1]
    
    # A. Capture Opponent (High Priority)
    for idx in opp_atari:
        g = groups[idx]
        move = list(g['liberties'])[0]
        # Score: 10000 base + 100 per stone captured
        score = 10000 + len(g['stones']) * 100
        candidates.append((score, move))
        
    # B. Save Own Groups (Critical Priority)
    for idx in my_atari:
        g = groups[idx]
        last_liberty = list(g['liberties'])[0]
        
        # Strategy B1: Capture the attacker (Counter-Atari)
        # Check adjacent opponent groups to see if they are also in atari
        adj_opp_groups = set()
        for sr, sc in g['stones']:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = sr + dr, sc + dc
                if 0 <= nr < board_size and 0 <= nc < board_size:
                    if board[nr, nc] == 2:
                        adj_opp_groups.add(stone_to_group[(nr, nc)])
        
        capture_save_found = False
        for opp_idx in adj_opp_groups:
            og = groups[opp_idx]
            if len(og['liberties']) == 1:
                move = list(og['liberties'])[0]
                # High score: Saving own stones by capturing is better than simple capture
                score = 20000 
                candidates.append((score, move))
                capture_save_found = True
        
        # Strategy B2: Extend (Run)
        # If we can't capture the attacker, try to add liberties
        if not capture_save_found:
            # Find empty spots adjacent to our group that add liberties
            potential_extensions = set()
            for sr, sc in g['stones']:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = sr + dr, sc + dc
                    if 0 <= nr < board_size and 0 <= nc < board_size:
                        if board[nr, nc] == 0 and (nr, nc) != last_liberty:
                            potential_extensions.add((nr, nc))
            
            for move in potential_extensions:
                # Check if this extension actually gains liberties
                # Heuristic: Does the new spot have empty neighbors?
                r, c = move
                gain = 0
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < board_size and 0 <= nc < board_size:
                        if board[nr, nc] == 0 and (nr, nc) != last_liberty:
                            gain += 1
                
                if gain > 0:
                    score = 15000 + gain * 10 # High priority save
                    candidates.append((score, move))

    # If we have tactical candidates, pick the best one
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_move = candidates[0][1]
        return (best_move[0] + 1, best_move[1] + 1)
        
    # --- 3. Default Policy (Heuristic Placement) ---
    # No urgent moves. Pick a move based on simple shape/influence.
    legal_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if board[r, c] == 0:
                # Basic Legality Check (Suicide)
                # Move is valid if:
                # 1. Has empty neighbor OR
                # 2. Captures opponent stone OR
                # 3. Connects to friendly stone (and isn't simple suicide)
                
                has_liberty = False
                captures = False
                connects = False
                is_eye = True # Assume eye initially
                
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < board_size and 0 <= nc < board_size:
                        val = board[nr, nc]
                        if val == 0:
                            has_liberty = True
                            is_eye = False
                        elif val == 2:
                            is_eye = False
                            # Check capture
                            adj_idx = stone_to_group.get((nr, nc))
                            if adj_idx is not None and len(groups[adj_idx]['liberties']) == 1:
                                captures = True
                        elif val == 1:
                            connects = True
                    else:
                        pass # Wall
                
                # Logic for Eye detection: surrounded by own stones or wall
                if has_liberty or captures:
                    is_eye = False
                
                if has_liberty or captures or (connects and not is_eye):
                    score = 0
                    # Heuristic: Prefer center
                    dist_center = abs(r - 9) + abs(c - 9)
                    score -= dist_center
                    
                    # Heuristic: Prefer connecting or extending
                    if connects: score += 5
                    
                    # Heuristic: Penalty for filling obvious eyes
                    if is_eye: score -= 1000
                    
                    legal_moves.append((score, (r, c)))
                    
    if legal_moves:
        legal_moves.sort(key=lambda x: x[0], reverse=True)
        move = legal_moves[0][1]
        return (move[0] + 1, move[1] + 1)
        
    return (0, 0)
