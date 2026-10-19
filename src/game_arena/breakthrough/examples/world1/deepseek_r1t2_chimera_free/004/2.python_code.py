
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    direction = 1 if color == 'w' else -1
    legal_moves = []
    
    # Generate all legal moves
    for (r, c) in me:
        # Forward move
        nr, nc = r + direction, c
        if 0 <= nr <= 7 and 0 <= nc <= 7:
            if (nr, nc) not in occupied:
                legal_moves.append(((r, c), (nr, nc)))
        # Diagonal left move
        nr, nc = r + direction, c - 1
        if 0 <= nr <= 7 and 0 <= nc <= 7:
            if (nr, nc) not in me_set:
                legal_moves.append(((r, c), (nr, nc)))
        # Diagonal right move
        nr, nc = r + direction, c + 1
        if 0 <= nr <= 7 and 0 <= nc <= 7:
            if (nr, nc) not in me_set:
                legal_moves.append(((r, c), (nr, nc)))
    
    # Check for immediate winning moves
    winning_moves = []
    for move in legal_moves:
        to_r, _ = move[1]
        if (color == 'w' and to_r == 7) or (color == 'b' and to_r == 0):
            winning_moves.append(move)
    if winning_moves:
        return random.choice(winning_moves)
    
    # Evaluate non-winning moves
    def is_vulnerable(pos):
        r, c = pos
        if color == 'w':
            threats = [(r + 1, c - 1), (r + 1, c + 1)]
        else:
            threats = [(r - 1, c - 1), (r - 1, c + 1)]
        return any(threat in opp_set for threat in threats)
    
    best_score = -float('inf')
    best_moves = []
    
    for move in legal_moves:
        (_, to_pos) = move
        to_r, to_c = to_pos
        is_capture = to_pos in opp_set
        progress = to_r if color == 'w' else (7 - to_r)
        center_score = 3.5 - abs(to_c - 3.5)  # Max 3.5 at center columns
        
        score = 0
        if is_capture:
            score += 1000
        score += progress * 100
        score += center_score * 50
        
        if is_vulnerable(to_pos):
            score -= 800
        
        # Update best moves
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    
    return random.choice(best_moves) if best_moves else legal_moves[0]
