
def policy(state: list[list[object]], role: str) -> str:
    # Precompute neighbors for 4x4 grid
    neighbors = {}
    for r in range(1, 5):
        for c in range(1, 5):
            neigh = []
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 4 and 1 <= nc <= 4:
                    neigh.append((nr, nc))
            neighbors[(r, c)] = neigh
    
    # Parse state
    my_marks = set()
    opp_marks = set()
    empty = set()
    
    for prop in state:
        if len(prop) >= 4 and prop[0] == "cell":
            r, c, content = int(prop[1]), int(prop[2]), prop[3]
            pos = (r, c)
            if content == role:
                my_marks.add(pos)
            elif content == "b":
                empty.add(pos)
            else:
                opp_marks.add(pos)
    
    # Helper to check if a cell is safe for a given set of marks
    def is_safe(cell, marks):
        for n in neighbors[cell]:
            if n in marks:
                return False
        return True
    
    # Find my safe moves
    my_safe = [cell for cell in empty if is_safe(cell, my_marks)]
    
    # If no safe moves, must make a losing move (any empty cell)
    if not my_safe:
        if empty:
            cell = next(iter(empty))
            return f"mark({cell[0]},{cell[1]})"
        return "mark(1,1)"  # Should not reach here
    
    # Check for immediate win: move that leaves opponent with no safe moves
    for move in my_safe:
        remaining = empty - {move}
        opp_has_safe = any(is_safe(cell, opp_marks) for cell in remaining)
        if not opp_has_safe:
            return f"mark({move[0]},{move[1]})"
    
    # Filter moves that don't let opponent win immediately
    good_moves = []
    for move in my_safe:
        remaining = empty - {move}
        opp_can_win = False
        # Check if opponent has a move that leaves me with no safe moves
        for opp_move in remaining:
            if not is_safe(opp_move, opp_marks):
                continue
            after_opp = remaining - {opp_move}
            my_future_marks = my_marks | {move}
            i_have_safe = any(is_safe(cell, my_future_marks) for cell in after_opp)
            if not i_have_safe:
                opp_can_win = True
                break
        if not opp_can_win:
            good_moves.append(move)
    
    # If all moves lead to opponent win, use all safe moves
    candidates = good_moves if good_moves else my_safe
    
    # Heuristic: maximize (my_mobility - opp_mobility)
    best_move = candidates[0]
    best_score = -1000
    
    for move in candidates:
        remaining = empty - {move}
        my_future = my_marks | {move}
        
        my_mobility = sum(1 for cell in remaining if is_safe(cell, my_future))
        opp_mobility = sum(1 for cell in remaining if is_safe(cell, opp_marks))
        
        score = my_mobility - opp_mobility
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"mark({best_move[0]},{best_move[1]})"
