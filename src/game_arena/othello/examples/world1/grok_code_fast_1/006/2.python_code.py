
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    def get_legal(me, opp):
        directions = [(dr, dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1] if dr != 0 or dc != 0]
        legal = []
        for r in range(8):
            for c in range(8):
                if me[r, c] != 0 or opp[r, c] != 0:
                    continue
                is_valid = False
                for dr, dc in directions:
                    cr, cc = r + dr, c + dc
                    found_opp = False
                    while 0 <= cr < 8 and 0 <= cc < 8:
                        if opp[cr, cc] == 1:
                            found_opp = True
                        elif me[cr, cc] == 1:
                            if found_opp:
                                is_valid = True
                                break
                            else:
                                break
                        else:
                            break
                        cr += dr
                        cc += dc
                    if is_valid:
                        break
                if is_valid:
                    legal.append((r, c))
        return legal

    def simulate_place(me, opp, r, c):
        directions = [(dr, dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1] if dr != 0 or dc != 0]
        me_new = me.copy()
        opp_new = opp.copy()
        me_new[r, c] = 1
        for dr, dc in directions:
            cr, cc = r + dr, c + dc
            to_flip = []
            while 0 <= cr < 8 and 0 <= cc < 8:
                if opp_new[cr, cc] == 1:
                    to_flip.append((cr, cc))
                elif me_new[cr, cc] == 1:
                    if to_flip:
                        for fr, fc in to_flip:
                            me_new[fr, fc] = 1
                            opp_new[fr, fc] = 0
                    break
                else:
                    break
                cr += dr
                cc += dc
        return me_new, opp_new

    weights = np.zeros((8, 8))
    # Corners are highly valued
    for pos in [(0, 0), (0, 7), (7, 0), (7, 7)]:
        weights[pos] = 100
    # Edges (excluding corners) are moderately valued
    for i in range(1, 7):
        weights[i, 0] = 20  # Left edge
        weights[0, i] = 20  # Top edge
        weights[7, i] = 20  # Bottom edge
        weights[i, 7] = 20  # Right edge

    legal_moves = get_legal(you, opponent)
    if not legal_moves:
        return "pass"
    
    best_move = None
    best_score = float('-inf')
    
    for r, c in legal_moves:
        me_new, opp_new = simulate_place(you, opponent, r, c)
        my_mobility = len(get_legal(me_new, opp_new))
        opp_mobility = len(get_legal(opp_new, me_new))
        positional_score = np.sum(me_new * weights) - np.sum(opp_new * weights)
        total_score = positional_score + my_mobility - opp_mobility
        if total_score > best_score:
            best_score = total_score
            best_move = (r, c)
    
    # Convert to algebraic notation
    row, col = best_move
    move_str = chr(ord('a') + col) + str(row + 1)
    return move_str
