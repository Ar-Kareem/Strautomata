
def policy(me, opp, color):
    from typing import List, Tuple, Set
    
    # Setup
    my_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opp)
    forward: int = 1 if color == 'w' else -1
    goal_row: int = 0 if color == 'b' else 7
    
    # Move categories
    winning_moves: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
    capture_moves: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
    forward_moves: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
    
    # Generate all legal moves
    for r, c in me:
        # Straight forward
        r2 = r + forward
        if 0 <= r2 < 8:
            pos = (r2, c)
            if pos not in my_set and pos not in opp_set:
                move = ((r, c), pos)
                if r2 == goal_row:
                    winning_moves.append(move)
                else:
                    forward_moves.append(move)
        
        # Diagonals
        for dc in (-1, 1):
            c2 = c + dc
            r2 = r + forward
            if 0 <= r2 < 8 and 0 <= c2 < 8:
                pos = (r2, c2)
                move = ((r, c), pos)
                if pos in opp_set:  # Capture
                    if r2 == goal_row:
                        winning_moves.append(move)
                    else:
                        capture_moves.append(move)
                elif pos not in my_set:  # Empty diagonal move
                    forward_moves.append(move)
    
    # Priority order
    all_moves = winning_moves or capture_moves + forward_moves
    
    if not all_moves:
        # Emergency fallback (shouldn't occur in valid game)
        return ((me[0][0], me[0][1]), (me[0][0] + forward, me[0][1]))
    
    # Immediate win
    if winning_moves:
        return winning_moves[0]
    
    # Score non-winning moves
    best_move = all_moves[0]
    best_score = float('-inf')
    
    for move in all_moves:
        _, to_pos = move
        tr, tc = to_pos
        
        # Score: advancement + capture + position
        score = 100 - abs(tr - goal_row)  # Closer to goal
        
        if move in capture_moves:
            score += 200  # Strong capture bonus
        
        # Center column bonus
        score += max(0, 3 - abs(tc - 3.5)) * 20
        
        # Penalize moving from back rank
        from_r = move[0][0]
        if (color == 'w' and from_r == 0) or (color == 'b' and from_r == 7):
            score -= 30
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
