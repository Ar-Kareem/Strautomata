
import numpy as np

# Othello/Reversi smart policy with depth-limited alpha-beta search and strong heuristics.

DIRECTIONS = [(-1,-1), (-1,0), (-1,1),
              (0,-1),          (0,1),
              (1,-1),  (1,0),  (1,1)]

def _on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def _board_from_states(you: np.ndarray, opponent: np.ndarray):
    # 0 empty, 1 you, 2 opp
    b = np.zeros((8,8), dtype=np.int8)
    b[you == 1] = 1
    b[opponent == 1] = 2
    return b

def _legal_moves_and_flips(b, player_val):
    # player_val: 1 or 2 in b. opponent is the other.
    opp_val = 2 if player_val == 1 else 1
    legal = []
    flips_map = {}  # (r,c) -> list of (fr,fc) flipped
    empties = np.argwhere(b == 0)
    for r, c in empties:
        total_flips = []
        for dr, dc in DIRECTIONS:
            rr, cc = r + dr, c + dc
            line = []
            while _on_board(rr, cc) and b[rr, cc] == opp_val:
                line.append((rr, cc))
                rr += dr
                cc += dc
            if line and _on_board(rr, cc) and b[rr, cc] == player_val:
                total_flips.extend(line)
        if total_flips:
            legal.append((r, c))
            flips_map[(r, c)] = total_flips
    return legal, flips_map

def _apply_move(b, player_val, move, flips):
    # returns new board
    nb = b.copy()
    r, c = move
    opp_val = 2 if player_val == 1 else 1
    nb[r, c] = player_val
    for fr, fc in flips:
        nb[fr, fc] = player_val
    return nb

def _count_discs(b):
    return np.sum(b == 1), np.sum(b == 2)

def _is_corner(r, c):
    return (r == 0 or r == 7) and (c == 0 or c == 7)

def _corner_adjacents():
    # squares adjacent to corners (X-squares and C-squares patterns)
    # We'll treat the 8 adjacents to each corner.
    coords = set()
    for cr, cc in [(0,0), (0,7), (7,0), (7,7)]:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                rr, rc = cr + dr, cc + dc
                if 0 <= rr < 8 and 0 <= rc < 8:
                    coords.add((rr, rc))
    return coords

_CORNER_ADJ = _corner_adjacents()

def _evaluate(b, perspective_player_val):
    # Heuristic evaluation: higher is better for perspective_player_val.
    # Components: corner occupancy, mobility, near-corner penalty/bonus,
    # edge weights, and piece difference with late-game emphasis.
    me = perspective_player_val
    opp = 2 if me == 1 else 1

    me_count, opp_count = _count_discs(b)
    empty_count = 64 - me_count - opp_count

    # Corners
    corners = [(0,0), (0,7), (7,0), (7,7)]
    corner_score = 0
    corner_me = 0
    corner_opp = 0
    for r, c in corners:
        if b[r, c] == me:
            corner_score += 25
            corner_me += 1
        elif b[r, c] == opp:
            corner_score -= 25
            corner_opp += 1

    # Near-corner (adjacent squares) - strong avoidance unless corner is owned
    # If we don't own the corner, occupying adjacent is often bad.
    near_pen = 0
    for (r, c) in _CORNER_ADJ:
        if b[r, c] == me:
            # Determine which corner this is adjacent to
            # If that corner is ours, it's less bad; otherwise penalize.
            penal = 0
            for cr, cc in [(0,0), (0,7), (7,0), (7,7)]:
                if max(abs(r-cr), abs(c-cc)) == 1:  # adjacent (including diagonals)
                    if b[cr, cc] != me:
                        penal += 1
            # penalize based on number of corners not owned (usually 1-2)
            near_pen -= 8 * penal
        elif b[r, c] == opp:
            penal = 0
            for cr, cc in [(0,0), (0,7), (7,0), (7,7)]:
                if max(abs(r-cr), abs(c-cc)) == 1:
                    if b[cr, cc] != opp:
                        penal += 1
            near_pen += 8 * penal

    # Edge occupancy (light)
    edge_score = 0
    for i in range(8):
        for (r, c) in [(0,i),(7,i),(i,0),(i,7)]:
            if b[r,c] == me:
                edge_score += 2
            elif b[r,c] == opp:
                edge_score -= 2

    # Mobility
    my_legal, _ = _legal_moves_and_flips(b, me)
    opp_legal, _ = _legal_moves_and_flips(b, opp)
    mobility = 0
    if len(my_legal) + len(opp_legal) > 0:
        mobility = 3 * (len(my_legal) - len(opp_legal))

    # Piece difference with late-game emphasis
    # As board empties decrease, parity becomes more important.
    if empty_count <= 14:
        parity = 1.2 * (me_count - opp_count)
    else:
        parity = 0.25 * (me_count - opp_count)

    # Combine
    score = corner_score + near_pen + edge_score + mobility + parity
    return float(score)

