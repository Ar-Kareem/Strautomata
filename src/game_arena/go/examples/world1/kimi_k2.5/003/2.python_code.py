
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    import numpy as np
    
    # Initialize board: 0=empty, 1=me, 2=opponent
    board = np.zeros((19, 19), dtype=np.int8)
    for r, c in me:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r-1, c-1] = 1
    for r, c in opponent:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r-1, c-1] = 2
    
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Pre-analyze groups to find liberty counts, capture moves, and save moves
    visited = np.zeros((19, 19), dtype=bool)
    group_libs = {}  # (r,c) -> liberty count for that stone's group
    pos_to_rep = {}  # (r,c) -> group representative
    capture_moves = {}  # (r,c) -> number of stones captured
    save_moves = {}     # (r,c) -> number of stones saved
    
    for r in range(19):
        for c in range(19):
            if board[r, c] != 0 and not visited[r, c]:
                color = board[r, c]
                group = []
                libs = set()
                stack = [(r, c)]
                rep = (r, c)
                while stack:
                    cr, cc = stack.pop()
                    if visited[cr, cc]:
                        continue
                    visited[cr, cc] = True
                    group.append((cr, cc))
                    pos_to_rep[(cr, cc)] = rep
                    for dr, dc in dirs:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 19 and 0 <= nc < 19:
                            if board[nr, nc] == 0:
                                libs.add((nr, nc))
                            elif board[nr, nc] == color and not visited[nr, nc]:
                                stack.append((nr, nc))
                
                lib_count = len(libs)
                for pos in group:
                    group_libs[pos] = lib_count
                
                if lib_count == 1:
                    lib_pos = list(libs)[0]
                    if color == 2:  # Opponent group in atari
                        capture_moves[lib_pos] = capture_moves.get(lib_pos, 0) + len(group)
                    else:  # My group in atari
                        save_moves[lib_pos] = save_moves.get(lib_pos, 0) + len(group)
    
    # Priority 1: Capture opponent stones (biggest capture first)
    if capture_moves:
        best_move = max(capture_moves.items(), key=lambda x: x[1])[0]
        return (best_move[0] + 1, best_move[1] + 1)
    
    # Priority 2: Save my own stones in atari (largest group first)
    if save_moves:
        sorted_saves = sorted(save_moves.items(), key=lambda x: -x[1])
        for (r, c), _ in sorted_saves:
            # Verify move is legal (not suicide)
            board[r, c] = 1
            valid = False
            # Check adjacent empty
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    valid = True
                    break
            # Check capture
            if not valid:
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 2:
                        if group_libs.get((nr, nc), 1) == 1:
                            valid = True
                            break
            board[r, c] = 0
            if valid:
                return (r + 1, c + 1)
    
    # Priority 3: Heuristic search for best shape move
    best_score = -float('inf')
    best_move = (0, 0)  # Pass by default
    
    for r in range(19):
        for c in range(19):
            if board[r, c] != 0:
                continue
            
            # Check legality
            board[r, c] = 1
            valid = False
            
            # 1. Adjacent empty point?
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    valid = True
                    break
            
            # 2. Captures opponent?
            if not valid:
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 2:
                        if group_libs.get((nr, nc), 1) == 1:
                            valid = True
                            break
            
            # 3. Connects to safe friendly group (libs > 1)?
            if not valid:
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 1:
                        if group_libs.get((nr, nc), 0) > 1:
                            valid = True
                            break
            
            board[r, c] = 0
            if not valid:
                continue
            
            # Score this move
            score = 0
            
            # Count neighbors
            my_neighbors = 0
            opp_neighbors = 0
            empty_neighbors = 0
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19:
                    if board[nr, nc] == 1:
                        my_neighbors += 1
                    elif board[nr, nc] == 2:
                        opp_neighbors += 1
                    else:
                        empty_neighbors += 1
            
            # Connection bonuses
            score += my_neighbors * 10
            score += opp_neighbors * 6
            
            # Avoid self-atari (simple heuristic)
            if my_neighbors > 0 and empty_neighbors <= 1:
                score -= 40
            
            # Line preference (3rd line optimal for territory)
            dist_edge = min(r, 18 - r, c, 18 - c)
            if dist_edge == 0:
                score -= 20
            elif dist_edge == 1:
                score += 4
            elif dist_edge == 2:
                score += 8
            elif dist_edge == 3:
                score += 5
            
            # Star points bonus (4-4, 4-10, etc. at indices 3, 9, 15)
            if (r in [3, 9, 15] and c in [3, 9, 15]):
                score += 12
            
            # Center control
            score += (9 - abs(r - 9)) * 0.4 + (9 - abs(c - 9)) * 0.4
            
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    if best_move != (0, 0):
        return (best_move[0] + 1, best_move[1] + 1)
    return (0, 0)
