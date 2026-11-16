
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Directions for white (row+) and black (row-)
    direction = 1 if color == 'w' else -1
    goal_row = 7 if color == 'w' else 0
    opp_set = set(opp)
    me_set = set(me)
    
    legal_moves = []
    
    for r, c in me:
        # Possible forward targets
        for dc in [-1, 0, 1]:
            nr, nc = r + direction, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7:
                # Capture rules (Diagonal only)
                if dc != 0:
                    if (nr, nc) in opp_set:
                        legal_moves.append(((r, c), (nr, nc)))
                    elif (nr, nc) not in me_set:
                        legal_moves.append(((r, c), (nr, nc)))
                else:
                    # Straight move (Target must be empty)
                    if (nr, nc) not in opp_set and (nr, nc) not in me_set:
                        legal_moves.append(((r, c), (nr, nc)))

    # 1. Check for immediate win
    for move in legal_moves:
        if move[1][0] == goal_row:
            return move

    # 2. Heuristic Scoring
    best_score = -float('inf')
    best_moves = []

    for move in legal_moves:
        (fr, fc), (tr, tc) = move
        score = 0
        
        # Priority: Capturing pieces
        is_capture = (tr, tc) in opp_set
        if is_capture:
            score += 15
        
        # Priority: Distance to goal (Advanced pieces)
        dist_advanced = tr if color == 'w' else (7 - tr)
        score += dist_advanced * 2
        
        # Penalty: Moving into a square where it can be captured by opponent
        # Check if any opponent piece can move to (tr, tc) diagonally next turn
        vulnerable = False
        opp_direction = -1 if color == 'w' else 1
        for odc in [-1, 1]:
            onr, onc = tr - opp_direction, tc + odc # Source of opponent
            if (onr, onc) in opp_set:
                vulnerable = True
                break
        
        if vulnerable:
            # Only risky if not a capture or not a trade
            if not is_capture:
                score -= 10
            else:
                score -= 2 # Small penalty for trading

        # Priority: Support (is there a friendly piece behind to recapture?)
        supported = False
        for sdc in [-1, 1]:
            snr, snc = tr - direction, tc + sdc
            if (snr, snc) in me_set and (snr, snc) != (fr, fc):
                supported = True
                break
        if supported:
            score += 3

        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    if not best_moves:
        return random.choice(legal_moves)
    
    return random.choice(best_moves)