def _alpha_beta(b, player_val, perspective_val, depth, alpha, beta):
    # Returns best value for perspective_val.
    legal, flips_map = _legal_moves_and_flips(b, player_val)
    opp_val = 2 if player_val == 1 else 1

    if depth == 0 or (not legal):
        # If no legal moves: if opponent has moves, pass turn; else terminal.
        if not legal:
            opp_legal, _ = _legal_moves_and_flips(b, opp_val)
            if not opp_legal:
                # Terminal: exact by disc difference
                me = perspective_val
                om = 2 if me == 1 else 1
                me_count, opp_count = _count_discs(b)
                # Large magnitude for decisive terminal
                diff = me_count - opp_count if me == 1 else opp_count - me_count
                return float(diff) * 1000.0
            # Pass
            return _alpha_beta(b, opp_val, perspective_val, depth-1, alpha, beta)
        return _evaluate(b, perspective_val)

    # Move ordering: corners first, then flips count
    def move_key(m):
        r, c = m
        base = 0
        if _is_corner(r,c):
            base += 1000
        # Avoid near-corner if corner not owned (ordering heuristic)
        if (r,c) in _CORNER_ADJ and not any(b[cr,cc] == player_val for (cr,cc) in [(0,0),(0,7),(7,0),(7,7)]):
            base -= 100
        base += len(flips_map[m])  # more flips often better early
        return -base  # for descending

    legal_sorted = sorted(legal, key=move_key)

    best_val = -1e18
    for m in legal_sorted:
        nb = _apply_move(b, player_val, m, flips_map[m])
        val = -_alpha_beta(nb, opp_val, perspective_val, depth-1, -beta, -alpha)
        if val > best_val:
            best_val = val
        alpha = max(alpha, val)
        if alpha >= beta:
            break
    return best_val

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    b = _board_from_states(you, opponent)
    my_val = 1
    opp_val = 2

    legal, flips_map = _legal_moves_and_flips(b, my_val)
    if not legal:
        return "pass"

    # Depth adapts to game stage: early fewer, late deeper.
    empty_count = np.sum(b == 0)
    if empty_count >= 40:
        depth = 3
    elif empty_count >= 24:
        depth = 3
    elif empty_count >= 10:
        depth = 4
    else:
        depth = 5  # near end, play deeper

    # Choose best move by searching
    alpha = -1e18
    beta = 1e18
    best_move = None
    best_score = -1e18

    # Order moves to improve pruning
    def order_key(m):
        r, c = m
        k = 0
        if _is_corner(r,c):
            k += 1e6
        if (r,c) in _CORNER_ADJ:
            # if corresponding corner not ours, deprioritize
            for cr, cc in [(0,0),(0,7),(7,0),(7,7)]:
                if max(abs(r-cr), abs(c-cc)) == 1 and b[cr, cc] != my_val:
                    k -= 2e5
        k += len(flips_map[m])
        return -k

    for m in sorted(legal, key=order_key):
        nb = _apply_move(b, my_val, m, flips_map[m])
        score = -_alpha_beta(nb, opp_val, my_val, depth-1, -beta, -alpha)
        if score > best_score:
            best_score = score
            best_move = m
        alpha = max(alpha, score)

    r, c = best_move
    move_str = f"{chr(ord('a') + c)}{r + 1}"
    return move_str
