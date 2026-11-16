
import copy

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine direction and home row based on color
    dr = -1 if color == 'b' else 1
    home = 0 if color == 'b' else 7
    
    # Convert lists to sets for fast lookups
    me_set = set(me)
    opp_set = set(opp)
    
    # Function to get positional value for a piece
    def pos_val(r):
        return 7 - r if color == 'b' else r
    
    # Generate all legal moves as list of (from, to, is_capture)
    moves = []
    for r, c in me:
        nr = r + dr
        if 0 <= nr < 8:
            # Straight forward if empty
            if (nr, c) not in me_set and (nr, c) not in opp_set:
                moves.append(((r, c), (nr, c), False))
            # Diagonals
            for dc in [-1, 1]:
                nc = c + dc
                if 0 <= nc < 8:
                    target = (nr, nc)
                    if target not in me_set:
                        is_capture = target in opp_set
                        moves.append(((r, c), target, is_capture))
    
    # Evaluate each move: simulate new positions and score
    best_move = None
    best_score = -float('inf')
    bonus_capture = 1  # Small bonus for captures
    for from_pos, to_pos, is_capture in moves:
        # Simulate new positions
        new_me = [p if p != from_pos else to_pos for p in me]
        new_opp = [p for p in opp if p != to_pos] if is_capture else opp
        
        # Score: sum of positional values for my pieces
        score = sum(pos_val(r) for r, _ in new_me)
        if is_capture:
            score += bonus_capture
        
        # Huge bonus if a piece reaches home and wins
        if to_pos[0] == home:
            score += 1000
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = (from_pos, to_pos)
    
    return best_move
