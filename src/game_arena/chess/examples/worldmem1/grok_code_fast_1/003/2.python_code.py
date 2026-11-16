
import random
import re

VAL = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

def find_to_sq(move):
    stripped = move.rstrip('=# +*')  # Adjust for possible annotations
    # Find the last occurrence of [a-h][1-8]
    m = re.search(r'([a-h][1-8])(?!.*[a-h][1-8])', stripped)
    if m:
        return m.group(1)
    return None

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    current_mat = sum(VAL[p[1]] * (1 if p[0] == 'w' else -1) for p in pieces.values())
    
    ## Prioritize checkmate moves
    mate_moves = [mv for mv in legal_moves if '#' in mv]
    if mate_moves:
        action = random.choice(mate_moves)
        return action, memory
    
    ## Evaluate other moves by static material delta
    move_scores = []
    for mv in legal_moves:
        to_sq = find_to_sq(mv)
        if not to_sq:
            continue
        is_capture = 'x' in mv
        is_promotion = '=' in mv
        is_check = '+' in mv and '#' not in mv
        captured_value = 0
        promotion_bonus = 0
        check_bonus = 0
        if is_capture and to_sq in pieces:
            captured_piece = pieces[to_sq]
            if captured_piece[0] != to_play[0]:
                captured_value = VAL[captured_piece[1]] * (1 if to_play == 'white' else -1)
        if is_promotion:
            prom_char = mv[mv.index('=') + 1]
            if prom_char in VAL:
                promotion_bonus = (VAL[prom_char] - 1) * (1 if to_play == 'white' else -1)
        if is_check:
            check_bonus = 0.5 * (1 if to_play == 'white' else -1)
        delta = captured_value + promotion_bonus + check_bonus
        new_mat = current_mat + delta
        move_scores.append((mv, new_mat))
    
    if not move_scores:
        action = random.choice(legal_moves)
    else:
        if to_play == 'white':
            best_mv = max(move_scores, key=lambda x: x[1])[0]
        else:
            best_mv = min(move_scores, key=lambda x: x[1])[0]
        action = best_mv
    
    return action, memory
